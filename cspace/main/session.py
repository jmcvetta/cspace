import StringIO
from socket import socket, AF_INET, SOCK_DGRAM
from nitro.async import AsyncOp
from nitro.ssl import sslAbort
from cspace.util.validate import validateInetAddress
from cspace.util.statemachine import StateMachine
from cspace.dht.rpc import RPCSocket
from cspace.dht.client import DHTClient
from cspace.network.nodetable import NodeTable, NodeTableRefresher
from cspace.network.nodetable import initNodeTable
from cspace.network.location import lookupUser
from cspace.network.locationcache import LocationCache
from cspace.network.listener import BaseIntStore
from cspace.network.listener import UserListener, acceptIncoming
from cspace.network.connector import userServiceConnect
from cspace.network.noderunner import NodeRunner
from cspace.main.common import localSettings, profileSettings, \
        isValidUserName, isValidServiceName
from cspace.main.permissions import Permissions
from cspace.main.permissions import ACCESS_ALLOW, ACCESS_DENY, ACCESS_PROMPT
from cspace.main.incomingprompt import IncomingPromptWindow

USERLIST_PUBLISH_TIMEOUT = 5*60

class Dummy : pass

class UpdateLevelStore( BaseIntStore ) :
    def __init__( self, profile ) :
        self.entry = profile.storeEntry + '/UpdateLevel'

    def get( self ) :
        return profileSettings().getInt( self.entry, 1 )

    def set( self, value ) :
        return profileSettings().setInt( self.entry, value )

def _loadNodeCache( nodeTable ) :
    data = localSettings().getData( 'NodeCache', '' )
    for addr in data.split() :
        try :
            ip,port = addr.split( ':' )
            port = int(port)
            nodeAddr = (ip,port)
            validateInetAddress( nodeAddr )
        except :
            continue
        nodeTable.addNode( nodeAddr )

def _saveNodeCache( nodeTable ) :
    out = StringIO.StringIO()
    for addr in nodeTable.getAllNonSeedNodes() :
        print>>out, '%s:%d' % addr
    return localSettings().setData( 'NodeCache', out.getvalue() )

