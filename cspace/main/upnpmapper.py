from time import time
from random import randint
from nitro.async import AsyncOp
from nitro.upnp import UPnpActions
from cspace.util.statemachine import StateMachine

class UPnpMapper( object ) :
    DEFAULT = 0
    INITIALIZING = 1
    READY = 2
    CLEANINGUP = 3
    CLOSED = 4

    def __init__( self, reactor ) :
        self.reactor = reactor
        self.sm = StateMachine( self.DEFAULT )
        self.device = None
        self.externalIP = None
        self.cleaningupCount = 0
        self.sm.appendCallback( self._onCleanup, dest=self.CLEANINGUP, single=True )
        self._initialize()

    def shutdown( self, callback=None ) :
        if self.sm.current() in (self.CLEANINGUP,self.CLOSED) :
            return None
        if self.sm.current() == self.READY :
            self.sm.change( self.CLEANINGUP )
        else :
            self.sm.change( self.CLOSED )
        if self.sm.current() == self.CLOSED :
            return None
        def onClosed() : op.notify()
        def doCancel() : self.sm.removeCallback( callbackId )
        callbackId = self.sm.appendCallback( onClosed,
                dest=self.CLOSED, single=True )
        op = AsyncOp( callback, doCancel )
        return op

    def _onCleanup( self ) :
        if self.cleaningupCount == 0 :
            self.sm.change( self.CLOSED )

    def _initialize( self ) :
        class Dummy : pass
        obj = Dummy()
        def onError() :
            self.sm.removeCallback( callbackId )
            self.sm.change( self.CLOSED )
        def onDiscover( device ) :
            if device is None :
                onError()
                return
            self.device = device
            obj.op = UPnpActions.getExternalIP( device, self.reactor,
                    onExternalIP )
        def onExternalIP( externalIP ) :
            if externalIP is None :
                onError()
                return
            self.externalIP = externalIP
            self.sm.removeCallback( callbackId )
            self.sm.change( self.READY )
        self.sm.change( self.INITIALIZING )
        obj.op = UPnpActions.findDevice( self.reactor, onDiscover )
        callbackId = self.sm.insertCallback( lambda : obj.op.cancel(),
                src=self.INITIALIZING, single=True )

    def addMapping( self, localIP, localPort, callback=None ) :
        class Dummy : pass
        obj = Dummy()
        if self.sm.current() not in (self.INITIALIZING,self.READY) :
            timerOp = self.reactor.callLater( 0, lambda : obj.op.notify(None) )
            obj.op = AsyncOp( callback, timerOp.cancel )
            return obj.op
        def doReady() :
            obj.attempt = 0
            doAttempt()
        def doAttempt() :
            if obj.attempt == 3 :
                obj.op.notify( None )
                return
            obj.attempt += 1
            obj.externalPort = randint( 10000, 20000 )
            desc = 'CSpace_t%d' % int(time())
            obj.addOp = UPnpActions.addMapping( self.device, obj.externalPort,
                    'TCP', localPort, localIP, desc, self.reactor, onAdd )
            obj.callbackId = self.sm.insertCallback( onAbort, src=self.READY,
                    single=True )
            obj.op.setCanceler( onCancel )
        def onCancel() :
            obj.addOp.cancel()
            self.sm.removeCallback( obj.callbackId )
        def onAbort() :
            obj.addOp.cancel()
            obj.op.notify( None )
        def onAdd( result ) :
            self.sm.removeCallback( obj.callbackId )
            if not result :
                doAttempt()
                return
            mapping = (self.externalIP,obj.externalPort)
            obj.op.notify( mapping )
            self.sm.insertCallback( onCleanup, dest=self.CLEANINGUP, single=True )
        def onCleanup() :
            self.cleaningupCount += 1
            UPnpActions.delMapping( self.device, obj.externalPort, 'TCP',
                    self.reactor, onDelMapping )
        def onDelMapping( result ) :
            self.cleaningupCount -= 1
            self._onCleanup()
        if self.sm.current() == self.INITIALIZING :
            def checkReady() :
                if self.sm.current() == self.READY :
                    obj.op.setCanceler( None )
                    doReady()
                    return
                obj.op.notify( None )
            obj.callbackId = self.sm.insertCallback( checkReady,
                    src=self.INITIALIZING, single=True )
            obj.op = AsyncOp( callback,
                    lambda : self.sm.removeCallback(obj.callbackId) )
            return obj.op
        obj.op = AsyncOp( callback, None )
        doReady()
        return obj.op
