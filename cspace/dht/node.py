import logging
from time import time
from random import choice, randint
from nitro.async import AsyncOp
from cspace.dht.params import DHT_K, DHT_ID_MAX
from cspace.dht.util import idToNum, numToId, addrToId
from cspace.dht.util import verifySignature
from cspace.dht.proto import MESSAGES, validateRequest, ProtocolError
from cspace.dht.client import DHTClient
from cspace.dht.firewalltest import firewallTestClient

DEFAULT_DATA_TIMEOUT = 15*60
STALE_DATA_INTERVAL = 10
REFRESH_NODES_INTERVAL = 10*60

logger = logging.getLogger( 'cspace.dht.node' )

class Dummy : pass

class DataStore( object ) :
    def __init__( self ) :
        self.d = {}

    def set( self, publicKeyData, data, updateLevel,
            signature, timeout ) :
        deadline = time() + timeout
        self.d[publicKeyData] = (data,updateLevel,signature,deadline)

    def get( self, publicKeyData ) :
        entry = self.d.get( publicKeyData )
        if entry is None :
            return None
        return entry[:3]

    def removeStale( self ) :
        t = time()
        for k,x in self.d.items() :
            if x[-1] < t : del self.d[k]

class KNodeInfo( object ) :
    def __init__( self, nodeAddr, nodeNumId ) :
        self.nodeAddr = nodeAddr
        self.nodeNumId = nodeNumId
        self.lastSeen = time()

    def refresh( self ) :
        self.lastSeen = time()

class KBucket( object ) :
    def __init__( self, start, end ) :
        self.start = start
        self.end = end
        self.nodes = []
        self.nodeDict = {}

    def size( self ) : return len(self.nodes)

    def contains( self, numId ) :
        return (self.start <= numId < self.end)

    def removeNode( self, nodeNumId ) :
        del self.nodeDict[nodeNumId]
        for i,nodeInfo in enumerate(self.nodes) :
            if nodeInfo.nodeNumId == nodeNumId : break
        del self.nodes[i]

    def addNode( self, nodeAddr, nodeNumId ) :
        assert self.contains( nodeNumId )
        if nodeNumId not in self.nodeDict :
            nodeInfo = KNodeInfo( nodeAddr, nodeNumId )
            self.nodes.insert( 0, nodeInfo )
            self.nodeDict[nodeNumId] = 1
            displaced = self.nodes[DHT_K:]
            del self.nodes[DHT_K:]
            for nodeInfo in displaced :
                del self.nodeDict[nodeInfo.nodeNumId]
        else :
            for i,nodeInfo in enumerate(self.nodes) :
                if nodeInfo.nodeNumId == nodeNumId : break
            del self.nodes[i]
            nodeInfo.refresh()
            self.nodes.insert( 0, nodeInfo )

    def split( self ) :
        mid = (self.start + self.end)/2
        a = KBucket( self.start, mid )
        b = KBucket( mid, self.end )
        for nodeInfo in self.nodes :
            c = a.contains(nodeInfo.nodeNumId) and a or b
            c.nodes.append( nodeInfo )
            c.nodeDict[nodeInfo.nodeNumId] = 1
        return (a,b)

class KTable( object ) :
    def __init__( self, selfNumId ) :
        self.selfNumId = selfNumId
        self.table = [KBucket(0,DHT_ID_MAX)]

    def nodeSeen( self, nodeAddr, nodeNumId=None ) :
        if nodeNumId is None :
            nodeNumId = idToNum( addrToId(nodeAddr) )
        if nodeNumId == self.selfNumId : return
        for i,bucket in enumerate(self.table) :
            if bucket.contains(nodeNumId) : break
        if not bucket.contains(self.selfNumId) :
            bucket.addNode( nodeAddr, nodeNumId )
        else :
            self.table[i:i+1] = bucket.split()
            self.nodeSeen( nodeAddr, nodeNumId )

    def getClosestNodes( self, destNumId ) :
        for i,bucket in enumerate(self.table) :
            if bucket.contains(destNumId) :
                break
        output = bucket.nodes[:]
        remaining = DHT_K - len(output)
        if remaining :
            def fetchLeft( i, n ) :
                if (n == 0) or (i == 0) : return []
                out = self.table[i-1].nodes[:]
                return out + fetchLeft(i-1,n-len(out))
            def fetchRight( i, n ) :
                if (n == 0) or (i+1 == len(self.table)) : return []
                out = self.table[i+1].nodes[:]
                return out + fetchRight(i+1,n-len(out))
            output.extend( fetchLeft(i,remaining) )
            output.extend( fetchRight(i,remaining) )
            output.sort( key = lambda ni : ni.nodeNumId^destNumId )
            del output[DHT_K:]
            output.sort( key = lambda ni : ni.lastSeen, reverse=True )
        return [ni.nodeAddr for ni in output]

