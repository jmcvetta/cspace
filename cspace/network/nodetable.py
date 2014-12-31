from random import randint, choice
from time import time
from bisect import bisect_left, insort_right
from nitro.async import AsyncOp
from cspace.dht.params import DHT_ID_MAX
from cspace.dht.util import numToId

MAX_NODES = 100
NODETABLE_PING_INTERVAL = 1*60
NODETABLE_LOOKUP_INTERVAL = 6*60

FIND_LIVE_NODES_TIMEOUT = 3
FIND_LIVE_NODES_TIMEOUT_COUNT = 1

class _NodeInfo( object ) :
    def __init__( self, nodeAddr, isSeedNode, sortId ) :
        self.nodeAddr = nodeAddr
        self.isSeedNode = isSeedNode
        self.sortId = sortId
        self.firstSeen = None
        self.lastSeen = None
        self.latency = None
        self.fails = None
        self.sortKey = self._calcSortKey()

    def _calcSortKey( self ) :
        notAlive = (self.fails is None) or (self.fails != 0)
        negPrio = self.isSeedNode
        if self.latency is None :
            latency = 1000
        else :
            latency = self.latency
        return (notAlive,negPrio,latency,self.sortId)

    def nodeSeen( self, latency ) :
        if self.firstSeen is None :
            self.firstSeen = self.lastSeen = time()
            self.latency = latency
            self.fails = 0
        else :
            self.lastSeen = time()
            self.latency = (self.latency + latency)/2.0
            self.fails = 0
        self.sortKey = self._calcSortKey()

    def nodeFailed( self ) :
        if self.firstSeen is not None :
            self.fails += 1
            self.sortKey = self._calcSortKey()

    def __cmp__( self, other ) :
        return cmp(self.sortKey,other.sortKey)

class NodeTable( object ) :
    def __init__( self, seedNodes ) :
        self.seedNodes = set( seedNodes )
        self.nodeList = []
        self.nodeDict = {}
        self.nextSortId = 0
        for nodeAddr in seedNodes :
            self.addNode( nodeAddr )

    def _getInfo( self, nodeAddr ) :
        info = self.nodeDict.pop( nodeAddr, None )
        if info is None :
            isSeedNode = nodeAddr in self.seedNodes
            sortId = self.nextSortId
            self.nextSortId += 1
            return _NodeInfo(nodeAddr,isSeedNode,sortId)
        pos = bisect_left( self.nodeList, info )
        del self.nodeList[pos]
        return info

    def _setInfo( self, nodeInfo ) :
        self.nodeDict[nodeInfo.nodeAddr] = nodeInfo
        insort_right( self.nodeList, nodeInfo )
        if len(self.nodeList) <= MAX_NODES : return
        extra = self.nodeList[MAX_NODES:]
        del self.nodeList[MAX_NODES:]
        for info in extra :
            del self.nodeDict[info.nodeAddr]

    def addNode( self, nodeAddr ) :
        info = self._getInfo( nodeAddr )
        self._setInfo( info )

    def nodeSeen( self, nodeAddr, latency ) :
        info = self._getInfo( nodeAddr )
        info.nodeSeen( latency )
        self._setInfo( info )

    def nodeFailed( self, nodeAddr ) :
        info = self._getInfo( nodeAddr )
        info.nodeFailed()
        self._setInfo( info )

    def getNodes( self, count=5 ) :
        return [info.nodeAddr for info in self.nodeList[:count]]

    def getLiveNodes( self, count=5 ) :
        count = min( count, len(self.nodeList) )
        out = []
        for pos in range(count) :
            info = self.nodeList[pos]
            if (info.fails is None) or (info.fails != 0) :
                break
            out.append( info.nodeAddr )
        if not out :
            out.extend( self.seedNodes )
        return out

    def getSeedNodes( self ) :
        return list(self.seedNodes)

    def getRandNode( self ) :
        return choice(self.nodeList).nodeAddr

    def getAllNodes( self ) :
        return self.getNodes( MAX_NODES )

    def getAllNonSeedNodes( self ) :
        return [info.nodeAddr for info in self.nodeList\
                if not info.isSeedNode]

