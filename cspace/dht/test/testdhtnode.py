import sys, logging
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
from cspace.dht.rpc import RPCSocket
from cspace.dht.node import DHTNode

def startNode( reactor, nodeAddr, knownNodes ) :
    print 'starting node: %s' % str(nodeAddr)
    sock = socket( AF_INET, SOCK_DGRAM )
    sock.bind( nodeAddr )
    rpcSocket = RPCSocket( sock, reactor )
    node = DHTNode( rpcSocket, reactor, knownNodes )
    return node

def main() :
    logging.getLogger().addHandler( logging.StreamHandler() )
    if len(sys.argv) == 2 :
        initialPort = int(sys.argv[1])
        assert checkPort( port )
    else : initialPort = 12345
    reactor = SelectReactor()
    seedNodeAddr = ('127.0.0.1',initialPort)
    seedNode = startNode( reactor, seedNodeAddr, [] )
    numNodes = 50
    for i in range(1,numNodes) :
        port = initialPort + i
        nodeAddr = ('127.0.0.1',port)
        node = startNode( reactor, nodeAddr, [seedNodeAddr] )
    print 'started %d nodes' % numNodes
    reactor.run()
    print '_requestCount =', _requestCount

def profile_main() :
    import hotshot
    prof = hotshot.Profile( 'test.prof' )
    prof.runcall( main )
    prof.close()

if __name__ == '__main__' :
    #profile_main()
    main()
