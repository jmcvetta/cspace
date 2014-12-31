import logging
from time import time
from bisect import insort
from nitro.async import AsyncOp
from cspace.dht.params import DHT_K, DHT_PARALLEL
from cspace.dht.util import toId, idToNum, addrToId
from cspace.dht.util import verifySignature, computeSignature
from cspace.dht.proto import validateResponse, ProtocolError

logger = logging.getLogger( 'cspace.dht.client' )

class Dummy : pass

class DHTClient( object ) :
    def __init__( self, rpcSocket, pureClient=True, nodeTracker=None ) :
        self.rpcSocket = rpcSocket
        if pureClient :
            self.useSourceAddr = 0
        else :
            self.useSourceAddr = 1
        self.nodeTracker = nodeTracker
        self.timeout = 3
        self.retries = 1
        self.backoff = 1.5

    def doCall( self, cmd, params, nodeAddr, callback,
            timeout=None, retries=None, backoff=None ) :
        def onResult( errCode, payload ) :
            if errCode < 0 :
                if self.nodeTracker is not None :
                    self.nodeTracker.nodeFailed( nodeAddr )
                op.notify( errCode, payload )
                return
            try :
                payload = validateResponse( cmd, payload )
            except ProtocolError, e :
                logger.exception( 'invalid response' )
                if self.nodeTracker is not None :
                    self.nodeTracker.nodeFailed( nodeAddr )
                op.notify( -2, e )
                return
            if self.nodeTracker is not None :
                self.nodeTracker.nodeSeen( nodeAddr, time()-startTime )
            op.notify( errCode, payload )
        data = (cmd,self.useSourceAddr) + params
        if timeout is None : timeout = self.timeout
        if retries is None : retries = self.retries
        if backoff is None : backoff = self.backoff
        rpcOp = self.rpcSocket.call( data, nodeAddr, onResult,
                timeout, retries, backoff )
        startTime = time()
        op = AsyncOp( callback, rpcOp.cancel )
        return op

    def callPing( self, nodeAddr, callback=None, **kwargs ) :
        return self.doCall( 'Ping', (), nodeAddr, callback, **kwargs )

    def callGetAddr( self, nodeAddr, callback=None, **kwargs ) :
        return self.doCall( 'GetAddr', (), nodeAddr, callback,
                **kwargs )

    def callGetKey( self, publicKeyData, nodeAddr,
            callback=None, **kwargs ) :
        return self.doCall( 'GetKey', (publicKeyData,), nodeAddr,
                callback, **kwargs )

    def callPutKey( self, publicKeyData, data, updateLevel,
            signature, nodeAddr, callback=None, **kwargs ) :
        args = ( publicKeyData, data, updateLevel, signature )
        return self.doCall( 'PutKey', args, nodeAddr, callback,
                **kwargs )

    def callFindNodes( self, destId, nodeAddr, callback=None, **kwargs ) :
        return self.doCall( 'FindNodes', (destId,), nodeAddr, callback, **kwargs )

    def callFirewallCheck( self, localIP, nodeAddr, callback=None,
            **kwargs ) :
        port = self.rpcSocket.getAddr()[1]
        addr = (localIP,port)
        kwargs['timeout'] = max( 20, kwargs.get('timeout',0) )
        kwargs['retries'] = 0
        kwargs['backoff'] = 1
        return self.doCall( 'FirewallCheck', addr, nodeAddr,
                callback, **kwargs )

    def lookup( self, destId, startNodes, callback=None ) :
        def hookCallback( *args, **kwargs ) :
            print 'done lookup %s' % str(id(lop))
            op.notify( *args, **kwargs )
        lop = _Lookup( self, destId, startNodes, hookCallback ).getOp()
        print 'starting lookup... %s' % str(id(lop))
        op = AsyncOp( callback, lop.cancel )
        return op

    def lookupGetKey( self, publicKey, startNodes, callback=None ) :
        obj = Dummy()
        def cancelGets() :
            for getOp in obj.getOps.keys() :
                getOp.cancel()
        def onGet( getOp, err, payload ) :
            del obj.getOps[getOp]
            if err >= 0 :
                result,data,updateLevel,signature = payload
                if result >= 0 :
                    if verifySignature(publicKey,data,updateLevel,\
                            signature) :
                        obj.getResults.append( (data,updateLevel,
                            signature) )
            if not obj.getOps :
                if obj.getResults :
                    maxUpdateLevel = max( [x[1] for x in obj.getResults] )
                    obj.getResults = [x for x in obj.getResults \
                            if x[1] == maxUpdateLevel]
                op.notify( obj.getResults )
        def doGetKey( nodeAddr ) :
            getOp = self.callGetKey( publicKeyData, nodeAddr,
                    lambda err,payload : onGet(getOp,err,payload) )
            obj.getOps[getOp] = 1
        def onResult( nodes ) :
            obj.getOps = {}
            obj.getResults = []
            for nodeAddr in nodes :
                doGetKey( nodeAddr )
            op.setCanceler( cancelGets )
            if not obj.getOps :
                op.notify( [] )
        publicKeyData = publicKey.toDER_PublicKey()
        lookupOp = self.lookup( toId(publicKeyData), startNodes,
                onResult )
        op = AsyncOp( callback, lookupOp.cancel )
        return op

    def lookupPutKey( self, rsaKey, data, updateLevel,
            startNodes, callback=None ) :
        obj = Dummy()
        def cancelPuts() :
            for putOp in obj.putOps.keys() :
                putOp.cancel()
        def doNotify() :
            op.notify( obj.successCount, obj.updateLevel )
        def onPut( putOp, err, payload ) :
            del obj.putOps[putOp]
            if err >= 0 :
                result,oldData,oldUpdateLevel,oldSignature = payload
                if result >= 0 :
                    obj.successCount += 1
                elif oldUpdateLevel >= obj.updateLevel :
                    if verifySignature(rsaKey,oldData,
                            oldUpdateLevel,oldSignature) :
                        obj.updateLevel = oldUpdateLevel + 1
                        cancelPuts()
                        obj.putOps.clear()
                        obj.successCount = 0
                        obj.signature = computeSignature( rsaKey, data,
                                obj.updateLevel )
                        for nodeAddr in obj.nodes :
                            doPutKey( nodeAddr )
            if not obj.putOps :
                doNotify()
        def doPutKey( nodeAddr ) :
            putOp = self.callPutKey( publicKeyData, data,
                    obj.updateLevel, obj.signature, nodeAddr,
                    lambda err,payload : onPut(putOp,err,payload) )
            obj.putOps[putOp] = 1
        def onResult( nodes ) :
            obj.nodes = nodes
            obj.successCount = 0
            obj.putOps = {}
            obj.updateLevel = updateLevel + 1
            obj.signature = computeSignature( rsaKey, data,
                obj.updateLevel )
            for nodeAddr in obj.nodes :
                doPutKey( nodeAddr )
            op.setCanceler( cancelPuts )
            if not obj.putOps :
                doNotify()
        publicKeyData = rsaKey.toDER_PublicKey()
        lookupOp = self.lookup( toId(publicKeyData), startNodes,
                onResult )
        op = AsyncOp( callback, lookupOp.cancel )
        return op

