import logging
logging.getLogger().addHandler( logging.StreamHandler() )

from nitro.selectreactor import SelectReactor
from nitro.tcp import TCPStream
from cspace.node.client import NodeClient

reactor = SelectReactor()
nodeAddr = ('127.0.0.1',13542)
nodeClient = None
routerId = ''

class EchoHandler( object ) :
    def __init__( self, sock, reactor ) :
        self.sock = sock
        self.reactor = reactor
        self.stream = TCPStream( sock, reactor )
        self.stream.setInputCallback( self._onInput )
        self.stream.setCloseCallback( self._onClose )
        self.stream.setErrorCallback( self._onError )
        self.stream.initiateRead( 8192 )

    def _onClose( self ) :
        print 'EchoHandler: on close'
        self.stream.close( deferred=True )

    def _onError( self, err, errMsg ) :
        print 'EchoHandler: error(%d): %s' % (err,errMsg)
        self.stream.close()

    def _onInput( self, data ) :
        self.stream.writeData( data )

def onIncoming( sock ) :
    print 'incoming node connection'
    EchoHandler( sock, reactor )

def registerAndInit() :
    def onPut( err, payload ) :
        if err < 0 :
            print 'unable to update node location'
            reactor.stop()
            return
        print 'updated node location'
    def onRegister( err, payload ) :
        global routerId
        if err < 0 :
            print 'unable to register with node'
            reactor.stop()
            return
        routerId = payload
        print 'routerId =', routerId
        nodeClient.callPut( 'Echo', routerId, onPut )
    def onConnect( err ) :
        if err < 0 :
            print 'unable to connect'
            reactor.stop()
            return
        nodeClient.callRegister( onRegister )
    nodeClient.connect( nodeAddr, onConnect )

def onClose() :
    print 'node connection closed'
    reactor.stop()

def main() :
    global nodeClient
    print 'Node Echo Server'
    nodeClient = NodeClient( reactor )
    nodeClient.setCloseCallback( onClose )
    nodeClient.setIncomingCallback( onIncoming )
    registerAndInit()
    reactor.run()

if __name__ == '__main__' :
    main()
