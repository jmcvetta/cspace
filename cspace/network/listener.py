from ncrypt.x509 import X509Error
from ncrypt.ssl import SSLConnection, SSLError
from nitro.async import AsyncOp
from nitro.tcp import tcpListen
from nitro.ssl import sslAccept, sslAbort, SSLMessageStream
from nitro.bencode import encode, decode, DecodeError
from cspace.network.localip import getLocalIP
from cspace.network.sslutil import makeSSLContext
from cspace.network.routerclient import RouterClient, routerAccept
from cspace.network.location import DirectLocation, RoutedLocation,\
        UserLocation, publishUserLocation

#logic for listener:
# bind locally on ADDR_ANY
# get a bunch of router nodes
# register with all of them
# determine localip
# build userlocation object and publish it
# then periodically keep publishing it
# re-publish user location when a router registration connection is lost
# shutdown when losing all router registration connections

#notifications:
# notify first successful location publish
# notify incoming connection after successful ssl handshake
# notify close when all router connections are lost

LOCATION_PUBLISH_TIMEOUT = 5*60

class Dummy : pass

class BaseIntStore( object ) :
    # fetch stored int value
    def get( self ) : raise NotImplementedError
    # save stored int value
    def set( self, value ) : raise NotImplementedError

def _publishLocation( rsaKey, location, updateLevelStore,
        dhtClient, nodeTable, callback=None ) :
    def onPublish( result, updateLevel ) :
        updateLevelStore.set( updateLevel )
        op.notify( result )
    publishOp = publishUserLocation( rsaKey, location,
            updateLevelStore.get(), dhtClient, nodeTable,
            onPublish )
    op = AsyncOp( callback, publishOp.cancel )
    return op

def _registerWithRouter( routerAddr, reactor, callback=None ) :
    obj = Dummy()
    def doCancel() :
        if obj.closed : return
        obj.closed = True
        client.close()
    def onError() :
        if obj.closed : return
        obj.closed = True
        client.close()
        op.notify( None, None, None )
    def checkNotify() :
        if (obj.routerId is not None) and (obj.publicIP is not None) :
            client.enableIncoming( False )
            op.notify( client, obj.routerId, obj.publicIP )
    def onRegister( routerId ) :
        if routerId is None :
            onError()
            return
        obj.routerId = routerId
        checkNotify()
    def onPing( publicAddr ) :
        if publicAddr is None :
            onError()
            return
        obj.publicIP = publicAddr[0]
        checkNotify()
    def onConnect( result ) :
        if not result :
            onError()
            return
        client.callPing( onPing )
        client.callRegister( onRegister, incomingCallback=None )
    obj.closed = False
    obj.routerId = None
    obj.publicIP = None
    client = RouterClient( routerAddr, reactor )
    client.connect( onConnect )
    op = AsyncOp( callback, doCancel )
    return op

def _registerWithRouters( routerAddrList, reactor, callback=None ) :
    obj = Dummy()
    def doCancel() :
        for regOp in obj.registerOps.keys() :
            regOp.cancel()
        obj.registerOps.clear()
        for client,rid,ip in obj.result :
            client.close()
        del obj.result[:]
    def checkNotify() :
        if obj.registerOps :
            return False
        if obj.timerOp :
            obj.timerOp.cancel()
            obj.timerOp = None
        op.notify( obj.result )
        return True
    def onTimer() :
        obj.timerOp = None
        for regOp in obj.registerOps.keys() :
            regOp.cancel()
        obj.registerOps.clear()
        checkNotify()
    def onRegister( regOp, client, routerId, publicIP ) :
        del obj.registerOps[regOp]
        if client is not None :
            obj.result.append( (client,routerId,publicIP) )
        if checkNotify() :
            return
        if (obj.timerOp is not None) and (len(obj.result) == 1) :
            obj.timerOp = reactor.callLater( 10, onTimer )
    obj.registerOps = {}
    obj.timerOp = None
    obj.result = []
    def doRegister( routerAddr ) :
        regOp = _registerWithRouter( routerAddr, reactor,
                lambda x,y,z : onRegister(regOp,x,y,z) )
        obj.registerOps[regOp] = 1
    for routerAddr in routerAddrList :
        doRegister( routerAddr )
    op = AsyncOp( callback, doCancel )
    return op

def _getMajority( values ) :
    assert values
    freq = {}
    for v in values :
        freq[v] = freq.get(v,0) + 1
    items = [(v,k) for k,v in freq.items()]
    items.sort()
    return items[-1][1]

