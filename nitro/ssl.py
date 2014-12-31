from struct import pack, unpack

from ncrypt.ssl import SSLWantReadError, SSLWantWriteError, SSLWantError, SSLError

from nitro.async import AsyncOp

def sslAccept( sslConn, reactor, callback=None ) :
    return SSLInitiator( sslConn, SSLInitiator.ACCEPT, reactor, callback ).getOp()

def sslConnect( sslConn, reactor, callback=None ) :
    return SSLInitiator( sslConn, SSLInitiator.CONNECT, reactor, callback ).getOp()

class SSLInitiator( object ) :
    ACCEPT = 0
    CONNECT = 1

    WANT_NONE = 0
    WANT_READ = 1
    WANT_WRITE = 2

    def __init__( self, sslConn, initiateCode, reactor, callback=None ) :
        self.sslConn = sslConn
        self.reactor = reactor
        if initiateCode == self.ACCEPT :
            self.sslFunc = self.sslConn.accept
        else :
            assert initiateCode == self.CONNECT 
            self.sslFunc = self.sslConn.connect
        self.sock = self.sslConn.sock
        self.sock.setblocking( 0 )
        timerOp = self.reactor.callLater( 0, self._doAction )
        self.op = AsyncOp( callback, timerOp.cancel )
        self.want = self.WANT_NONE

    def getOp( self ) : return self.op

    def _removeRead( self ) :
        self.reactor.removeReadCallback( self.sock.fileno() )
        self.want = self.WANT_NONE

    def _removeWrite( self ) :
        self.reactor.removeWriteCallback( self.sock.fileno() )
        self.want = self.WANT_NONE

    def _doAction( self ) :
        try :
            self.sslFunc()
        except SSLWantReadError :
            if self.want != self.WANT_READ :
                if self.want == self.WANT_WRITE : self._removeWrite()
                self.reactor.addReadCallback( self.sock.fileno(), self._doAction )
                self.want = self.WANT_READ
                self.op.setCanceler( self._removeRead )
            return
        except SSLWantWriteError :
            if self.want != self.WANT_WRITE :
                if self.want == self.WANT_READ : self._removeRead()
                self.reactor.addWriteCallback( self.sock.fileno(), self._doAction )
                self.want = self.WANT_WRITE
                self.op.setCanceler( self._removeWrite )
            return
        except SSLError, e :
            if self.want == self.WANT_READ : self._removeRead()
            elif self.want == self.WANT_WRITE : self._removeWrite()
            self.op.notify( e )
            return
        if self.want == self.WANT_READ : self._removeRead()
        elif self.want == self.WANT_WRITE : self._removeWrite()
        self.op.notify( None )

class SSLWriter( object ) :
    def __init__( self, sslConn, pendingWrite, reactor, timeout=60 ) :
        self.sslConn = sslConn
        self.pendingWrite = pendingWrite
        self.reactor = reactor
        self.timeout = timeout
        self.sock = sslConn.sock
        self.maxWriteChunk = 32768
        self.writeCompleteCallback = None
        self.errorCallback = None
        self.timeoutCallback = None
        self.timeoutOp = self.reactor.callLater( self.timeout, self._onTimeout )
        self.timerOp = self.reactor.callLater( 0, self._onAction )
        self.hasRead = self.hasWrite = False

    def setWriteCompleteCallback( self, writeCompleteCallback ) :
        self.writeCompleteCallback = writeCompleteCallback

    def setErrorCallback( self, errorCallback ) :
        self.errorCallback = errorCallback

    def setTimeoutCallback( self, timeoutCallback ) :
        self.timeoutCallback = timeoutCallback

    def shutdown( self ) :
        if self.timerOp :
            self.timerOp.cancel()
            self.timerOp = None
        if self.timeoutOp :
            self.timeoutOp.cancel()
            self.timeoutOp = None
        if self.hasRead :
            assert not self.hasWrite
            self.reactor.removeReadCallback( self.sock.fileno() )
            self.hasRead = False
        elif self.hasWrite :
            self.reactor.removeWriteCallback( self.sock.fileno() )
            self.hasWrite = False

    def onWriteComplete( self ) :
        if not self.writeCompleteCallback :
            raise NotImplementedError
        self.writeCompleteCallback()

    def onError( self, sslErr ) :
        if self.errorCallback :
            raise NotImplementedError
        self.errorCallback( sslErr )

    def onTimeout( self ) :
        if not self.timeoutCallback :
            raise NotImplementedError
        self.timeoutCallback()

    def _onAction( self ) :
        self.timerOp = None
        self._doAction()

    def _doAction( self ) :
        try :
            while self.pendingWrite :
                written = self.sslConn.send( self.pendingWrite[:self.maxWriteChunk] )
                self.pendingWrite = self.pendingWrite[written:]
        except SSLWantReadError :
            if not self.hasRead :
                if self.hasWrite :
                    self.reactor.removeWriteCallback( self.sock.fileno() )
                    self.hasWrite = False
                self.reactor.addReadCallback( self.sock.fileno(), self._doAction )
                self.hasRead = True
            return
        except SSLWantWriteError :
            if not self.hasWrite :
                if self.hasRead :
                    self.reactor.removeReadCallback( self.sock.fileno() )
                    self.hasRead = False
                self.reactor.addWriteCallback( self.sock.fileno() )
                self.hasWrite = True
            return
        except SSLError, e :
            self.shutdown()
            self.onError( e )
            return
        self.shutdown()
        self.onWriteComplete()

    def _onTimeout( self ) :
        self.timeoutOp = None
        self.shutdown()
        self.onTimeout()

