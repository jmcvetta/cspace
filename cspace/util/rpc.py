import logging
from types import IntType, ListType

from nitro.async import AsyncOp
from nitro.tcp import TCPMessageStream
from nitro.bencode import encode, decode, DecodeError

logger = logging.getLogger( 'cspace.net' )

class RPCContext(object) :
    def __init__( self, requestId, rpcConnection ) :
        self.requestId = requestId
        self.rpcConnection = rpcConnection
    def getRequestId( self ) : return self.requestId
    def getRPCConnection( self ) : return self.rpcConnection

    def response( self, data ) :
        self.rpcConnection.response( data, self.requestId )

class RPCOp(AsyncOp) :
    def __init__( self, requestId, callback=None, canceler=None ) :
        AsyncOp.__init__( self, callback, canceler )
        self.requestId = requestId
    def getRequestId( self ) : return self.requestId

class RPCConnection(object) :
    def __init__( self, sock, reactor ) :
        self.sock = sock
        self.reactor = reactor
        self.nextRequestId = 0
        self.pending = {}
        self.closeCallback = None
        self.requestCallback = None
        self.onewayCallback = None
        ms = TCPMessageStream( sock, reactor )
        self.msgStream = ms
        ms.setCloseCallback( self._onClose )
        ms.setErrorCallback( self._onError )
        ms.setInvalidMessageCallback( self._onInvalidMessage )
        ms.setInputCallback( self._onInput )
        ms.enableRead( True )
        self.hasShutdown = False

    def getSock( self ) : return self.sock

    def setRequestCallback( self, requestCallback ) :
        self.requestCallback = requestCallback
    def setOnewayCallback( self, onewayCallback ) :
        self.onewayCallback = onewayCallback
    def setCloseCallback( self, closeCallback ) :
        self.closeCallback = closeCallback
    def setWriteCompleteCallback( self, writeCompleteCallback ) :
        self.msgStream.setWriteCompleteCallback( writeCompleteCallback )

    def getPendingWrite( self ) : return self.msgStream.getPendingWrite()

    def close( self, deferred=False ) :
        self._shutdownInternal()
        if not self.msgStream.hasShutdown() :
            self.msgStream.close( deferred=deferred )

    def shutdown( self ) :
        self._shutdownInternal()
        if not self.msgStream.hasShutdown() :
            self.msgStream.shutdown()

    def _shutdownInternal( self ) :
        if self.hasShutdown : return
        self.hasShutdown = True
        while self.pending :
            (requestId,op) = self.pending.popitem()
            op.notify( -1, None )

    def _shutdownAndNotify( self ) :
        assert not self.hasShutdown
        self._shutdownInternal()
        if not self.msgStream.hasShutdown() :
            if self.closeCallback :
                self.closeCallback()
            else :
                self.close()

    def allowIncoming( self, allow ) :
        self.msgStream.enableRead( allow )

    def request( self, payload, callback=None ) :
        requestId = self.nextRequestId
        self.nextRequestId += 1
        msg = (0,requestId,payload)
        s = encode( msg )
        def cancelRequest() :
            del self.pending[requestId]
        op = RPCOp( requestId, callback, cancelRequest )
        self.pending[requestId] = op
        self.msgStream.sendMessage( s )
        return op

    def response( self, payload, requestId ) :
        msg = (1,requestId,payload)
        s = encode( msg )
        self.msgStream.sendMessage( s )

    def oneway( self, payload ) :
        requestId = self.nextRequestId
        self.nextRequestId += 1
        msg = (2,requestId,payload)
        s = encode( msg )
        self.msgStream.sendMessage( s )

    def _onClose( self ) :
        self._shutdownAndNotify()

    def _onError( self, err, errMsg ) :
        logger.warning( 'error in rpc connection(%d): %s', err, errMsg )
        self._shutdownAndNotify()

    def _onInvalidMessage( self ) :
        logger.warning( 'invalid rpc message received. closing...' )
        self._shutdownAndNotify()

    def _onInput( self, data ) :
        try :
            (msgCode,requestId,payload) = decode(data)
            if (type(msgCode) is not IntType) or (type(requestId) is not IntType) :
                raise TypeError, 'invalid msg structure'
        except DecodeError, de :
            logger.warning( 'invalid msg structure: %s', de )
            return
        except (TypeError,ValueError), e :
            logger.warning( 'invalid msg: %s', e )
            return
        if msgCode == 0 : # incoming request
            ctx = RPCContext( requestId, self )
            if self.requestCallback :
                self.requestCallback( payload, ctx )
        elif msgCode == 1 : # incoming response
            op = self.pending.get( requestId, None )
            if op is None :
                logger.warning( 'unmatched response requestId(%d)', requestId )
                return
            del self.pending[requestId]
            op.notify( 0, payload )
        elif msgCode == 2 : # incoming one-way message
            if self.onewayCallback :
                self.onewayCallback( payload )
        else :
            logger.warning( 'invalid msg code: %d', msgCode )

class RPCSwitchboard( object ) :
    def __init__( self, rpcConnection ) :
        self.rpcConnection = rpcConnection
        self.requestAgents = {}
        self.onewayAgents = {}
        self.rpcConnection.setRequestCallback( self._onRequest )
        self.rpcConnection.setOnewayCallback( self._onOneway )

    def addRequestAgent( self, agentName, agentCallback ) :
        assert agentName not in self.requestAgents
        self.requestAgents[agentName] = agentCallback

    def addOnewayAgent( self, agentName, agentCallback ) :
        assert agentName not in self.onewayAgents
        self.onewayAgents[agentName] = agentCallback

    def delRequestAgent( self, agentName ) :
        del self.requestAgents[agentName]

    def delOnewayAgent( self, agentName ) :
        del self.onewayAgents[agentName]

    def _onRequest( self, payload, ctx ) :
        if type(payload) is not ListType :
            logger.warning( 'invalid payload type: %s', str(type(payload)) )
            return
        try :
            agentName,payload = payload
        except ValueError, e :
            logger.warning( 'error decoding payload: %s', str(e) )
            return
        agentCallback = self.requestAgents.get( agentName, None )
        if agentCallback is None :
            logger.warning( 'request agent not found: %s' % agentName )
            return
        agentCallback( payload, ctx )

    def _onOneway( self, payload ) :
        if type(payload) is not ListType :
            logger.warning( 'invalid payload type: %s', str(type(payload)) )
            return
        try :
            agentName,payload = payload
        except ValueError, e :
            logger.warning( 'error decoding payload: %s', str(e) )
            return
        agentCallback = self.onewayAgents.get( agentName, None )
        if agentCallback is None :
            logger.warning( 'oneway agent not found: %s' % agentName )
            return
        agentCallback( payload )

class RPCStub( object ) :
    def __init__( self, rpcConnection, objectName ) :
        self.rpcConnection = rpcConnection
        self.objectName = objectName

    def request( self, payload, callback=None ) :
        return self.rpcConnection.request( (self.objectName,payload), callback )

    def oneway( self, payload ) :
        self.rpcConnection.oneway( (self.objectName,payload) )
