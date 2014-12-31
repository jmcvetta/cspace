from cspace.dht.params import DHT_ID_LENGTH, DHT_K
from cspace.dht.util import checkAddr

class ProtocolError(Exception) : pass

def _assert( cond, msg=None ) :
    if not cond :
        if msg is None : msg = 'invalid message data'
        raise ProtocolError, msg

def validatePingRequest( msg ) :
    _assert( len(msg) == 0 )
    return msg

def validatePingResponse( msg ) :
    _assert( type(msg) is str )
    _assert( len(msg) == 0 )
    return msg

def validateGetAddrRequest( msg ) :
    _assert( len(msg) == 0 )
    return msg

def validateGetAddrResponse( msg ) :
    _assert( type(msg) is list )
    msg = tuple(msg)
    _assert( checkAddr(msg) )
    return msg

def validateGetKeyRequest( msg ) :
    _assert( len(msg) == 1 )
    _assert( type(msg[0]) is str )
    return msg

def validateGetKeyResponse( msg ) :
    _assert( type(msg) is list )
    _assert( len(msg) == 4 )
    result,data,updateLevel,signature = msg
    _assert( type(result) is int )
    _assert( type(data) is str )
    _assert( type(updateLevel) is int )
    _assert( updateLevel >= 0 )
    _assert( type(signature) is str )
    return msg

def validatePutKeyRequest( msg ) :
    _assert( len(msg) == 4 )
    publicKeyData,data,updateLevel,signature = msg
    _assert( type(publicKeyData) is str )
    _assert( type(data) is str )
    _assert( type(updateLevel) is int )
    _assert( updateLevel > 0 )
    _assert( type(signature) is str )
    return msg

def validatePutKeyResponse( msg ) :
    _assert( type(msg) is list )
    _assert( len(msg) == 4 )
    result,data,updateLevel,signature = msg
    _assert( type(result) is int )
    _assert( type(data) is str )
    _assert( type(updateLevel) is int )
    _assert( updateLevel >= 0 )
    _assert( type(signature) is str )
    return msg

def validateFindNodesRequest( msg ) :
    _assert( len(msg) == 1 )
    _assert( type(msg[0]) is str )
    _assert( len(msg[0]) == DHT_ID_LENGTH )
    return msg

def validateFindNodesResponse( msg ) :
    _assert( type(msg) is list )
    msg = msg[:DHT_K]
    out = []
    for x in msg :
        _assert( type(x) is list )
        x = tuple(x)
        _assert( checkAddr(x) )
        out.append( x )
    return out

def validateFirewallCheckRequest( msg ) :
    _assert( len(msg) == 2 )
    addr = tuple( msg )
    _assert( checkAddr(addr) )
    return addr

def validateFirewallCheckResponse( msg ) :
    _assert( type(msg) is list )
    fwResult,token = msg
    _assert( type(fwResult) is int )
    _assert( type(token) is str )
    return msg

MESSAGES = ( 'Ping', 'GetAddr', 'GetKey', 'PutKey', 'FindNodes', 'FirewallCheck' )
requestValidators = {}
responseValidators = {}
def _initTables() :
    g = globals()
    for m in MESSAGES :
        requestValidators[m] = g[ 'validate' + m + 'Request' ]
        responseValidators[m] = g[ 'validate' + m + 'Response' ]
_initTables()

def validateRequest( msg ) :
    _assert( type(msg) is list )
    _assert( len(msg) >= 2 )
    cmd, useSourceAddr = msg[0], msg[1]
    del msg[:2]
    _assert( type(cmd) is str )
    _assert( type(useSourceAddr) is int )
    _assert( useSourceAddr in (0,1) )
    validator = requestValidators.get( cmd )
    _assert( validator is not None )
    msg = validator( msg )
    return (cmd, useSourceAddr, msg)

def validateResponse( cmd, msg ) :
    validator = responseValidators[cmd]
    return validator( msg )
