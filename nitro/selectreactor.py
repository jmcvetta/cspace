import sys, logging
from time import sleep
from select import select
from bisect import bisect, insort

from nitro.async import AsyncOp
from nitro.hirestimer import seconds
from nitro.reactor import Reactor

logger = logging.getLogger( 'nitro.selectreactor' )

def win32select( r, w, e, timeout ) :
    if not r and not w and not e :
        sleep( timeout )
        return [], [], []
    return select( r, w, e, timeout )

if sys.platform == 'win32' :
    _select = win32select
else :
    _select = select

def _add( which, sockfd, callback ) :
    assert sockfd not in which
    which[sockfd] = callback

def _remove( which, sockfd ) :
    assert sockfd in which
    del which[sockfd]

class TimerInfo(object) :
    def __init__( self, timerId, timeout, callback, singleShot ) :
        self.timerId = timerId
        self.timeout = timeout
        self.callback = callback
        self.singleShot = singleShot
        self.deadline = seconds() + timeout

class SelectStoppedError( Exception ) : pass

class SelectReactor( Reactor ) :
    def __init__( self ) :
        self.r, self.w, self.e = {}, {}, {}
        self.timers = {}
        self.deadlineList = []
        self.nextTimerId = 0
        self.stopped = False
        self._failOnException = False

    def addReadCallback( self, sockfd, callback ) :
        _add( self.r, sockfd, callback )

    def removeReadCallback( self, sockfd ) :
        _remove( self.r, sockfd )

    def addWriteCallback( self, sockfd, callback ) :
        _add( self.w, sockfd, callback )

    def removeWriteCallback( self, sockfd ) :
        _remove( self.w, sockfd )

    def addExceptionCallback( self, sockfd, callback ) :
        _add( self.e, sockfd, callback )

    def removeExceptionCallback( self, sockfd ) :
        _remove( self.e, sockfd )

    def addTimer( self, timeout, callback=None ) :
        op = AsyncOp( callback, lambda : self._cancelTimer(timerId) )
        timerId = self._addTimer( timeout, op.notify, False )
        return op

    def callLater( self, timeout, callback=None ) :
        op = AsyncOp( callback, lambda : self._cancelTimer(timerId) )
        timerId = self._addTimer( timeout, op.notify, True )
        return op

    def usesWSAAsyncSelect( self ) :
        return False

    def _addTimer( self, timeout, callback, singleShot ) :
        timerId = self.nextTimerId
        self.nextTimerId += 1
        ti = TimerInfo( timerId, timeout, callback, singleShot )
        self.timers[timerId] = ti
        insort( self.deadlineList, (ti.deadline,ti) )
        return timerId

    def _cancelTimer( self, timerId ) :
        ti = self.timers.get( timerId, None )
        assert ti is not None
        del self.timers[timerId]
        i = bisect( self.deadlineList, (ti.deadline,ti) )
        if (i > 0) and (self.deadlineList[i-1][1] is ti) :
            del self.deadlineList[i-1]

    def failOnException( self, fail ) :
        self._failOnException = fail

    def stop( self ) :
        self.stopped = True

    def runOnce( self ) :
        timeout = 0.1
        now = seconds()
        dl = self.deadlineList
        if dl and (timeout+now > dl[0][0]) :
            timeout = dl[0][0] - now
            if timeout < 0 : timeout = 0

        if self.stopped :
            raise SelectStoppedError
        (rs, ws, es) = _select( self.r.keys(), self.w.keys(), self.e.keys(), timeout )

        now = seconds()
        fired = []
        for (deadline,ti) in dl :
            if deadline <= now :
                fired.append(ti)
            else : break
        if fired : del dl[0:len(fired)]
        for ti in fired :
            if ti.timerId in self.timers :
                if ti.singleShot :
                    del self.timers[ti.timerId]
                try :
                    ti.callback()
                except :
                    logger.exception( 'Error in timer callback' )
                    if self._failOnException : raise
                if (not ti.singleShot) and (ti.timerId in self.timers) :
                    ti.deadline = now + ti.timeout
                    insort( dl, (ti.deadline,ti) )

        for (fired,map) in ((rs,self.r), (ws,self.w), (es,self.e)) :
            for sockfd in fired :
                cb = map.get( sockfd, None )
                if cb is not None :
                    try :
                        cb()
                    except :
                        logger.exception( 'Error in socket event handler' )
                        if self._failOnException : raise
                    if self.stopped :
                        raise SelectStoppedError

    def run( self, timeout=None ) :
        self.stopped = False
        deadline = None
        if timeout is not None :
            deadline = seconds() + timeout
        try :
            while 1 :
                if (deadline is not None) and (seconds() >= deadline) :
                    break
                self.runOnce()
        except SelectStoppedError :
            return
        except KeyboardInterrupt :
            print 'Ctrl-C detected'
            return
