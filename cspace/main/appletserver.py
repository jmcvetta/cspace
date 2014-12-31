import os, sys, threading
from string import Template
from ncrypt.rand import bytes as rand_bytes
from ncrypt.rsa import RSAKey, RSAError
from nitro.selectreactor import SelectReactor
from nitro.tcp import tcpListen, TCPStream
from nitro.ssl import sslAbort
from nitro.linestream import TCPLineStream

from cspace.util.spawn import spawnProcess
from cspace.util.hexcode import hexEncode, hexDecode, HexDecodeError
from cspace.util.wordcode import wordEncode, wordDecode, WordDecodeError
from cspace.util.settings import getAppDir
from cspace.util.queue import ThreadQueue
from cspace.main.common import localSettings, appSettings, \
        isValidUserName, isValidServiceName
from cspace.main.sslbridge import SSLBridge

def _substituteMetaVars( s ) :
    if sys.platform == 'win32' :
        _metaDict = dict( python='python.exe', pythonw='pythonw.exe' )
    else :
        _metaDict = dict( python='python', pythonw='python' )
    _metaDict['approot'] = getAppDir()
    return Template( s ).safe_substitute( _metaDict )

def _readCommand( settings, entryPath ) :
    data = settings.getData( entryPath ).strip()
    lines = [line.strip() for line in data.split('\n')]
    return lines

class ServiceConfig( object ) :
    def _listServices( self, settings ) :
        services = []
        for entry in settings.listEntries('Services') :
            serviceName = entry.split('/')[-1]
            assert isValidServiceName(serviceName)
            serviceCommand = _readCommand( settings, entry )
            services.append( (serviceName,serviceCommand) )
        return services

    def listSystemServices( self ) :
        return self._listServices( appSettings() )

    def listUserServices( self ) :
        return self._listServices( localSettings() )

    def listActiveServices( self ) :
        sysServices = self.listSystemServices()
        userServices = self.listUserServices()
        serviceDict = {}
        out = []
        for x in userServices+sysServices :
            if x[0] in serviceDict : continue
            serviceDict[x[0]] = x
            out.append( x )
        return out

class ActionConfig( object ) :
    def _listActions( self, settings ) :
        actions = []
        for entry in settings.listEntries('ContactActions') :
            actionDir = entry.split('/')[-1]
            assert isValidServiceName(actionDir)
            actionName = settings.getData( entry+'/Action' ).strip()
            actionCommand = _readCommand( settings, entry+'/Command' )
            actionOrder = settings.getInt(entry+'/SortOrder',10000)
            actions.append( (actionDir,actionName,actionCommand,actionOrder) )
        return actions

    def listSystemActions( self ) :
        return self._listActions( appSettings() )

    def listUserActions( self ) :
        return self._listActions( localSettings() )

    def listActiveActions( self ) :
        sysActions = self.listSystemActions()
        userActions = self.listUserActions()
        actionDict = {}
        out = []
        for x in userActions+sysActions :
            if x[0] in actionDict : continue
            actionDict[x[0]] = x
            out.append( x )
        return out

class BridgeThread( threading.Thread ) :
    def __init__( self ) :
        threading.Thread.__init__( self )
        self.reactor = SelectReactor()
        self.threadQueue = ThreadQueue( self._onMessage, self.reactor )
        self.bridges = {}
        self.start()

    def _onMessage( self, msg ) :
        cmd,args = msg[0],msg[1:]
        if cmd == 'bridge' :
            sock,sslConn = args
            bridge = SSLBridge( sock, sslConn, self.reactor )
            self.bridges[bridge] = 1
            bridge.setCloseCallback( lambda : self._onBridgeClosed(bridge) )
        elif cmd == 'clear' :
            for b in self.bridges.keys() :
                b.shutdown()
            self.bridges.clear()
        elif cmd == 'stop' :
            for b in self.bridges.keys() :
                b.shutdown()
            self.bridges.clear()
            self.reactor.stop()

    def _onBridgeClosed( self, bridge ) :
        del self.bridges[bridge]

    def run( self ) :
        self.reactor.run()

