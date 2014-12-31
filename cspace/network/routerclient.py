from nitro.async import AsyncOp
from nitro.tcp import tcpConnect
from cspace.util.validate import validateInetAddress
from cspace.util.rpc import RPCConnection

class Dummy : pass

def _doRPCCall( rpcConn, msg, args, callback=None ) :
    def onResult( err, result ) :
        if err < 0 :
            op.notify( -1, None )
            return
        try :
            assert type(result) is list
            assert len(result) >= 1
            remoteErr = result.pop( 0 )
            assert type(remoteErr) is int
        except :
            op.notify( -1, None )
            return
        if remoteErr < 0 :
            op.notify( -1, None )
            return
        op.notify( 0, result )
    rpcOp = rpcConn.request( [msg]+args, onResult )
    op = AsyncOp( callback, rpcOp.cancel )
    return op

def routerConnect( routerAddr, routerId, reactor, callback=None ) :
    obj = Dummy()
    def doCancel() :
        if obj.op : obj.op.cancel()
        if obj.rpcConn : obj.rpcConn.close()
    def onError() :
        doCancel()
        op.notify( None )
    def onRouterConnect( err, result ) :
        obj.op = None
        if err < 0 :
            onError()
            return
        sock = obj.rpcConn.getSock()
        obj.rpcConn.shutdown()
        op.notify( sock )
    def onTCPConnect( connector ) :
        obj.op = None
        if connector.getError() != 0 :
            onError()
            return
        obj.rpcConn = RPCConnection( connector.getSock(), reactor )
        obj.rpcConn.setCloseCallback( onError )
        obj.op = _doRPCCall( obj.rpcConn, 'Connect', [routerId], onRouterConnect )
    obj.op = tcpConnect( routerAddr, reactor, onTCPConnect )
    op = AsyncOp( callback, doCancel )
    obj.rpcConn = None
    return op

def routerAccept( routerAddr, connectionId, reactor, callback=None ) :
    obj = Dummy()
    def doCancel() :
        if obj.op : obj.op.cancel()
        if obj.rpcConn : obj.rpcConn.close()
    def onError() :
        doCancel()
        op.notify( None )
    def onRouterAccept( err, result ) :
        obj.op = None
        if err < 0 :
            onError()
            return
        sock = obj.rpcConn.getSock()
        obj.rpcConn.shutdown()
        op.notify( sock )
    def onTCPConnect( connector ) :
        obj.op = None
        if connector.getError() != 0 :
            onError()
            return
        obj.rpcConn = RPCConnection( connector.getSock(), reactor )
        obj.rpcConn.setCloseCallback( onError )
        obj.op = _doRPCCall( obj.rpcConn, 'Accept', [connectionId],
                onRouterAccept )
    obj.op = tcpConnect( routerAddr, reactor, onTCPConnect )
    op = AsyncOp( callback, doCancel )
    obj.rpcConn = None
    return op

class RouterClient( object ) :
    (CLOSED,CONNECTING,CONNECTED,REGISTERING,REGISTERED) = range(5)
    def __init__( self, routerAddr, reactor ) :
        self.routerAddr = routerAddr
        self.reactor = reactor
        self.state = self.CLOSED
        self.connectOp = None
        self.rpcConn = None
        self.pingOps = {}
        self.registerOp = None
        self.closeCallback = None

    def setCloseCallback( self, closeCallback ) :
        self.closeCallback = closeCallback

    def close( self ) :
        if self.state == self.CONNECTING :
            self.connectOp.cancel()
            self.connectOp = None
        else :
            for pingOp in self.pingOps.keys() :
                pingOp.cancel()
            self.pingOps.clear()
            if self.state == self.REGISTERING :
                self.registerOp.cancel()
                self.registerOp = None
            if self.state in (self.CONNECTED,self.REGISTERING,self.REGISTERED) :
                self.rpcConn.close()
                self.rpcConn = None
        self.state = self.CLOSED

    def enableIncoming( self, flag ) :
        assert self.state == self.REGISTERED
        self.rpcConn.allowIncoming( flag )

    def setIncomingCallback( self, incomingCallback ) :
        assert self.state == self.REGISTERED
        self.incomingCallback = incomingCallback

    def getRouterAddr( self ) : return self.routerAddr

    def _onClose( self ) :
        self.close()
        if self.closeCallback :
            self.closeCallback()

    def connect( self, connectCallback ) :
        assert self.state == self.CLOSED
        def onTCPConnect( connector ) :
            self.connectOp = None
            if connector.getError() != 0 :
                self.state = self.CLOSED
                connectCallback( False )
                return
            self.rpcConn = RPCConnection( connector.getSock(), self.reactor )
            self.rpcConn.setCloseCallback( self._onClose )
            self.state = self.CONNECTED
            connectCallback( True )
        self.connectOp = tcpConnect( self.routerAddr, self.reactor, onTCPConnect )
        self.state = self.CONNECTING

    def callPing( self, pingCallback ) :
        assert self.state in (self.CONNECTED,self.REGISTERING,self.REGISTERED)
        def onResult( err, result) :
            del self.pingOps[pingOp]
            if err < 0 :
                pingCallback( None )
                return
            assert type(result) is list
            if (len(result) != 1) or (type(result[0]) is not list) :
                pingCallback( None )
                return
            addr = tuple(result[0])
            try :
                validateInetAddress( addr )
            except :
                pingCallback( None )
                return
            pingCallback( addr )
        pingOp = _doRPCCall( self.rpcConn, 'Ping', [], onResult )
        self.pingOps[pingOp] = 1

    def callRegister( self, registerCallback, incomingCallback ) :
        assert self.state == self.CONNECTED
        def onResult( err, result ) :
            self.registerOp = None
            if err < 0 :
                self.state = self.CONNECTED
                registerCallback( None )
                return
            if (len(result) != 1) or \
                    (type(result[0]) is not str) or (not result[0]) :
                self.state = self.CONNECTED
                registerCallback( None )
                return
            self.state = self.REGISTERED
            self.routerId = result[0]
            self.rpcConn.setOnewayCallback( self._onOneway )
            self.incomingCallback = incomingCallback
            registerCallback( self.routerId )
        self.registerOp = _doRPCCall( self.rpcConn, 'Register', [], onResult )
        self.state = self.REGISTERING

    def _onOneway( self, payload ) :
        assert self.state == self.REGISTERED
        print 'oneway payload =', payload
        if (type(payload) is not str) or (not payload) :
            return
        connectionId = payload
        self.incomingCallback( connectionId )
