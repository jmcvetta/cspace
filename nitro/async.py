class AsyncOp( object ) :
    def __init__( self, callback=None, canceler=None ) :
        self.callback = callback
        self.canceler = canceler

    def setCallback( self, callback ) :
        self.callback = callback
        return self

    def setCanceler( self, canceler ) :
        self.canceler = canceler
        return self

    def cancel( self ) :
        if self.canceler : self.canceler()

    def notify( self, *args, **kwargs ) :
        if self.callback : self.callback( *args, **kwargs )

Op = AsyncOp
