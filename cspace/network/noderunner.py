from socket import socket, AF_INET, SOCK_DGRAM
from socket import error as sock_error
from ncrypt.rand import bytes as rand_bytes
from nitro.async import AsyncOp
from nitro.tcp import tcpListen
from cspace.dht.rpc import RPCSocket
from cspace.dht.firewalltest import FirewallTestServer
from cspace.dht.client import DHTClient
from cspace.dht.node import DHTNode
from cspace.network.localip import getLocalIP
from cspace.network.router import Router

NODE_CHECK_TIME_DELAY = 60*60

class Dummy : pass

def _testFirewall( tcpListener, rpcSock, nodeAddrList, localIP,
        reactor, callback=None ) :
    def doCancel() :
        for checkOp in checkOps :
            checkOp.cancel()
        checkOps.clear()
        testServer.close()
    def onCheck( checkOp, err, payload ) :
        checkOps.remove( checkOp )
        if err >= 0 :
            fwResult,fwToken = payload
            if (fwResult >= 0) and (fwToken == token) :
                successList.append( 1 )
        if not checkOps :
            testServer.close()
            # n(success)/n(nodes) >= 1/2
            op.notify( 2*len(successList) >= len(nodeAddrList) )
    def doCheck( nodeAddr ) :
        checkOp = dhtClient.callFirewallCheck( localIP, nodeAddr,
                lambda e,p : onCheck(checkOp,e,p) )
        checkOps.add( checkOp )
    assert nodeAddrList
    successList = []
    checkOps = set()
    token = rand_bytes( 20 )
    dhtClient = DHTClient( rpcSock )
    testServer = FirewallTestServer( tcpListener, token, reactor )
    for nodeAddr in nodeAddrList :
        doCheck( nodeAddr )
    op = AsyncOp( callback, doCancel )
    return op

class NodeRunner( object ) :
    def __init__( self, nodeTable, reactor ) :
        self.nodeTable = nodeTable
        self.reactor = reactor
        self.timerOp = None
        self.firewallOp = None
        self.rpcSock = None
        self.tcpListener = None
        self.router = None
        self.dhtNode = None
        self._initTimer()

    def close( self ) :
        if self.timerOp :
            self.timerOp.cancel()
            self.timerOp = None
        if self.firewallOp :
            self.firewallOp.cancel()
            self.firewallOp = None
        if self.rpcSock :
            self.rpcSock.close()
            self.rpcSock = None
        if self.tcpListener :
            self.tcpListener.close()
            self.tcpListener = None
        if self.router is not None :
            self.router.close()
            self.router = None
        if self.dhtNode is not None :
            self.dhtNode.close()
            self.dhtNode = None

    def _initTimer( self ) :
        timeout = NODE_CHECK_TIME_DELAY
        self.timerOp = self.reactor.callLater( timeout, self._onTimer )

    def _onTimer( self ) :
        self.timerOp = None
        localIP = getLocalIP()
        if localIP is None :
            self._initTimer()
            return
        nodeAddrList = self.nodeTable.getLiveNodes()
        if not nodeAddrList :
            self._initTimer()
            return
        tcpListener = None
        udpSock = None
        for port in xrange(10001,20000) :
            addr = (localIP,port)
            try :
                tcpListener = tcpListen( addr, self.reactor, None )
            except sock_error :
                continue
            udpSock = socket( AF_INET, SOCK_DGRAM )
            try :
                udpSock.bind( addr )
            except sock_error :
                udpSock.close()
                tcpListener.close()
                udpSock = tcpListener = None
                continue
            break
        if tcpListener is None :
            self._initTimer()
            return
        self.rpcSock = RPCSocket( udpSock, self.reactor )
        self.tcpListener = tcpListener
        self.firewallOp = _testFirewall( self.tcpListener,
                self.rpcSock, nodeAddrList, localIP, self.reactor,
                self._onFirewallCheck )
    
    def _onFirewallCheck( self, result ) :
        self.firewallOp = None
        if not result :
            self.rpcSock.close()
            self.rpcSock = None
            self.tcpListener.close()
            self.tcpListener = None
            self._initTimer()
            return
        self.router = Router( self.tcpListener, self.reactor )
        self.dhtNode = DHTNode( self.rpcSock, self.reactor,
                self.nodeTable.getLiveNodes() )
        self.tcpListener = None
        self.rpcSock = None
