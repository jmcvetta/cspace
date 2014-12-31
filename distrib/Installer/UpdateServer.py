import os, sys, stat
import CalcDigest

def fileSize( f ) : return os.stat(f)[stat.ST_SIZE]

def execRemote( cmd ) :
    return os.popen( 'plink ks@210.210.1.102 %s' % cmd ).read()

def main() :
    updateBuildNumber = int(file('CSpaceUpdate-BuildNumber.txt').read().strip())
    updateFile = 'CSpaceUpdate%d.exe' % updateBuildNumber
    updateRequires = int(file('CSpaceUpdate-Requires.txt').read().strip())
    updateSize = fileSize( updateFile )
    setupBuildNumber = int(file('CSpaceSetup-BuildNumber.txt').read().strip())
    setupFile = 'CSpaceSetup%d.exe' % setupBuildNumber
    setupRequires = 0
    setupSize = fileSize( setupFile )
    latest = file('LatestVersion.txt','w')
    print>>latest, '%s:%d:%d:%d' % (updateFile,updateSize,updateBuildNumber,updateRequires)
    print>>latest, '%s:%d:%d:%d' % (setupFile,setupSize,setupBuildNumber,setupRequires)
    latest.close()
    fileList = [updateFile,setupFile,'LatestVersion.txt']
    fileList.extend( ['CalcDigest.py', 'UpdateLatest.py'] )
    localDigests = CalcDigest.digestList( fileList )
    remoteDigests = {}
    print 'Fetching server digest list...'
    data = execRemote( 'cd /var/www-cspace.in/setupfiles; python CalcDigest.py %s' % (' '.join(fileList)) )
    for line in data.split('\n') :
        line = line.strip()
        if not line : continue
        fileName,digest = line.split()
        remoteDigests[fileName] = digest

    for (fileName,digest) in localDigests :
        rd = remoteDigests.get( fileName, None )
        sendFile = False
        if rd is None :
            status = 'file not found on remote server'
            sendFile = True
        elif digest == rd :
            status = 'file same on remote server'
        else :
            status = 'file differs on remote server'
            sendFile = True
        print '%s: %s' % (fileName,status)
        if sendFile :
            remoteUpdated = True
            print 'uploading file: %s' % fileName
            os.system( 'pscp %s ks@210.210.1.102:/var/www-cspace.in/setupfiles/%s' % (fileName,fileName) )
    print 'Activating latest files'
    execRemote( 'cd /var/www-cspace.in/setupfiles; python UpdateLatest.py' )

if __name__ == '__main__' :
    main()
