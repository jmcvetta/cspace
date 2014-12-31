from time import time
from socket import error as sock_error
from ncrypt.rand import bytes as rand_bytes
from nitro.tcp import TCPStream
from nitro.tcpbridge import TCPBridge
from cspace.util.rpc import RPCConnection

ROUTER_IDLE_TIMEOUT = 30*60

class RouterState( object ) :
    def __init__( self ) :
        self.handlers = {}
        self.registered = {}
        self.connecting = {}
        self.bridgeInitiators = {}
        self.bridges = {}

def startBridge( sock1, sock2, reactor, routerState ) :
    bridge = TCPBridge( sock1, sock2, reactor )
    routerState.bridges[bridge] = 1
    def onClose() :
        del routerState.bridges[bridge]
    bridge.setCloseCallback( onClose )

class BridgeInitiator( object ) :
    def __init__( self, sock1, pendingWrite1, sock2, pendingWrite2, reactor, routerState ) :
        self.reactor = reactor
        self.streams = []
        self._initStream( sock1, pendingWrite1 )
        self._initStream( sock2, pendingWrite2 )
        self.written = 0
        self.routerState = routerState
        self.routerState.bridgeInitiators[self] = 1

    def _initStream( self, sock, pendingWrite ) :
        assert pendingWrite
        stream = TCPStream( sock, self.reactor )
        self.streams.append( stream )
        stream.setCloseCallback( self.close )
        stream.setErrorCallback( lambda e,m : self.close() )
        stream.setWriteCompleteCallback( self._onWritten )
        stream.writeData( pendingWrite )

    def close( self ) :
        for s in self.streams : s.close()
        del self.stream[:]
        del self.routerState.bridgeInitiators[self]

    def _onWritten( self ) :
        self.written += 1
        if self.written < 2 : return
        socks = [s.getSock() for s in self.streams]
        for s in self.streams : s.shutdown()
        del self.streams[:]
        del self.routerState.bridgeInitiators[self]
        startBridge( socks[0], socks[1], self.reactor, self.routerState )

class RouterServerHandler( object ) :
    (INITIAL,REGISTERED,CONNECTING,CLOSED) = range(4)
    def __init__( self, sock, reactor, routerState ) :
        self.rpcConn = RPCConnection( sock, reactor )
        self.reactor = reactor
        self.routerState = routerState
        self.rpcConn.setCloseCallback( self.close )
        self.rpcConn.setRequestCallback( self._onRequest )
        self.requestTable = {}
        for msg in 'Ping Register Connect Accept'.split() :
            self.requestTable[msg] = getattr( self, '_do%s' % msg )
        self.routerState.handlers[self] = 1
        self.state = self.INITIAL
        self._lastActiveTime = time()

    def close( self ) :
        self.rpcConn.close()
        del self.routerState.handlers[self]
        if self.state == self.REGISTERED :
            del self.routerState.registered[self.routerId]
        elif self.state == self.CONNECTING :
            del self.routerState.connecting[self.connectionId]
        self.state = self.CLOSED

    def lastActiveTime( self ) :
        return self._lastActiveTime

    def sendIncoming( self, connectionId ) :
        assert self.state == self.REGISTERED
        self.rpcConn.oneway( connectionId )

    def _onRequest( self, payload, ctx ) :
        self._lastActiveTime = time()
        try :
            assert type(payload) is list
            assert len(payload) >= 1
            msg = payload.pop( 0 )
            assert type(msg) is str
            handler = self.requestTable.get( msg )
            assert handler is not None
        except :
            ctx.response( [-1] )
            return
        handler( payload, ctx )

    def _doPing( self, args, ctx ) :
        try :
            peerAddr = self.rpcConn.getSock().getpeername()
        except sock_error :
            ctx.response( [-1] )
            return
        ctx.response( (0,peerAddr) )

    def _doRegister( self, args, ctx ) :
        try :
            assert self.state == self.INITIAL
            assert len(args) == 0
        except :
            ctx.response( (-1,'') )
            return
        while True :
            routerId = rand_bytes( 20 )
            if routerId not in self.routerState.registered : break
        self.routerId = routerId
        self.state = self.REGISTERED
        self.routerState.registered[routerId] = self
        ctx.response( (0,self.routerId) )

    def _doConnect( self, args, ctx ) :
        try :
            assert self.state == self.INITIAL
            assert len(args) == 1
            routerId = args[0]
            assert type(routerId) is str
            handler = self.routerState.registered.get( routerId )
            assert handler is not None
        except :
            ctx.response( [-1] )
            return
        while True :
            connectionId = rand_bytes( 20 )
            if connectionId not in self.routerState.connecting : break
        self.connectionId = connectionId
        self.connectCtx = ctx
        self.state = self.CONNECTING
        self.routerState.connecting[connectionId] = self
        handler.sendIncoming( connectionId )

    def finishConnect( self ) :
        assert self.state == self.CONNECTING
        self.connectCtx.response( [0] )
        del self.routerState.connecting[self.connectionId]
        del self.routerState.handlers[self]
        sock = self.rpcConn.getSock()
        pendingWrite = self.rpcConn.getPendingWrite()
        self.rpcConn.shutdown()
        self.state = self.CLOSED
        return (sock,pendingWrite)

    def _doAccept( self, args, ctx ) :
        try :
            assert self.state == self.INITIAL
            assert len(args) == 1
            connectionId = args[0]
            assert type(connectionId) is str
            handler = self.routerState.connecting.get( connectionId )
            assert handler is not None
        except :
            ctx.response( [-1] )
            return
        sock1,pendingWrite1 = handler.finishConnect()
        ctx.response( [0] )
        del self.routerState.handlers[self]
        sock2 = self.rpcConn.getSock()
        pendingWrite2 = self.rpcConn.getPendingWrite()
        self.rpcConn.shutdown()
        self.state = self.CLOSED
        BridgeInitiator( sock1, pendingWrite1, sock2, pendingWrite2, self.reactor, self.routerState )

class Router( object ) :
    def __init__( self, listener, reactor ) :
        self.listener = listener
        self.reactor = reactor
        self.listener.setCallback( self._onIncoming )
        self.listener.enable( True )
        self.routerState = RouterState()
        self.timerOp = reactor.addTimer( ROUTER_IDLE_TIMEOUT/2, self._onTimer )

    def close( self ) :
        for handler in self.routerState.handlers.keys() :
            handler.close()
        for initiator in self.routerState.bridgeInitiators.keys() :
            initiator.close()
        for bridge in self.routerState.bridges.keys() :
            bridge.close()
        self.routerState.bridges.clear()
        self.listener.close()
        self.listener = None
        self.timerOp.cancel()
        self.timerOp = None

    def _onIncoming( self, sock ) :
        RouterServerHandler( sock, self.reactor, self.routerState )

    def _onTimer( self ) :
        curTime = time()
        for bridge in self.routerState.bridges.keys() :
            idleTime = curTime - bridge.lastActiveTime()
            if idleTime > ROUTER_IDLE_TIMEOUT :
                bridge.close()
                del self.routerState.bridges[bridge]
        for handler in self.routerState.handlers.keys() :
            idleTime = curTime - handler.lastActiveTime()
            if idleTime > ROUTER_IDLE_TIMEOUT :
                handler.close()
