from hexcode import hexByteEncode, hexByteDecode, HexDecodeError

class WordDecodeError( Exception ) : pass

def wordEncode( s ) :
    out = []
    for c in s :
        if (not c.isalnum()) and (c not in '_-.') :
            out.append( '%' )
            out.append( hexByteEncode(c) )
        else :
            out.append( c )
    return ''.join( out )

def wordDecode( s ) :
    try :
        out = []
        i = 0
        while i < len(s) :
            if s[i] == '%' :
                out.append( hexByteDecode(s,i+1) )
                i += 3
            else :
                out.append( s[i] )
                i += 1
        return ''.join( out )
    except HexDecodeError :
        raise WordDecodeError
