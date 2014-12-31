'''
pywin32utils
PyWin32 Based Replacement for the C based CreateProcess Wrapper
'''
import sys

if sys.platform == 'win32' :
    import ctypes

    class win32_STARTUPINFO(ctypes.Structure):
        _fields_ = [('cb',ctypes.c_ulong),
                    ('lpReserved',ctypes.c_char_p),
                    ('lpDesktop',ctypes.c_char_p),
                    ('lpTitle',ctypes.c_char_p),
                    ('dwX',ctypes.c_ulong),
                    ('dwY',ctypes.c_ulong),
                    ('dwXSize',ctypes.c_ulong),
                    ('dwYSize',ctypes.c_ulong),
                    ('dwXCountChars',ctypes.c_ulong),
                    ('dwYCountChars',ctypes.c_ulong),
                    ('dwFillAttribute',ctypes.c_ulong),
                    ('dwFlags',ctypes.c_ulong),
                    ('wShowWindow',ctypes.c_ulong),
                    ('cbReserved2',ctypes.c_ulong),
                    ('lpReserved2',ctypes.c_ulong),
                    ('hStdInput',ctypes.c_void_p),
                    ('hStdOutput',ctypes.c_void_p),
                    ('hStdError',ctypes.c_void_p),
        ]

    class win32_PROCESS_INFORMATION(ctypes.Structure):
        _fields_ = [('hProcess',ctypes.c_void_p),
                    ('hThread',ctypes.c_void_p),
                    ('dwProcessId',ctypes.c_ulong),
                    ('dwThreadId',ctypes.c_ulong)
        ]

    def spawnProcess( appName, argv, env, startingDir, inheritHandles ) :
        cmdLine = []
        for arg in argv :
            if arg.find(' ') >= 0 :
                arg = '"%s"' % arg
            cmdLine.append( arg )
        cmdLine = ' '.join( cmdLine )
        environ = []
        for k,v in env.items() :
            environ.append( '%s=%s' % (k,v) )
        environ.append( '\x00' )
        environ = '\x00'.join( environ )
        startupInfo = win32_STARTUPINFO()
        processInfo = win32_PROCESS_INFORMATION()
        retval = ctypes.windll.kernel32.CreateProcessA(ctypes.c_char_p(appName),ctypes.c_char_p(cmdLine),None,None,inheritHandles,0,
        ctypes.c_char_p(environ),ctypes.c_char_p(startingDir),ctypes.pointer(startupInfo),ctypes.pointer(processInfo))
        ctypes.windll.kernel32.CloseHandle(processInfo.hProcess)
        ctypes.windll.kernel32.CloseHandle(processInfo.hThread)
        return retval
else :
    import subprocess

    def spawnProcess( appName, argv, env, startingDir, inheritHandles ) :
        p = subprocess.Popen( args=argv, executable=appName,
                close_fds=True, cwd=startingDir, env=env )
        return p.pid

__all__ = ['spawnProcess']
