import urllib, StringIO
from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import pyqtSignature, Qt, SIGNAL, QString
from PyQt4.QtGui import QWidget, QDialog, QMessageBox, QTextCursor
from ncrypt.digest import DigestType, Digest
from ncrypt.rsa import RSAKey, RSAError
from nitro.async import AsyncOp
from nitro.http import HttpRequest
from cspace.util.flashwin import FlashWindow
from cspace.util.delaygc import delaygc
from cspace.main.common import isValidUserName, localSettings
from cspace.main.profile import Contact, listProfiles, loadProfile
from cspace.main.permissions import BadRuleError, BadUserInRuleError, BadServiceInRuleError
from cspace.main.ui.Ui_CreateKeyDialog import Ui_CreateKeyDialog
from cspace.main.ui.Ui_CreateKeyDoneDialog import Ui_CreateKeyDoneDialog
from cspace.main.ui.Ui_GoOnlineDialog import Ui_GoOnlineDialog
from cspace.main.ui.Ui_KeyInfoDialog import Ui_KeyInfoDialog
from cspace.main.ui.Ui_AddContactDialog import Ui_AddContactDialog
from cspace.main.ui.Ui_ContactInfoDialog import Ui_ContactInfoDialog
from cspace.main.ui.Ui_PermissionsDialog import Ui_PermissionsDialog
from cspace.main.ui.Ui_UpdateNotifyWindow import Ui_UpdateNotifyWindow

class CreateKeyDialog( QDialog ) :
    def __init__( self, parent, reactor ) :
        QDialog.__init__( self, parent )
        self.ui = Ui_CreateKeyDialog()
        self.ui.setupUi( self )
        self.reactor = reactor
        self.registerOp = None
        self.ui.stack.setCurrentWidget( self.ui.inputPage )

    def _showError( self, msg ) :
        QMessageBox.critical( self, 'Error', msg )
    
    @pyqtSignature('')
    def on_createKeyButton_clicked( self ) :
        password = unicode(self.ui.password.text()).encode('utf8')
        if not password :
            self._showError( 'Please enter a password.' )
            self.ui.password.setFocus()
            self.ui.password.selectAll()
            return
        password2 = unicode(self.ui.password2.text()).encode('utf8')
        if password != password2 :
            self._showError( 'Re-entered password does not match.' )
            self.ui.password2.setFocus()
            self.ui.password2.selectAll()
            return
        userName = unicode(self.ui.userName.text()).encode('utf8')
        if not userName :
            self._showError( 'Please enter a username.' )
            self.ui.userName.setFocus()
            self.ui.userName.selectAll()
            return
        if not isValidUserName(userName) :
            self._showError( 'Only lowercase alphabets(a-z), ' +
                    'digits(0-9), and underscore(\'_\') are allowed ' +
                    'in the username.' )
            self.ui.userName.setFocus()
            self.ui.userName.selectAll()
            return
        self.userName = userName
        self.password = password
        self._doCreateKey()

    def _doCreateKey( self ) :
        self.ui.stack.setCurrentWidget( self.ui.progressPage )
        self.ui.msgLabel.setText( 'Creating RSA Key...' )
        self.repaint()
        self.rsaKey = RSAKey()
        self.rsaKey.generate( bits=2048 )
        self._doRegisterKey()

    def _registerKey( self, callback=None ) :
        data = 'username:%s' % self.userName
        digestType = DigestType( 'SHA1' )
        digest = Digest(digestType).digest( data )
        signature = self.rsaKey.sign( digest, digestType )

        form = dict( username=self.userName,
                public_key=self.rsaKey.toDER_PublicKey(),
                signature=signature )
        postData = urllib.urlencode( form )

        request = HttpRequest( self.reactor )
        def onResponse( returnCode, data ) :
            if returnCode != 200 :
                op.notify( -1 )
                return
            try :
                keyId = int(data)
                op.notify( keyId )
            except ValueError :
                op.notify( -1 )
        httpOp = request.post( 'http://cspace.in/addkey', postData, onResponse )
        op = AsyncOp( callback, httpOp.cancel )
        return op

    def _doRegisterKey( self ) :
        self.ui.stack.setCurrentWidget( self.ui.progressPage )
        self.ui.msgLabel.setText( 'Registering Public Key...' )
        self.registerOp = self._registerKey( self._onRegister )

    def _onRegister( self, keyId ) :
        self.registerOp = None
        if keyId < 0 :
            self.ui.stack.setCurrentWidget( self.ui.errorPage )
            return
        self.keyId = str(keyId)
        self.accept()

    @pyqtSignature('')
    def on_tryAgainButton_clicked( self ) :
        self._doRegisterKey()

    def done( self, r ) :
        QDialog.done( self, r )
        self.close()

    def closeEvent( self, ev ) :
        if self.registerOp :
            self.registerOp.cancel()
            self.registerOp = None
        delaygc( self )
        QDialog.closeEvent( self, ev )

