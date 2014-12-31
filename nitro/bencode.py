from types import IntType, LongType, StringType, ListType, TupleType, DictType

def encodeInt( x, out ) :
    assert type(x) in (IntType,LongType)
    out.extend( ('i', str(x), 'e') )

def encodeString( x, out ) :
    assert type(x) is StringType
    out.extend( (str(len(x)), ':', x) )

def encodeList( x, out ) :
    assert type(x) in (ListType,TupleType)
    out.append( 'l' )
    for i in x : encoderTable[type(i)]( i, out )
    out.append( 'e' )

def encodeDict( x, out ) :
    assert type(x) is DictType
    out.append( 'd' )
    items = x.items()
    items.sort()
    for a,b in items :
        encodeString( a, out )
        encoderTable[type(b)]( b, out )
    out.append( 'e' )

encoderTable = {}
encoderTable[IntType] = encodeInt
encoderTable[LongType] = encodeInt
encoderTable[StringType] = encodeString
encoderTable[ListType] = encodeList
encoderTable[TupleType] = encodeList
encoderTable[DictType] = encodeDict

def encode( x ) :
    out = []
    encoderTable[type(x)]( x, out )
    return ''.join( out )

class DecodeError( Exception ) : pass

def decodeInt( x, i ) :
    assert x[i] == 'i'
    e = x.index( 'e', i )
    i += 1
    ret = int(x[i:e])
    if x[i] == '-' :
        if x[i+1] == '0' : raise ValueError
    elif x[i] == '0' :
        if e != i+1 : raise ValueError
    return (ret, e+1)

def decodeString( x, i ) :
    e = x.index( ':', i )
    count = int( x[i:e] )
    if count < 0 : raise ValueError
    if x[i] == '0' and e != i+1 : raise ValueError
    e += 1
    ret = x[e:e+count]
    return (ret, e+count)

def decodeList( x, i ) :
    assert x[i] == 'l'
    ret, i = [], i+1
    next = x[i]
    while next != 'e' :
        (v, i) = decoderTable[next]( x, i )
        ret.append( v )
        next = x[i]
    return (ret, i+1)

def decodeDict( x, i ) :
    assert x[i] == 'd'
    ret, i = {}, i+1
    prev = None
    while x[i] != 'e' :
        (a, i) = decodeString( x, i )
        if a <= prev : raise ValueError
        prev = a
        (b, i) = decoderTable[x[i]]( x, i )
        ret[a] = b
    return (ret, i+1)

decoderTable = {}
decoderTable['i'] = decodeInt
for i in range(10) :
    decoderTable[chr(ord('0')+i)] = decodeString
decoderTable['l'] = decodeList
decoderTable['d'] = decodeDict

def decode( x ) :
    try :
        (ret,i) = decoderTable[x[0]]( x, 0 )
    except (KeyError, IndexError, ValueError) :
        raise DecodeError, 'invalid bencoded data'
    if i != len(x) :
        raise DecodeError, 'invalid tail data'
    return ret
