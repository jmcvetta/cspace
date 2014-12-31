import os, sys, logging
from types import StringType, ListType

logger = logging.getLogger( 'cspace.util.settings' )

_appDir = os.path.dirname( os.path.abspath(sys.argv[0]) )
def getAppDir() :
    return _appDir

def getHomeDir() :
    if sys.platform != 'win32' :
        return os.path.expanduser( '~' )

    def valid(path) :
        if path and os.path.isdir(path) :
            return True
        return False
    def env(name) :
        return os.environ.get( name, '' )
    
    homeDir = env( 'USERPROFILE' )
    if not valid(homeDir) :
        homeDir = env( 'HOME' )
        if not valid(homeDir) :
            homeDir = '%s%s' % (env('HOMEDRIVE'),env('HOMEPATH'))
            if not valid(homeDir) :
                homeDir = env( 'SYSTEMDRIVE' )
                if homeDir and (not homeDir.endswith('\\')) :
                    homeDir += '\\'
                if not valid(homeDir) :
                    homeDir = 'C:\\'
    return homeDir

def getConfigDir( name ) :
    homeDir = getHomeDir()
    if sys.platform == 'win32' :
        subDir = '_%s' % name
    else :
        subDir = '.%s' % name
    configDir = os.path.join( homeDir, subDir )
    return configDir

class BaseSettings( object ) :
    def __init__( self, configDir ) :
        self.configDir = configDir

    def getConfigDir( self ) :
        return self.configDir

    def _mkdir( self, dpath ) :
        if os.path.isfile(dpath) :
            self._unlink( dpath )
        if not os.path.isdir(dpath) :
            try :
                if sys.platform == 'win32' :
                    os.makedirs( dpath )
                else :
                    os.makedirs( dpath, 0700 )
                return True
            except OSError :
                logger.exception( 'error creating directory: %s', dpath )
                return False
        return True

    def _listdir( self, dpath ) :
        try :
            return os.listdir( dpath )
        except OSError :
            logger.exception( 'error listing dir: %s', dpath )
            return []

    def _unlink( self, fpath ) :
        try :
            if os.path.isdir(fpath) :
                os.rmdir( fpath )
            else :
                os.unlink( fpath )
            return True
        except OSError :
            logger.exception( 'error unlinking: %s', fpath )
            return False

    def _rmrf( self, fpath ) :
        if os.path.isdir(fpath) :
            files = self._listdir( fpath )
            for f in files :
                childPath = os.path.join( fpath, f )
                self._rmrf( childPath )
            return self._unlink( fpath )
        elif os.path.isfile(fpath) :
            return self._unlink( fpath )
        return False

    def _validateElemList( self, elemList ) :
        for x in elemList :
            assert x.strip() == x
            assert '\\' not in x
            assert '/' not in x
            assert x not in ('.','..')

    def _parseEntryPath( self, entryPath ) :
        elemList = entryPath.split( '/' )
        if elemList and (not elemList[0]) :
            del elemList[0]
        if elemList :
            assert elemList[-1]
        self._validateElemList( elemList )
        return elemList

    def _get( self, entryPath ) :
        elemList = self._parseEntryPath( entryPath )
        fpath = os.path.join( self.configDir, *elemList )
        if os.path.isdir(fpath) :
            out = []
            for x in self._listdir(fpath) :
                childPath = '/'.join( elemList + [x] )
                out.append( childPath )
            return out
        elif os.path.isfile(fpath) :
            data = None
            try :
                f = file( fpath, 'rb' )
                data = f.read()
                f.close()
            except (OSError,IOError) :
                logger.exception( 'error reading file: %s', fpath )
            return data
        return None

    def _set( self, entryPath, data ) :
        elemList = self._parseEntryPath( entryPath )
        assert elemList
        dpath = self.configDir
        for d in elemList[:-1] :
            dpath = os.path.join( dpath, d )
            self._mkdir( dpath )
        fpath = os.path.join( dpath, elemList[-1] )
        try :
            f = file( fpath, 'wb' )
            f.write( data )
            f.close()
            return True
        except (OSError,IOError) :
            logger.exception( 'error writing file: %s', fpath )
            return False

    def remove( self, entryPath ) :
        elemList = self._parseEntryPath( entryPath )
        fpath = os.path.join( self.configDir, *elemList )
        return self._rmrf( fpath )

    def listEntries( self, entryPath ) :
        entries = self._get( entryPath )
        t = type(entries)
        if t is StringType :
            logger.warning( 'argument to listEntries is a file: %s', entryPath )
            return []
        if entries is None :
            return []
        assert t is ListType
        return entries

    def getData( self, entryPath, default=None ) :
        data = self._get( entryPath )
        if data is None : return default
        if type(data) is ListType :
            logger.warning( 'argument to getData is a directory: %s', entryPath )
            return default
        return data

    def setData( self, entryPath, value ) :
        return self._set( entryPath, value )

    def getInt( self, entryPath, default=None ) :
        data = self.getData( entryPath )
        if data is None : return default
        try :
            return int(data.strip())
        except ValueError :
            return default

    def setInt( self, entryPath, value ) :
        return self._set( entryPath, str(value) )

    def getString( self, entryPath, default=None ) :
        data = self.getData( entryPath )
        if data is None : return default
        data = data.strip()
        if len(data) < 2 : return default
        if not (data[0] == data[-1] == '"') : return default
        data = data[1:-1]
        try :
            out = []
            i = 0
            while i < len(data) :
                c = data[i]
                if c == '\\' :
                    out.append( data[i+1] )
                    i += 2
                else :
                    out.append( c )
                    i += 1
            return ''.join( out )
        except IndexError :
            return default

    def setString( self, entryPath, value ) :
        out = ['"']
        for x in value :
            if x in '\\"' :
                out.append( '\\' )
            out.append( x )
        out.append( '"' )
        return self._set( entryPath, ''.join(out) )

class LocalSettings( BaseSettings ) :
    def __init__( self, name ) :
        configDir = getConfigDir( name )
        BaseSettings.__init__( self, configDir )
        self._mkdir( configDir )

class AppSettings( BaseSettings ) :
    def __init__( self ) :
        BaseSettings.__init__( self, getAppDir() )
