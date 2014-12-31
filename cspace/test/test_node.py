import logging
logging.getLogger().addHandler( logging.StreamHandler() )

from nitro.selectreactor import SelectReactor
from cspace.node.client import NodeClient

reactor = None
nodeAddr = None
nodeClient = None

def Poll() :
    reactor.run( 1 )

def Connect() :
    def onConnect( errCode ) :
        print 'onConnect: errCode=%d' % errCode
        reactor.stop()
    op = nodeClient.connect( nodeAddr, onConnect )
    reactor.run()

def Close() :
    nodeClient.close()

def Get( k ) :
    def onGet( errCode, value ) :
        print 'onGet: errCode=%d, value=%s' % (errCode,value)
        reactor.stop()
    op = nodeClient.callGet( k, onGet )
    reactor.run()

def Put( k, v, timeout ) :
    def onPut( errCode, value ) :
        print 'onPut: errCode=%d, value=%s' % (errCode,value)
        reactor.stop()
    op = nodeClient.callPut( k, v, timeout, onPut )
    reactor.run()

def Del( k ) :
    def onDel( errCode, value ) :
        print 'onDel: errCode=%d, value=%s' % (errCode,value)
        reactor.stop()
    op = nodeClient.callDel( k, onDel )
    reactor.run()

def GetAll() :
    def onGetAll( errCode, value ) :
        print 'onGetAll: errCode=%d, value=%s' % (errCode,value)
        reactor.stop()
    op = nodeClient.callGetAll( onGetAll )
    reactor.run()

def Register() :
    def onRegister( errCode, value ) :
        print 'onRegister: errCode=%d, value=%s' % (errCode,value)
        reactor.stop()
    op = nodeClient.callRegister( onRegister )
    reactor.run()

def onClose() :
    print 'onClose'

def imain() :
    global reactor, nodeClient, nodeAddr
    reactor = SelectReactor()
    nodeAddr = ('127.0.0.1',13542)
    nodeClient = NodeClient( reactor )
    nodeClient.setCloseCallback( onClose )

def main() :
    pass

if __name__ == '__main__' :
    main()
