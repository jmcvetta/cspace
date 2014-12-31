import logging
from ncrypt.x509 import X509Error
from ncrypt.ssl import SSLConnection, SSLError
from nitro.async import AsyncOp
from nitro.tcp import tcpConnect
from nitro.ssl import sslConnect, sslAbort, SSLMessageStream
from nitro.bencode import encode, decode, DecodeError
from cspace.network.sslutil import makeSSLContext
from cspace.network.location import lookupUser
from cspace.network.routerclient import routerConnect

logger = logging.getLogger( 'cspace.network.connector' )

CACHED_CONNECT_REFRESH = 3

class Dummy : pass

def _authenticateUser( sock, sslContext, remotePublicKey, reactor, callback=None ) :
    def doCancel() :
        connectOp.cancel()
        sslAbort( sslConn )
    def onSSLConnect( err ) :
        if err is not None :
            logger.error( 'ssl connect err=%s' % str(err) )
            sslAbort( sslConn )
            op.notify( None )
            return
        try :
            peerCert = sslConn.getPeerCertificate()
            peerKey = peerCert.getPublicKey()
        except (SSLError,X509Error), e :
            logger.exception( 'ssl connect error' )
            sslAbort( sslConn )
            op.notify( None )
            return
        if peerKey.toDER_PublicKey() != remotePublicKey.toDER_PublicKey() :
            logger.error( 'ssl connect public key mismatch' )
            sslAbort( sslConn )
            op.notify( None )
            return
        op.notify( sslConn )
    sslConn = SSLConnection( sslContext, sock )
    connectOp = sslConnect( sslConn, reactor, onSSLConnect )
    op = AsyncOp( callback, doCancel )
    return op

def _directConnect( sslContext, remotePublicKey, directLocation,
        reactor, callback=None ) :
    def onConnect( connector ) :
        if connector.getError() != 0 :
            op.notify( None )
            return
        authOp = _authenticateUser( connector.getSock(), sslContext,
                remotePublicKey, reactor, op.notify )
        op.setCanceler( authOp.cancel )
    connectOp = tcpConnect( directLocation.addr, reactor, onConnect )
    op = AsyncOp( callback, connectOp.cancel )
    return op

def _routedConnect( sslContext, remotePublicKey, routerLocation,
        reactor, callback=None ) :
    def onConnect( sock ) :
        if sock is None :
            op.notify( None )
            return
        authOp = _authenticateUser( sock, sslContext,
                remotePublicKey, reactor, op.notify )
        op.setCanceler( authOp.cancel )
    connectOp = routerConnect( routerLocation.routerAddr, routerLocation.routerId,
            reactor, onConnect )
    op = AsyncOp( callback, connectOp.cancel )
    return op

def _locationConnect( localUserName, localRSAKey, localPublicIP,
        remotePublicKey, remoteLocation, reactor, callback=None ) :
    sslContext = makeSSLContext( localUserName, localRSAKey )
    directLocations = remoteLocation.directLocations
    routedLocations = remoteLocation.routedLocations
    remotePublicIP = remoteLocation.publicIP
    maybePublic = False
    for dloc in directLocations :
        if remotePublicIP == dloc.addr[0] :
            maybePublic = True
            break
    samePublic = (localPublicIP == remotePublicIP)
    connOps = {}
    def doCancel() :
        for connOp in connOps.keys() :
            connOp.cancel()
        connOps.clear()
    def onConnect( connOp, sslConn ) :
        del connOps[connOp]
        if sslConn is None :
            if not connOps :
                op.notify( None )
            return
        doCancel()
        op.notify( sslConn )
    def doDirectConnect( dloc ) :
        connOp = _directConnect( sslContext, remotePublicKey,
                dloc, reactor, lambda x : onConnect(connOp,x) )
        connOps[connOp] = 1
    def doRoutedConnect( rloc ) :
        connOp = _routedConnect( sslContext, remotePublicKey,
                rloc, reactor, lambda x : onConnect(connOp,x) )
        connOps[connOp] = 1
    def onTimer() :
        del connOps[timerOp]
        for rloc in routedLocations : doRoutedConnect( rloc )
        if not connOps :
            op.notify( None )
    for dloc in directLocations : doDirectConnect( dloc )
    routedDelay = 0
    if (maybePublic or samePublic) and (len(connOps) > 0) :
        routedDelay = 1
    timerOp = reactor.callLater( routedDelay, onTimer )
    connOps[timerOp] = 1
    op = AsyncOp( callback, doCancel )
    return op