def sslAbort( sslConn ) :
    sslConn.sock.close()

def sslClose( sslConn, reactor, callback=None, timeout=30 ) :
    return SSLCloser( sslConn, reactor, callback, timeout ).getOp()

class SSLCloser( object ) :
    WANT_NONE = 0
    WANT_READ = 1
    WANT_WRITE = 2
    def __init__( self, sslConn, reactor, callback=None, timeout=30 ) :
        self.sslConn = sslConn
        self.reactor = reactor
        self.timeout = timeout
        self.sock = sslConn.sock
        self.want = self.WANT_NONE
        self.timerOp = self.reactor.callLater( 0, self._onAction )
        self.timeoutOp = self.reactor.callLater( self.timeout, self._onTimeout )
        self.op = AsyncOp( callback, self._close )

    def getOp( self ) : return self.op

    def _close( self ) :
        if self.timerOp : self.timerOp.cancel()
        if self.timeoutOp : self.timeoutOp.cancel()
        if self.want == self.WANT_READ : self._removeRead()
        elif self.want == self.WANT_WRITE : self._removeWrite()
        self.sock.close()

    def _closeNotify( self ) :
        self._close()
        self.op.notify()

    def _removeRead( self ) :
        assert self.want == self.WANT_READ
        self.reactor.removeReadCallback( self.sock.fileno() )
        self.want = self.WANT_NONE

    def _removeWrite( self ) :
        assert self.want == self.WANT_WRITE
        self.reactor.removeWriteCallback( self.sock.fileno() )
        self.want = self.WANT_NONE

    def _onAction( self ) :
        self.timerOp = None
        self._doAction()

    def _doAction( self ) :
        try :
            result = self.sslConn.shutdown()
            if result == 0 :
                result = self.sslConn.shutdown()
        except SSLWantReadError :
            if self.want != self.WANT_READ :
                if self.want == self.WANT_WRITE : self._removeWrite()
                self.reactor.addReadCallback( self.sock.fileno(), self._doAction )
                self.want = self.WANT_READ
            return
        except SSLWantWriteError :
            if self.want != self.WANT_WRITE :
                if self.want == self.WANT_READ : self._removeRead()
                self.reactor.addWriteCallback( self.sock.fileno(), self._doAction )
                self.want = self.WANT_WRITE
            return
        except SSLError, e :
            self._closeNotify()
            return
        self._closeNotify()

    def _onTimeout( self ) :
        self.timeoutOp = None
        self._closeNotify()