class KTracker( object ) :
    def __init__( self, ktable ) :
        self.ktable = ktable

    def nodeSeen( self, nodeAddr, latency ) :
        self.ktable.nodeSeen( nodeAddr )

    def nodeFailed( self, nodeAddr ) :
        pass

class DHTNode( object ) :
    def __init__( self, rpcSocket, reactor, knownNodes=[] ) :
        self.rpcSocket = rpcSocket
        self.reactor = reactor
        self.rpcSocket.setRequestCallback( self._onInput )
        self.store = DataStore()
        self.ktable = KTable( idToNum(addrToId(rpcSocket.getAddr())) )
        self.ktracker = KTracker( self.ktable )
        for nodeAddr in knownNodes :
            self.ktable.nodeSeen( nodeAddr )
        self.client = DHTClient( rpcSocket, False, self.ktracker )
        self.requestTable = {}
        for x in MESSAGES :
            self.requestTable[x] = getattr( self, 'do%s' % x )
        self.otherOps = set()
        self._initNodeRefresher()
        self._initDataTimer()

    def close( self ) :
        for op in self.otherOps :
            op.cancel()
        self.otherOps.clear()
        self.rpcSocket.close()
        self.rpcSocket = None

    def _onInput( self, msg, ctx ) :
        try :
            cmd,useSourceAddr,params = validateRequest( msg )
        except ProtocolError, e :
            logger.exception( 'invalid request msg' )
            return
        if useSourceAddr :
            self.ktable.nodeSeen( ctx.addr )
        self.requestTable[cmd]( msg, ctx )

    def doPing( self, msg, ctx ) :
        ctx.response( '' )

    def doGetAddr( self, msg, ctx ) :
        ctx.response( ctx.addr )

    def doGetKey( self, msg, ctx ) :
        publicKeyData = msg[0]
        entry = self.store.get( publicKeyData )
        if entry is None :
            ctx.response( (-1,'',0,'') )
            return
        data,updateLevel,signature = entry
        ctx.response( (0,data,updateLevel,signature) )

    def doPutKey( self, msg, ctx ) :
        publicKeyData,data,updateLevel,signature = msg
        if not verifySignature(publicKeyData,data,updateLevel,signature) :
            return
        entry = self.store.get( publicKeyData )
        if entry is not None :
            oldData,oldUpdateLevel,oldSignature = entry
            if updateLevel <= oldUpdateLevel :
                ctx.response( (-1,oldData,oldUpdateLevel,oldSignature) )
                return
        self.store.set( publicKeyData, data, updateLevel, signature,
                DEFAULT_DATA_TIMEOUT )
        ctx.response( (0,data,updateLevel,signature) )

    def doFindNodes( self, msg, ctx ) :
        destNumId = idToNum( msg[0] )
        ctx.response( self.ktable.getClosestNodes(destNumId) )

    def doFirewallCheck( self, msg, ctx ) :
        addr = tuple( msg )
        if ctx.addr != addr :
            ctx.response( (-1,'') )
            return
        def onTest( err, token ) :
            self.otherOps.remove( op )
            ctx.response( (err,token) )
        op = firewallTestClient( addr, self.reactor, onTest )
        self.otherOps.add( op )

    def _initNodeRefresher( self ):
        obj = Dummy()
        def doWait() :
            timeout = REFRESH_NODES_INTERVAL
            obj.op = self.reactor.callLater( timeout, doRefresh )
        def onLookup( nodes ) :
            doWait()
        def doRefresh() :
            bucket = choice( self.ktable.table )
            destNumId = randint( bucket.start, bucket.end-1 )
            destId = numToId( destNumId )
            startNodes = self.ktable.getClosestNodes( destNumId )
            if not startNodes :
                doWait()
                return
            obj.op = self.client.lookup( destId, startNodes, onLookup )
        def doCancel() :
            obj.op.cancel()
        obj.op = self.reactor.callLater( 0, doRefresh )
        op = AsyncOp( None, doCancel )
        self.otherOps.add( op )

    def _initDataTimer( self ) :
        def onTimer() :
            self.store.removeStale()
        timeout = STALE_DATA_INTERVAL
        timerOp = self.reactor.addTimer( timeout, onTimer )
        self.otherOps.add( timerOp )
