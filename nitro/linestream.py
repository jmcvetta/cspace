from nitro.tcp import TCPStream

class TCPLineStream( object ) :
    def __init__( self, sock, reactor ) :
        self.reactor = reactor
        self.stream = TCPStream( sock, reactor )
        self.readEnabled = False
        self.readInitiated = False
        self.timerOp = None
        self.inputBuffer = [ '' ]
        self.inputCallback = None
        self.stream.setInputCallback( self._onInput )

        self.getSock = self.stream.getSock
        self.setCloseCallback = self.stream.setCloseCallback
        self.setErrorCallback = self.stream.setErrorCallback
        self.setWriteCompleteCallback = self.stream.setWriteCompleteCallback
        self.hasShutdown = self.stream.hasShutdown
        self.writeData = self.stream.writeData

    def setInputCallback( self, inputCallback ) :
        self.inputCallback = inputCallback

    def shutdown( self ) :
        self.enableRead( False )
        self.stream.shutdown()

    def close( self, deferred=False, callback=None ) :
        self.enableRead( False )
        return self.stream.close( deferred, callback )

    def enableRead( self, enable=True ) :
        assert not self.hasShutdown()
        if enable != self.readEnabled :
            self.readEnabled = enable
            if enable :
                assert not self.readInitiated
                assert not self.timerOp
                if len(self.inputBuffer) > 1 :
                    self.timerOp = self.reactor.addTimer( 0, self._onTimer )
                else :
                    self.readInitiated = True
                    self.stream.initiateRead( 4096 )
            else :
                if self.timerOp :
                    self.timerOp.cancel()
                    self.timerOp = None
                else :
                    self.readInitiated = False
                    self.stream.cancelRead()

    def _onInput( self, data ) :
        while data :
            i = data.find( '\n' )
            if i < 0 :
                self.inputBuffer[-1] += data
                break
            else :
                i += 1
                self.inputBuffer[-1] += data[:i]
                self.inputBuffer.append( '' )
                data = data[i:]
        while len(self.inputBuffer) > 1 :
            line = self.inputBuffer.pop( 0 )
            self.inputCallback( line )
            if not self.readEnabled : return

    def _onTimer( self ) :
        while len(self.inputBuffer) > 1 :
            line = self.inputBuffer.pop( 0 )
            self.inputCallback( line )
            if not self.readEnabled : return
        if self.timerOp :
            self.timerOp.cancel()
            self.timerOp = None
            self.readInitiated = True
            self.stream.initiateRead( 4096 )