def _initializeListen( rsaKey, updateLevelStore, dhtClient,
        nodeTable, reactor, callback=None ) :
    obj = Dummy()
    def doCancel() :
        if obj.publishOp :
            obj.publishOp.cancel()
            obj.publishOp = None
        for client,rid,ip in obj.routerList :
            client.close()
        del obj.routerList[:]
        if obj.registerOp :
            obj.registerOp.cancel()
            obj.registerOp = None
        obj.listener.close()
        obj.listener = None
    def onError() :
        doCancel()
        op.notify( None )
    def onPublish( result ) :
        obj.publishOp = None
        if not result :
            onError()
            return
        data = (obj.listener,obj.routerList,obj.publicIP,\
                obj.localIP,obj.localPort)
        op.notify( data )
    def getLocation() :
        directLocations = [DirectLocation((obj.localIP,obj.localPort))]
        routedLocations = [RoutedLocation(rc.getRouterAddr(),rid)\
                for rc,rid,ip in obj.routerList]
        location = UserLocation( directLocations, routedLocations,
                obj.publicIP )
        return location
    def onRegister( routerList ) :
        obj.registerOp = None
        if not routerList :
            onError()
            return
        obj.routerList = routerList
        obj.localIP = getLocalIP()
        if obj.localIP is None :
            onError()
            return
        ipList = [ip for client,rid,ip in obj.routerList]
        obj.publicIP = _getMajority( ipList )
        obj.publishOp = _publishLocation( rsaKey, getLocation(),
                updateLevelStore, dhtClient, nodeTable, onPublish )
    obj.listener = tcpListen( ('',0), reactor, None )
    obj.listener.enable( False )
    obj.localPort = obj.listener.getSock().getsockname()[1]
    obj.registerOp = _registerWithRouters( nodeTable.getLiveNodes(),
            reactor, onRegister )
    obj.routerList = []
    obj.publishOp = None
    op = AsyncOp( callback, doCancel )
    return op

def _sslHandshake( sock, sslContext, reactor, callback=None ) :
    def doCancel() :
        acceptOp.cancel()
        sslAbort( sslConn )
    def onSSLAccept( err ) :
        if err is not None :
            sslAbort( sslConn )
            op.notify( None )
            return
        try :
            peerCert = sslConn.getPeerCertificate()
            peerKey = peerCert.getPublicKey()
            peerName = peerCert.getSubject().lookupEntry('commonName')
        except (SSLError,X509Error) :
            sslAbort( sslConn )
            op.notify( None )
            return
        data = (sslConn,peerKey,peerName)
        op.notify( data )
    sslConn = SSLConnection( sslContext, sock )
    acceptOp = sslAccept( sslConn, reactor, onSSLAccept )
    op = AsyncOp( callback, doCancel )
    return op

def _readServiceName( sock, sslContext, reactor, callback=None ) :
    obj = Dummy()
    def doCancel() :
        if obj.handshakeOp :
            obj.handshakeOp.cancel()
            obj.handshakeOp = None
        if obj.stream :
            obj.stream.close()
            obj.stream = None
    def onError() :
        doCancel()
        op.notify( None )
    def onClose( *args ) :
        onError()
    def onInput( data ) :
        try :
            serviceName = decode( data )
            assert type(serviceName) is str
            assert len(serviceName) > 0
        except :
            onError()
            return
        obj.stream.shutdown()
        obj.stream = None
        op.notify( (obj.sslConn,obj.peerKey,obj.peerName,serviceName) )
    def onHandshake( data ) :
        obj.handshakeOp = None
        if data is None :
            onError()
            return
        obj.sslConn,obj.peerKey,obj.peerName = data
        obj.stream = SSLMessageStream( obj.sslConn, reactor )
        obj.stream.setCloseCallback( onClose )
        obj.stream.setErrorCallback( onClose )
        obj.stream.setInvalidMessageCallback( onClose )
        obj.stream.setInputCallback( onInput )
        obj.stream.enableRead( True )
    obj.handshakeOp = _sslHandshake( sock, sslContext, reactor, onHandshake )
    obj.stream = None
    op = AsyncOp( callback, doCancel )
    return op

def acceptIncoming( acceptFlag, sslConn, reactor, callback=None ) :
    def doCancel() :
        stream.close()
    def onError( *args ) :
        doCancel()
        op.notify( None )
    def onWriteComplete() :
        stream.shutdown()
        op.notify( sslConn )
    stream = SSLMessageStream( sslConn, reactor )
    stream.setCloseCallback( onError )
    stream.setErrorCallback( onError )
    stream.setInvalidMessageCallback( onError )
    stream.setInputCallback( onError )
    stream.setWriteCompleteCallback( onWriteComplete )
    if acceptFlag :
        data = 0
    else :
        data = -1
    stream.sendMessage( encode(data) )
    op = AsyncOp( callback, doCancel )
    return op

