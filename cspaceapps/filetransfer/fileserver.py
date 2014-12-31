import os, sys, stat

from cspace.util.rpc import RPCConnection

from cspaceapps.filetransfer.fileproto import validateRequest, ProtocolError
from cspaceapps.filetransfer.fileproto import ERR_NONE, ERR_UNKNOWN

class FSError( Exception ) : pass

class BaseFS( object ) :
    def list( self, pathList ) : raise NotImplementedError
    def getSize( self, pathList ) : raise NotImplementedError
    def read( self, pathList, offset, size ) : raise NotImplementedError

class SimpleFS( BaseFS ) :
    def __init__( self, baseDir ) :
        self.baseDir = baseDir

    def list( self, pathList ) :
        try :
            theDir = os.path.join( self.baseDir, *pathList )
            entries = os.listdir( theDir )
            out = []
            for e in entries :
                if os.path.isdir(os.path.join(theDir,e)) :
                    out.append( e + '/' )
                else :
                    out.append( e )
            return out
        except OSError, e :
            raise FSError, e

    def getSize( self, pathList ) :
        try :
            theFile = os.path.join( self.baseDir, *pathList )
            statres = os.stat( theFile )
            return statres[stat.ST_SIZE]
        except OSError, e :
            raise FSError, e

    def read( self, pathList, offset, size ) :
        f = None
        try :
            theFile = os.path.join( self.baseDir, *pathList )
            f = file( theFile, 'rb' )
            f.seek( offset )
            data = f.read( size )
            f.close()
            return data
        except (OSError,IOError), e :
            if f : f.close()
            raise FSError, e

class FileServer( object ) :
    def __init__( self, fs, switchboard, objectName='FileServer' ) :
        self.fs = fs
        self.switchboard = switchboard
        self.objectName = objectName
        self.switchboard.addRequestAgent( self.objectName, self._onRequest )
        rt = {}
        rt['List'] = self._doList
        rt['GetSize'] = self._doGetSize
        rt['Read'] = self._doRead
        self.requestTable = rt

    def shutdown( self ) :
        self.switchboard.delRequestAgent( self.objectName )

    def _doList( self, args, ctx ) :
        pathList = args
        try :
            entries = self.fs.list( pathList )
            ctx.response( (ERR_NONE,entries) )
        except FSError, e :
            ctx.response( (ERR_UNKNOWN,[]) )

    def _doGetSize( self, args, ctx ) :
        pathList = args
        try :
            size = self.fs.getSize( pathList )
            ctx.response( (ERR_NONE,size) )
        except FSError, e :
            ctx.response( (ERR_UNKNOWN,0) )

    def _doRead( self, args, ctx ) :
        pathList, offset, size = args
        try :
            data = self.fs.read( pathList, offset, size )
            ctx.response( (ERR_NONE,data) )
        except FSError, e :
            ctx.response( (ERR_UNKNOWN,'') )

    def _onRequest( self, payload, ctx ) :
        try :
            cmd,args = validateRequest( payload )
        except ProtocolError, e :
            print 'error in decoding:', e
            self.close()
            return
        requestHandler = self.requestTable.get( cmd, None )
        if requestHandler is None :
            print 'unsupported rpc call: %s' % cmd
            self.close()
            return
        requestHandler( args, ctx )