class Dummy : pass

def _findLiveNodes( count, nodeTable, dhtClient, reactor, callback=None ) :
    obj = Dummy()
    def doCancel() :
        for pingOp in obj.pingOps :
            pingOp.cancel()
        obj.pingOps.clear()
        obj.timerOp.cancel()
        obj.timerOp = None
    def doNotify() :
        doCancel()
        op.notify()
    def onPing( pingOp, err, payload ) :
        obj.pingOps.remove( pingOp )
        if err >= 0 :
            obj.success += 1
        if obj.success >= count :
            doNotify()
        elif (not obj.nodes) and (not obj.pingOps) :
            doNotify()
    def doPing( nodeAddr ) :
        pingOp = dhtClient.callPing( nodeAddr,
                lambda e,p : onPing(pingOp,e,p) )
        obj.pingOps.add( pingOp )
    def doPingNodes( count ) :
        current = obj.nodes[:count]
        del obj.nodes[:count]
        for nodeAddr in current :
            doPing( nodeAddr )
    def onTimer() :
        obj.timerCount += 1
        if not obj.pingedSeed :
            if (not obj.nodes) or (obj.timerCount == \
                    FIND_LIVE_NODES_TIMEOUT_COUNT ) :
                for nodeAddr in nodeTable.getSeedNodes() :
                    doPing( nodeAddr )
                obj.pingedSeed = True
                return
        if not obj.nodes :
            return
        doPingNodes( 10 )
    obj.success = 0
    obj.pingOps = set()
    obj.nodes = nodeTable.getAllNodes()
    doPingNodes( 10 )
    obj.timerCount = 0
    obj.pingedSeed = False
    obj.timerOp = reactor.addTimer( FIND_LIVE_NODES_TIMEOUT, onTimer )
    op = AsyncOp( callback, doCancel )
    return op

def _findNewNodes( nodeTable, dhtClient, reactor, callback=None ) :
    destId = numToId( randint(0,DHT_ID_MAX-1) )
    startNodes = nodeTable.getLiveNodes()
    def onLookup( nodes ) :
        op.notify()
    lookupOp = dhtClient.lookup( destId, startNodes, onLookup )
    op = AsyncOp( callback, lookupOp.cancel )
    return op

def initNodeTable( nodeTable, dhtClient, reactor, callback=None ) :
    def onFindLive() :
        print 'done finding live nodes'
        findNewOp = _findNewNodes( nodeTable, dhtClient, reactor,
                op.notify )
        op.setCanceler( findNewOp.cancel )
    print 'finding live nodes...'
    findLiveOp = _findLiveNodes( 5, nodeTable, dhtClient, reactor,
            onFindLive )
    op = AsyncOp( callback, findLiveOp.cancel )
    return op

class NodeTableRefresher( object ) :
    def __init__( self, nodeTable, dhtClient, reactor ) :
        self.nodeTable = nodeTable
        self.dhtClient = dhtClient
        self.reactor = reactor
        self.pingOp = reactor.callLater( NODETABLE_PING_INTERVAL,
                self._onPingTimer )
        self.lookupOp = reactor.callLater( NODETABLE_LOOKUP_INTERVAL,
                self._onLookupTimer )

    def close( self ) :
        self.pingOp.cancel()
        self.lookupOp.cancel()

    def _onPing( self, err, payload ) :
        if err < 0 :
            self._onPingTimer()
            return
        self.pingOp = self.reactor.callLater( NODETABLE_PING_INTERVAL,
                self._onPingTimer )

    def _onPingTimer( self ) :
        nodeAddr = self.nodeTable.getRandNode()
        self.pingOp = self.dhtClient.callPing( nodeAddr, self._onPing )

    def _onLookup( self, nodes ) :
        self.lookupOp = self.reactor.callLater( NODETABLE_LOOKUP_INTERVAL,
                self._onLookupTimer )

    def _onLookupTimer( self ) :
        destId = numToId( randint(0,DHT_ID_MAX-1) )
        startNodes = self.nodeTable.getLiveNodes()
        self.lookupOp = self.dhtClient.lookup( destId, startNodes,
                self._onLookup )
