import os, sys, stat, logging
from types import ListType, IntType

from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import SIGNAL
from PyQt4.QtGui import QApplication, QWidget, QListWidgetItem, QAbstractItemView, QFileDialog

from nitro.qt4reactor import Qt4Reactor
from nitro.tcp import tcpConnect
from cspace.util.rpc import RPCConnection, RPCSwitchboard
from cspace.util.delaygc import initdelaygc, delaygc
from cspace.main.common import localSettings
from cspaceapps.appletutil import CSpaceEnv, CSpaceConnector, \
        initializeLogFile
import cspaceapps.images_rc
from cspaceapps.filetransfer.fileserver import BaseFS, FSError, FileServer
from cspaceapps.filetransfer.Ui_FileSenderWindow import Ui_FileSenderWindow

class FlatFS( BaseFS ) :
    def __init__( self, fileList ) :
        self.fileList = []
        self.files = {}
        lowercase = {}
        for f in fileList :
            fname = os.path.split(f)[1]
            lfname = fname.lower()
            if lfname in lowercase : continue
            lowercase[lfname] = 1
            self.fileList.append( fname )
            self.files[fname] = (f,self._getSize(f))

    def _getSize( self, f ) :
        try :
            statres = os.stat( f )
            return statres[stat.ST_SIZE]
        except OSError :
            return -1

    def list( self, pathList ) :
        if '/'.join(pathList) != '' : raise FSError
        return self.fileList

    def getSize( self, pathList ) :
        fname = '/'.join( pathList )
        info = self.files.get( fname, None )
        if info is None : raise FSError
        if info[1] < 0 : raise FSError
        return info[1]

    def read( self, pathList, offset, size ) :
        fname = '/'.join( pathList )
        info = self.files.get( fname, None )
        if info is None : raise FSError
        if info[1] < 0 : raise FSError
        f = None
        try :
            f = file( info[0], 'rb' )
            f.seek( offset )
            data = f.read( size )
            f.close()
            return data
        except (OSError,IOError), e :
            if f : f.close()
            raise FSError, e