class SSLReactor( object ) :
    INITIAL = 0
    SUCCESS = 1
    WANT_READ = 2
    WANT_WRITE = 3
    def __init__( self, sslConn, reactor, readCallback, writeCallback ) :
        self.sslConn = sslConn
        self.reactor = reactor
        self.readCallback = readCallback
        self.writeCallback = writeCallback
        self.sock = sslConn.sock
        self.readEnabled = False
        self.writeEnabled = False
        self.readState = self.INITIAL
        self.writeState = self.INITIAL

        self.hasRead = self.hasWrite = False
        self.timerOp = None

    def getSSL( self ) : return self.sslConn

    def shutdown( self ) :
        self.readEnabled = self.writeEnabled = False
        self._updateEvents()

    def enableRead( self, enable=True ) :
        if enable != self.readEnabled :
            self.readEnabled = enable
            self._updateEvents()

    def isReadEnabled( self ) : return self.readEnabled

    def enableWrite( self, enable=True ) :
        if enable != self.writeEnabled :
            self.writeEnabled = enable
            self._updateEvents()

    def isWriteEnabled( self ) : return self.writeEnabled

    def read( self, bufSize ) :
        self.readState = self.SUCCESS
        try :
            data = self.sslConn.recv( bufSize )
        except SSLWantReadError :
            self.readState = self.WANT_READ
            self._updateEvents()
            raise
        except SSLWantWriteError :
            self.readState = self.WANT_WRITE
            self._updateEvents()
            raise
        return data

    def write( self, data ) :
        self.writeState = self.SUCCESS
        try :
            written = self.sslConn.send( data )
        except SSLWantReadError :
            self.writeState = self.WANT_READ
            self._updateEvents()
            raise
        except SSLWantWriteError :
            self.writeState = self.WANT_WRITE
            self._updateEvents()
            raise
        return written

    def _updateEvents( self ) :
        regRead = regWrite = regTimer = False
        if self.readEnabled :
            pending = self.sslConn.pending()
            if self.readState == self.INITIAL :
                regTimer = True
            elif self.readState == self.SUCCESS :
                if pending > 0 : regTimer = True
                else : regRead = True
            elif self.readState == self.WANT_READ :
                regRead = True
            else :
                assert self.readState == self.WANT_WRITE
                regWrite = True
        if self.writeEnabled :
            if self.writeState == self.INITIAL :
                regTimer = True
            elif self.writeState == self.SUCCESS :
                regWrite = True
            elif self.writeState == self.WANT_READ :
                regRead = True
            else :
                assert self.writeState == self.WANT_WRITE
                regWrite = True
        if regRead != self.hasRead :
            self.hasRead = regRead
            if regRead :
                self.reactor.addReadCallback( self.sock.fileno(), self._onRead )
            else :
                self.reactor.removeReadCallback( self.sock.fileno() )
        if regWrite != self.hasWrite :
            self.hasWrite = regWrite
            if regWrite :
                self.reactor.addWriteCallback( self.sock.fileno(), self._onWrite )
            else :
                self.reactor.removeWriteCallback( self.sock.fileno() )
        if regTimer and not self.timerOp :
            self.timerOp = self.reactor.callLater( 0, self._onTimer )
        elif (not regTimer) and self.timerOp :
            self.timerOp.cancel()
            self.timerOp = None

    def _processEvent( self ) :
        if self.readEnabled : self.readCallback()
        if self.writeEnabled : self.writeCallback()
        self._updateEvents()

    def _onRead( self ) : self._processEvent()
    def _onWrite( self ) : self._processEvent()
    def _onTimer( self ) :
        self.timerOp = None
        self._processEvent()

