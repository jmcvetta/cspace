#!/usr/bin/python
import os, sys
#from cspace.network import localip
#localip.USE_LOCALHOST = True
#if len(sys.argv) < 2 :
#    sys.argv.append( '127.0.0.1:10001' )
from cspace.main.app import main

def _setupPythonPath() :
    pwd = os.path.dirname( os.path.abspath(__file__) )
    sys.path.append( pwd )
    # sys.path doesn't propagate to subprocesses (applets)
    if os.environ.has_key( 'PYTHONPATH' ) :
        if pwd in os.environ['PYTHONPATH'] :
            return
        if sys.platform == 'win32' :
            s = ';%s' % pwd
        else :
            s = ':%s' % pwd
        os.environ['PYTHONPATH'] = os.environ['PYTHONPATH'] + s
    else :
        os.environ['PYTHONPATH'] = pwd

if __name__ == '__main__' :
    if not hasattr(sys,'frozen') :
        _setupPythonPath()
    main()
