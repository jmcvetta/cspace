import sys, os, logging
from socket import socket, AF_INET, SOCK_DGRAM
from nitro.selectreactor import SelectReactor

from cspace.dht import rpc
_requestCount = 0
_oldRequestMethod = rpc.RPCSocket.request
def _newRequestMethod( *args, **kwargs ) :
    global _requestCount
    _requestCount += 1
    return _oldRequestMethod( *args, **kwargs )
rpc.RPCSocket.request = _newRequestMethod

from cspace.dht.util import checkPort
from cspace.dht.util import computeSignature
from cspace.dht.rpc import RPCSocket
from cspace.dht.client import DHTClient

logging.getLogger().addHandler( logging.StreamHandler() )

def NodeAddr( port ) :
    return ('127.0.0.1',port)

class TestClient( object ) :
    def __init__( self, nodeAddr ) :
        self.nodeAddr = nodeAddr
        self.sock = socket( AF_INET, SOCK_DGRAM )
        self.sock.bind( ('',0) )
        self.reactor = SelectReactor()
        self.rpcSocket = RPCSocket( self.sock, self.reactor )
        self.client = DHTClient( self.rpcSocket )
        self.client.timeout = 1.5
        self.client.retries = 1
        self.client.backoff = 1

    def _initCount( self ) :
        self.startRequestCount = _requestCount

    def _getCount( self ) :
        return _requestCount - self.startRequestCount

    def _doneCount( self ) :
        count = self._getCount()
        print 'request count =', count

    def _onResult( self, err, payload ) :
        print 'err=%d, payload=%s' % (err,str(payload))
        self._doneCount()
        self.reactor.stop()

    def _initCount( self ) :
        self.startRequestCount = _requestCount

    def Ping( self ) :
        self._initCount()
        self.client.callPing( self.nodeAddr, self._onResult )
        self.reactor.run()

    def GetAddr( self ) :
        self._initCount()
        self.client.callGetAddr( self.nodeAddr, self._onResult )
        self.reactor.run()

    def GetKey( self, publicKey ) :
        self._initCount()
        self.client.callGetKey( publicKey.toDER_PublicKey(),
                self.nodeAddr, self._onResult )
        self.reactor.run()

    def PutKey( self, rsaKey, data, updateLevel ) :
        self._initCount()
        signature = computeSignature( rsaKey, data, updateLevel )
        self.client.callPutKey( rsaKey.toDER_PublicKey(), data,
                updateLevel, signature, self.nodeAddr,
                self._onResult )
        self.reactor.run()

    def FindNodes( self, destId ) :
        self._initCount()
        self.client.callFindNodes( destId, self.nodeAddr, self._onResult )
        self.reactor.run()

    def Lookup( self, destId ) :
        def onResult( result ) :
            print 'result = %s' % str(result)
            self._doneCount()
            self.reactor.stop()
        self._initCount()
        self.client.lookup( destId, [self.nodeAddr], onResult )
        self.reactor.run()

    def LookupGetKey( self, publicKey ) :
        def onResult( result ) :
            print 'result = %s' % str(result)
            self._doneCount()
            self.reactor.stop()
        self._initCount()
        self.client.lookupGetKey( publicKey, [self.nodeAddr], onResult )
        self.reactor.run()

    def LookupPutKey( self, rsaKey, data, updateLevel ) :
        def onResult( successCount, latestUpdateLevel ) :
            print 'successCount=%d, latestUpdateLevel=%d' % (
                    successCount, latestUpdateLevel)
            self._doneCount()
            self.reactor.stop()
        self._initCount()
        self.client.lookupPutKey( rsaKey, data, updateLevel,
                [self.nodeAddr], onResult )
        self.reactor.run()
