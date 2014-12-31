import sys, os
from struct import pack, unpack
from socket import socket, AF_INET, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR, SO_ERROR
from socket import error as sock_error

from nitro.async import AsyncOp
from nitro.errors import *

def tcpListen( addr, reactor, callback ) :
    l = TCPListener( reactor, callback )
    l.listen( addr )
    return l

class TCPListener(object) :
    def __init__( self, reactor, callback ) :
        self.reactor = reactor
        self.callback = callback
        self.initialized = False
        self.enabled = False

    def setCallback( self, callback ) :
        self.callback = callback

    def getSock( self ) :
        assert self.initialized
        return self.sock

    def close( self ) :
        assert self.initialized
        self.enable( False )
        self.sock.close()
        self.initialized = False

    def enable( self, flag ) :
        assert self.initialized
        if self.enabled == flag : return
        self.enabled = flag
        if flag :
            self.reactor.addReadCallback( self.sock.fileno(), self._onRead )
        else :
            self.reactor.removeReadCallback( self.sock.fileno() )

    def listen( self, addr ) :
        self.sock = socket( AF_INET, SOCK_STREAM )
        try :
            self.sock.setsockopt( SOL_SOCKET, SO_REUSEADDR, 1 )
            self.sock.bind( addr )
            self.sock.listen( 5 )
        except sock_error :
            self.sock.close()
            raise
        self.initialized = True
        self.enable( True )

    def _onRead( self ) :
        (newSock, address) = self.sock.accept()
        newSock.setblocking( 0 )
        self.callback( newSock )

def tcpConnect( addr, reactor, callback=None ) :
    return TCPConnector().connect( addr, reactor, callback )

class TCPConnector( object ) :
    def __init__( self ) :
        self.errorCode = EINPROGRESS
        self.errorMsg = 'In progress.'
        self.sock = None

    def getError( self ) : return self.errorCode
    def getErrorMsg( self ) : return self.errorMsg
    def getSock( self ) : return self.sock

    def connect( self, addr, reactor, callback=None ) :
        def doConnect() :
            def doNotify( err=0, errMsg='' ) :
                (self.errorCode, self.errorMsg) = (err,errMsg)
                if err == 0 :
                    self.sock = sock
                else :
                    sock.close()
                op.notify( self )

            def addEvents() :
                reactor.addWriteCallback( sock.fileno(), onEvent )
                if (sys.platform == 'win32') and (not reactor.usesWSAAsyncSelect()) :
                    reactor.addExceptionCallback( sock.fileno(), onEvent )

            def removeEvents() :
                reactor.removeWriteCallback( sock.fileno() )
                if (sys.platform == 'win32') and (not reactor.usesWSAAsyncSelect()) :
                    reactor.removeExceptionCallback( sock.fileno() )
                if pollTimer :
                    pollTimer.cancel()

            def doCancel() :
                removeEvents()
                sock.close()

            def onPollTimer() :
                try :
                    err = sock.getsockopt( SOL_SOCKET, SO_ERROR )
                    if err not in (0,EWOULDBLOCK,EAGAIN,EINPROGRESS) :
                        onEvent()
                except sock_error :
                    pass
            
            def onEvent() :
                removeEvents()
                try :
                    err = sock.getsockopt( SOL_SOCKET, SO_ERROR )
                    doNotify( err, os.strerror(err) )
                except sock_error, (err,errMsg) :
                    doNotify( err, errMsg )

            pollTimer = None
            sock = socket( AF_INET, SOCK_STREAM )
            sock.setblocking( 0 )
            try :
                sock.connect( addr )
                doNotify()
            except sock_error, (err,errMsg) :
                if err in (EWOULDBLOCK,EAGAIN,EINPROGRESS) :
                    addEvents()
                    if reactor.usesWSAAsyncSelect() :
                        pollTimer = reactor.addTimer( 1, onPollTimer )
                    op.setCanceler( doCancel )
                    return
                doNotify( err, errMsg )

        timerOp = reactor.callLater( 0, doConnect )
        op = AsyncOp( callback, timerOp.cancel )
        return op

class TCPWriter( object ) :
    def __init__( self, sock, pendingWrite, reactor, timeout=60 ) :
        self.sock = sock
        self.pendingWrite = pendingWrite
        self.reactor = reactor
        self.timeout = timeout
        self.maxWriteChunk = 8192
        self.reactor.addWriteCallback( self.sock.fileno(), self._onWrite )
        self.timerOp = self.reactor.callLater( self.timeout, self._onTimeout )
        self.writeCompleteCallback = None
        self.errorCallback = None
        self.timeoutCallback = None

    def setWriteCompleteCallback( self, writeCompleteCallback ) :
        self.writeCompleteCallback = writeCompleteCallback
    def setErrorCallback( self, errorCallback ) :
        self.errorCallback = errorCallback
    def setTimeoutCallback( self, timeoutCallback ) :
        self.timeoutCallback = timeoutCallback

    def shutdown( self ) :
        self.timerOp.cancel()
        self.reactor.removeWriteCallback( self.sock.fileno() )

    def onWriteComplete( self ) :
        if not self.writeCompleteCallback :
            raise NotImplementedError
        self.writeCompleteCallback()

    def onError( self, err, errMsg ) :
        if not self.errorCallback :
            raise NotImplementedError
        self.errorCallback( err, errMsg )

    def onTimeout( self ) :
        if not self.timeoutCallback :
            raise NotImplementedError
        self.timeoutCallback()

    def _onWrite( self ) :
        try :
            while self.pendingWrite :
                numWritten = self.sock.send( self.pendingWrite[:self.maxWriteChunk] )
                self.pendingWrite = self.pendingWrite[numWritten:]
        except sock_error, (err,errMsg) :
            if err in (EWOULDBLOCK,EAGAIN) : return
            self.reactor.removeWriteCallback( self.sock.fileno() )
            self.timerOp.cancel()
            self.onError( err, errMsg )
            return
        self.reactor.removeWriteCallback( self.sock.fileno() )
        self.timerOp.cancel()
        self.onWriteComplete()

    def _onTimeout( self ) :
        self.reactor.removeWriteCallback( self.sock.fileno() )
        self.onTimeout()