class _LookupNodeInfo( object ) :
    def __init__( self, nodeAddr, destNumId ) :
        self.nodeAddr = nodeAddr
        self.numId = idToNum(addrToId(nodeAddr))
        self.distance = destNumId ^ self.numId

    def __cmp__( self, other ) :
        return cmp( self.distance, other.distance )

class _Lookup( object ) :
    def __init__( self, clientObj, destId, startNodes, callback=None ) :
        assert startNodes
        self.clientObj = clientObj
        self.destId = destId
        self.destNumId = idToNum( destId )
        self.seen = {}
        self.closest = []
        self.pending = []
        self.calling = {}
        for nodeAddr in startNodes :
            self._newNode( nodeAddr )
        self._callPending()
        self.op = AsyncOp( callback, self._doCancel )

    def getOp( self ) : return self.op

    def _doCancel( self ) :
        for op in self.calling.values() :
            op.cancel()
        self.calling.clear()

    def _newNode( self, nodeAddr ) :
        if nodeAddr in self.seen : return
        info = _LookupNodeInfo( nodeAddr, self.destNumId )
        self.seen[nodeAddr] = info
        self._addPending( info )

    def _addPending( self, info ) :
        insort( self.pending, info )
        del self.pending[DHT_K*3/2:]

    def _callPending( self ) :
        count = DHT_PARALLEL - len(self.calling)
        nodeInfoList = self.pending[:count]
        del self.pending[:count]
        for info in nodeInfoList :
            self._callNode( info )

    def _callNode( self, info ) :
        assert len(self.calling) < DHT_PARALLEL
        def onResult( err, payload ) :
            self._onResult( info, err, payload )
        op = self.clientObj.callFindNodes( self.destId, info.nodeAddr,
                onResult, timeout=3, retries=0, backoff=1 )
        self.calling[info.nodeAddr] = op

    def _onResult( self, info, err, payload ) :
        del self.calling[info.nodeAddr]
        if err >= 0 :
            insort( self.closest, info )
            del self.closest[DHT_K:]
            for nodeAddr in payload :
                self._newNode( nodeAddr )
        self._callPending()
        if not self.calling :
            assert len(self.pending) == 0
            self.op.notify( [ni.nodeAddr for ni in self.closest] )
