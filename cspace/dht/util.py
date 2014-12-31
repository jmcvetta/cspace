from socket import inet_aton
from struct import pack, unpack
from types import IntType, StringType, TupleType
from ncrypt.digest import DigestType, Digest
from ncrypt.rsa import RSAKey, RSAError
from nitro.bencode import encode
from cspace.dht.params import DHT_ID_LENGTH, DHT_ID_MAX

digestType = DigestType( 'SHA1' )
digestLength = digestType.size()
assert digestLength == DHT_ID_LENGTH

def toId( x ) :
    return Digest(digestType).digest(x)

def idToNum( x ) :
    return long(x.encode('hex'),16)

def numToId( numId ) :
    s = hex( numId )
    assert s.startswith('0x')
    if s.endswith('L') : s = s[2:-1]
    else : s = s[2:]
    if len(s) < 2*DHT_ID_LENGTH :
        s = ('0'*(2*DHT_ID_LENGTH-len(s))) + s
    x = s.decode('hex')
    assert len(x) == DHT_ID_LENGTH
    return x

def checkIP( ip ) :
    if type(ip) is not StringType : return False
    if not ip : return False
    try :
        inet_aton( ip )
        return True
    except :
        return False

def checkPort( port ) :
    if type(port) is not IntType : return False
    return 0 < port < 65536

def checkAddr( addr ) :
    if type(addr) is not TupleType :
        return False
    if len(addr) != 2 : return False
    if not checkIP(addr[0]) : return False
    return checkPort( addr[1] )

def addrToStr( addr ) :
    ip = unpack( 'L', inet_aton(addr[0]) )[0]
    port = addr[1]
    return pack( '!LH', ip, port )

def addrToId( addr ) :
    return toId( addrToStr(addr) )

def verifySignature( publicKey, data, updateLevel, signature ) :
    payload = encode( ('DHT-DATA',data,updateLevel) )
    if type(publicKey) is str :
        k = RSAKey()
        try :
            k.fromDER_PublicKey( publicKey )
        except RSAError :
            return False
    else :
        k = publicKey
    try :
        digest = Digest(digestType).digest( payload )
        k.verify( signature, digest, digestType )
        return True
    except RSAError :
        return False

def computeSignature( rsaKey, data, updateLevel ) :
    payload = encode( ('DHT-DATA',data,updateLevel) )
    digest = Digest(digestType).digest( payload )
    return rsaKey.sign( digest, digestType )