class UserSession( object ) :
    (OFFLINE,CONNECTING,ONLINE,DISCONNECTING) = range(4)

    def __init__( self, seedNodes, reactor ) :
        self.seedNodes = seedNodes
        self.reactor = reactor
        self.sm = StateMachine( self.OFFLINE )
        self.services = {}
        self.nodeTable = None
        self.nodeTableRefresher = None
        self.rpcSocket = None
        self.dhtClient = None
        self.locationCache = None
        self.profile = None
        self.listener = None
        self.permissions = None
        #self.nodeRunner = None

    def getProfile( self ) : return self.profile
    def getPermissions( self ) : return self.permissions

    def isOnline( self ) : return self.sm.current() == self.ONLINE

    def registerService( self, serviceName, serviceCallback ) :
        assert isValidServiceName(serviceName)
        if serviceName in self.services :
            return False
        self.services[serviceName] = serviceCallback
        return True

    def unregisterService( self, serviceName ) :
        if self.services.pop(serviceName,None) is None :
            return False
        return True

    def goOnline( self, profile ) :
        assert self.sm.current() == self.OFFLINE
        obj = Dummy()
        def doCleanup() :
            if obj.initNodeTableOp is not None :
                obj.initNodeTableOp.cancel()
            if obj.nodeTableRefresher is not None :
                obj.nodeTableRefresher.close()
            if obj.listener is not None :
                obj.listener.close()
            obj.rpcSocket.close()
        def onOffline() :
            #self.nodeRunner.close()
            #self.nodeRunner = None
            self.listener.close()
            self.listener = None
            self.permissions = None
            self.locationCache.close()
            self.locationCache = None
            self.nodeTableRefresher.close()
            self.nodeTableRefresher = None
            _saveNodeCache( self.nodeTable )
            self.nodeTable = None
            self.dhtClient = None
            self.rpcSocket.close()
            self.rpcSocket = None
            self.profile = None
        def onListenerStart( result ) :
            if not result :
                self.sm.removeCallback( obj.callbackId )
                doCleanup()
                self.sm.change( self.OFFLINE )
                return
            obj.listener.setCloseCallback( self._onListenerClose )
            obj.listener.setIncomingCallback( self._onIncoming )
            self.profile = profile
            self.rpcSocket = obj.rpcSocket
            self.dhtClient = obj.dhtClient
            self.nodeTable = obj.nodeTable
            self.nodeTableRefresher = obj.nodeTableRefresher
            self.locationCache = LocationCache( self.dhtClient,
                    self.nodeTable, self.reactor )
            self.listener = obj.listener
            self.permissions = Permissions( profile, self.services.keys() )
            if self.permissions.isModified() :
                self.permissions.savePermissions()
            #self.nodeRunner = NodeRunner( self.nodeTable, self.reactor )
            self.sm.removeCallback( obj.callbackId )
            self.sm.appendCallback( onOffline, dest=self.OFFLINE, single=True )
            self.sm.change( self.ONLINE )
        def onNodeTableInit() :
            obj.initNodeTableOp = None
            obj.nodeTableRefresher = NodeTableRefresher(
                    obj.nodeTable, obj.dhtClient, self.reactor )
            updateLevelStore = UpdateLevelStore( profile )
            obj.listener = UserListener( profile.name,
                    profile.rsaKey, updateLevelStore,
                    obj.dhtClient, obj.nodeTable, self.reactor )
            obj.listener.start( onListenerStart )
        self.sm.change( self.CONNECTING )
        obj.callbackId = self.sm.insertCallback( doCleanup,
                src=self.CONNECTING, single=True )
        obj.nodeTable = NodeTable( self.seedNodes )
        #_loadNodeCache( obj.nodeTable )
        udpSock = socket( AF_INET, SOCK_DGRAM )
        udpSock.bind( ('',0) )
        obj.rpcSocket = RPCSocket( udpSock, self.reactor )
        obj.dhtClient = DHTClient( obj.rpcSocket,
                nodeTracker=obj.nodeTable )
        obj.initNodeTableOp = initNodeTable( obj.nodeTable,
                obj.dhtClient, self.reactor, onNodeTableInit )
        obj.nodeTableRefresher = None
        obj.listener = None

    def _onListenerClose( self ) :
        self.sm.change( self.OFFLINE )

    def _rejectIncoming( self, sslConn, callback=None ) :
        def onReject( sslConn ) :
            if sslConn is None :
                op.notify( False )
                return
            sslAbort( sslConn )
            op.notify( True )
        rejectOp = acceptIncoming( False, sslConn, self.reactor,
                onReject )
        op = AsyncOp( callback, rejectOp.cancel )
        return op

    def _acceptIncoming( self, sslConn, serviceName, peerKey,
            contactName, incomingName, callback=None ) :
        def onAccept( sslConn ) :
            if sslConn is None :
                op.notify( False )
                return
            serviceCallback = self.services.get( serviceName )
            if serviceCallback is None :
                sslAbort( sslConn )
                op.notify( False )
                return
            serviceCallback( sslConn, peerKey, contactName,
                    incomingName )
            op.notify( True )
        acceptOp = acceptIncoming( True, sslConn, self.reactor,
                onAccept )
        op = AsyncOp( callback, acceptOp.cancel )
        return op

    def _promptIncoming( self, sslConn, serviceName, peerKey,
            contactName, incomingName, callback=None ) :
        def doCancel() :
            promptOp.cancel()
            sslAbort( sslConn )
        def onPromptResult( promptResult ) :
            if not promptResult :
                rejectOp = self._rejectIncoming( sslConn, op.notify )
                op.setCanceler( rejectOp.cancel )
            else :
                acceptOp = self._acceptIncoming( sslConn, serviceName,
                        peerKey, contactName, incomingName, op.notify )
                op.setCanceler( acceptOp.cancel )
        promptName = contactName
        if not promptName :
            promptName = '(Unknown %s)' % incomingName
        promptOp = IncomingPromptWindow( promptName, serviceName,
                self.reactor, onPromptResult ).getOp()
        op = AsyncOp( callback, doCancel )
        return op

    def _onIncoming( self, sslConn, peerKey, incomingName,
            serviceName ) :
        assert self.sm.current() == self.ONLINE
        if not isValidUserName(incomingName) :
            sslAbort( sslConn )
            return
        if not isValidServiceName(serviceName) :
            sslAbort( sslConn )
            return
        contact = self.profile.getContactByPublicKey( peerKey )
        if contact is None :
            contactName = ''
        else :
            contactName = contact.name

        if serviceName not in self.services :
            action = ACCESS_DENY
        else :
            action = self.permissions.execute( contactName,
                    serviceName )
        def onActionDone( result ) :
            self.sm.removeCallback( callbackId )
        if action == ACCESS_DENY :
            actionOp = self._rejectIncoming( sslConn, onActionDone )
        elif action == ACCESS_ALLOW :
            actionOp = self._acceptIncoming( sslConn, serviceName,
                    peerKey, contactName, incomingName, onActionDone )
        else :
            assert action == ACCESS_PROMPT
            actionOp = self._promptIncoming( sslConn, serviceName,
                    peerKey, contactName, incomingName, onActionDone )
        callbackId = self.sm.insertCallback( actionOp.cancel,
                src=self.ONLINE, single=True )

    def goOffline( self ) :
        assert self.sm.current() == self.ONLINE
        def onStop( result ) :
            self.sm.change( self.OFFLINE )
        self.sm.change( self.DISCONNECTING )
        self.listener.stop( onStop )

    def shutdown( self ) :
        self.sm.change( self.OFFLINE )

    def probeUserOnline( self, publicKey, callback=None ) :
        assert self.sm.current() == self.ONLINE
        def onStateChange() :
            lookupOp.cancel()
            op.notify( False )
        def doCancel() :
            lookupOp.cancel()
            self.sm.removeCallback( callbackId )
        def onLookup( location ) :
            self.sm.removeCallback( callbackId )
            if location is None :
                op.notify( False )
                return
            if (not location.directLocations) and (not location.routedLocations) :
                op.notify( False )
                return
            op.notify( True )
        lookupOp = self.locationCache.refreshUser( publicKey,
                onLookup )
        callbackId = self.sm.insertCallback( onStateChange,
                src=self.ONLINE, single=True )
        op = AsyncOp( callback, doCancel )
        return op

    def connectTo( self, publicKey, serviceName, callback=None ) :
        assert self.sm.current() == self.ONLINE
        def onStateChange() :
            connectOp.cancel()
            op.notify( -1, None )
        def doCancel() :
            connectOp.cancel()
            self.sm.removeCallback( callbackId )
        def onConnect( sslConn ) :
            self.sm.removeCallback( callbackId )
            if sslConn is None :
                op.notify( -1, None )
                return
            op.notify( 0, sslConn )
        connectOp = userServiceConnect( self.profile.name,
                self.profile.rsaKey, self.listener.getPublicIP(),
                publicKey, serviceName, self.locationCache,
                self.reactor, onConnect )
        callbackId = self.sm.insertCallback( onStateChange,
                src=self.ONLINE, single=True )
        op = AsyncOp( callback, doCancel )
        return op
