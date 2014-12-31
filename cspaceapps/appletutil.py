import sys, os
from nitro.async import AsyncOp
from nitro.tcp import tcpConnect, TCPStream
from cspace.main.common import localSettings

class CSpaceEnv( object ) :
    def __init__( self ) :
        self.port = int( os.environ['CSPACE_PORT'] )
        self.user = os.environ['CSPACE_USER']
        self.event = os.environ['CSPACE_EVENT']
        self.isContactAction = (self.event == 'CONTACTACTION')
        self.isIncoming = (self.event == 'INCOMING')
        if self.isContactAction :
            self.contactName = os.environ['CSPACE_CONTACTNAME']
            self.actionDir = os.environ['CSPACE_ACTIONDIR']
            self.action = os.environ['CSPACE_ACTION']
            self.displayName = self.contactName
        elif self.isIncoming :
            self.service = os.environ['CSPACE_SERVICE']
            self.connectionId = os.environ['CSPACE_CONNECTIONID']
            self.contactName = os.environ['CSPACE_CONTACTNAME']
            self.incomingName = os.environ['CSPACE_INCOMINGNAME']
            if self.contactName :
                self.displayName = self.contactName
            else :
                self.displayName = '(Unknown %s)' % self.incomingName

class CSpaceConnector( object ) :
    def __init__( self, sock, remoteUser, remoteService, reactor, callback ) :
        self.stream = TCPStream( sock, reactor )
        self.stream.setCloseCallback( self._onClose )
        self.stream.setErrorCallback( self._onError )
        self.stream.setInputCallback( self._onInput )
        self.stream.initiateRead( 1 )
        self.stream.writeData( 'CONNECT %s %s\r\n' % (remoteUser,remoteService) )
        self.response = ''
        self.op = AsyncOp( callback, self.stream.close )

    def getOp( self ) : return self.op

    def _onClose( self ) :
        self.stream.close()
        self.op.notify( -1, None )

    def _onError( self, err, errMsg ) :
        self._onClose()

    def _onInput( self, data ) :
        self.response += data
        if self.response.endswith('\n') :
            if not self.response.startswith('OK') :
                self._onClose()
                return
            self.stream.shutdown()
            sock = self.stream.getSock()
            self.op.notify( 0, sock )

class CSpaceAcceptor( object ) :
    def __init__( self, sock, connectionId, reactor, callback ) :
        self.stream = TCPStream( sock, reactor )
        self.stream.setCloseCallback( self._onClose )
        self.stream.setErrorCallback( self._onError )
        self.stream.setInputCallback( self._onInput )
        self.stream.initiateRead( 1 )
        self.stream.writeData( 'ACCEPT %s\r\n' % connectionId )
        self.response = ''
        self.op = AsyncOp( callback, self.stream.close )

    def getOp( self ) : return self.op

    def _onClose( self ) :
        self.stream.close()
        self.op.notify( -1, None )

    def _onError( self, err, errMsg ) :
        self._onClose()

    def _onInput( self, data ) :
        self.response += data
        if self.response.endswith('\n') :
            if not self.response.startswith('OK') :
                self._onClose()
                return
            self.stream.shutdown()
            sock = self.stream.getSock()
            self.op.notify( 0, sock )

def cspaceConnect( cspaceAddr, remoteUser, remoteService, reactor, callback ) :
    def onTCPConnect( connector ) :
        if connector.getError() != 0 :
            op.notify( -1, None )
            return
        connectOp = CSpaceConnector( connector.getSock(), remoteUser,
                remoteService, reactor, op.notify ).getOp()
        op.setCanceler( connectOp.cancel )
    tcpOp = tcpConnect( cspaceAddr, reactor, onTCPConnect )
    op = AsyncOp( callback, tcpOp.cancel )
    return op

def cspaceAccept( cspaceAddr, connectionId, reactor, callback ) :
    def onTCPConnect( connector ) :
        if connector.getError() != 0 :
            op.notify( -1, None )
            return
        acceptOp = CSpaceAcceptor( connector.getSock(), connectionId,
                reactor, op.notify ).getOp()
        op.setCanceler( acceptOp.cancel )
    tcpOp = tcpConnect( cspaceAddr, reactor, onTCPConnect )
    op = AsyncOp( callback, tcpOp.cancel )
    return op

class LogFile( object ) :
    def __init__( self, fileName ) :
        configDir = localSettings().getConfigDir()
        logFile = os.path.join( configDir, fileName )
        try :
            if os.path.getsize(logFile) >= 1024*1024 :
                os.remove( logFile )
        except OSError :
            pass
        self.f = file( logFile, 'a' )

    def write( self, s ) :
        self.f.write( s )
        self.f.flush()

    def flush( self ) :
        pass

def initializeLogFile( fileName ) :
    logFile = LogFile( fileName )
    sys.stdout = logFile
    sys.stderr = logFile
