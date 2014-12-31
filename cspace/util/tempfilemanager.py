import os, logging
from tempfile import mkdtemp, mkstemp

logger = logging.getLogger( 'cspace.util.tempfilemanager' )

class TempFileManager( object ) :
    def __init__( self, dirPrefix='tempfiles-' ) :
        self.tempDir = mkdtemp( '', dirPrefix )
        self.tempFiles = []

    def allocTempFile( self, suffix='.tmp', prefix='' ) :
        (fd,filePath) = mkstemp( suffix, prefix, self.tempDir )
        os.close( fd )
        self.tempFiles.append( filePath )
        return filePath

    def cleanup( self ) :
        for f in self.tempFiles :
            try :
                os.unlink( f )
            except :
                logger.exception( 'Unable to delete temp file: %s', f )
        self.tempFiles = []
        try :
            os.rmdir( self.tempDir )
        except :
            logger.exception( 'Unable to remove temp dir: %s', self.tempDir )
        self.tempDir = None
