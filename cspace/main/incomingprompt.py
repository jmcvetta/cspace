from PyQt4 import QtCore, QtGui
from nitro.async import AsyncOp
from cspace.util.flashwin import FlashWindow
from cspace.util.delaygc import delaygc
from cspace.main.ui.Ui_IncomingPromptWindow import Ui_IncomingPromptWindow

class IncomingPromptWindow( QtGui.QWidget, FlashWindow ) :
    def __init__( self, user, service, reactor, callback=None ) :
        QtGui.QWidget.__init__( self )
        self.ui = Ui_IncomingPromptWindow()
        self.ui.setupUi( self )
        FlashWindow.__init__( self, reactor )
        msg = 'User <b>%s</b> is accessing service <b>%s</b>.<br/>' % (user,service)
        msg += 'Allow this connection?'
        self.ui.prompt.setText( msg )
        self.connect( self.ui.allowButton, QtCore.SIGNAL('clicked()'), self._onAllow )
        self.connect( self.ui.denyButton, QtCore.SIGNAL('clicked()'), self.close )
        self.op = AsyncOp( callback, self._doCancel )
        self.show()
        self.flash()

    def getOp( self ) : return self.op

    def _onAllow( self ) :
        op = self.op
        self.op = None
        op.notify( True )
        self.close()

    def _doCancel( self ) :
        self.op = None
        self.close()

    def closeEvent( self, ev ) :
        if self.op :
            op = self.op
            self.op = None
            op.notify( False )
        self.cancelFlash()
        delaygc( self )
        QtGui.QWidget.closeEvent( self, ev )
