import sys, ctypes
from PyQt4 import QtGui
from nitro.async import AsyncOp

if sys.platform == 'win32' :
    def _flash( window, yes ) :
        ctypes.windll.user32.FlashWindow( int(window.winId()), yes )

    def _isForegroundWindow( window ) :
        return int(window.winId()) == ctypes.windll.user32.GetForegroundWindow()

    def _startWindowFlashing( window, reactor, callback=None ) :
        _flash( window, False )
        _flash( window, True )
        def onTimer() :
            if _isForegroundWindow(window) :
                doCancel()
                op.notify()
                return
            _flash( window, True )
        def doCancel() :
            timerOp.cancel()
            _flash( window, False )
        timerOp = reactor.addTimer( 1, onTimer )
        op = AsyncOp( callback, doCancel )
        return op 

    class FlashWindow( object ) :
        def __init__( self, reactor ) :
            self.__flashOp = None
            self.__reactor = reactor

        def flash( self ) :
            if self.__flashOp : return
            if _isForegroundWindow(self) : return
            def onFlashComplete() :
                self.__flashOp = None
            self.__flashOp = _startWindowFlashing( self,
                    self.__reactor, onFlashComplete )

        def cancelFlash( self ) :
            if self.__flashOp is not None :
                self.__flashOp.cancel()
     
elif sys.platform.startswith('linux') :
    class _XClientMessage_data( ctypes.Union ) :
        _fields_ = [('b', ctypes.c_char*20),
                    ('s', ctypes.c_short*10),
                    ('l', ctypes.c_long*5)
                ]

    class XClientMessageEvent( ctypes.Structure ) :
        _fields_ = [('type', ctypes.c_int),
                    ('serial', ctypes.c_ulong),
                    ('send_event', ctypes.c_int),
                    ('display', ctypes.c_void_p),
                    ('window', ctypes.c_ulong),
                    ('message_type', ctypes.c_ulong),
                    ('format', ctypes.c_int),
                    ('data', _XClientMessage_data)
                ]

    class XEvent( ctypes.Union ) :
        _fields_ = [('xclient', XClientMessageEvent),
                    ('padding', ctypes.c_char*96)
                ]

    ClientMessage = 33
    SubstructureRedirectmask = 1048576
    SubstructureNotifyMask = 524288

    def _isForegroundWindow( window ) :
        aWin = QtGui.QApplication.activeWindow()
        if aWin is None :
            return False
        else :
            return int(window.winId()) == aWin.winId()

    def _flash( window, yes ) :
        xdisplay = ctypes.c_void_p( int(QtGui.QX11Info.display()) )
        rootwin = QtGui.QX11Info.appRootWindow()
        winId = int(window.winId())
        demandsAttention = ctypes.cdll.X11.XInternAtom( xdisplay, "_NET_WM_STATE_DEMANDS_ATTENTION", 1 )
        wmState = ctypes.cdll.X11.XInternAtom( xdisplay, "_NET_WM_STATE", 1 )

        e = XEvent()
        e.xclient.type = ClientMessage
        e.xclient.message_type = wmState
        e.xclient.display = xdisplay
        e.xclient.window = winId
        e.xclient.format = 32
        e.xclient.data.l[1] = demandsAttention
        e.xclient.data.l[2] = 0
        e.xclient.data.l[3] = 0
        e.xclient.data.l[4] = 0

        if yes :
            e.xclient.data.l[0] = 1
        else :
            e.xclient.data.l[0] = 0
        ctypes.cdll.X11.XSendEvent( xdisplay, rootwin, 0, (SubstructureRedirectmask | SubstructureNotifyMask), ctypes.pointer(e) )

    class FlashWindow( object ) :
        def __init__( self, reactor ) :
            self.__reactor = reactor
            self.__flashing = False
            self.__timer = None

        def __stopFlash( self ) :
            _flash( self, False )
            self.__flashing = False
            self.__timer.cancel()
            self.__timer = None

        def flash( self ) :
            if self.__flashing :
                return
            _flash( self, True )
            self.__flashing = True
            def onTimer( ) :
                if _isForegroundWindow( self ) :
                    self.__stopFlash()
            self.__timer = self.__reactor.addTimer( 1, onTimer )

        def cancelFlash( self ) :
            if self.__flashing :
                self.__stopFlash()

else :
    class FlashWindow( object ) :
        def __init__( self, reactor ) :
            pass

        def flash( self ) :
            pass

        def cancelFlash( self ) :
            pass
