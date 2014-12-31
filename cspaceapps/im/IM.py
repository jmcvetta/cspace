import os, sys, logging, time
from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import Qt, QObject, QEvent, SIGNAL, SLOT
from PyQt4.QtGui import QApplication, QMessageBox, QWidget, QKeyEvent
from nitro.async import AsyncOp
from nitro.qt4reactor import Qt4Reactor
from nitro.tcp import tcpConnect
from nitro.linestream import TCPLineStream
from cspace.util.flashwin import FlashWindow
from cspace.util.wordcode import wordEncode, wordDecode, WordDecodeError
from cspace.util.delaygc import initdelaygc, delaygc
from cspaceapps.appletutil import CSpaceEnv, initializeLogFile
import cspaceapps.images_rc
from cspaceapps.im.Ui_IMWindow import Ui_IMWindow

class IMInitializer( object ) :
    CONNECTING = 0
    GETTINGKEY = 1
    NOTIFYING = 2
    REGISTERING = 3
    REGISTERED = 4
    CLOSED = 5
    def __init__( self, reactor, callback=None ) :
        assert env.isContactAction or env.isIncoming
        self.reactor = reactor
        self.op = AsyncOp( callback, self._doCancel )
        self.state = self.CONNECTING
        self.connectOp = tcpConnect( ('127.0.0.1',env.port), self.reactor, self._onConnect )
        self.stream = None

    def getOp( self ) : return self.op

    def _doCancel( self ) :
        if self.connectOp : self.connectOp.cancel()
        if self.stream : self.stream.close( deferred=True )
        self.state = self.CLOSED

    def _onConnect( self, connector ) :
        self.connectOp = None
        if connector.getError() != 0 :
            self.op.notify( -1, None )
            return
        self.stream = TCPLineStream( connector.getSock(), self.reactor )
        self.stream.setCloseCallback( self._onClose )
        self.stream.setErrorCallback( self._onError )
        self.stream.setInputCallback( self._onInput )
        self.stream.enableRead( True )
        if env.isContactAction :
            self.stream.writeData( 'GETPUBKEY %s\r\n' % env.contactName )
        else :
            self.stream.writeData( 'GETINCOMINGPUBKEY %s\r\n' % env.connectionId )
        self.state = self.GETTINGKEY

    def _onClose( self ) :
        self._doCancel()
        self.op.notify( -1, None )

    def _onError( self, err, errMsg ) :
        self._onClose()

    def _onInput( self, line ) :
        if self.state == self.GETTINGKEY :
            if not line.startswith('OK') :
                self._doCancel()
                self.op.notify( -1, None )
                return
            self.pubKey = line.split()[1]
            self.state = self.REGISTERING
            self.listenerName = 'CSpaceIM-%s' % self.pubKey
            self.stream.writeData( 'REGISTERLISTENER %s\r\n' % self.listenerName )
        elif self.state == self.REGISTERING :
            if not line.startswith('OK') :
                self.state = self.NOTIFYING
                if env.isContactAction :
                    msg = 'CONTACTACTION'
                else :
                    msg = 'INCOMING %s' % env.connectionId
                self.stream.writeData( 'SENDLISTENER %s %s\r\n' %
                        (self.listenerName,msg) )
                return
            self.state = self.REGISTERED
            self.stream.setCloseCallback( None )
            self.stream.setErrorCallback( None )
            self.stream.setInputCallback( None )
            self.op.notify( 1, self )
        elif self.state == self.NOTIFYING :
            if not line.startswith('OK') :
                self._doCancel()
                self.op.notify( -1, None )
                return
            self._doCancel()
            self.op.notify( 0, self )
        else :
            assert False

class IMConnection( object ) :
    INITIAL = 0
    CONNECTING = 1
    ACCEPTING = 2
    CONNECTED = 3
    CLOSED = 4
    def __init__( self, reactor ) :
        self.reactor = reactor
        self.closeCallback = None
        self.inputCallback = None
        self.state = self.INITIAL
        self.connectOp = None
        self.stream = None

    def setCloseCallback( self, closeCallback ) :
        self.closeCallback = closeCallback

    def setInputCallback( self, inputCallback ) :
        self.inputCallback = inputCallback

    def shutdown( self, notify=False ) :
        if self.state == self.CLOSED : return
        if self.connectOp : self.connectOp.cancel()
        if self.stream : self.stream.close( deferred=True )
        self.state = self.CLOSED
        if notify and self.closeCallback : self.closeCallback()

    def connectTo( self, peerPubKey, callback=None ) :
        assert self.state == self.INITIAL
        self.connectCallback = callback
        self.state = self.CONNECTING
        self.peerPubKey = peerPubKey
        self.connectOp = tcpConnect( ('127.0.0.1',env.port), self.reactor, self._onConnect )

    def acceptConnection( self, connectionId, callback=None ) :
        assert self.state == self.INITIAL
        self.connectCallback = callback
        self.state = self.ACCEPTING
        self.connectionId = connectionId
        self.connectOp = tcpConnect( ('127.0.0.1',env.port), self.reactor, self._onConnect )

    def writeLine( self, line ) :
        self.stream.writeData( line + '\r\n' )

    def _onConnect( self, connector ) :
        self.connectOp = None
        if connector.getError() != 0 :
            self.shutdown( notity=True )
            return
        self.stream = TCPLineStream( connector.getSock(), self.reactor )
        self.stream.setCloseCallback( self._onClose )
        self.stream.setErrorCallback( self._onError )
        self.stream.setInputCallback( self._onInput )
        self.stream.enableRead( True )
        if self.state == self.CONNECTING :
            self.stream.writeData( 'CONNECTPUBKEY %s TextChat\r\n' % self.peerPubKey )
        else :
           assert self.state == self.ACCEPTING
           self.stream.writeData( 'ACCEPT %s\r\n' % self.connectionId )

    def _onClose( self ) :
        self.shutdown( notify=True )

    def _onError( self, err, errMsg ) :
        self._onClose()

    def _onInput( self, line ) :
        if self.state in (self.CONNECTING,self.ACCEPTING) :
            if not line.startswith('OK') :
                self.shutdown( notify=True )
                return
            self.state = self.CONNECTED
            if self.connectCallback : self.connectCallback()
            return
        elif self.state == self.CONNECTED :
            self.inputCallback( line )
        else :
            self.shutdown( notify=True )

