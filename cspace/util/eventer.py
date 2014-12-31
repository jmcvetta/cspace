import logging

logger = logging.getLogger( 'cspace.util.eventer' )

class Eventer( object ) :
    def __init__( self ) :
        self.__nextId = 0
        self.__callbacks = {}
        self.__callbackIds = {}

    def register( self, event, callback ) :
        callbackId = self.__nextId
        self.__nextId += 1
        cbList = self.__callbacks.setdefault( event, [] )
        cbList.append( (callback,callbackId) )
        self.__callbackIds[callbackId] = event
        return callbackId

    def remove( self, callbackId ) :
        event = self.__callbackIds.pop( callbackId )
        cbList = self.__callbacks[event]
        for i,info in enumerate(cbList) :
            if info[1] == callbackId :
                del cbList[i]
                if not cbList :
                    del self.__callbacks[event]
                return
        assert False

    def trigger( self, event, *args, **kwargs ) :
        cbList = self.__callbacks.get( event )
        if cbList is None :
            logger.warning( 'no event handler registered for event: %s', event )
            return
        for cb,cbid in cbList[:] :
            if cbid in self.__callbackIds :
                cb( *args, **kwargs )
