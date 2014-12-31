import os, sys, threading, logging
from PyQt4 import QtCore, QtGui
from nitro.selectreactor import SelectReactor
from nitro.qt4reactor import Qt4Reactor
from nitro.tcp import tcpConnect, tcpListen
from nitro.tcpbridge import TCPBridge
from cspace.util.spawn import spawnProcess
from cspace.util.queue import ThreadQueue
from cspaceapps.appletutil import CSpaceEnv, CSpaceConnector, \
        initializeLogFile
import cspaceapps.images_rc

if sys.platform == 'win32' :
    vncViewerPath = 'CSpaceVNCViewer.exe'
    vncViewerType = 'realvnc'
else :
    _viewers = ( ('realvnc', '/usr/bin/vncviewer'), ('tightvnc', '/usr/bin/xtightvncviewer') )
    vncViewerType, vncViewerPath = None, None
    for n, b in _viewers :
        if os.path.isfile( b ) :
            vncViewerType = n
            vncViewerPath = b
            break

class BridgeThread( threading.Thread ) :
    def __init__( self ) :
        threading.Thread.__init__( self )
        self.setDaemon( True )
        self.reactor = SelectReactor()
        self.threadQueue = ThreadQueue( self._onMessage, self.reactor )
        self.start()

    def _onMessage( self, msg ) :
        sock1,sock2,notifytq = msg
        bridge = TCPBridge( sock1, sock2, self.reactor )
        bridge.setCloseCallback( lambda : notifytq.postMessage(True) )

    def run( self ) :
        self.reactor.run()

class MainWindow( QtGui.QLabel ) :
    def __init__( self, reactor ) :
        QtGui.QLabel.__init__( self )
        self.reactor = reactor
        self.setAlignment( QtCore.Qt.AlignCenter )
        self.setWindowIcon( QtGui.QIcon(':/images/cspace32.png') )
        self.setWindowTitle( '%s - VNC Client' % env.contactName )
        self.setText( 'Connecting to CSpace...' )
        self.connectOp = tcpConnect( ('127.0.0.1',env.port), self.reactor, self._onConnect )

    def _onConnect( self, connector ) :
        self.connectOp = None
        if connector.getError() != 0 :
            self.setText( 'Unable to connect to CSpace' )
            return
        self.setText( 'Connecting to %s...' % env.contactName )
        userConnector = CSpaceConnector( connector.getSock(), env.contactName,
                'RemoteDesktop', self.reactor, self._onConnectUser )
        self.userConnectOp = userConnector.getOp()

    def _onConnectUser( self, err, sock ) :
        self.userConnectOp = None
        if err < 0 :
            self.setText( 'Error connecting to %s' % env.contactName )
            return
        self.setText( 'Connected to %s' % env.contactName )
        self.connectedSock = sock
        self.listener = tcpListen( ('127.0.0.1',0), self.reactor, self._onIncoming )
        listenPort = self.listener.getSock().getsockname()[1]
        vncViewer = os.path.join( os.path.split(sys.argv[0])[0], vncViewerPath )
        if vncViewerType == 'tightvnc' :
            args = [vncViewer, '127.0.0.1::%d' % listenPort ]
        elif vncViewerType == 'realvnc' :
            if sys.platform == 'win32' :
                args = [vncViewer, 'AutoReconnect=0', '127.0.0.1:%d' % listenPort ]
            else :
                args = [vncViewer, '127.0.0.1:%d' % listenPort ]
        else :
            raise RuntimeError, "No suitable vnc viewer found"
        startingDir = os.path.split( vncViewer )[0]
        result = spawnProcess( vncViewer, args, os.environ, startingDir, 0 )
        if not result :
            self.connectedSock.close()
            self.listener.close()
            self.setText( 'Error starting vncviewer: %s' % vncViewer )
            return

    def _onIncoming( self, sock ) :
        self.listener.close()
        self.notifyThreadQueue = ThreadQueue( self._onMessage, self.reactor )
        msg = (sock,self.connectedSock,self.notifyThreadQueue)
        self.bridgeThread = BridgeThread()
        self.bridgeThread.threadQueue.postMessage( msg )
        self.setText( 'VNC Connected to %s' % env.contactName )

    def _onMessage( self, msg ) :
        self.setText( 'Disconnected' )

def main() :
    initializeLogFile( 'VNCClient.log' )
    logging.getLogger().addHandler( logging.StreamHandler() )
    global env
    env = CSpaceEnv()
    assert env.isContactAction
    app = QtGui.QApplication( sys.argv )
    reactor = Qt4Reactor()
    mw = MainWindow( reactor )
    mw.resize( 250, 50 )
    mw.show()
    app.exec_()

if __name__ == '__main__' :
    main()