class IMWindow( QWidget, FlashWindow ) :
    def __init__( self, peerName, peerPubKey, listenerStream, reactor ) :
        QWidget.__init__( self )
        FlashWindow.__init__( self, reactor )
        self.ui = Ui_IMWindow()
        self.ui.setupUi( self )
        self.peerName = peerName
        self.peerPubKey = peerPubKey
        self.listenerStream = listenerStream
        self.reactor = reactor
        self.listenerStream.setCloseCallback( self._onListenerClose )
        self.listenerStream.setErrorCallback( self._onListenerError )
        self.listenerStream.setInputCallback( self._onListenerInput )
        self.connect( self.ui.chatInputEdit, SIGNAL('textChanged()'), self._onChatInputChanged )
        self.baseTitle = self.peerName + ' - ' + str(self.windowTitle())
        self.setWindowTitle( self.baseTitle )
        self.connecting = []
        self.connected = []
        self.pendingMessages = []
        self.lastSentTyping = False
        self.lastSentTypingTime = 0
        self.lastReceivedTyping = False
        self.lastReceivedTypingTime = 0
        self.timerOp = self.reactor.addTimer( 1, self._updateTypingStatus )
        self.ui.chatLogView.installEventFilter( self )
        self.ui.chatInputEdit.installEventFilter( self )

    def shutdown( self ) :
        self.listenerStream.close()
        for conn in self.connecting+self.connected : conn.shutdown()
        del self.connecting[:]
        del self.connected[:]
        self.ui.chatInputEdit.setReadOnly( True )
        self.setWindowTitle( 'DISCONNECTED: ' + self.baseTitle )
        self.timerOp.cancel()
        self.timerOp = None
        if self.isHidden() : self.close()

    def _onListenerClose( self ) :
        self.shutdown()

    def _onListenerError( self, err, errMsg ) :
        self._onListenerClose()

    def _onListenerInput( self, line ) :
        words = line.split()
        if len(words) < 2 : return
        if words[0].lower() != 'msg' : return
        words = words[1:]
        cmd,args = words[0].lower(),words[1:]
        if cmd == 'contactaction' :
            if len(args) != 0 : return
            self._onContactAction()
        elif cmd == 'incoming' :
            if len(args) != 1 : return
            connectionId = args[0]
            self._onIncoming( connectionId )

    def _onContactAction( self ) :
        if self.isHidden() : self.show()
        if self.isMinimized() : self.showNormal()
        self.activateWindow()
        if self.connecting or self.connected : return
        conn = IMConnection( self.reactor )
        conn.setCloseCallback( lambda : self._onConnClose(conn) )
        conn.setInputCallback( lambda line : self._onConnInput(conn,line) )
        conn.connectTo( self.peerPubKey, lambda : self._onConnected(conn) )
        self.connecting.append( conn )
        self.ui.statusLabel.setText( 'Connecting...' )

    def _onIncoming( self, connectionId ) :
        conn = IMConnection( self.reactor )
        conn.setCloseCallback( lambda : self._onConnClose(conn) )
        conn.setInputCallback( lambda line : self._onConnInput(conn,line) )
        conn.acceptConnection( connectionId, lambda : self._onConnected(conn) )
        self.connecting.append( conn )
        self.ui.statusLabel.setText( 'Receiving connection...' )

    def _onConnClose( self, conn ) :
        if conn in self.connecting :
            self.connecting.remove( conn )
            self.ui.statusLabel.setText( 'Connection failed' )
        else :
            assert conn in self.connected
            self.connected.remove( conn )
            #self.ui.statusLabel.setText( 'Connection closed.' )
            self.ui.statusLabel.setText( '' )
        if (not self.connecting) and (not self.connected) and self.isHidden() :
            self.shutdown()

    def _onConnected( self, conn ) :
        assert conn in self.connecting
        self.connecting.remove( conn )
        self.connected.append( conn )
        self.ui.statusLabel.setText( 'Connected.' )
        if self.pendingMessages :
            assert len(self.connected) == 1
            for msg in self.pendingMessages :
                conn.writeLine( 'msg %s' % wordEncode(msg) )
            del self.pendingMessages[:]

    def _onConnInput( self, conn, line ) :
        words = line.split()
        if len(words) == 0 : return
        cmd = words[0].lower()
        if cmd == 'msg' :
            if len(words) != 2 : return
            try :
                msg = wordDecode( words[1] )
            except WordDecodeError :
                return
            if self.isHidden() : self.show()
            self._chatMessage( msg, self.peerName )
            self.lastReceivedTyping = False
            self._updateTypingStatus()
        elif cmd == 'typing' :
            if len(words) != 1 : return
            self.lastReceivedTyping = True
            self.lastReceivedTypingTime = time.time()
            self._updateTypingStatus()

    def _updateTypingStatus( self ) :
        if not self.connected : return
        typing = self.lastReceivedTyping
        if (time.time() - self.lastReceivedTypingTime) > 5 :
            typing = False
        if typing :
            status = '%s is typing...' % self.peerName
        else :
            status = ''
        self.ui.statusLabel.setText( status )

    def _onChatInputEnter( self ) :
        msg = unicode(self.ui.chatInputEdit.toPlainText()).encode('utf8')
        self.ui.chatInputEdit.clear()
        if msg.endswith('\n') : msg = msg[:-1]
        if msg.endswith('\r') : msg = msg[:-1]
        if not msg : return
        self._chatMessage( msg, env.user )
        self.lastSentTyping = False
        if not self.connected :
            self.pendingMessages.append( msg )
            self._onContactAction()
            return
        for conn in self.connected :
            conn.writeLine( 'msg %s' % wordEncode(msg) )

    def _onChatInputChanged( self ) :
        curTime = time.time()
        if self.lastSentTyping and (curTime - self.lastSentTypingTime < 2) :
            return
        self.lastSentTyping = True
        self.lastSentTypingTime = curTime
        for conn in self.connected :
            conn.writeLine( 'typing' )

    def eventFilter( self, obj, event ) :
        if event.type() == QEvent.FocusIn :
            if obj is self.ui.chatLogView :
                if event.reason() == Qt.ActiveWindowFocusReason :
                    self.ui.chatInputEdit.setFocus()
        if event.type() == QEvent.KeyPress :
            if obj is self.ui.chatInputEdit :
                if event.key() in (Qt.Key_Enter,Qt.Key_Return) :
                    if event.modifiers() & Qt.ShiftModifier :
                        pass
                    elif event.modifiers() & Qt.ControlModifier :
                        # QTextEdit inserts <br/> with Ctrl+Enter, and a new
                        # <p> element with Shift+Enter. There seem to be some
                        # rendering issues with <br/>, so convert all Ctrl+Enter
                        # keys to Shift+Enter.
                        mod = event.modifiers() & (~Qt.ControlModifier)
                        mod = mod | Qt.ShiftModifier
                        newEvent = QKeyEvent( event.type(), event.key(), mod,
                                event.text(), event.isAutoRepeat(), event.count() )
                        QApplication.sendEvent( self.ui.chatInputEdit, newEvent )
                        return True
                    else :
                        self._onChatInputEnter()
                        return True
        return False

    def _chatMessage( self, msg, fromUser ) :
        msg = unicode( msg, 'utf8', 'replace' )
        msg = unicode( Qt.escape(msg) )
        msg = msg.replace( '\r\n', '<br/>' )
        msg = msg.replace( '\n', '<br/>' )
        msg = msg.replace( '\t', '    ' )
        msg = msg.replace( '  ', ' &nbsp;' )
        color = (fromUser == self.peerName) and '#FF821C' or 'black'
        self.ui.chatLogView.append( u'<font face="Verdana" size=-1 color="%s"><b>%s: </b></font>%s' % (color,fromUser,msg) )
        self.flash()

    def closeEvent( self, ev ) :
        self.cancelFlash()
        ev.accept()
        delaygc( self )

def _onInitialize( err, initializer ) :
    if err == 1 :
        peerName = env.displayName
        peerPubKey = initializer.pubKey
        listenerStream = initializer.stream
        imw = IMWindow( peerName, peerPubKey, listenerStream, reactor )
        if env.isContactAction :
            imw._onContactAction()
        elif env.isIncoming :
            imw._onIncoming( env.connectionId )
    elif err == 0 :
        QApplication.exit()
    else :
        QMessageBox.critical( None, 'Error', 'Error initializing CSpace IM' )
        QApplication.exit()

def main() :
    initializeLogFile( 'IM.log' )
    logging.getLogger().addHandler( logging.StreamHandler() )
    global env, app, reactor
    env = CSpaceEnv()
    app = QApplication( sys.argv )
    reactor = Qt4Reactor()
    initdelaygc( reactor )
    IMInitializer( reactor, _onInitialize )
    app.exec_()

if __name__ == '__main__' :
    main()
