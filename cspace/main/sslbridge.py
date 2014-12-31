from socket import error as sock_error

from ncrypt.ssl import SSLError, SSLWantReadError, SSLWantWriteError
from nitro.errors import EWOULDBLOCK, EAGAIN
from nitro.ssl import sslClose

class HandleState( object ) :
    def __init__( self, isSSL, sock=None, sslConn=None ) :
        self.isSSL = isSSL
        if isSSL :
            self.sslConn = sslConn
            self.handle = sslConn.sock
        else :
            self.sock = sock
            self.handle = sock
        self.closed = False
        self.hasReadEvent = False
        self.hasWriteEvent = False

class StreamState( object ) :
    def __init__( self, srcHandle, destHandle ) :
        self.handles = [srcHandle, destHandle]
        self.wantRead = [False,False]
        self.wantWrite = [False,False]
        self.data = ''
        self.maxData = 16384

    def empty( self ) : return len(self.data) == 0
    def size( self ) : return len(self.data)
    def remaining( self ) : return self.maxData - len(self.data)
    def addData( self, data ) : self.data += data

class SSLBridge( object ) :
    def __init__( self, sock, sslConn, reactor ) :
        self.sock = sock
        self.sslConn = sslConn
        self.reactor = reactor
        self.handles = [ HandleState(False,sock=sock), HandleState(True,sslConn=sslConn) ]
        self.streams = [
            StreamState(self.handles[0],self.handles[1]),
            StreamState(self.handles[1],self.handles[0]) ]

        for s in self.streams : s.wantRead[0] = True
        self.updateEvents()
        self.closeCallback = None

    def setCloseCallback( self, closeCallback ) :
        self.closeCallback = closeCallback

    def shutdown( self ) :
        for hs in self.handles :
            if not hs.closed :
                self.closeHandle( hs )

    def updateEvents( self ) :
        needRead = [False,False]
        needWrite = [False,False]
        h, s = self.handles, self.streams
        for i in (0,1) :
            needRead[i] = (not h[i].closed) and (s[i].wantRead[0] or s[1-i].wantRead[1])
            needWrite[i] = (not h[i].closed) and (s[i].wantWrite[0] or s[1-i].wantWrite[1])
            if needRead[i] != h[i].hasReadEvent :
                if needRead[i] :
                    def regRead( handle ) :
                        self.reactor.addReadCallback( handle.fileno(), lambda : self._onRead(handle) )
                    regRead( h[i].handle )
                else :
                    self.reactor.removeReadCallback( h[i].handle.fileno() )
                h[i].hasReadEvent = needRead[i]
            if needWrite[i] != h[i].hasWriteEvent :
                if needWrite[i] :
                    def regWrite( handle ) :
                        self.reactor.addWriteCallback( handle.fileno(), lambda : self._onWrite(handle) )
                    regWrite( h[i].handle )
                else :
                    self.reactor.removeWriteCallback( h[i].handle.fileno() )
                h[i].hasWriteEvent = needWrite[i]

    def closeHandle( self, hs ) :
        assert not hs.closed
        hs.closed = True
        if hs.hasReadEvent :
            self.reactor.removeReadCallback( hs.handle.fileno() )
            hs.hasReadEvent = False
        if hs.hasWriteEvent :
            self.reactor.removeWriteCallback( hs.handle.fileno() )
            hs.hasWriteEvent = False
        if hs.isSSL :
            sslClose( hs.sslConn, self.reactor )
        else :
            hs.sock.close()

    def pumpStream( self, stream ) :
        src = stream.handles[0]
        dest = stream.handles[1]
        finished = False
        while not finished :
            finished = True
            stream.wantRead[0] = stream.wantWrite[0] = False
            while (not src.closed) and (stream.remaining() > 0) :
                if not src.isSSL :
                    try :
                        data = src.sock.recv( stream.remaining() )
                        if not data :
                            self.closeHandle( src )
                            break
                        stream.addData( data )
                    except sock_error, (err,errMsg) :
                        if err in (EWOULDBLOCK,EAGAIN) :
                            stream.wantRead[0] = True
                        else :
                            self.closeHandle( src )
                        break
                else :
                    try :
                        data = src.sslConn.recv( stream.remaining() )
                        if not data :
                            self.closeHandle( src )
                            break
                        stream.addData( data )
                    except SSLWantReadError :
                        stream.wantRead[0] = True
                        break
                    except SSLWantWriteError :
                        stream.wantWrite[0] = True
                        break
                    except SSLError :
                        self.closeHandle( src )
                        break
            srcNoSpace = (stream.remaining() == 0)

            stream.wantRead[1] = stream.wantWrite[1] = False
            while (not dest.closed) and (stream.size() > 0) :
                if not dest.isSSL :
                    try :
                        written = dest.sock.send( stream.data )
                        stream.data = stream.data[written:]
                    except sock_error, (err,errMsg) :
                        if err in (EWOULDBLOCK,EAGAIN) :
                            stream.wantWrite[1] = True
                        else :
                            self.closeHandle( dest )
                        break
                else :
                    try :
                        written = dest.sslConn.send( stream.data )
                        stream.data = stream.data[written:]
                    except SSLWantReadError :
                        stream.wantRead[1] = True
                        break
                    except SSLWantWriteError :
                        stream.wantWrite[1] = True
                        break
                    except SSLError :
                        self.closeHandle( dest )
                        break
            if (srcNoSpace) and (stream.remaining() > 0) :
                finished = False
        if src.closed and stream.empty() and (not dest.closed) :
            assert not stream.wantRead[1]
            assert not stream.wantWrite[1]
            self.closeHandle( dest )

    def _onRead( self, handle ) :
        h = self.handles
        hs = (handle == h[0].handle) and h[0] or h[1]
        if not hs.hasReadEvent : return
        for ss in self.streams : self.pumpStream( ss )
        self.updateEvents()
        if self.closeCallback :
            if self.handles[0].closed and self.handles[1].closed :
                self.closeCallback()
                self.closeCallback = 1 # set to some non-callable

    def _onWrite( self, handle ) :
        h = self.handles
        hs = (handle == h[0].handle) and h[0] or h[1]
        if not hs.hasWriteEvent : return
        for ss in self.streams : self.pumpStream( ss )
        self.updateEvents()
        if self.closeCallback :
            if self.handles[0].closed and self.handles[1].closed :
                self.closeCallback()
                self.closeCallback = 1 # set to some non-callable