class AppletConnection( object ) :
    DEFAULT = 0
    CONNECTING = 1
    WAITING_BRIDGE = 2
    LISTENER = 3
    CLOSED = 4
    def __init__( self, sock, reactor, appletServer ) :
        self.reactor = reactor
        self.stream = TCPLineStream( sock, reactor )
        self.appletServer = appletServer
        self.appletServer.appletConnections[self] = 1
        self.session = appletServer.session
        self.incoming = appletServer.incoming
        self.state = self.DEFAULT
        self._writeData = self.stream.writeData
        rt = {}
        self.requestTable = rt
        rt['echo'] = self._doEcho
        rt['getcontacts'] = self._doGetContacts
        rt['getpubkey'] = self._doGetPubKey
        rt['getcontactpubkeys'] = self._doGetContactPubKeys
        rt['connect'] = self._doConnect
        rt['connectpubkey'] = self._doConnectPubKey
        rt['accept'] = self._doAccept
        rt['getincomingpubkey'] = self._doGetIncomingPubKey
        rt['registerlistener'] = self._doRegisterListener
        rt['sendlistener'] = self._doSendListener
        self.stream.setInputCallback( self._onInput )
        self.stream.setCloseCallback( self._onClose )
        self.stream.setErrorCallback( self._onError )
        self.stream.enableRead( True )

    def _setClosed( self ) :
        del self.appletServer.appletConnections[self]
        self.state = self.CLOSED

    def shutdown( self, deferred=False ) :
        if self.state == self.CONNECTING :
            self.connectOp.cancel()
        elif self.state == self.LISTENER :
            self.appletServer.unregisterListener( self.listenerName )
        elif self.state == self.WAITING_BRIDGE :
            sslAbort( self.peerSSLConn )
        self.stream.close( deferred )
        self._setClosed()

    def _onClose( self ) :
        self.shutdown()

    def _onError( self, err, errMsg ) :
        self.shutdown()

    def _writeLine( self, line ) :
        self._writeData( line + '\r\n' )

    def _writeWords( self, words ) :
        words = [wordEncode(w) for w in words]
        self._writeData( ' '.join(words) + '\r\n' )

    def _writeError( self, msg ) :
        self._writeLine( 'ERROR %s' % msg )

    def _writeResult( self, words ) :
        self._writeWords( ['OK'] + words )

    def dispatchMessage( self, msg ) :
        assert self.state == self.LISTENER
        self._writeWords( ['MSG'] + msg )

    def _doEcho( self, words ) :
        self._writeResult( words )

    def _doGetContacts( self, words ) :
        if len(words) != 0 :
            self._writeError( 'Malformed request' )
            return
        if not self.session.isOnline() :
            self._writeError( 'Not online' )
            return
        names = self.session.getProfile().getContactNames()
        self._writeResult( [c.getNickName() for c in contacts] )

    def _doGetPubKey( self, words ) :
        if len(words) > 1 :
            self._writeError( 'Malformed request' )
            return
        if not self.session.isOnline() :
            self._writeError( 'Not online' )
            return
        if len(words) == 0 :
            keyData = self.session.getProfile().rsaKey.toDER_PublicKey()
            self._writeResult( [hexEncode(keyData)] )
            return
        contact = self.session.getProfile().getContactByName( words[0] )
        if contact is None :
            self._writeError( 'Unknown contact' )
            return
        self._writeResult( [hexEncode(contact.publicKeyData)] )

    def _doGetContactPubKeys( self, words ) :
        if len(words) != 0 :
            self._writeError( 'Malformed request' )
            return
        if not self.session.isOnline() :
            self._writeError( 'Not online' )
            return
        out = []
        profile = self.session.getProfile()
        for name in profile.getContactNames() :
            c = profile.getContactByName( name )
            out.extend( [c.name,hexEncode(c.publicKeyData)] )
        self._writeResult( out )

    def _connectInternal( self, publicKey, service ) :
        def onWriteComplete() :
            self.stream.shutdown()
            sock = self.stream.getSock()
            self.appletServer.bridgeThread.threadQueue.postMessage(
                    ('bridge',sock,self.peerSSLConn) )
            self._setClosed()
        def onConnect( err, sslConn ) :
            if err < 0 :
                self._writeError( 'Connect failed' )
                self.state = self.DEFAULT
                return
            self._writeResult( ['Connected'] )
            self.peerSSLConn = sslConn
            self.state = self.WAITING_BRIDGE
            self.stream.enableRead( False )
            self.stream.setWriteCompleteCallback( onWriteComplete )
        self.connectOp = self.session.connectTo( publicKey, service,
                onConnect )
        self.state = self.CONNECTING

    def _doConnect( self, words ) :
        if len(words) != 2 :
            self._writeError( 'Malformed request' )
            return
        contactName, service = words
        if not self.session.isOnline() :
            self._writeError( 'Not online' )
            return
        contact = self.session.getProfile().getContactByName( contactName )
        if not contact :
            self._writeError( 'Unknown contact' )
            return
        self._connectInternal( contact.publicKey, service )

    def _doConnectPubKey( self, words ) :
        if len(words) != 2 :
            self._writeError( 'Malformed request' )
            return
        hexPubKey, service = words
        if not self.session.isOnline() :
            self._writeError( 'Not online' )
            return
        try :
            pubKeyData = hexDecode( hexPubKey )
            pubKey = RSAKey()
            pubKey.fromDER_PublicKey( pubKeyData )
        except (HexDecodeError,RSAError) :
            self._writeError( 'Malformed publickey' )
            return
        self._connectInternal( pubKey, service )

    def _doAccept( self, words ) :
        if len(words) != 1 :
            self._writeError( 'Malformed request' )
            return
        connectionId = words[0]
        sslConn = self.incoming.acceptIncoming( connectionId )
        if not sslConn :
            self._writeError( 'Invalid connection' )
            return
        self._writeResult( ['Connected'] )
        self.peerSSLConn = sslConn
        self.state = self.WAITING_BRIDGE
        self.stream.enableRead( False )
        def onWriteComplete() :
            self.stream.shutdown()
            sock = self.stream.getSock()
            self.appletServer.bridgeThread.threadQueue.postMessage(
                    ('bridge',sock,self.peerSSLConn) )
            self._setClosed()
        self.stream.setWriteCompleteCallback( onWriteComplete )

    def _doGetIncomingPubKey( self, words ) :
        if len(words) != 1 :
            self._writeError( 'Malformed request' )
            return
        connectionId = words[0]
        peerKey = self.incoming.getPeerKey( connectionId )
        if not peerKey :
            self._writeError( 'Invalid connection' )
            return
        self._writeResult( [hexEncode(peerKey.toDER_PublicKey())] )

    def _doRegisterListener( self, words ) :
        if len(words) != 1 :
            self._writeError( 'Malformed request' )
            return
        listenerName = words[0]
        result = self.appletServer.registerListener( listenerName, self )
        if not result :
            self._writeError( 'Listener already registered' )
            return
        self.listenerName = listenerName
        self.state = self.LISTENER
        self._writeResult( ['Registered'] )

    def _doSendListener( self, words ) :
        if len(words) <= 1 :
            self._writeError( 'Malformed request' )
            return
        listenerName = words[0]
        listener = self.appletServer.getListener( listenerName )
        if listener is None :
            self._writeError( 'No such listener' )
            return
        listener.dispatchMessage( words[1:] )
        self._writeResult( ['Sent'] )

    def _onInput( self, line ) :
        assert self.state in (self.DEFAULT,self.CONNECTING,self.LISTENER)
        if self.state in (self.CONNECTING,self.LISTENER) :
            self._writeError( 'Junk received' )
            self.shutdown( deferred=True )
            return
        words = line.strip().split()
        if len(words) == 0 : return
        try :
            words = [wordDecode(w) for w in words]
        except WordDecodeError :
            self._writeError( 'Malformed request' )
            return
        cmd = words[0].lower()
        handler = self.requestTable.get( cmd, None )
        if not handler :
            self._writeError( 'Unknown request' )
            return
        handler( words[1:] )