class CreateKeyDoneDialog( QDialog ) :
    def __init__( self, parent, keyId ) :
        QDialog.__init__( self, parent )
        self.ui = Ui_CreateKeyDoneDialog()
        self.ui.setupUi( self )
        self.ui.keyId.setText( keyId )
        self.ui.rememberKey.setChecked( True )

    @pyqtSignature('')
    def on_goOnlineButton_clicked( self ) :
        self.rememberKey = self.ui.rememberKey.isChecked()
        self.accept()

class GoOnlineDialog( QDialog ) :
    def __init__( self, parent ) :
        QDialog.__init__( self, parent )
        self.ui = Ui_GoOnlineDialog()
        self.ui.setupUi( self )
        self.profiles = listProfiles()
        for userName,keyId,entry in self.profiles :
            text = userName
            if keyId :
                text += ' (KeyID: %s)' % keyId
            self.ui.keys.addItem( QString(text) )
        entries = [entry for userName,keyId,entry in self.profiles]
        st = localSettings()
        if st.getInt('Settings/RememberKey',0) :
            self.ui.rememberKey.setChecked( True )
            entry = st.getString( 'Settings/SavedProfile' )
            password = st.getString( 'Settings/SavedPassword' )
            if entry and password and (entry in entries) :
                self.ui.keys.setCurrentIndex( entries.index(entry) )
                self.ui.password.setText( password )
        else :
            self.ui.rememberKey.setChecked( False )

    @pyqtSignature( '' )
    def on_goOnlineButton_clicked( self ) :
        entryIndex = self.ui.keys.currentIndex()
        if entryIndex < 0 : return
        entry = self.profiles[entryIndex][2]
        password = unicode(self.ui.password.text()).encode('utf8')
        profile = loadProfile( entry, password )
        if profile is None :
            QMessageBox.critical( self, 'Error', 'Invalid Password.' )
            self.ui.password.setFocus()
            self.ui.password.selectAll()
            return
        self.profile = profile
        st = localSettings()
        if self.ui.rememberKey.isChecked() :
            st.setInt( 'Settings/RememberKey', 1 )
            st.setString( 'Settings/SavedProfile', profile.storeEntry )
            st.setString( 'Settings/SavedPassword', password )
        else :
            st.setInt( 'Settings/RememberKey', 0 )
            st.remove( 'Settings/SavedProfile' )
            st.remove( 'Settings/SavedPassword' )
        self.accept()

    @pyqtSignature( '' )
    def on_cancelButton_clicked( self ) :
        self.reject()

class KeyInfoDialog( QDialog ) :
    def __init__( self, parent, profile, closeCallback ) :
        QDialog.__init__( self, parent )
        self.ui = Ui_KeyInfoDialog()
        self.ui.setupUi( self )
        self.ui.keyId.setText( profile.keyId )
        pemPublicKey = profile.rsaKey.toPEM_PublicKey()
        self.ui.publicKey.setPlainText( pemPublicKey )
        self.closeCallback = closeCallback

    def done( self, r ) :
        QDialog.done( self, r )
        self.close()

    def closeEvent( self, ev ) :
        self.closeCallback()
        delaygc( self )
        QDialog.closeEvent( self, ev )

