import os, sys, logging

from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import SIGNAL, QString
from PyQt4.QtGui import QWidget, QFileDialog, QMessageBox, QApplication

from nitro.qt4reactor import Qt4Reactor
from nitro.tcp import tcpConnect
from cspace.util.flashwin import FlashWindow
from cspace.util.rpc import RPCConnection, RPCStub
from cspace.util.delaygc import initdelaygc, delaygc
from cspace.main.common import localSettings
from cspaceapps.appletutil import CSpaceEnv, CSpaceAcceptor, \
        initializeLogFile
import cspaceapps.images_rc
from cspaceapps.filetransfer.fileclient import FileClient, FileFetcher
from cspaceapps.filetransfer.Ui_FileReceiverWindow import Ui_FileReceiverWindow

class FileReceiverWindow( QWidget, FlashWindow ) :
    def __init__( self, reactor ) :
        QWidget.__init__( self )
        FlashWindow.__init__( self, reactor )
        self.ui = Ui_FileReceiverWindow()
        self.ui.setupUi( self )
        self.reactor = reactor
        self.setWindowTitle( env.displayName + ' - ' + str(self.windowTitle()) )
        self.connect( self.ui.acceptButton, SIGNAL('clicked()'), self._onAcceptFiles )
        self.connect( self.ui.cancelButton, SIGNAL('clicked()'), self.close )
        tcpConnect( ('127.0.0.1',env.port), self.reactor, self._onConnect )
        self._setStatus( 'Connecting to CSpace...' )
        self.disconnected = False

    def _setStatus( self, text, isError=False ) :
        lines = text.split( '\n' )
        text = '<b>%s</b>' % '<br/>'.join(lines)
        if isError :
            text = '<font color=red>%s</font>' % text
        self.ui.status.setText( text )

    def _setError( self, text ) :
        self._setStatus( text, True )
        self.ui.cancelButton.setText( '&Close' )

    def _onConnect( self, connector ) :
        if connector.getError() != 0 :
            self._setError( 'Error connecting to CSpace.' )
            return
        sock = connector.getSock()
        self._setStatus( 'Accepting connection from %s.' % env.displayName )
        CSpaceAcceptor( sock, env.connectionId, self.reactor, self._onAccept )

    def _onAccept( self, err, sock ) :
        if err < 0 :
            self._setError( 'Error accepting connection from %s.' % env.displayName )
            return
        self.rpcConn = RPCConnection( sock, self.reactor )
        self.fileClient = FileClient( self.rpcConn )
        self._setStatus( 'Fetching file list from %s...' % env.displayName )
        self.fileClient.callList( '/', self._onList )

    def _onList( self, err, result ) :
        if err != 0 :
            self._setError( 'Error fetching file list from %s.' % env.displayName )
            return
        self.files = []
        for x in result :
            if not x.endswith('/') :
                self.files.append( x )
                self.ui.fileList.addItem( x )
        self._setStatus( ('%s is sending the following files.\n' % env.displayName ) + 
                'Would you like to accept?' )
        self.ui.acceptButton.setEnabled( True )
        self.rpcConn.setCloseCallback( self._onClose )
        self.flash()

    def _onClose( self ) :
        self.disconnected = True
        self._setError( 'Disconnected.' )
        self.ui.acceptButton.setEnabled( False )

    def _chooseTargetDir( self ) :
        defaultDir = os.path.expanduser( '~/Desktop' )
        if not os.path.isdir(defaultDir) :
            defaultDir = QString()
        dir = localSettings().getString( 'Settings/FileReceiverSaveDir' )
        if (not dir) or (not os.path.isdir(dir)) :
            dir = defaultDir
        while True :
            dir = QFileDialog.getExistingDirectory( self, 'Choose directory to save the file(s)',
                    dir )
            if dir.isEmpty() : return None
            dir = str(dir)
            existing = []
            for f in self.files :
                if os.path.exists(os.path.join(dir,f)) : existing.append(f)
            if not existing : break
            msg = 'The following file(s) already exist in\n%s.\nWould you like to overwrite?\n%s' % (dir,'\n'.join(existing))
            result = QMessageBox.question( self, 'Overwrite Prompt', msg, QMessageBox.Yes, QMessageBox.No, QMessageBox.Cancel|QMessageBox.Escape )
            if result == QMessageBox.Yes : break
            if result == QMessageBox.No : continue
            assert result == QMessageBox.Cancel
            return None
        localSettings().setString( 'Settings/FileReceiverSaveDir', dir )
        return dir

    def _onAcceptFiles( self ) :
        self.ui.acceptButton.setEnabled( False )
        targetDir = self._chooseTargetDir()
        if self.disconnected : return
        if not targetDir :
            self.ui.acceptButton.setEnabled( True )
            return
        self.targetDir = targetDir
        self.curFileId = 0
        self.rpcConn.setCloseCallback( None )
        self.statusStub = RPCStub( self.rpcConn, 'TransferStatus' )
        self._doTransfer()

    def _doTransfer( self ) :
        if self.curFileId >= len(self.files) :
            self._setStatus( 'Completed.' )
            self.ui.cancelButton.setText( '&Close' )
            self.rpcConn.close( deferred=True )
            return
        fname = self.files[self.curFileId]
        self.curFileId += 1
        self._setStatus( 'Receiving file(%d/%d): %s'
                % (self.curFileId,len(self.files),fname) )
        remotePath = '/' + fname
        localPath = os.path.join( self.targetDir, fname )
        try :
            self.fetcher = FileFetcher( self.fileClient,
                    remotePath, localPath, self._onTransfer )
        except (OSError, IOError), e :
            self._setError( 'Error saving file: %s' % localPath )
            return

    def _onTransfer( self, transferred, fullSize ) :
        fname = self.files[self.curFileId-1]
        if transferred < 0 :
            self._setError( 'Error fetching file: %s' % fname )
            return
        self.statusStub.oneway( (self.curFileId,len(self.files),transferred,fullSize) )
        if transferred == fullSize :
            self._doTransfer()
            return
        percent = transferred * 100 / fullSize
        self._setStatus( 'Receiving file(%d/%d): %s (%d%%)'
                % (self.curFileId,len(self.files),fname,percent) )

    def closeEvent( self, ev ) :
        self.cancelFlash()
        ev.accept()
        delaygc( self )

def main() :
    initializeLogFile( 'FileReceiver.log' )
    logging.getLogger().addHandler( logging.StreamHandler() )
    global env
    env = CSpaceEnv()
    assert env.isIncoming
    app = QApplication( sys.argv )
    reactor = Qt4Reactor()
    initdelaygc( reactor )
    frw = FileReceiverWindow( reactor )
    frw.show()
    app.exec_()

if __name__ == '__main__' :
    main()
