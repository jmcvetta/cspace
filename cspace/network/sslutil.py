import time
from ncrypt.digest import DigestType
from ncrypt.dh import DH
from ncrypt.x509 import X509Certificate, X509Name
from ncrypt.ssl import SSLContext, SSL_METHOD_TLSv1, SSL_VERIFY_MODE_SELF_SIGNED

def _makeCertificate( userName, rsaKey ) :
    certName = X509Name()
    certName.addEntry( 'commonName', userName )
    cert = X509Certificate()
    cert.setVersion( 3 )
    cert.setSerialNumber( 1 )
    cert.setSubject( certName )
    cert.setIssuer( certName )
    cert.setPublicKey( rsaKey )
    cert.setNotBefore( 0 )
    cert.setNotAfter( int(time.time()) + 10*365*24*60*60 )
    cert.sign( rsaKey, DigestType('sha1') )
    return cert

_dh_params_pem = """
-----BEGIN DH PARAMETERS-----
MIGHAoGBAPSI/VhOSdvNILSd5JEHNmszbDgNRR0PfIizHHxbLY7288kjwEPwpVsY
jY67VYy4XTjTNP18F1dDox0YbN4zISy1Kv884bEpQBgRjXyEpwpy1obEAxnIByl6
ypUM2Zafq9AKUJsCRtMIPWakXUGfnHy9iUsiGSa6q6Jew1XpL3jHAgEC
-----END DH PARAMETERS-----
copied from openssl-0.9.8b/apps/dh1024.pem
"""

def makeSSLContext( userName, rsaKey ) :
    cert = _makeCertificate( userName, rsaKey )
    sslContext = SSLContext( SSL_METHOD_TLSv1 )
    sslContext.setCertificate( cert )
    sslContext.setPrivateKey( rsaKey )
    sslContext.setVerifyMode( SSL_VERIFY_MODE_SELF_SIGNED )
    dh = DH()
    dh.fromPEM_Parameters( _dh_params_pem )
    sslContext.enableDH( dh )
    return sslContext
