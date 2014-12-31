import logging
logging.getLogger().addHandler( logging.StreamHandler() )

from ncrypt.rsa import RSAKey
from nitro.selectreactor import SelectReactor
from cspace.main.profile import UserProfile
from cspace.main.session import UserSession

reactor = None
session = None

def onOnline( err ) :
    print 'onOnline, err =', err

def doOnline() :
    print 'calling goOnline...'
    session.goOnline( ('127.0.0.1',13542), onOnline )

def onClose() :
    print 'onClose'

def getProfile() :
    key = RSAKey()
    key.fromPEM_PrivateKey( file('ks.key').read() )
    profile = UserProfile( key, 'ks' )
    return profile

def main() :
    global reactor, session
    reactor = SelectReactor()
    profile = getProfile()
    session = UserSession( profile, reactor )
    session.setCloseCallback( onClose )
    reactor.callLater( 1, doOnline )
    reactor.run()

if __name__ == '__main__' :
    main()
