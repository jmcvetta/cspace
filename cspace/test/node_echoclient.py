import logging
logging.getLogger().addHandler( logging.StreamHandler() )

from time import time

from nitro.selectreactor import SelectReactor
from nitro.tcp import TCPStream
from cspace.node.client import NodeClient

reactor = SelectReactor()
nodeAddr = ('127.0.0.1',13542)
nodeClient = None

class EchoClient(object) :
    def __init__( self, sock, reactor ) :
        self.sock = sock
        self.reactor = reactor
        self.stream = TCPStream( self.sock, self.reactor )
        self.stream.setCloseCallback( self._onClose )
        self.stream.setErrorCallback( self._onError )
        self.stream.setInputCallback( self._onInput )
        self.timerOp = self.reactor.addTimer( 1, self._onTimer )
        self.stream.initiateRead( 8192 )
    
    def _shutdown( self ) :
        self.stream.shutdown()
        self.sock.close()
        self.timerOp.cancel()
        self.reactor.stop()

    def _onClose( self ) :
        print 'closed'
        self._shutdown()

    def _onError( self, err, errMsg ) :
        print 'error(%d): %s' % (err,errMsg)
        self._shutdown()

    def _onInput( self, data ) :
        print 'received: %s' % data

    def _onTimer( self ) :
        msg = 'time() = %f' % time()
        print 'sending: %s' % msg
        self.stream.writeData( msg )

def onConnectTo( err, sock ) :
    if err < 0 :
        print 'unable to connect to node echo server'
        reactor.stop()
        return
    print 'connected to node echo server'
    EchoClient( sock, reactor )

def onGet( err, value ) :
    if err < 0 :
        print 'unable to locate node echo server'
        reactor.stop()
        return
    routerId = value
    if not routerId :
        print 'node echo server not found'
        reactor.stop()
        return
    print 'connecting to node echo server...'
    nodeClient.connectTo( routerId, onConnectTo )

def onConnect( err ) :
    if err < 0 :
        print 'unable to connect to node'
        reactor.stop()
        return
    print 'locating node echo server...'
    nodeClient.callGet( 'Echo', onGet )

def onClose() :
    print 'node connection closed'
    reactor.stop()

def main() :
    global nodeClient
    nodeClient = NodeClient( reactor )
    nodeClient.setCloseCallback( onClose )
    print 'connecting to node...'
    nodeClient.connect( nodeAddr, onConnect )
    reactor.run()

if __name__ == '__main__' :
    main()
