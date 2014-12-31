class Reactor(object) :
    def addReadCallback( self, sockfd, callback ) :
        raise NotImplementedError
    def removeReadCallback( self, sockfd ) :
        raise NotImplementedError

    def addWriteCallback( self, sockfd, callback ) :
        raise NotImplementedError
    def removeWriteCallback( self, sockfd ) :
        raise NotImplementedError

    def addExceptionCallback( self, sockfd, callback ) :
        raise NotImplementedError
    def removeExceptionCallback( self, sockfd ) :
        raise NotImplementedError

    # timeout is seconds in floating point, returns async.Op
    def addTimer( self, timeout, callback=None ) :
        raise NotImplementedError

    # single shot timer, timeout is float, return async.Op
    def callLater( self, timeout, callback=None ) :
        raise NotImplementedError
