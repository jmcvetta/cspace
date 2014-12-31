from socket import socket, AF_INET, SOCK_DGRAM
from socket import error as sock_error
from nitro.tcp import tcpListen
from cspace.dht.rpc import RPCSocket
from cspace.dht.node import DHTNode
from cspace.network.router import Router

class NetworkNode( object ) :
    def __init__( self, listener, rpcSock, reactor, knownNodes=[] ) :
        self.listener = listener
        self.rpcSock = rpcSock
        self.reactor = reactor
        self.router = Router( self.listener, self.reactor )
        self.dhtNode = DHTNode( self.rpcSock, self.reactor, knownNodes )

    def getAddr( self ) :
        return self.listener.getSock().getsockname()

    def close( self ) :
        self.router.close()
        self.router = None
        self.dhtNode.close()
        self.dhtNode = None

def startNetworkNode( ipAddr, reactor, knownNodes=[] ) :
    for port in xrange(10001,20000) :
        addr = (ipAddr,port)
        try :
            listener = tcpListen( addr, reactor, None )
        except sock_error :
            continue
        sock = socket( AF_INET, SOCK_DGRAM )
        try :
            sock.bind( addr )
        except sock_error :
            sock.close()
            listener.close()
            continue
        rpcSock = RPCSocket( sock, reactor )
        node = NetworkNode( listener, rpcSock, reactor, knownNodes )
        return node

def main() :
    import sys, logging
    from nitro.selectreactor import SelectReactor
    logging.getLogger().addHandler( logging.StreamHandler() )
    args = sys.argv[1:]
    if args :
        ipAddr = args.pop( 0 )
    else :
        ipAddr = '127.0.0.1'
    reactor = SelectReactor()
    knownNodes = []
    for nodeAddr in args :
        try :
            ip,port = nodeAddr.split( ':' )
            port = int(port)
        except TypeError, ValueError :
            print 'invalid nodeaddr: %s' % nodeAddr
            return
        knownNodes.append( (ip,port) )
    node = startNetworkNode( ipAddr, reactor, knownNodes )
    if node is None :
        print 'unable to bind to any port on %s' % ipAddr
        return
    print 'node address =', node.getAddr()
    reactor.run()

if __name__ == '__main__' :
    main()
