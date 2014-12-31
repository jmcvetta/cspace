from nitro.async import AsyncOp
from nitro.bencode import encode, decode, DecodeError

from cspace.util.validate import validateIPAddress, validateInetAddress

class RoutedLocation( object ) :
    def __init__( self, routerAddr, routerId ) :
        self.routerAddr = routerAddr
        self.routerId = routerId
    
    def __cmp__( self, other ) :
        if other is None :
            return 1
        return cmp( (self.routerAddr,self.routerId), (other.routerAddr,other.routerId) )

class DirectLocation( object ) :
    def __init__( self, addr ) :
        self.addr = addr

    def __cmp__( self, other ) :
        if other is None :
            return 1
        return cmp( self.addr, other.addr )

class UserLocation( object ) :
    def __init__( self, directLocations, routedLocations, publicIP ) :
        self.directLocations = directLocations
        self.routedLocations = routedLocations
        self.publicIP = publicIP

    def __cmp__( self, other ) :
        if other is None :
            return 1
        selfKey = ( self.directLocations, self.routedLocations,
                self.publicIP )
        otherKey = ( other.directLocations, other.routedLocations,
                other.publicIP )
        return cmp( selfKey, otherKey )

    def encode( self ) :
        directList = [loc.addr for loc in self.directLocations]
        routedList = [(loc.routerAddr,loc.routerId) for loc in self.routedLocations]
        data = { 'direct' : directList,
            'routed' : routedList,
            'publicIP' : self.publicIP }
        return encode( data )

    @staticmethod
    def decode( data ) :
        data = decode( data )
        if type(data) is not dict : raise TypeError
        publicIP = data.get( 'publicIP' )
        try :
            validateIPAddress( publicIP )
        except :
            publicIP = ''
        directLocations = []
        routedLocations = []
        for direct in data.get('direct',[]) :
            if type(direct) is not list : continue
            direct = tuple( direct )
            try :
                validateInetAddress( direct )
            except :
                continue
            directLocations.append( DirectLocation(direct) )
        for routed in data.get('routed',[]) :
            if type(routed) is not list : continue
            if len(routed) != 2 : continue
            routerAddr,routerId = routed
            if type(routerId) is not str : continue
            if type(routerAddr) is not list : continue
            routerAddr = tuple( routerAddr )
            try :
                validateInetAddress( routerAddr )
            except :
                continue
            routedLocations.append( RoutedLocation(routerAddr,routerId) )
        return UserLocation( directLocations, routedLocations, publicIP )

def publishUserLocation( rsaKey, location, updateLevel, dhtClient,
        nodeTable, callback=None ) :
    def onResult( putCount, updateLevel ) :
        op.notify( putCount>0, updateLevel )
    dhtOp = dhtClient.lookupPutKey( rsaKey, location.encode(),
            updateLevel, nodeTable.getLiveNodes(), onResult )
    op = AsyncOp( callback, dhtOp.cancel )
    return op

def lookupUser( publicKey, dhtClient, nodeTable, callback=None ) :
    def onResult( result ) :
        if len(result) == 0 :
            op.notify( None )
            return
        try :
            location = UserLocation.decode( result[0][0] )
        except :
            op.notify( None )
            return
        op.notify( location )
    dhtOp = dhtClient.lookupGetKey( publicKey, nodeTable.getLiveNodes(),
            onResult )
    op = AsyncOp( callback, dhtOp.cancel )
    return op
