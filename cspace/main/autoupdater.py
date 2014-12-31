import os, glob
from tempfile import mkstemp
from nitro.http import HttpRequest
from cspace.main.common import appSettings

def currentBuildNumber() :
    return appSettings().getInt( 'BuildNumber.txt', -1 )

UPDATE_CHECK_INTERVAL = 30*60
UPDATE_BASE_URL = 'http://cspace.in/downloads/'
UPDATE_LATEST_VERSION = 'LatestVersion.txt'

class AutoUpdater( object ) :
    def __init__( self, reactor ) :
        self.reactor = reactor
        self.buildNumber = currentBuildNumber()
        self.timerOp = None
        self.httpOp = None
        self.updateCallback = None
        self._startTimer()

    def setUpdateCallback( self, updateCallback ) :
        self.updateCallback = updateCallback

    def shutdown( self ) :
        if self.timerOp : self.timerOp.cancel()
        if self.httpOp : self.httpOp.cancel()

    def _startTimer( self ) :
        assert self.timerOp is None
        self.timerOp = self.reactor.callLater( UPDATE_CHECK_INTERVAL, self._onTimer )

    def _onTimer( self ) :
        self.deleteOldInstallers()
        self.timerOp = None
        url = UPDATE_BASE_URL + UPDATE_LATEST_VERSION
        http = HttpRequest( self.reactor )
        self.httpOp = http.get( url, self._onGetVersionInfo )

    def _onGetVersionInfo( self, responseCode, data ) :
        self.httpOp = None
        if responseCode != 200 :
            print 'unable to get version info, response = %d' % responseCode
            self._startTimer()
            return
        installers = []
        try :
            for line in data.split('\n') :
                line = line.strip()
                if not line : continue
                info = line.split( ':' )
                for i,x in enumerate(info) :
                    if i > 0 : info[i] = int(x)
                fileName,fileSize,buildNumber,requires = info
                info = (-buildNumber,fileSize,requires,fileName)
                installers.append( info )
        except (TypeError,ValueError), e :
            print 'error parsing version info, e =', e
            self._startTimer()
            return
        installers.sort()
        for info in installers :
            buildNumber,fileSize,requires,fileName = info
            buildNumber = -buildNumber
            if buildNumber <= self.buildNumber :
                self._startTimer()
                return
            if requires > self.buildNumber : continue
            print 'fetching installer = %s' % fileName
            url = UPDATE_BASE_URL + fileName
            self.updateFileName = fileName
            http = HttpRequest( self.reactor )
            self.httpOp = http.get( url, self._onFetchInstaller )
            return
        self._startTimer()

    def _onFetchInstaller( self, responseCode, data ) :
        self.httpOp = None
        if responseCode != 200 :
            print 'unable to fetch update installer, response = %d' % responseCode
            self._startTimer()
            return
        print 'fetched update installer: %d' % len(data)
        if self.updateCallback :
            self.updateCallback( self.updateFileName, data )
            return
        self._startTimer()
        return

    def deleteOldInstallers( self ) :
        for envVar in 'TEMP TMP TMPDIR'.split() :
            if not os.environ.has_key(envVar) : continue
            tempDir = os.environ[envVar]
            if not os.path.isdir(tempDir) : continue
            fileList = []
            try :
                fileList = glob.glob( os.path.join(tempDir,'CSpaceUpdate*.exe') )
            except Exception, e :
                print 'unable to list installers in %s: %s' % (tempDir,e)
            for f in fileList :
                try :
                    os.unlink( f )
                    print 'deleted old installer %s' % f
                except Exception, e :
                    print 'unable to delete installer %s: %s' % (f,e)

    def saveInstaller( self, updateFileName, updateFileData ) :
        for envVar in 'TEMP TMP TMPDIR'.split() :
            if not os.environ.has_key(envVar) : continue
            tempDir = os.environ[envVar]
            if not os.path.isdir(tempDir) : continue
            try :
                fd,filePath = mkstemp( '.exe', 'CSpaceUpdate', tempDir )
            except :
                continue
            try :
                os.close( fd )
                out = file( filePath, 'wb' )
                out.write( updateFileData )
                out.close()
            except :
                continue
            return filePath
        return None