class AddContactDialog( QDialog ) :
    def __init__( self, parent, reactor, profile, addContactCallback,
            closeCallback ) :
        QDialog.__init__( self, parent )
        self.ui = Ui_AddContactDialog()
        self.ui.setupUi( self )
        self.reactor = reactor
        self.profile = profile
        self.addContactCallback = addContactCallback
        self.closeCallback = closeCallback
        self.fetchOp = None
        self.fetchError = False
        self.origStatus = self.ui.keyIdStatus.text()
        self.connect( self.ui.keyId,
                SIGNAL('textChanged(const QString&)'),
                self._onKeyIdChanged )
        self.connect( self.ui.keyId, SIGNAL('returnPressed()'),
                self._onKeyIdReturn )
        self.connect( self.ui.keyId, SIGNAL('clicked()'),
                self._onFetchKeyClicked )
        self.connect( self.ui.fetchKeyButton, SIGNAL('clicked()'),
                self._onFetchKeyClicked )
        self.connect( self.ui.publicKey, SIGNAL('textChanged()'),
                self._onPublicKeyChanged )
        self.connect( self.ui.contactName,
                SIGNAL('textChanged(const QString&)'),
                self._onContactNameChanged )
        self.connect( self.ui.contactName, SIGNAL('returnPressed()'),
                self._onContactNameReturn )
        self.connect( self.ui.addContactButton, SIGNAL('clicked()'),
                self._onAddContactClicked )
        self.connect( self.ui.cancelButton, SIGNAL('clicked()'),
                self.close )
        self._updateUI()

    def _showError( self, msg ) :
        QMessageBox.critical( self, 'Error', msg )

    def _readData( self ) :
        self.keyId = unicode(self.ui.keyId.text()).encode('utf8')
        self.pemPublicKey = unicode(self.ui.publicKey.toPlainText()).encode('utf8')
        self.contactName = unicode(self.ui.contactName.text()).encode('utf8')

    def _updateUI( self ) :
        self._readData()
        if self.fetchOp :
            self.ui.keyIdStatus.setText( 'Fetching public key...' )
            self.ui.keyId.setEnabled( False )
            self.ui.fetchKeyButton.setEnabled( False )
            self.ui.publicKey.setEnabled( False )
            self.ui.contactName.setEnabled( False )
            self.ui.addContactButton.setEnabled( False )
            return
        if self.fetchError :
            self.ui.keyIdStatus.setText( 'Error fetching key. Check KeyID.' )
        else :
            self.ui.keyIdStatus.setText( self.origStatus )
        self.ui.keyId.setEnabled( True )
        self.ui.publicKey.setEnabled( True )
        self.ui.contactName.setEnabled( True )
        self.ui.fetchKeyButton.setEnabled( bool(self.keyId) )
        self.ui.addContactButton.setEnabled( bool(self.pemPublicKey)
                and bool(self.contactName) )

    def _onKeyIdChanged( self, text ) :
        self.fetchError = False
        self._updateUI()

    def _onKeyIdReturn( self ) :
        self.ui.fetchKeyButton.click()

    def _fetchKey( self, keyId, callback=None ) :
        def onFetchKey( responseCode, data ) :
            if responseCode != 200 :
                op.notify( None )
                return
            inp = StringIO.StringIO( data )
            name = inp.readline().strip()
            pemPublicKey = inp.read()
            if name and not isValidUserName(name) :
                op.notify( None )
                return
            op.notify( (name,pemPublicKey) )
        httpOp = HttpRequest( self.reactor ).get(
                'http://cspace.in/pubkey/%s' % keyId,
                onFetchKey )
        op = AsyncOp( callback, httpOp.cancel )
        return op

    def _onFetchKeyClicked( self ) :
        try :
            int(self.keyId)
        except ValueError :
            self._showError( 'Invalid KeyID' )
            self.ui.keyId.setFocus()
            self.ui.keyId.selectAll()
            return
        self.ui.publicKey.clear()
        self.ui.contactName.clear()
        self.fetchError = False
        self.fetchOp = self._fetchKey( self.keyId, self._onKeyFetched )
        self._updateUI()

    def _onKeyFetched( self, result ) :
        self.fetchOp = None
        if result is None :
            self.fetchError = True
            self._updateUI()
            self.ui.keyId.setFocus()
            self.ui.keyId.selectAll()
            return
        self.fetchError = False
        name,pemPublicKey = result
        self.ui.contactName.setText( name )
        self.ui.publicKey.setPlainText( pemPublicKey )
        self._updateUI()
        self.ui.contactName.setFocus()
        self.ui.contactName.selectAll()

    def _onPublicKeyChanged( self ) :
        self.fetchError = False
        self._updateUI()

    def _onContactNameChanged( self, text ) :
        self.fetchError = False
        self._updateUI()

    def _onContactNameReturn( self ) :
        self.ui.addContactButton.click()

    def _onAddContactClicked( self ) :
        k = RSAKey()
        try :
            k.fromPEM_PublicKey( self.pemPublicKey )
        except RSAError :
            self._showError( 'Invalid public key.' )
            self.ui.publicKey.setFocus()
            self.ui.publicKey.selectAll()
            return
        if not isValidUserName(self.contactName) :
            self._showError( 'Only lowercase alphabets(a-z), ' +
                    'digits(0-9), and underscore(\'_\') are allowed ' +
                    'in the contact name.' )
            self.ui.contactName.setFocus()
            self.ui.contactName.selectAll()
            return
        contact = self.profile.getContactByPublicKey( k )
        if contact :
            self._showError( 'This public key is already present in ' +
                    'your contact list as \'%s\'.' % contact.name )
            self.ui.publicKey.setFocus()
            self.ui.publicKey.selectAll()
            return
        contact = self.profile.getContactByName( self.contactName )
        if contact :
            self._showError( 'This name is already present in your ' +
                    'contact list.\nPlease choose a different name.' )
            self.ui.contactName.setFocus()
            self.ui.contactName.selectAll()
            return
        contact = Contact( k, self.contactName )
        self.addContactCallback( contact )
        self.accept()

    def done( self, r ) :
        QDialog.done( self, r )
        self.close()

    def closeEvent( self, ev ) :
        if self.fetchOp :
            self.fetchOp.cancel()
            self.fetchOp = None
        if self.closeCallback :
            self.closeCallback()
            self.closeCallback = None
        delaygc( self )
        QDialog.closeEvent( self, ev )

