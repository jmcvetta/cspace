import sys, os
try :
    import modulefinder
    import win32com
    for p in win32com.__path__[1:]:
        modulefinder.AddPackagePath( 'win32com', p )
    for extra in ['win32com.shell'] :
        __import__( extra )
        m = sys.modules[extra]
        for p in m.__path__[1:] :
            modulefinder.AddPackagePath( extra, p )
except ImportError :
    pass

sys.path.insert( 0, os.path.join(os.path.split(__file__)[0],'..') )

from distutils.core import setup
import py2exe

opts = {
    'py2exe' : {
        'includes' : 'sip',
        'excludes' : '_ssl',
        'ignores' : 'ncrypt.digest,ncrypt.cipher,ncrypt.rand,ncrypt.rsa,ncrypt.x509,ncrypt.ssl'
    }
}

cspaceApp = {
    'script' : '../CSpace.pyw',
    'icon_resources' : [(1,'../cspace/main/ui/images/cspace.ico')]
    }

imApp = {
    'script' : '../cspaceapps/im/IM.py',
    'icon_resources' : [(1,'../cspace/main/ui/images/cspace.ico')]
    }

fileSenderApp = {
    'script' : '../cspaceapps/filetransfer/FileSender.py',
    'icon_resources' : [(1,'../cspace/main/ui/images/cspace.ico')]
    }

fileReceiverApp = {
    'script' : '../cspaceapps/filetransfer/FileReceiver.py',
    'icon_resources' : [(1,'../cspace/main/ui/images/cspace.ico')]
    }


vncClientApp = {
    'script' : '../cspaceapps/vnc/VNCClient.py',
    'icon_resources' : [(1,'../cspace/main/ui/images/cspace.ico')]
    }

vncServerApp = {
    'script' : '../cspaceapps/vnc/VNCServer.py',
    'icon_resources' : [(1,'../cspace/main/ui/images/cspace.ico')]
    }

apps = [cspaceApp]
apps.extend( [imApp] )
apps.extend( [fileSenderApp,fileReceiverApp] )
apps.extend( [vncClientApp,vncServerApp] )
setup(
        options=opts,
        windows=apps
        )
