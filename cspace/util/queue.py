import threading

class ThreadQueue( object ) :
    def __init__( self, callback, reactor ) :
        self.callback = callback
        self.reactor = reactor
        self.timerOp = reactor.addTimer( 0.2, self._onTimer )
        self.messages = []
        self.lock = threading.Lock()

    def shutdown( self ) :
        if self.timerOp :
            self.timerOp.cancel()
            self.timerOp = None

    def postMessage( self, msg ) :
        self.lock.acquire()
        try :
            self.messages.append( msg )
        finally :
            self.lock.release()

    def getMessage( self ) :
        self.lock.acquire()
        try :
            if len(self.messages) > 0 :
                msg = self.messages[0]
                del self.messages[0]
                return msg
            else :
                return None
        finally :
            self.lock.release()

    def _onTimer( self ) :
        msg = self.getMessage()
        if msg is not None :
            self.callback( msg )
