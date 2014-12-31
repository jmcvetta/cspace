from nitro.async import AsyncOp
from nitro.tcp import tcpConnect, TCPCloser, TCPStream

class Dummy : pass

def _writeAndClose( sock, data, reactor, callback=None ) :
    def doCancel() :
        closerOp.cancel()
        sock.close()
    def onCloserDone() :
        op.notify()
    closerOp = TCPCloser( sock, data, reactor, onCloserDone ).getOp()
    op = AsyncOp( callback, doCancel )
    return op

class FirewallTestServer( object ) :
    def __init__( self, tcpListener, token, reactor ) :
        self.tcpListener = tcpListener
        self.token = token
        self.reactor = reactor
        tcpListener.enable( True )
        tcpListener.setCallback( self._onIncoming )
        self.connOps = set()

    def close( self ) :
        for connOp in self.connOps :
            connOp.cancel()
        self.connOps.clear()
        self.tcpListener.enable( False )
        self.tcpListener.setCallback( None )

    def _onIncoming( self, sock ) :
        def onComplete() :
            self.connOps.remove( connOp )
        connOp = _writeAndClose( sock, self.token, self.reactor,
                onComplete )
        self.connOps.add( connOp )

def firewallTestClient( addr, reactor, callback=None ) :
    obj = Dummy()
    def doCancel() :
        if obj.connectOp :
            obj.connectOp.cancel()
            obj.connectOp = None
        if obj.stream :
            obj.stream.close()
            obj.stream = None
        if obj.timerOp :
            obj.timerOp.cancel()
            obj.timerOp = None
    def doNotify() :
        doCancel()
        if obj.data :
            op.notify( 0, obj.data )
        else :
            op.notify( -1, '' )
    def onClose( *args ) :
        doNotify()
    def onInput( data ) :
        obj.data += data
        if len(obj.data) > 100 :
            obj.data = ''
            doNotify()
            return
    def onTimer() :
        obj.timerOp = None
        doNotify()
    def onConnect( connector ) :
        obj.connectOp = None
        if connector.getError() != 0 :
            doNotify()
            return
        sock = connector.getSock()
        obj.stream = TCPStream( sock, reactor )
        obj.stream.setCloseCallback( onClose )
        obj.stream.setErrorCallback( onClose )
        obj.stream.setInputCallback( onInput )
        obj.stream.initiateRead( 100 )
    obj.connectOp = tcpConnect( addr, reactor, onConnect )
    obj.timerOp = reactor.callLater( 15, onTimer )
    obj.stream = None
    obj.data = ''
    op = AsyncOp( callback, doCancel )
    return op
