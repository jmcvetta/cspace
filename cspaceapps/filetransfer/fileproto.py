from types import IntType, StringType, ListType

_errorValues = range( 6 )
(
ERR_NONE,
ERR_NOTFOUND,
ERR_DENIED,
ERR_NOTAFILE,
ERR_NOTADIR,
ERR_UNKNOWN
) = _errorValues
assert ERR_NONE == 0

class ProtocolError(Exception) : pass

_badPathElements = ('','.','..')

def _validateDirPath( p ) :
    _assert( p.find('\\') == -1 )
    elems = p.split( '/' )
    _assert( len(elems) >= 2 )
    _assert( elems[0] == elems[-1] == '' )
    del elems[0]
    for x in elems[:-1] :
        _assert( x not in _badPathElements )
    return elems

def _validateFilePath( p ) :
    _assert( p.find('\\') == -1 )
    elems = p.split( '/' )
    _assert( len(elems) >= 2 )
    _assert( elems[0] == '' )
    del elems[0]
    for x in elems :
        _assert( x not in _badPathElements )
    return elems

def _validateEntry( f ) :
    s = len( f )
    _assert( s > 0 )
    isDir = f[-1] == '/'
    if isDir :
        dirName = f[:-1]
        _assert( dirName not in _badPathElements )
        _assert( dirName.find('/') == -1 )
        _assert( dirName.find('\\') == -1 )
    else :
        _assert( f not in _badPathElements )
        _assert( f.find('/') == -1 )
        _assert( f.find('\\') == -1 )

def _vResponseHeader( msg, size ) :
    _assert( type(msg) is ListType )
    _assert( len(msg) == size )
    err = msg[0]
    _assert( type(err) is IntType )
    _assert( err >= 0 )

def _assert( cond, msg='protocol error' ) :
    if not cond :
        raise ProtocolError, msg

def _vListRequest( msg ) :
    _assert( len(msg) == 1 )
    _assert( type(msg[0]) is StringType )
    pathElements = _validateDirPath( msg[0] )
    return pathElements

def _vListResponse( msg ) :
    _vResponseHeader( msg, 2 )
    ls = msg[1]
    _assert( type(ls) is ListType )
    for x in ls :
        _assert( type(x) is StringType )
        _validateEntry( x )
    return msg

def _vGetSizeRequest( msg ) :
    _assert( len(msg) == 1 )
    _assert( type(msg[0]) is StringType )
    pathElements = _validateFilePath( msg[0] )
    return pathElements

def _vGetSizeResponse( msg ) :
    _vResponseHeader( msg, 2 )
    size = msg[1]
    _assert( type(size) is IntType )
    _assert( size >= 0 )
    return msg

def _vReadRequest( msg ) :
    _assert( len(msg) == 3 )
    path, offset, size = msg
    _assert( type(path) is StringType )
    pathElements = _validateFilePath( path )
    _assert( (type(offset) is IntType) and (offset >= 0) )
    _assert( (type(size) is IntType) and (size > 0) )
    return [ pathElements, offset, size ]

def _vReadResponse( msg ) :
    _vResponseHeader( msg, 2 )
    data = msg[1]
    _assert( type(data) is StringType )
    return msg

_validators = {}
_validators['List'] = (_vListRequest,_vListResponse)
_validators['GetSize'] = (_vGetSizeRequest,_vGetSizeResponse)
_validators['Read'] = (_vReadRequest,_vReadResponse)

def validateRequest( msg ) :
    _assert( type(msg) is ListType )
    _assert( len(msg) >= 1 )
    cmd = msg[0]
    args = msg[1:]
    _assert( type(cmd) is StringType )
    validator = _validators.get( cmd, (None,None) )[0]
    _assert( validator is not None )
    args = validator( args )
    return (cmd,args)

def validateResponse( cmd, msg ) :
    validator = _validators.get( cmd, (None,None) )[1]
    _assert( validator is not None )
    return validator( msg )
