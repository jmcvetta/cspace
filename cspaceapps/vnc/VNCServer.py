import os, sys, threading, logging
from PyQt4 import QtCore, QtGui
from nitro.selectreactor import SelectReactor
from nitro.qt4reactor import Qt4Reactor
from nitro.tcp import tcpConnect, tcpListen
from nitro.tcpbridge import TCPBridge
from cspace.util.spawn import spawnProcess
from cspace.util.queue import ThreadQueue
from cspaceapps.appletutil import CSpaceEnv, CSpaceAcceptor, \
        initializeLogFile
import cspaceapps.images_rc

vncServerPath = 'CSpaceWinVNC.exe'
#vncServerPath = r'D:\projects\CSpaceApps\vnc_winsrc\CSpaceWinVNC.exe'

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
        self.setWindowTitle( '%s - VNC Server' % env.displayName )
        self.setText( 'Connecting to CSpace...' )
        tcpConnect( ('127.0.0.1',env.port), self.reactor,
                self._onCSpaceConnect )

    def _onCSpaceConnect( self, connector ) :
        if connector.getError() != 0 :
            self.setText( 'Unable to connect to CSpace' )
            return
        CSpaceAcceptor( connector.getSock(), env.connectionId, self.reactor,
                self._onAccept )
        self.setText( 'Accepting connection from %s' % env.displayName )

    def _onAccept( self, err, sock ) :
        if err < 0 :
            self.setText( 'Error in accepting connection from %s' % env.displayName )
            return
        self.peerSock = sock
        self.setText( 'Waiting for VNC Server to connect...' )
        self.listener = tcpListen( ('127.0.0.1',0), self.reactor, self._onIncoming )
        listenPort = self.listener.getSock().getsockname()[1]
        vncServer = os.path.join( os.path.split(sys.argv[0])[0], vncServerPath )
        args = [vncServer]
        environ = dict( os.environ.items() )
        environ['VNC_SERVER_PORT'] = str(listenPort)
        startingDir = os.path.split( vncServer )[0]
        result = spawnProcess( vncServer, args, environ, startingDir, 0 )
        if not result :
            self.peerSock.close()
            self.listener.close()
            self.setText( 'Error starting vnc server: %s' % vncServer )
            return

    def _onIncoming( self, sock ) :
        self.listener.close()
        self.notifyThreadQueue = ThreadQueue( self._onMessage, self.reactor )
        msg = (sock,self.peerSock,self.notifyThreadQueue)
        self.bridgeThread = BridgeThread()
        self.bridgeThread.threadQueue.postMessage( msg )
        self.setText( 'VNC connected from %s' % env.displayName )

    def _onMessage( self, msg ) :
        self.setText( 'Disconnected' )

def main() :
    initializeLogFile( 'VNCServer.log' )
    logging.getLogger().addHandler( logging.StreamHandler() )
    global env
    env = CSpaceEnv()
    assert env.isIncoming
    app = QtGui.QApplication( sys.argv )
    reactor = Qt4Reactor()
    mw = MainWindow( reactor )
    mw.resize( 250, 50 )
    mw.show()
    app.exec_()

if __name__ == '__main__' :
    main()