class SSLStream( object ) :
    def __init__( self, sslConn, reactor ) :
        self.sslConn = sslConn
        self.reactor = reactor
        self.closeCallback = None
        self.errorCallback = None
        self.inputCallback = None
        self.writeCompleteCallback = None
        self.sslReactor = SSLReactor( sslConn, reactor, self._onRead, self._onWrite )
        self.pendingWrite = ''
        self.maxReadSize = 0
        self.hasShutdown = False

    def getSSL( self ) : return self.sslConn

    def setCloseCallback( self, closeCallback ) :
        self.closeCallback = closeCallback

    def setErrorCallback( self, errorCallback ) :
        self.errorCallback = errorCallback

    def setInputCallback( self, inputCallback ) :
        self.inputCallback = inputCallback

    def setWriteCompleteCallback( self, writeCompleteCallback ) :
        self.writeCompleteCallback = writeCompleteCallback

    def shutdown( self ) :
        assert not self.hasShutdown
        self.hasShutdown = True
        self.sslReactor.shutdown()
        self.pendingWrite = ''

    def close( self, deferred=False, callback=None ) :
        assert not self.hasShutdown
        if not deferred :
            self.shutdown()
            sslAbort( self.sslConn )
            return
        pendingWrite = self.pendingWrite
        self.shutdown()
        sslConn, reactor = self.sslConn, self.reactor
        if not pendingWrite :
            return sslClose( sslConn, reactor, callback )
        def doClose() :
            closeOp = sslClose( sslConn, reactor, op.notify )
            op.setCanceler( closeOp.cancel )
        writer = SSLWriter( sslConn, pendingWrite, reactor )
        writer.setWriteCompleteCallback( doClose )
        writer.setErrorCallback( lambda err : doClose() )
        writer.setTimeoutCallback( doClose )
        op = AsyncOp( callback, writer.shutdown )
        return op

    def initiateRead( self, maxReadSize ) :
        self.maxReadSize = maxReadSize
        self.sslReactor.enableRead( True )

    def cancelRead( self ) :
        self.sslReactor.enableRead( False )

    def writeData( self, data ) :
        self.pendingWrite += data
        self.sslReactor.enableWrite( True )

    def getPendingWrite( self ) :
        return self.pendingWrite

    def _notifyClose( self ) :
        self.sslReactor.enableRead( False )
        if self.closeCallback :
            self.closeCallback()
        else :
            self.close( deferred=True )

    def _notifyError( self, err ) :
        if self.errorCallback :
            self.errorCallback( err )
        else :
            self.close()

    def _notifyInput( self, data ) :
        if self.inputCallback :
            self.inputCallback( data )

    def _notifyWriteComplete( self ) :
        if self.writeCompleteCallback :
            self.writeCompleteCallback()

    def _onRead( self ) :
        try :
            data = self.sslReactor.read( self.maxReadSize )
            if not data :
                self._notifyClose()
                return
            self._notifyInput( data )
        except SSLWantError :
            return
        except SSLError, e :
            self._notifyError( e )

    def _onWrite( self ) :
        try :
            while self.pendingWrite :
                written = self.sslReactor.write( self.pendingWrite )
                self.pendingWrite = self.pendingWrite[written:]
            self.sslReactor.enableWrite( False )
            self._notifyWriteComplete()
        except SSLWantError :
            return
        except SSLError, e :
            self._notifyError( e )

class SSLMessageStream( object ) :
    def __init__( self, sslConn, reactor ) :
        self.stream = SSLStream( sslConn, reactor )
        self.readEnabled = False
        self.maxMsgLength = 65536
        self.readingLength = True
        self.msgLength = 0
        self.buffer = ''
        self.stream.setInputCallback( self._onInput )

        self.getSSL = self.stream.getSSL
        self.shutdown = self.stream.shutdown
        self.close = self.stream.close
        self.getPendingWrite = self.stream.getPendingWrite

        self.setCloseCallback = self.stream.setCloseCallback
        self.setErrorCallback = self.stream.setErrorCallback
        self.setWriteCompleteCallback = self.stream.setWriteCompleteCallback

        self.invalidMessageCallback = None
        self.inputCallback = None

    def setInvalidMessageCallback( self, invalidMessageCallback ) :
        self.invalidMessageCallback = invalidMessageCallback
    def setInputCallback( self, inputCallback ) :
        self.inputCallback = inputCallback

    def enableRead( self, enable ) :
        if enable != self.readEnabled :
            self.readEnabled = enable
            if enable :
                if self.readingLength :
                    assert len(self.buffer) < 4
                    self.stream.initiateRead( 4-len(self.buffer) )
                else :
                    assert len(self.buffer) < self.msgLength
                    self.stream.initiateRead( self.msgLength - len(self.buffer) )
            else :
                self.stream.cancelRead()

    def isReadEnabled( self ) : return self.readEnabled

    def sendMessage( self, data ) :
        msg = pack( '<i%ds' % len(data), len(data), data )
        self.stream.writeData( msg )

    def _onInput( self, data ) :
        assert self.readEnabled
        if self.readingLength :
            assert len(data) + len(self.buffer) <= 4
            self.buffer += data
            if len(self.buffer) == 4 :
                self.msgLength = unpack( '<i', self.buffer )[0]
                self.readingLength = False
                if (self.msgLength <= 0) or (self.msgLength > self.maxMsgLength) :
                    if self.invalidMessageCallback :
                        self.invalidMessageCallback()
                    else :
                        self.close()
                    return
                self.buffer = ''
                self.stream.initiateRead( self.msgLength )
            else :
                self.stream.initiateRead( 4-len(self.buffer) )
        else :
            assert len(data) + len(self.buffer) <= self.msgLength
            self.buffer += data
            if len(self.buffer) == self.msgLength :
                data = self.buffer
                self.buffer = ''
                self.msgLength = 0
                self.readingLength = True
                self.stream.initiateRead( 4 )
                if self.inputCallback :
                    self.inputCallback( data )
            else :
                self.stream.initiateRead( self.msgLength - len(self.buffer) )
