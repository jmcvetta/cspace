_objects = []
_timerOp = None
_reactor = None

def initdelaygc( reactor ) :
    global _reactor
    _reactor = reactor

def delaygc( obj ) :
    global _timerOp
    _objects.append( obj )
    if _timerOp is not None :
        _timerOp.cancel()
    _timerOp = _reactor.callLater( 1, _onTimer )

def _onTimer() :
    global _timerOp
    _timerOp = None
    del _objects[:]
