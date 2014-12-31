_hexChars = '0123456789abcdef'
_hexTab = {}
def _initHexTab() :
    for (i,c) in enumerate(_hexChars) :
        _hexTab[c] = i
        _hexTab[c.upper()] = i
_initHexTab()


class HexDecodeError( Exception ) : pass

def hexByteEncode( c ) :
    x = ord(c)
    return _hexChars[x >> 4] + _hexChars[x&15]

def hexByteDecode( s, i=0 ) :
    try :
        return chr( _hexTab[s[i]]*16 + _hexTab[s[i+1]] )
    except (KeyError,IndexError) :
        raise HexDecodeError

def hexEncode( s ) :
    return ''.join( [hexByteEncode(c) for c in s] )

def hexDecode( s ) :
    return ''.join( [hexByteDecode(s,i) for i in range(0,len(s),2)] )
