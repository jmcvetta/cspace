import sys, logging
from nitro.async import AsyncOp
from nitro.reactor import Reactor

from qt import *

logger = logging.getLogger( 'nitro.qtreactor' )

def _addCallback( handleMap, sockfd, callback, notifyType ) :
    assert sockfd not in handleMap
    notifier = QSocketNotifier( sockfd, notifyType )
    QObject.connect( notifier, SIGNAL('activated(int)'), callback )
    handleMap[sockfd] = (callback, notifier)

def _removeCallback( handleMap, sockfd ) :
    assert sockfd in handleMap
    notifier = handleMap[sockfd][1]
    notifier.setEnabled( False )
    del handleMap[sockfd]

class Qt3Reactor( Reactor ) :
    def __init__( self ) :
        self.readMap = {}
        self.writeMap = {}
        self.exceptionMap = {}
        self.timers = {}
        pass

    def addReadCallback( self, sockfd, callback ) :
        _addCallback( self.readMap, sockfd, callback, QSocketNotifier.Read )

    def removeReadCallback( self, sockfd ) :
        _removeCallback( self.readMap, sockfd )

    def addWriteCallback( self, sockfd, callback ) :
        _addCallback( self.writeMap, sockfd, callback, QSocketNotifier.Write )

    def removeWriteCallback( self, sockfd ) :
        _removeCallback( self.writeMap, sockfd )

    def addExceptionCallback( self, sockfd, callback ) :
        _addCallback( self.exceptionMap, sockfd, callback, QSocketNotifier.Exception )

    def removeExceptionCallback( self, sockfd ) :
        _removeCallback( self.exceptionMap, sockfd )

    def addTimer( self, timeout, callback=None ) :
        def onTimer() :
            op.notify()
        def doCancel() :
            del self.timers[op]
            timer.stop()
        timer = QTimer()
        QObject.connect( timer, SIGNAL('timeout()'), onTimer )
        timer.start( int(timeout*1000) )
        op = AsyncOp( callback, doCancel )
        self.timers[op] = (timer, op, onTimer, doCancel)
        return op

    def callLater( self, timeout, callback=None ) :
        def onTimer() :
            del self.timers[op]
            op.notify()
        def doCancel() :
            del self.timers[op]
            timer.stop()
        timer = QTimer()
        QObject.connect( timer, SIGNAL('timeout()'), onTimer )
        timer.start( int(timeout*1000), True )
        op = AsyncOp( callback, doCancel )
        self.timers[op] = (timer, op, onTimer, doCancel)
        return op

    def usesWSAAsyncSelect( self ) :
        return sys.platform == 'win32'
