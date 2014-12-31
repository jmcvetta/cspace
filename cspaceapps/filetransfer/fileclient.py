from nitro.async import AsyncOp
from cspace.util.rpc import RPCConnection, RPCStub
from cspaceapps.filetransfer.fileproto import validateResponse, ProtocolError

class FileClient( object ) :
    def __init__( self, rpcConn, objectName='FileServer' ) :
        self.stub = RPCStub( rpcConn, objectName )

    def _doCall( self, payload, callback ) :
        cmd = payload[0]
        def onResponse( err, result ) :
            if err < 0 :
                op.notify( err, result )
                return
            try :
                msg = validateResponse( cmd, result )
            except ProtocolError, e :
                print 'error decoding response:', e
                op.notify( -1, None )
                return
            err,result = msg
            assert err >= 0
            op.notify( err, result )
        rpcOp = self.stub.request( payload, onResponse )
        op = AsyncOp( callback, rpcOp.cancel )
        return op

    def callList( self, dirPath, callback=None ) :
        return self._doCall( ('List',dirPath), callback )

    def callGetSize( self, filePath, callback=None ) :
        return self._doCall( ('GetSize',filePath), callback )

    def callRead( self, filePath, offset, size, callback=None ) :
        return self._doCall( ('Read',filePath,offset,size), callback )

class FileFetcher( object ) :
    def __init__( self, fileClient, remotePath, localPath, callback=None ) :
        self.fileClient = fileClient
        self.remotePath = remotePath
        self.localPath = localPath
        self.out = file( localPath, 'w+b' )
        self.sizeOp = self.fileClient.callGetSize( remotePath, self._onGetSize )
        self.fileSize = -1
        self.op = AsyncOp( callback, self._doCancel )
        self.blockSize = 16384
        self.requestedSize = 0
        self.receivedSize = 0
        self.fetchOps = {}

    def getOp( self ) : return self.op

    def _doCancel( self ) :
        if self.sizeOp : self.sizeOp.cancel()
        for fop in self.fetchOps.keys() : fop.cancel()
        self.out.close()

    def _notifyError( self ) :
        self._doCancel()
        self.op.notify( -1, self.fileSize )

    def _onGetSize( self, err, size ) :
        self.sizeOp = None
        if err != 0 :
            self._notifyError()
            return
        self.fileSize = size
        self._fetchMore()

    def _fetchMore( self ) :
        while (self.requestedSize < self.fileSize) and (len(self.fetchOps) < 5) :
            self._fetchBlock()
        if self.receivedSize == self.fileSize :
            assert len(self.fetchOps) == 0
            self.out.close()
            self.op.notify( self.receivedSize, self.fileSize )
            return
        self.op.notify( self.receivedSize, self.fileSize )

    def _fetchBlock( self ) :
        size = min( self.fileSize-self.requestedSize, self.blockSize )
        assert size > 0
        offset = self.requestedSize
        def onResponse( err, data ) :
            del self.fetchOps[rpcOp]
            if err != 0 :
                self._notifyError()
                return
            if len(data) != size :
                self._notifyError()
                return
            try :
                self.out.write( data )
            except (IOError,OSError), e :
                self._notifyError()
                return
            self.receivedSize += size
            self._fetchMore()
        rpcOp = self.fileClient.callRead( self.remotePath, offset, size, onResponse )
        self.requestedSize += size
        self.fetchOps[rpcOp] = 1