class IncomingConnections( object ) :
    def __init__( self, reactor ) :
        self.reactor = reactor
        self.connections = {}

    def clearConnections( self ) :
        for sslConn,peerKey,timerOp in self.connections.values() :
            sslAbort( sslConn )
            timerOp.cancel()
        self.connections.clear()

    def addIncoming( self, sslConn, peerKey ) :
        while True :
            connectionId = hexEncode( rand_bytes(8) )
            if connectionId not in self.connections : break
        def onTimeout() : self._onTimeout( connectionId )
        timerOp = self.reactor.callLater( 30, onTimeout )
        self.connections[connectionId] = (sslConn,peerKey,timerOp)
        return connectionId

    def acceptIncoming( self, connectionId ) :
        info = self.connections.pop( connectionId, None )
        if info is None :
            return None
        sslConn,peerKey,timerOp = info
        timerOp.cancel()
        return sslConn

    def getPeerKey( self, connectionId ) :
        info = self.connections.get( connectionId )
        if info is None :
            return None
        return info[1]

    def _onTimeout( self, connectionId ) :
        sslConn,peerKey,timerOp = self.connections.pop( connectionId )
        sslAbort( sslConn )

class AppletServer( object ) :
    def __init__( self, session, actionManager, reactor ) :
        self.session = session
        self.actionManager = actionManager
        self.reactor = reactor
        self.listener = tcpListen( ('127.0.0.1',0), reactor, self._onNewConnection )
        self.listenPort = self.listener.getSock().getsockname()[1]
        print 'listenport = %d' % self.listenPort
        self.serviceConfig = ServiceConfig()
        self.actionConfig = ActionConfig()
        self.listeners = {}
        self.incoming = IncomingConnections( self.reactor )
        self.services = []
        self.appletConnections = {}
        for (service,command) in self.serviceConfig.listActiveServices() :
            def doRegisterService( service, command ) :
                def onService( sslConn, peerKey, contactName, incomingName ) :
                    self._onService( service, command, sslConn,
                            peerKey, contactName, incomingName )
                self.session.registerService( service, onService )
            doRegisterService( service, command )
            self.services.append( service )
        self.actions = []
        for (actionDir,action,command,order) in self.actionConfig.listActiveActions() :
            def doRegisterAction( actionDir, action, command, order ) :
                def onAction( contactName ) :
                    self._onAction( actionDir, action, command, contactName )
                return self.actionManager.registerAction( action, onAction, order )
            actionId = doRegisterAction( actionDir, action, command, order )
            self.actions.append( actionId )
            if actionDir == 'TextChat' :
                self.actionManager.setDefaultAction( actionId )
        self.bridgeThread = BridgeThread()

    def shutdown( self ) :
        self.incoming.clearConnections()
        appletConns = self.appletConnections.keys()
        for conn in appletConns :
            conn.shutdown()
        self.bridgeThread.threadQueue.postMessage( ('stop',) )
        self.bridgeThread.join()
        self.listener.close()

    def clearConnections( self ) :
        self.incoming.clearConnections()
        appletConns = self.appletConnections.keys()
        for conn in appletConns :
            conn.shutdown()
        self.bridgeThread.threadQueue.postMessage( ('clear',) )

    def getListenPort( self ) : return self.listenPort

    def registerListener( self, name, connection ) :
        conn = self.listeners.setdefault( name, connection )
        return conn is connection

    def unregisterListener( self, name ) :
        del self.listeners[name]

    def getListener( self, name ) :
        return self.listeners.get( name, None )

    def _onNewConnection( self, sock ) :
        AppletConnection( sock, self.reactor, self )

    def _findProgram( self, relPath ) :
        dirList = os.environ.get( 'PATH', '' ).split( ';' )
        for d in dirList :
            p = os.path.join( d, relPath )
            if os.path.isfile(p) :
                return p
        return relPath

    def _runCommand( self, command, envNew ) :
        env = dict( os.environ.items() )
        env.update( envNew )
        cmdLine = [_substituteMetaVars(x) for x in command]
        p = os.path.join( getAppDir(), cmdLine[0] )
        if not os.path.isfile(p) :
            p = self._findProgram( cmdLine[0] )
        args = [p] + cmdLine[1:]
        startingDir = os.getcwd()
        result = spawnProcess( p, args, env, startingDir, 0 )
        if not result :
            print 'error starting command (%s)' % p

    def _onService( self, service, command, sslConn, peerKey,
            contactName, incomingName ) :
        print '_onService( service=%s command=%s from=(%s,%s) )' % (
                service, command, contactName, incomingName )
        connectionId = self.incoming.addIncoming( sslConn, peerKey )
        env = {}
        env['CSPACE_PORT'] = str(self.listenPort)
        env['CSPACE_USER'] = self.session.getProfile().name
        env['CSPACE_EVENT'] = 'INCOMING'
        env['CSPACE_SERVICE'] = service
        env['CSPACE_CONNECTIONID'] = connectionId
        env['CSPACE_CONTACTNAME'] = contactName
        env['CSPACE_INCOMINGNAME'] = incomingName
        self._runCommand( command, env )

    def _onAction( self, actionDir, action, command, contactName ) :
        print '_onAction( actionDir=%s, action=%s, command=%s, contact=%s )' % (
                actionDir, action, command, contactName )
        env = {}
        env['CSPACE_PORT'] = str(self.listenPort)
        env['CSPACE_USER'] = self.session.getProfile().name
        env['CSPACE_EVENT'] = 'CONTACTACTION'
        env['CSPACE_CONTACTNAME'] = contactName
        env['CSPACE_ACTIONDIR'] = actionDir
        env['CSPACE_ACTION'] = action
        self._runCommand( command, env )
