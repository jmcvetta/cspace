import logging
from types import IntType, StringType
from socket import error as sock_error
from ncrypt.rand import bytes as rand_bytes
from nitro.async import AsyncOp
from nitro.bencode import encode, decode, DecodeError

logger = logging.getLogger( 'cspace.dht.rpc' )

class RPCContext(object) :
    def __init__( self, id, addr, rpcSocket ) :
        self.id = id
        self.addr = addr
        self.rpcSocket = rpcSocket

    def response( self, data ) :
        self.rpcSocket.response( data, self )

class RPCOp( AsyncOp ) :
    def __init__( self, opId, callback=None, canceler=None ) :
        AsyncOp.__init__( self, callback, canceler )
        self.opId = opId

    def getId( self ) : return self.opId

class RPCSocket( object ) :
    def __init__( self, sock, reactor ) :
        self.sock = sock
        self.reactor = reactor
        self.pending = {}
        self.requestCallback = None
        reactor.addReadCallback( sock.fileno(), self._onRead )

    def getAddr( self ) : return self.sock.getsockname()
    
    def setRequestCallback( self, requestCallback ) :
        self.requestCallback = requestCallback

    def close( self ) :
        self.reactor.removeReadCallback( self.sock.fileno() )
        self.sock.close()

    def _onRead( self ) :
        try :
            (data,fromaddr) = self.sock.recvfrom( 8192 )
        except sock_error, (err,errMsg) :
            return
        self._onInput( data, fromaddr )

    def _onInput( self, data, fromaddr ) :
        try :
            (msgCode,id,payload) = decode( data )
            if (type(msgCode) is not IntType) or (type(id) is not StringType) :
                raise TypeError, 'invalid msg structure'
        except DecodeError, de :
            logger.exception( 'decode error: %s', de )
            return
        except (TypeError, ValueError), e :
            logger.exception( 'invalid msg: %s', e )
            return
        if msgCode == 0 : # incoming request
            ctx = RPCContext( id, fromaddr, self )
            self._onRequest( payload, ctx )
        elif msgCode == 1 : # incoming response
            op = self.pending.pop( id, None )
            if op is None :
                logger.warning( 'invalid response msg' )
                return
            op.notify( payload, fromaddr )
        else :
            logger.warning( 'invalid msg code: %d', msgCode )

    def _onRequest( self, payload, ctx ) :
        if self.requestCallback is not None :
            self.requestCallback( payload, ctx )
            return
        logger.warning( 'unhandled incoming msg from %s', ctx.addr )

    def _sendData( self, data, destaddr ) :
        try :
            self.sock.sendto( data, 0, destaddr )
        except sock_error, (err,errMsg) :
            logger.exception( 'error sending data(%d): %s', err, errMsg )

    def request( self, data, destaddr, callback=None ) :
        while 1 :
            id = rand_bytes( 20 )
            if not self.pending.has_key(id) : break
        msg = (0, id, data)
        s = encode( msg )
        def cancelRequest() :
            del self.pending[id]
        op = RPCOp( id, callback, cancelRequest )
        self.pending[id] = op
        self._sendData( s, destaddr )
        return op

    def retry( self, id, data, destaddr ) :
        assert id in self.pending
        msg = (0, id, data)
        s = encode( msg )
        self._sendData( s, destaddr )

    def response( self, data, ctx ) :
        assert ctx.rpcSocket is self
        msg = (1, ctx.id, data )
        s = encode( msg )
        self._sendData( s, ctx.addr )

    def call( self, data, destaddr, callback=None,
            timeout=2, retries=1, backoff=1 ) :
        return _Call( data, destaddr, self, callback,
                timeout, retries, backoff ).getOp()

class _Call(object) :
    def __init__( self, data, destaddr, rpcSocket, callback, timeout, retries, backoff ) :
        self.data = data
        self.destaddr = destaddr
        self.rpcSocket = rpcSocket
        self.timeout = timeout
        self.retries = retries
        self.backoff = backoff
        self.reactor = rpcSocket.reactor
        self.attempt = 0
        self.rpcOp = rpcSocket.request( data, destaddr, self.onResult )
        self.timerOp = self.reactor.callLater( timeout, self.onTimeout )
        self.op = RPCOp( self.rpcOp.getId(), callback, self.cancel )
        self.active = True

    def getOp( self ) : return self.op

    def cancel( self ) :
        assert self.active
        self.active = False
        self.rpcOp.cancel()
        self.timerOp.cancel()

    def onResult( self, payload, fromaddr ) :
        assert self.active
        self.active = False
        self.timerOp.cancel()
        self.op.notify( self.attempt, payload )

    def onTimeout( self ) :
        assert self.active
        if self.attempt == self.retries :
            self.active = False
            self.rpcOp.cancel()
            self.op.notify( -1, None )
        else :
            self.attempt += 1
            self.timeout *= self.backoff
            self.timerOp = self.reactor.callLater( self.timeout, self.onTimeout )
            self.rpcSocket.retry( self.rpcOp.getId(), self.data, self.destaddr )
