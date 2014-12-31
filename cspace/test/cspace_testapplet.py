import os, sys
from qt import *

from nitro.qtreactor import QtReactor
from nitro.tcp import tcpConnect
from nitro.linestream import TCPLineStream

cspacePort = os.environ['CSPACE_PORT']
cspaceUser = os.environ['CSPACE_USER']
cspaceEvent = os.environ['CSPACE_EVENT']
if cspaceEvent == 'CONTACTACTION' :
    cspaceContactNickName = os.environ['CSPACE_CONTACTNICKNAME']
    cspaceActionDir = os.environ['CSPACE_ACTIONDIR']
    cspaceAction = os.environ['CSPACE_ACTION']
elif cspaceEvent == 'INCOMING' :
    cspaceService = os.environ['CSPACE_SERVICE']
    cspaceConnectionId = os.environ['CSPACE_CONNECTIONID']
    cspacePeerNickName = os.environ['CSPACE_PEERNICKNAME']

class MainWindow( QVBox ) :
    CONNECTING = 0
    CONNECTED = 1
    CLOSED = 2
    def __init__( self, parent, reactor ) :
        QVBox.__init__( self, parent )
        self.reactor = reactor
        self.setCaption( 'CSpace Test Applet' )
        self.chatOutputView = QTextEdit( self )
        self.chatOutputView.setReadOnly( True )
        self.chatInputEdit = QLineEdit( self )
        self.chatInputEdit.setFocus()
        self.state = self.CONNECTING
        self.chatInputEdit.setEnabled( False )
        self.isClient = (cspaceEvent == 'CONTACTACTION')
        self.chatOutputView.append( self.isClient and
            'Connecting to %s...' % cspaceContactNickName or
            'Accepting connection from %s' % cspacePeerNickName )
        addr = ('127.0.0.1',int(cspacePort))
        self.tcpConnectOp = tcpConnect( addr, self.reactor, self._onTCPConnect )
        self.stream = None

    def _onTCPConnect( self, connector ) :
        self.tcpConnectOp = None
        if connector.getError() != 0 :
            self.chatOutputView.append( 'ERROR' )
            return
        self.sock = connector.getSock()
        self.stream = TCPLineStream( self.sock, self.reactor )
        self.stream.setCloseCallback( self._onClose )
        self.stream.setErrorCallback( self._onError )
        self.stream.setInputCallback( self._onInput )
        self.stream.enableRead( True )
        if self.isClient :
            self.stream.writeData( 'CONNECT %s test\r\n' % cspaceContactNickName )
        else :
            self.stream.writeData( 'ACCEPT %s\r\n' % cspaceConnectionId )

    def shutdown( self ) :
        if self.tcpConnectOp : self.tcpConnectOp.cancel()
        if self.stream : self.stream.close()
        self.state = self.CLOSED

    def _onClose( self ) :
        self.chatOutputView.append( 'Connection closed' )
        self.shutdown()

    def _onError( self, err, errMsg ) :
        self.chatOutputView.append( 'Connection error(%d): %s' % (err,errMsg) )
        self.shutdown()

    def _onInput( self, line ) :
        if self.state == self.CONNECTING :
            if line.startswith('ERROR') :
                self.chatOutputView.append( 'Connection failed' )
                return
            if line.startswith('OK') :
                self.chatOutputView.append( 'Connected' )
                self.state = self.CONNECTED
                self.chatInputEdit.setEnabled( True )
                self.chatInputEdit.setFocus()
                self.connect( self.chatInputEdit, SIGNAL('returnPressed()'), self._onChatInputReturnPressed )
        elif self.state == self.CONNECTED :
            line = line.strip()
            self.chatOutputView.append( line )

    def _onChatInputReturnPressed( self ) :
        if self.state != self.CONNECTED : return
        s = str(self.chatInputEdit.text()).strip()
        if not s : return
        self.chatOutputView.append( s )
        self.stream.writeData( s + '\r\n' )
        self.chatInputEdit.clear()

def main() :
    global app, reactor
    app = QApplication( sys.argv )
    reactor = QtReactor()
    mw = MainWindow( None, reactor )
    mw.show()
    app.setMainWidget( mw )
    app.exec_loop()

if __name__ == '__main__' :
    main()