class FileSenderWindow( QWidget ) :
    SELECTINGFILES = 0
    CONNECTINGCSPACE = 1
    CONNECTINGUSER = 2
    OFFERINGFILES = 3
    def __init__( self, reactor ) :
        QWidget.__init__( self )
        self.ui = Ui_FileSenderWindow()
        self.ui.setupUi( self )
        self.reactor = reactor
        self._setStatus( 'Drag and drop files to be sent...' )
        self.setWindowTitle( env.contactName + ' - ' + str(self.windowTitle()) )
        self.setAcceptDrops( True )
        self.files = {}
        self.fileItems = {}
        self.connect( self.ui.fileList, SIGNAL('itemSelectionChanged()'), self._onFileSelectionChanged )
        self.connect( self.ui.addFilesButton, SIGNAL('clicked()'), self._onAddClicked )
        self.connect( self.ui.removeFilesButton, SIGNAL('clicked()'), self._onRemoveClicked )
        self.connect( self.ui.removeAllButton, SIGNAL('clicked()'), self._onRemoveAllClicked )
        self.connect( self.ui.sendFilesButton, SIGNAL('clicked()'), self._onSendFilesClicked )
        self.connect( self.ui.closeButton, SIGNAL('clicked()'), self.close )
        self.state = self.SELECTINGFILES

    def _setStatus( self, text, isError=False ) :
        lines = text.split( '\n' )
        text = '<b>%s</b>' % '<br>'.join(lines)
        if isError :
            text = '<font color=red>%s</font>' % text
        self.ui.status.setText( text )

    def _setError( self, text ) :
        self._setStatus( text, True )

    def _removeFile( self, item ) :
        info = self.fileItems.pop( item )
        self.ui.fileList.takeItem( self.ui.fileList.row(item) )
        fname = os.path.split( info[0] )[1]
        del self.files[fname.lower()]
        if not self.files :
            self.ui.sendFilesButton.setEnabled( False )
            self.ui.removeAllButton.setEnabled( False )

    def _addFile( self, f ) :
        if not os.path.isfile(f) : return False
        fname = os.path.split(f)[1]
        k = fname.lower()
        info = self.files.get( k, None )
        if info is not None :
            self._removeFile( info[1] )
        item = QListWidgetItem( fname, self.ui.fileList )
        info = [f,item]
        self.files[k] = info
        self.fileItems[item] = info
        self.ui.sendFilesButton.setEnabled( True )
        self.ui.removeAllButton.setEnabled( True )

    def _onFileSelectionChanged( self ) :
        if self.state != self.SELECTINGFILES : return
        selectCount = 0
        for item in self.fileItems.keys() :
            if self.ui.fileList.isItemSelected(item) :
                selectCount += 1
        self.ui.removeFilesButton.setEnabled( selectCount > 0 )

    def dragEnterEvent( self, ev ) :
        if self.state != self.SELECTINGFILES :
            return
        mimeData = ev.mimeData()
        if mimeData.hasUrls() :
            isLocal = True
            for url in mimeData.urls() :
                if url.toLocalFile().isEmpty() :
                    isLocal = False
            if isLocal :
                ev.acceptProposedAction()

    def dropEvent( self, ev ) :
        if self.state != self.SELECTINGFILES : return
        mimeData = ev.mimeData()
        if mimeData.hasUrls() :
            for url in mimeData.urls() :
                f = url.toLocalFile()
                if not f.isEmpty() :
                    self._addFile( str(f) )
            self._onFileSelectionChanged()
            ev.acceptProposedAction()

    def _onAddClicked( self ) :
        defaultDir = os.path.expanduser( '~/Desktop' )
        if not os.path.isdir(defaultDir) :
            defaultDir = ''
        openDir = localSettings().getString( 'Settings/FileSenderOpenDir' )
        if (not openDir) or (not os.path.isdir(openDir)) :
            openDir = defaultDir
        fileList = QFileDialog.getOpenFileNames( self, 'Select file(s) to add...', openDir )
        for f in fileList :
            self._addFile( str(f) )
        if len(fileList) :
            openDir = os.path.split( str(fileList[0]) )[0]
            localSettings().setString( 'Settings/FileSenderOpenDir', openDir )
        self._onFileSelectionChanged()

    def _onRemoveClicked( self ) :
        selItems = [ i for i in self.fileItems.keys() if self.ui.fileList.isItemSelected(i) ]
        for item in selItems :
            self._removeFile( item )
        self._onFileSelectionChanged()

    def _onRemoveAllClicked( self ) :
        for item in self.fileItems.keys() :
            self._removeFile( item )
        self._onFileSelectionChanged()

    def _onSendFilesClicked( self ) :
        self.setAcceptDrops( False )
        self.ui.fileList.clearSelection()
        self.ui.fileList.setSelectionMode( QAbstractItemView.NoSelection )
        self.ui.addFilesButton.setEnabled( False )
        self.ui.removeFilesButton.setEnabled( False )
        self.ui.removeAllButton.setEnabled( False )
        self.ui.sendFilesButton.setEnabled( False )
        self._doConnect()

    def _doConnect( self ) :
        def onConnect( connector ) :
            self.connectOp = None
            if connector.getError() != 0 :
                self._setError( 'Unable to connect to CSpace.' )
                return
            self._doConnectUser( connector.getSock() )
        self.connectOp = tcpConnect( ('127.0.0.1',env.port), self.reactor, onConnect )
        self._setStatus( 'Connecting to CSpace...' )
        self.state = self.CONNECTINGCSPACE

    def _doConnectUser( self, sock ) :
        self._setStatus( 'Connecting to %s...' % env.contactName )
        self.state = self.CONNECTINGUSER
        def onConnect( err, sock ) :
            if err < 0 :
                self._setError( 'Error connecting to %s.' % env.contactName )
                return
            self._doOfferFiles( sock )
        connector = CSpaceConnector( sock, env.contactName, 'FileTransfer',
                self.reactor, onConnect )
        self.connectOp = connector.getOp()

    def _doOfferFiles( self, sock ) :
        self._setStatus( 'Sending request ...' )
        self.state = self.OFFERINGFILES
        fileList = []
        for row in range(self.ui.fileList.count()) :
            item = self.ui.fileList.item( row )
            fileList.append( self.fileItems[item][0] )
        self.rpcConn = RPCConnection( sock, self.reactor )
        self.switchboard = RPCSwitchboard( self.rpcConn )
        self.fs = FlatFS( fileList )
        self.fileServer = FileServer( self.fs, self.switchboard )

        pending = {}
        for i,f in enumerate(fileList) :
            pending[os.path.split(f)[1].lower()] = i
        def onClose() :
            if pending :
                self._setError( 'Disconnected.' )
            else :
                self._setStatus( 'Completed.' )
        def onTransferStatus( payload ) :
            if type(payload) is not ListType : return
            if len(payload) != 4 : return
            for x in payload :
                if type(x) is not IntType : return
                if x < 0 : return
            fileId,numFiles,transferred,fileSize = payload
            if numFiles != len(fileList) : return
            if not (1 <= fileId <= numFiles) : return
            if transferred > fileSize : return
            fname = os.path.split(fileList[fileId-1])[1]
            lfname = fname.lower()
            pos = pending.get( lfname, None )
            if pos is None : return
            if transferred == fileSize :
                percent = 100
                del pending[lfname]
            else :
                percent = transferred*100 / fileSize
            self._setStatus( 'Sending file (%d/%d): %s (%d%%)'
                    % (pos+1,len(fileList),fname,percent) )
        self.switchboard.addOnewayAgent( 'TransferStatus', onTransferStatus )
        self.rpcConn.setCloseCallback( onClose )

    def closeEvent( self, ev ) :
        ev.accept()
        delaygc( self )

def main() :
    initializeLogFile( 'FileSender.log' )
    logging.getLogger().addHandler( logging.StreamHandler() )
    global env
    env = CSpaceEnv()
    assert env.isContactAction
    app = QApplication( sys.argv )
    reactor = Qt4Reactor()
    initdelaygc( reactor )
    fsw = FileSenderWindow( reactor )
    fsw.show()
    app.exec_()

if __name__ == '__main__' :
    main()
