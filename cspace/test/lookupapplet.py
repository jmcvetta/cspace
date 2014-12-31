import sys, os, time
import logging
import socket

from ncrypt.rsa import RSAKey
from nitro.selectreactor import SelectReactor

from cspace.dht.rpc import RPCSocket
from cspace.dht.client import DHTClient
from cspace.network.nodetable import NodeTable
from cspace.network.location import lookupUser

logger = logging.getLogger( 'lookupapplet' )

def getPublicKey( name, addr ) :
    s = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
    s.connect( addr )
    s.send( 'getpubkey %s\n' % name )
    line = ''
    while 1 :
        data = s.recv( 1 )
        line += data
        if data == '\n' : break
    s.close()
    result,pubKeyData = line.split()
    assert result == 'OK'
    publicKey = RSAKey()
    publicKey.fromDER_PublicKey( pubKeyData.decode('hex') )
    return publicKey

def getLocation( publicKey ) :
    reactor = SelectReactor()
    udpSock = socket.socket( socket.AF_INET, socket.SOCK_DGRAM )
    udpSock.bind( ('',0) )
    rpcSocket = RPCSocket( udpSock, reactor )
    dhtClient = DHTClient( rpcSocket )
    nodeAddr = ('210.210.1.102',10001)
    nodeTable = NodeTable( [nodeAddr] )
    locList = []
    def onLookup( location ) :
        locList.append( location )
        reactor.stop()
    lookupUser( publicKey, dhtClient, nodeTable, onLookup )
    reactor.run()
    rpcSocket.close()
    return locList[0]

def showLocation( name, addr ) :
    print 'name = %s' % name
    print 'getting public key...'
    publicKey = getPublicKey( name, addr )
    print 'getting user location...'
    location = getLocation( publicKey )
    if location is None :
        print 'user is not online'
        return
    try :
        nameInfo = str( socket.gethostbyaddr(location.publicIP) )
    except :
        nameInfo = '(no name)'
    print 'publicIP: %s %s' % (location.publicIP,nameInfo)
    sys.stdout.write( 'routed: ' )
    first = True
    for rloc in location.routedLocations :
        a = rloc.routerAddr
        rid = rloc.routerId.encode('hex')
        if not first :
            sys.stdout.write( ', ' )
        sys.stdout.write( '(%s,%d,%s)' % (a[0],a[1],rid) )
        first = False
    print ''
    sys.stdout.write( 'direct: ' )
    first = True
    for dloc in location.directLocations :
        a = dloc.addr
        if not first :
            sys.stdout.write( ', ' )
        sys.stdout.write( '(%s,%d)' % a )
        first = False
    print ''

def main() :
    logging.getLogger().addHandler( logging.StreamHandler() )
    port = int(os.environ['CSPACE_PORT'])
    event = os.environ['CSPACE_EVENT']
    assert event == 'CONTACTACTION'
    name = os.environ['CSPACE_CONTACTNAME']
    showLocation( name, ('127.0.0.1',port) )
    reactor = SelectReactor()
    reactor.run()

if __name__ == '__main__' :
    try :
        main()
    except :
        logger.exception( 'some exception' )
        time.sleep( 10 )
