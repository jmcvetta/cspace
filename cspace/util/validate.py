from socket import inet_aton

class ValidationError( Exception ) : pass

def validateIPAddress( addr ) :
    if type(addr) is not str :
        raise ValidationError, 'invalid ip address'
    try :
        inet_aton( addr )
    except :
        raise ValidationError, 'invalid ip address'

def validatePortNumber( port ) :
    if type(port) is not int :
        raise ValidationError, 'invalid port number'
    if not (0 < port < 65536) :
        raise ValidationError, 'invalid port number'

def validateInetAddress( addr ) :
    if type(addr) is not tuple :
        raise ValidationError, 'invalid inet address'
    if len(addr) != 2 :
        raise ValidationError, 'invalid inet address'
    validateIPAddress( addr[0] )
    validatePortNumber( addr[1] )
