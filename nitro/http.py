import pycurl
from nitro.async import AsyncOp

def curlPerform( curlHandle, reactor, callback=None ) :
    return CurlPerformer(curlHandle,reactor,callback).getOp()

class CurlPerformer( object ) :
    def __init__( self, curlHandle, reactor, callback=None ) :
        self.reactor = reactor
        self.cm = pycurl.CurlMulti()
        self.c = curlHandle
        self.cm.add_handle( self.c )
        self.fdsets = ( [], [], [] )
        self.timerOp = self.reactor.callLater( 0, self._onInitialTimer )
        self.op = AsyncOp( callback, self._doCancel )

    def getOp( self ) : return self.op

    def _onInitialTimer( self ) :
        self.timerOp = self.reactor.addTimer( 1, self._onProcess )
        self._onProcess()

    def _addEvents( self ) :
        self.fdsets = self.cm.fdset()
        r = self.reactor
        for fd in self.fdsets[0] :
            r.addReadCallback( fd, self._onProcess )
        for fd in self.fdsets[1] :
            r.addWriteCallback( fd, self._onProcess )
        for fd in self.fdsets[2] :
            r.addExceptionCallback( fd, self._onProcess )

    def _removeEvents( self ) :
        r = self.reactor
        for fd in self.fdsets[0] :
            r.removeReadCallback( fd )
        for fd in self.fdsets[1] :
            r.removeWriteCallback( fd )
        for fd in self.fdsets[2] :
            r.removeExceptionCallback( fd )

    def _doCancel( self ) :
        self.timerOp.cancel()
        self.timerOp = None
        self._removeEvents()
        self.cm.remove_handle( self.c )
        self.cm.close()

    def _doNotify( self, errCode ) :
        self.timerOp.cancel()
        self.timerOp = None
        self.cm.remove_handle( self.c )
        self.cm.close()
        self.op.notify( errCode )

    def _onProcess( self ) :
        self._removeEvents()
        while 1 :
            ret,numHandles = self.cm.perform()
            if ret != pycurl.E_CALL_MULTI_PERFORM :
                break
        numQ, okList, errList = self.cm.info_read()
        assert numQ == 0
        assert len(okList)+len(errList) <= 1
        if len(okList) > 0 :
            self._doNotify( 0 )
        elif len(errList) > 0 :
            c,err,errMsg = errList[0]
            self._doNotify( err )
        else :
            self._addEvents()

class HttpRequest( object ) :
    def __init__( self, reactor ) :
        self.reactor = reactor
        self.c = pycurl.Curl()
        self.c.setopt( pycurl.FOLLOWLOCATION, 1 )
        self.c.setopt( pycurl.MAXREDIRS, 5 )
        self.c.setopt( pycurl.NOSIGNAL, 1 )
        self.headers = []

    def addHeader( self, header ) :
        self.headers.append( header )

    def _request( self, url, callback ) :
        self.c.setopt( pycurl.URL, url )
        if self.headers :
            self.c.setopt( pycurl.HTTPHEADER, self.headers )
        self.data = []
        self.c.setopt( pycurl.WRITEFUNCTION, self.data.append )
        def doCancel() :
            curlOp.cancel()
            self.c.close()
        def onDone( errCode ) :
            if errCode != 0 :
                code,data = -1,None
            else :
                code = self.c.getinfo( pycurl.RESPONSE_CODE )
                data = ''.join( self.data )
            self.c.close()
            op.notify( code, data )
        curlOp = curlPerform( self.c, self.reactor, onDone )
        op = AsyncOp( callback, doCancel )
        return op

    def get( self, url, callback=None ) :
        return self._request( url, callback )

    def post( self, url, postData, callback=None ) :
        self.c.setopt( pycurl.POST, 1 )
        self.c.setopt( pycurl.POSTFIELDS, postData )
        self.c.setopt( pycurl.POSTFIELDSIZE, len(postData) )
        hasExpect = False
        for h in self.headers :
            if h.startswith('Expect:') : hasExpect = True
        if not hasExpect :
            self.addHeader( 'Expect:' )
        return self._request( url, callback )

if __name__ == '__main__' :
    import sys, logging
    logging.getLogger().addHandler( logging.StreamHandler() )
    from nitro.selectreactor import SelectReactor
    reactor = SelectReactor()
    url = sys.argv[1]
    def onHttpGet( returnCode, data ) :
        print 'returnCode = %d' % returnCode
        if data is not None :
            print 'len(data) = %d' % len(data)
            sys.stdout.write( data )
            sys.stdout.flush()
        reactor.stop()
    HttpRequest( reactor ).get( url, onHttpGet )
    reactor.run()
