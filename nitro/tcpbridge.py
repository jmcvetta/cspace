from time import time
from socket import error as sock_error

from nitro.errors import EWOULDBLOCK, EAGAIN

class StreamState(object) :
    def __init__( self, srcSock, destSock ) :
        self.src = srcSock
        self.dest = destSock
        self.srcClosed = False
        self.destClosed = False
        self.data = ''
        self.maxData = 65536
        self.hasRead = False
        self.hasWrite = False

    def canRead( self ) :
        if self.destClosed or self.srcClosed : return False
        if len(self.data) == self.maxData : return False
        return True

    def canWrite( self ) :
        if self.destClosed : return False
        if len(self.data) == 0 : return False
        return True

class TCPBridge(object) :
    def __init__( self, sock1, sock2, reactor ) :
        self.socks = [ sock1, sock2 ]
        self.reactor = reactor
        self.streams = [ StreamState(sock1,sock2), StreamState(sock2,sock1) ]
        for s in self.streams : self.updateEvents(s)
        for i in range(2) : self.streams[i].index = i
        self.closeCallback = None
        self._setActive()

    def setCloseCallback( self, closeCallback ) :
        self.closeCallback = closeCallback

    def close( self ) :
        for stream in self.streams :
            if stream.hasRead :
                self.reactor.removeReadCallback( stream.src.fileno() )
            if stream.hasWrite :
                self.reactor.removeWriteCallback( stream.dest.fileno() )
        for s in self.socks : s.close()

    def lastActiveTime( self ) :
        return self._lastActiveTime

    def _setActive( self ) :
        self._lastActiveTime = time()

    def closeInternal( self ) :
        for stream in self.streams :
            assert not stream.hasRead
            assert not stream.hasWrite
        for s in self.socks : s.close()
        if self.closeCallback : self.closeCallback()

    def updateEvents( self, stream ) :
        if (stream.srcClosed) and (len(stream.data) == 0) and (not stream.destClosed) :
            try :
                stream.dest.shutdown( 1 )
                stream.destClosed = True
            except sock_error, (err,errMsg) :
                self.handleError( stream.dest )

        readEvent = stream.canRead()
        if readEvent != stream.hasRead :
            stream.hasRead = readEvent
            if readEvent :
                self.reactor.addReadCallback( stream.src.fileno(), lambda : self._onRead(stream) )
            else :
                self.reactor.removeReadCallback( stream.src.fileno() )
        writeEvent = stream.canWrite()
        if writeEvent != stream.hasWrite :
            stream.hasWrite = writeEvent
            if writeEvent :
                self.reactor.addWriteCallback( stream.dest.fileno(), lambda : self._onWrite(stream) )
            else :
                self.reactor.removeWriteCallback( stream.dest.fileno() )

    def handleError( self, sock ) :
        if sock is self.socks[0] :
            self.streams[0].srcClosed = True
            self.streams[1].destClosed = True
        else :
            assert sock is self.socks[1]
            self.streams[0].destClosed = True
            self.streams[1].srcClosed = True

    def _onRead( self, stream ) :
        self._setActive()
        if stream.canRead() :
            try :
                data = stream.src.recv( stream.maxData - len(stream.data) )
                if not data :
                    stream.srcClosed = True
                else :
                    stream.data += data
            except sock_error, (err,errMsg) :
                if err not in (EWOULDBLOCK,EAGAIN) :
                    self.handleError( stream.src )
        if stream.canWrite() :
            try :
                numWritten = stream.dest.send( stream.data )
                stream.data = stream.data[numWritten:]
            except sock_error, (err,errMsg) :
                if err not in (EWOULDBLOCK,EAGAIN) :
                    self.handleError( stream.dest )
        for s in self.streams : self.updateEvents(s)

        if self.streams[0].destClosed and self.streams[1].destClosed :
            self.closeInternal()

    def _onWrite( self, stream ) :
        self._setActive()
        finished = False
        writeBlocked = False
        readBlocked = False
        while stream.canWrite() and not writeBlocked :
            try :
                numWritten = stream.dest.send( stream.data )
                stream.data = stream.data[numWritten:]
            except sock_error, (err,errMsg) :
                if err not in (EWOULDBLOCK,EAGAIN) :
                    self.handleError( stream.dest )
                else :
                    writeBlocked = True

            if stream.canRead() and not readBlocked :
                try :
                    data = stream.src.recv( stream.maxData - len(stream.data) )
                    if not data :
                        stream.srcClosed = True
                    else :
                        stream.data += data
                except sock_error, (err,errMsg) :
                    if err not in (EWOULDBLOCK,EAGAIN) :
                        self.handleError( stream.src )
                    else :
                        readBlocked = True
        for s in self.streams : self.updateEvents(s)

        if self.streams[0].destClosed and self.streams[1].destClosed :
            self.closeInternal()