class ContactInfoDialog( QDialog ) :
    def __init__( self, parent, contact, profile,
            updateNameCallback, closeCallback ) :
        QDialog.__init__( self, parent )
        self.ui = Ui_ContactInfoDialog()
        self.ui.setupUi( self )
        self.contact = contact
        self.profile = profile
        self.updateNameCallback = updateNameCallback
        self.closeCallback = closeCallback
        self.ui.name.setText( self.contact.name )
        pemPublicKey = self.contact.publicKey.toPEM_PublicKey()
        self.ui.publicKey.setPlainText( pemPublicKey )
        self.connect( self.ui.name,
                SIGNAL('textChanged(const QString&)'),
                self._onNameChanged )
        self.connect( self.ui.name, SIGNAL('returnPressed()'),
                self._onNameReturn )
        self.connect( self.ui.updateNameButton, SIGNAL('clicked()'),
                self._onUpdateNameClicked )
        self._updateUI()

    def _showError( self, msg ) :
        QMessageBox.critical( self, 'Error', msg )

    def _updateUI( self ) :
        curName = unicode(self.ui.name.text()).encode('utf8')
        nameChanged = (curName != self.contact.name)
        self.ui.updateNameButton.setEnabled( curName != self.contact.name )

    def _onNameChanged( self, text ) :
        self._updateUI()

    def _onNameReturn( self ) :
        self.ui.updateNameButton.click()

    def _onUpdateNameClicked( self ) :
        newName = unicode(self.ui.name.text()).encode('utf8')
        assert newName != self.contact.name
        if not isValidUserName(newName) :
            self._showError( 'Only lowercase alphabets(a-z), ' +
                    'digits(0-9), and underscore(\'_\') are allowed ' +
                    'in the contact name.' )
            self.ui.name.setFocus()
            self.ui.name.selectAll()
            return
        existing = self.profile.getContactByName( newName )
        if existing :
            self._showError( 'The new name is already present in ' +
                    'your contact list.\n' +
                    'Please choose a different name.' )
            self.ui.name.setFocus()
            self.ui.name.selectAll()
            return
        self.updateNameCallback( newName )
        self._updateUI()

    def done( self, r ) :
        QDialog.done( self, r )
        self.close()

    def closeEvent( self, ev ) :
        self.closeCallback()
        delaygc( self )
        QDialog.closeEvent( self, ev )

