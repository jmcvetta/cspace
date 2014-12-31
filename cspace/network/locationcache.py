from time import time
from nitro.async import AsyncOp
from cspace.network.location import lookupUser

# cache entry states
(ES_DEFAULT,ES_LOOKINGUP,ES_NOTIFYING) = range(3)

class _Entry( object ) :
    def __init__( self, publicKey ) :
        self.publicKey = publicKey
        self.location = None
        self.timestamp = time()
        self.state = ES_DEFAULT
        self.lookupOp = None
        self.notifyOps = None

class LocationCache( object ) :
    def __init__( self, dhtClient, nodeTable, reactor ) :
        self.dhtClient = dhtClient
        self.nodeTable = nodeTable
        self.reactor = reactor
        self.d = {}

    def close( self ) :
        for entry in self.d.values() :
            assert entry.state != ES_NOTIFYING
            if entry.state == ES_LOOKINGUP :
                entry.lookupOp.cancel()
                entry.notifyOps = None
        self.d.clear()

    def _getEntry( self, publicKey ) :
        return self.d.get( publicKey.toDER_PublicKey() )

    def getLocation( self, publicKey ) :
        entry = self._getEntry( publicKey )
        if entry is None :
            return None
        return entry.location

    def _onLookupUser( self, entry, location ) :
        entry.location = location
        entry.timestamp = time()
        entry.lookupOp = None
        entry.state = ES_NOTIFYING
        for op in list(entry.notifyOps) :
            if op in entry.notifyOps :
                entry.notifyOps.remove(op)
                op.notify( location )
        entry.notifyOps = None
        entry.state = ES_DEFAULT

    def refreshUser( self, publicKey, callback=None ) :
        pubKeyData = publicKey.toDER_PublicKey()
        entry = self.d.get( pubKeyData )
        if entry is None :
            entry = _Entry( publicKey )
            self.d[pubKeyData] = entry
        assert entry.state != ES_NOTIFYING
        if entry.state == ES_DEFAULT :
            assert entry.lookupOp is None
            assert entry.notifyOps is None
            def onLookupUser( location ) :
                self._onLookupUser( entry, location )
            entry.lookupOp = lookupUser( publicKey, self.dhtClient,
                    self.nodeTable,
                    lambda loc : self._onLookupUser(entry,loc) )
            entry.state = ES_LOOKINGUP
            entry.notifyOps = set()
        def doCancel() :
            entry.notifyOps.remove( op )
        op = AsyncOp( callback, doCancel )
        entry.notifyOps.add( op )
        return op