def _userConnect( localUserName, localRSAKey, localPublicIP,
        remotePublicKey, locationCache, reactor, callback=None ) :
    obj = Dummy()
    def doCancel() :
        if obj.connectOp :
            obj.connectOp.cancel()
            obj.connectOp = None
        if obj.lookupOp :
            obj.lookupOp.cancel()
            obj.lookupOp = None
        if obj.timerOp :
            obj.timerOp.cancel()
            obj.timerOp = None
    def onError() :
        doCancel()
        op.notify( None )
    def doNotify( sslConn ) :
        doCancel()
        op.notify( sslConn )
    def onConnect( sslConn ) :
        obj.connectOp = None
        if sslConn is not None :
            doNotify( sslConn )
            return
        if not obj.cached :
            onError()
            return
        if obj.timerOp :
            obj.timerOp.cancel()
            obj.timerOp = None
        old = obj.location
        obj.location = locationCache.getLocation( remotePublicKey )
        if old != obj.location :
            if obj.location is None :
                onError()
                return
            if obj.lookupOp :
                obj.lookupOp.cancel()
                obj.lookupOp = None
            obj.cached = False
            doConnectLocation()
            return
        if not obj.lookupOp :
            obj.lookupOp = locationCache.refreshUser( remotePublicKey,
                    onLookup )
    def onTimer() :
        obj.timerOp = None
        assert not obj.lookupOp
        obj.lookupOp = locationCache.refreshUser( remotePublicKey,
                onLookup )
    def onLookup( location ) :
        obj.lookupOp = None
        assert not obj.timerOp
        if location is None :
            onError()
            return
        if obj.location == location :
            if obj.connectOp :
                obj.cached = False
                return
            onError()
            return
        obj.cached = False
        obj.location = location
        if obj.connectOp :
            obj.connectOp.cancel()
            obj.connectOp = None
        doConnectLocation()
    def doConnectLocation() :
        obj.connectOp = _locationConnect( localUserName, localRSAKey,
                localPublicIP, remotePublicKey, obj.location,
                reactor, onConnect )
    obj.cached = False
    obj.lookupOp = None
    obj.connectOp = None
    obj.timerOp = None
    obj.location = locationCache.getLocation( remotePublicKey )
    if obj.location is None :
        obj.lookupOp = locationCache.refreshUser( remotePublicKey,
                onLookup )
    else :
        doConnectLocation()
        timeout = CACHED_CONNECT_REFRESH
        obj.timerOp = reactor.callLater( timeout, onTimer )
        obj.cached = True
    op = AsyncOp( callback, doCancel )
    return op

def _serviceConnect( sslConn, serviceName, reactor, callback=None ) :
    def doCancel() :
        ms.shutdown()
        sslAbort( sslConn )
    def onClose( *args ) :
        doCancel()
        op.notify( None )
    def onInput( data ) :
        try :
            result = decode( data )
            assert type(result) is int
            assert result == 0
        except :
            doCancel()
            op.notify( None )
            return
        ms.shutdown()
        op.notify( sslConn )
    ms = SSLMessageStream( sslConn, reactor )
    ms.setCloseCallback( onClose )
    ms.setErrorCallback( onClose )
    ms.setInvalidMessageCallback( onClose )
    ms.setInputCallback( onInput )
    ms.sendMessage( encode(serviceName) )
    ms.enableRead( True )
    op = AsyncOp( callback, doCancel )
    return op

def userServiceConnect( localUserName, localRSAKey, localPublicIP,
        remotePublicKey, remoteServiceName, locationCache,
        reactor, callback=None ) :
    def onConnect( sslConn ) :
        if sslConn is None :
            op.notify( sslConn )
            return
        serviceOp = _serviceConnect( sslConn, remoteServiceName,
                reactor, op.notify )
        op.setCanceler( serviceOp.cancel )
    connectOp = _userConnect( localUserName, localRSAKey, localPublicIP,
            remotePublicKey, locationCache, reactor, onConnect )
    op = AsyncOp( callback, connectOp.cancel )
    return op