class UserListener( object ) :
    (STOPPED,STARTING,STARTED,STOPPING) = range(4)
    def __init__( self, userName, rsaKey, updateLevelStore,
            dhtClient, nodeTable, reactor ) :
        self.userName = userName
        self.rsaKey = rsaKey
        self.updateLevelStore = updateLevelStore
        self.dhtClient = dhtClient
        self.nodeTable = nodeTable
        self.reactor = reactor
        self.state = self.STOPPED
        self.closeCallback = None
        self.sslContext = makeSSLContext( userName, rsaKey )
        self.incomingCallback = None

        self.initOp = None
        self.tcpListener = None
        self.routerList = None
        self.publicIP = None
        self.localIP = None
        self.localPort = None
        self.publishOp = None
        self.otherOps = {}

    def setIncomingCallback( self, incomingCallback ) :
        self.incomingCallback = incomingCallback

    def setCloseCallback( self, closeCallback ) :
        self.closeCallback = closeCallback

    def getPublicIP( self ) : return self.publicIP

    def _shutdownInternal( self ) :
        while self.otherOps :
            op,x = self.otherOps.popitem()
            op.cancel()
        if self.publishOp is not None :
            self.publishOp.cancel()
            self.publishOp = None
        if self.tcpListener is not None :
            self.tcpListener.close()
            self.tcpListener = None
        if self.routerList is not None :
            for rc,rid,ip in self.routerList :
                rc.close()
            self.routerList = None
        self.publicIP = None
        self.localIP = None
        self.localPort = None
        if self.initOp is not None :
            self.initOp.cancel()
            self.initOp = None

    def close( self ) :
        self._shutdownInternal()
        self.state = self.STOPPED

    def closeNotify( self ) :
        self.close()
        if self.closeCallback :
            self.closeCallback()

    def start( self, startCallback ) :
        assert self.state == self.STOPPED
        self.state = self.STARTING
        def onError() :
            self.state = self.STOPPED
            startCallback( False )
        def onSuccess() :
            self.state = self.STARTED
            startCallback( True )
        def enableRouter( rc ) :
            rc.setIncomingCallback( lambda cid : self._onIncomingRouted(rc,cid) )
            rc.setCloseCallback( lambda : self._onRouterClose(rc) )
            rc.enableIncoming( True )
        def onInit( result ) :
            self.initOp = None
            if result is None :
                onError()
                return
            self.tcpListener,self.routerList,self.publicIP,\
                    self.localIP,self.localPort = result
            self.tcpListener.setCallback( self._onIncomingTCP )
            self.tcpListener.enable( True )
            for rc,rid,ip in self.routerList :
                enableRouter( rc )
            self._initPublishTimer()
            onSuccess()
        self.initOp = _initializeListen( self.rsaKey,
                self.updateLevelStore, self.dhtClient,
                self.nodeTable, self.reactor, onInit )

    def _initPublishTimer( self ) :
        def onDummyPing( publicAddr ) :
            pass
        def getLocation() :
            directLocations = [DirectLocation((self.localIP,self.localPort))]
            routedLocations = [RoutedLocation(rc.getRouterAddr(),rid)\
                    for rc,rid,ip in self.routerList]
            location = UserLocation( directLocations, routedLocations,
                    self.publicIP )
            return location
        def onPublish( result ) :
            self.publishOp = self.reactor.callLater( timeout, onTimer )
        def onTimer() :
            self.publishOp = _publishLocation( self.rsaKey,
                    getLocation(), self.updateLevelStore,
                    self.dhtClient, self.nodeTable, onPublish )
            for rc,rid,ip in self.routerList :
                rc.callPing( onDummyPing )
        timeout = LOCATION_PUBLISH_TIMEOUT
        self.publishOp = self.reactor.callLater( timeout, onTimer )

    def _onRouterClose( self, routerClient ) :
        assert self.state == self.STARTED
        index = -1
        for i,router in enumerate(self.routerList) :
            if router[0] is routerClient :
                index = i
                break
        assert index >= 0
        del self.routerList[index]
        if not self.routerList :
            self.closeNotify()

    def _onIncomingRouted( self, routerClient, connectionId ) :
        assert self.state == self.STARTED
        def onAccept( sock ) :
            del self.otherOps[acceptOp]
            if sock is None :
                return
            self._onIncomingTCP( sock )
        acceptOp = routerAccept( routerClient.getRouterAddr(),
                connectionId, self.reactor, onAccept )
        self.otherOps[acceptOp] = 1

    def _onIncomingTCP( self, sock ) :
        assert self.state == self.STARTED
        def onRead( data ) :
            del self.otherOps[op]
            if data is None :
                return
            sslConn,peerKey,peerName,serviceName = data
            if self.incomingCallback is None :
                sslAbort( sslConn )
                return
            self.incomingCallback( sslConn, peerKey, peerName, serviceName )
        op = _readServiceName( sock, self.sslContext,
                self.reactor, onRead )
        self.otherOps[op] = 1

    def stop( self, stopCallback ) :
        assert self.state == self.STARTED
        self.state = self.STOPPING
        self._shutdownInternal()
        def onPublish( result ) :
            del self.otherOps[stopOp]
            self.state = self.STOPPED
            stopCallback( result )
        emptyLocation = UserLocation( [], [], '' )
        stopOp = _publishLocation( self.rsaKey, emptyLocation,
                self.updateLevelStore, self.dhtClient,
                self.nodeTable, onPublish )
        self.otherOps[stopOp] = 1