class TCPCloser( TCPWriter ) :
    def __init__( self, sock, pendingWrite, reactor, callback=None ) :
        TCPWriter.__init__( self, sock, pendingWrite, reactor )
        self.op = AsyncOp( callback, self.shutdown )

    def getOp( self ) : return self.op

    def _notify( self ) :
        self.sock.close()
        self.op.notify()
    def onWriteComplete( self ) : self._notify()
    def onError( self, err, errMsg ) : self._notify()
    def onTimeout( self ) : self._notify()

class TCPStream( object ) :
    def __init__( self, sock, reactor ) :
        sock.setblocking( 0 )
        self.sock = sock
        self.reactor = reactor
        self.readEnabled = False
        self.maxReadSize = 0
        self.writeEnabled = False
        self.pendingWrite = ''
        self.closeCallback = None
        self.errorCallback = None
        self.inputCallback = None
        self.writeCompleteCallback = None
        self.shutdownFlag = False

    def getSock( self ) : return self.sock

    def setCloseCallback( self, closeCallback ) :
        self.closeCallback = closeCallback
    def setErrorCallback( self, errorCallback ) :
        self.errorCallback = errorCallback
    def setInputCallback( self, inputCallback ) :
        self.inputCallback = inputCallback
    def setWriteCompleteCallback( self, writeCompleteCallback ) :
        self.writeCompleteCallback = writeCompleteCallback

    def shutdown( self ) :
        assert not self.shutdownFlag
        self.shutdownFlag = True
        if self.readEnabled :
            self.reactor.removeReadCallback( self.sock.fileno() )
            self.readEnabled = False
        if self.writeEnabled :
            self.reactor.removeWriteCallback( self.sock.fileno() )
            self.writeEnabled = False
            self.pendingWrite = ''

    def close( self, deferred=False, callback=None ) :
        assert not self.shutdownFlag
        if not deferred :
            self.shutdown()
            self.sock.close()
            return
        pendingWrite = self.pendingWrite
        self.shutdown()
        return TCPCloser( self.sock, pendingWrite, self.reactor, callback ).getOp()

    def hasShutdown( self ) : return self.shutdownFlag

    def initiateRead( self, maxReadSize ) :
        self.maxReadSize = maxReadSize
        if not self.readEnabled :
            self.reactor.addReadCallback( self.sock.fileno(), self._onRead )
            self.readEnabled = True

    def cancelRead( self ) :
        if self.readEnabled :
            self.reactor.removeReadCallback( self.sock.fileno() )
            self.readEnabled = False

    def writeData( self, data ) :
        if self.writeEnabled :
            assert self.pendingWrite
            self.pendingWrite += data
            return
        self.pendingWrite = data
        self.writeEnabled = True
        self.reactor.addWriteCallback( self.sock.fileno(), self._onWrite )

    def getPendingWrite( self ) :
        return self.pendingWrite

    def _notifyClose( self ) :
        if self.readEnabled :
            self.reactor.removeReadCallback( self.sock.fileno() )
            self.readEnabled = False
        if self.closeCallback :
            self.closeCallback()
        else :
            self.close()

    def _notifyError( self, err, errMsg ) :
        if self.errorCallback :
            self.errorCallback( err, errMsg )
        else :
            self.close()

    def _notifyInput( self, data ) :
        if self.inputCallback :
            self.inputCallback( data )

    def _notifyWriteComplete( self ) :
        if self.writeCompleteCallback :
            self.writeCompleteCallback()

    def _onRead( self ) :
        assert self.readEnabled
        try :
            data = self.sock.recv( self.maxReadSize )
            if not data :
                self._notifyClose()
                return
            self._notifyInput( data )
        except sock_error, (err,errMsg) :
            if err in (EWOULDBLOCK,EAGAIN) : return
            self._notifyError( err, errMsg )

    def _onWrite( self ) :
        assert self.writeEnabled
        assert self.pendingWrite
        try :
            while self.pendingWrite :
                numWritten = self.sock.send( self.pendingWrite )
                self.pendingWrite = self.pendingWrite[numWritten:]
            self.writeEnabled = False
            self.reactor.removeWriteCallback( self.sock.fileno() )
            self._notifyWriteComplete()
        except sock_error, (err,errMsg) :
            if err in (EWOULDBLOCK,EAGAIN) : return
            self._notifyError( err, errMsg )

class TCPMessageStream( object ) :
    def __init__( self, sock, reactor ) :
        self.stream = TCPStream( sock, reactor )
        self.readEnabled = False
        self.maxMsgLength = 65536
        self.readingLength = True
        self.msgLength = 0
        self.buffer = ''
        self.stream.setInputCallback( self._onInput )

        self.getSock = self.stream.getSock
        self.shutdown = self.stream.shutdown
        self.close = self.stream.close
        self.hasShutdown = self.stream.hasShutdown
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
                    self.stream.initiateRead( 4-len(self.buffer)  )
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
