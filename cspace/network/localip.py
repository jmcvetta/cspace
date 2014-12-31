import socket

USE_LOCALHOST = False

def getLocalIP() :
    s = socket.socket( socket.AF_INET, socket.SOCK_DGRAM )
    try :
        try :
            s.bind( ('',0) )
            s.connect( ('12.23.34.45',1234) )
            return s.getsockname()[0]
        except :
            if USE_LOCALHOST :
                return '127.0.0.1'
            return None
    finally :
        s.close()
