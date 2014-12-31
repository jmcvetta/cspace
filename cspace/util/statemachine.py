class StateMachine( object ) :
    def __init__( self, initial ) :
        assert initial >= 0
        self.__current = initial
        self.__previous = None
        self.__nextId = 0
        self.__callbacks = []
        self.__callbackIds = {}
        self.__changing = False

    def current( self ) : return self.__current
    def previous( self ) : return self.__previous

    def insertCallback( self, callback, src=None, dest=None, single=False ) :
        callbackId = self.__nextId
        self.__nextId += 1
        self.__callbacks.insert( 0, (src,dest,callback,callbackId,single) )
        self.__callbackIds[callbackId] = 1
        return callbackId

    def appendCallback( self, callback, src=None, dest=None, single=False ) :
        callbackId = self.__nextId
        self.__nextId += 1
        self.__callbacks.append( (src,dest,callback,callbackId,single) )
        self.__callbackIds[callbackId] = 1
        return callbackId

    def removeCallback( self, callbackId ) :
        del self.__callbackIds[callbackId]
        for i,info in enumerate(self.__callbacks) :
            if info[3] == callbackId :
                del self.__callbacks[i]
                return
        assert False

    def change( self, state ) :
        assert not self.__changing
        if self.__current == state : return
        self.__previous = self.__current
        self.__current = state
        receivers = []
        for src,dest,cb,cbid,single in self.__callbacks :
            if (src is not None) and (src != self.__previous) : continue
            if (dest is not None) and (dest != self.__current) : continue
            receivers.append( (cb,cbid,single) )
        if not receivers : return
        last = receivers.pop()
        self.__changing = True
        for cb,cbid,single in receivers :
            if cbid in self.__callbackIds :
                if single :
                    self.removeCallback( cbid )
                cb()
        self.__changing = False
        cb,cbid,single = last
        if cbid in self.__callbackIds :
            if single :
                self.removeCallback( cbid )
            cb()