class PermissionsDialog( QDialog ) :
    def __init__( self, parent, permissions, closeCallback ) :
        QDialog.__init__( self, parent )
        self.ui = Ui_PermissionsDialog()
        self.ui.setupUi( self )
        self.permissions = permissions
        self.closeCallback = closeCallback
        self.ui.predefinedPermissions.setPlainText( self.permissions.getPredefinedPermissions() )
        self.savedData = self.permissions.getUserPermissions()
        self.ui.permissions.setPlainText( self.savedData )
        self.ui.permissions.setToolTip( self.permissions.getHelpText() )
        self.connect( self.ui.closeButton, SIGNAL('clicked()'), self.close )

    def _updateUI( self ) :
        curData = unicode(self.ui.permissions.toPlainText()).encode( 'utf8' )
        modified = curData != self.savedData
        self.ui.applyButton.setEnabled( modified )
        closeText = modified and '&Cancel' or '&Close'
        self.ui.closeButton.setText( closeText )

    @pyqtSignature( '' )
    def on_permissions_textChanged( self ) :
        self._updateUI()

    @pyqtSignature( '' )
    def on_applyButton_clicked( self ) :
        curData = unicode(self.ui.permissions.toPlainText()).encode('utf8')
        try :
            self.permissions.setUserPermissions( curData )
            self.ui.status.setText( '<b>Permissions updated.</b>' )
            self.permissions.savePermissions()
            self.savedData = curData
            self._updateUI()
            return
        except BadUserInRuleError, ue :
            line = ue.lineNumber
            errorMsg = 'Invalid user \'%s\'' % ue.user
        except BadServiceInRuleError, se :
            line = se.lineNumber
            errorMsg = 'Invalid service \'%s\'' % se.service
        except BadRuleError, e :
            line = e.lineNumber
            errorMsg = 'Invalid rule'
        errorMsg = 'Error: %s' % errorMsg
        errorMsg = QtCore.Qt.escape( errorMsg )
        errorMsg = QString( '<font color=red><b>%1</b></font>' ).arg( errorMsg )
        self.ui.status.setText( errorMsg )
        def selectLine( line ) :
            count = 0
            start = 0
            while count+1 < line :
                start = curData.find( '\n', start )
                if start < 0 : return
                count += 1
                start += 1
            end = curData.find( '\n', start )
            if end < 0 :
                end = len(curData)
            c = self.ui.permissions.textCursor()
            c.setPosition( start, QTextCursor.MoveAnchor )
            c.setPosition( end, QTextCursor.KeepAnchor )
            self.ui.permissions.setTextCursor( c )
        selectLine( line )

    def done( self, r ) :
        QDialog.done( self, r )
        self.close()

    def closeEvent( self, ev ) :
        self.closeCallback()
        delaygc( self )
        QDialog.closeEvent( self, ev )

class UpdateNotifyWindow( QWidget, FlashWindow ) :
    def __init__( self, reactor, installCallback ) :
        QWidget.__init__( self )
        self.ui = Ui_UpdateNotifyWindow()
        self.ui.setupUi( self )
        FlashWindow.__init__( self, reactor )
        self.installCallback = installCallback
        self.show()
        self.flash()

    @pyqtSignature( '' )
    def on_installUpdateButton_clicked( self ) :
        self.installCallback()

    def closeEvent( self, ev ) :
        ev.ignore()
