import os, sys, logging
from bisect import bisect
from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import pyqtSignature, SIGNAL, QSize
from PyQt4.QtGui import QApplication, qApp, QMessageBox, \
        QIcon, QMainWindow, QDialog, QListWidgetItem, \
        QMenu, QAction, QPixmap

try :
    from qtrayicon import TrayIcon
    HAS_TRAY = True
except ImportError :
    HAS_TRAY = False

from nitro.qt4reactor import Qt4Reactor

from cspace.util.spawn import spawnProcess
from cspace.util.eventer import Eventer
from cspace.util.delaygc import initdelaygc
from cspace.main.common import SETTINGS_VERSION, localSettings
from cspace.main.profile import listProfiles, loadProfile, \
        createProfile, saveProfileContacts
from cspace.main.session import UserSession
from cspace.main.appletserver import AppletServer
from cspace.main.autoupdater import currentBuildNumber, AutoUpdater
from cspace.main.dialogs import CreateKeyDialog, CreateKeyDoneDialog, \
        GoOnlineDialog, KeyInfoDialog, AddContactDialog, \
        ContactInfoDialog, PermissionsDialog, UpdateNotifyWindow
import cspace.main.ui.images_rc
from cspace.main.ui.Ui_MainWindow import Ui_MainWindow

CONTACT_PROBE_INTERVAL = 4*60
CONTACT_NEXT_PROBE_INTERVAL = 30
execFileAfterExit = None

class Dummy : pass

class ActionManager( object ) :
    def __init__( self, contextMenu ) :
        self.contextMenu = contextMenu
        self.nextActionId = 0
        self.actions = []
        self.defaultActionId = -1

    def registerAction( self, action, actionCallback, actionOrder ) :
        if not self.actions :
            self.contextMenu.insertSeparator( self.contextMenu.actions()[0] )
        actionId = self.nextActionId
        self.nextActionId += 1
        info = [actionOrder,action,actionId,actionCallback,-1]
        pos = bisect( self.actions, info )
        self.actions.insert( pos, info )
        actionObj = QAction( action, None )
        info[4] = actionObj
        self.contextMenu.insertAction( self.contextMenu.actions()[pos], actionObj )
        return actionId

    def setDefaultAction( self, actionId ) :
        if self.defaultActionId >= 0 : return False
        self.defaultActionId = actionId
        return True

    def unregisterAction( self, actionId ) :
        for pos,info in enumerate(self.actions) :
            if info[2] == actionId :
                self.contextMenu.removeAction( info[4] )
                del self.actions[pos]
                if not self.actions :
                    self.contextMenu.removeAction( self.contextMenu.actions()[0] )
                if self.defaultActionId == actionId :
                    self.defaultActionId = -1
                return True
        assert False

    def execAction( self, actionObj, contactName ) :
        for info in self.actions :
            if info[4] is actionObj :
                info[3]( contactName )
                return

    def execDefaultAction( self, contactName ) :
        if self.defaultActionId < 0 : return
        for info in self.actions :
            if info[2] == self.defaultActionId :
                info[3]( contactName )
                return

class Reconnector( object ) :
    def __init__( self, profile, timerCallback, reactor ) :
        self.reconnecting = False
        self.profile = profile
        self.timerCallback = timerCallback 
        self.reactor = reactor
        self.timerOp = None

    def startReconnectTimer( self, errorMsg ) :
        self.errorMsg = errorMsg
        self.reconnecting = True
        self.timeLeft = 20
        self.timerOp = self.reactor.addTimer( 1, self._onTimer )

    def shutdown( self ) :
        if self.timerOp :
            self.timerOp.cancel()
            self.timerOp = None
        self.reconnecting = False

    def _onTimer( self ) :
        self.timeLeft -= 1
        if self.timeLeft == 0 :
            self.shutdown()
        self.timerCallback()

class StatusChecker( object ) :
    def __init__( self, contactsView, session, eventer, reactor ) :
        self.contactsView = contactsView
        self.session = session
        self.reactor = reactor
        self.checkOps = {}
        self.timerOp = None
        def onRemoveContact( item, contact ) :
            self.stop( item )
        eventer.register( 'contact.remove', onRemoveContact )

    def initialize( self ) :
        obj = Dummy()
        def count() : return self.contactsView.count()
        def checking( i ) : return self.contactsView.item(i) in self.checkOps
        def pollTimer() :
            self.timerOp = self.reactor.callLater(
                    CONTACT_NEXT_PROBE_INTERVAL, onTimer )
        def checkNext() :
            if obj.i < count() :
                self.check( self.contactsView.item(obj.i) )
                pollTimer()
                return
            obj.i = -1
            self.timerOp = self.reactor.callLater(
                    CONTACT_PROBE_INTERVAL, onTimer )
        def onTimer() :
            self.timerOp = None
            if obj.i < 0 :
                obj.i = 0
                checkNext()
                return
            if (obj.i < count()) and checking(obj.i) :
                pollTimer()
                return
            obj.i += 1
            checkNext()
        obj.i = -1
        self.timerOp = self.reactor.callLater(
                CONTACT_PROBE_INTERVAL, onTimer )

    def shutdown( self ) :
        if self.timerOp :
            self.timerOp.cancel()
            self.timerOp = None
        for op in self.checkOps.values() :
            op.cancel()
        self.checkOps.clear()

    def check( self, item ) :
        if item in self.checkOps : return
        name = str( item.text() )
        contact = self.session.getProfile().getContactByName( name )
        assert contact
        def onProbe( result ) :
            del self.checkOps[item]
            if result : img = 'user_online.png'
            else : img = 'user_offline.png'
            item.setIcon( QIcon(':/images/%s'%img) )
        op = self.session.probeUserOnline( contact.publicKey, onProbe )
        item.setIcon( QIcon(':/images/user_checking.png') )
        self.checkOps[item] = op 

    def stop( self, item ) :
        op = self.checkOps.pop( item, None )
        if op is not None :
            op.cancel()
        if item in self.checkOps :
            del self.checkOps[item]

class MainWindow( QMainWindow ) :
    OFFLINE = UserSession.OFFLINE
    CONNECTING = UserSession.CONNECTING
    ONLINE = UserSession.ONLINE
    DISCONNECTING = UserSession.DISCONNECTING

    def __init__( self, seedNodes, reactor ) :
        QMainWindow.__init__( self )
        self.ui = Ui_MainWindow()
        self.ui.setupUi( self )
        self._setupIcons()
        self.seedNodes = seedNodes
        self.reactor = reactor
        self.session = UserSession( seedNodes, reactor )
        self.sm = self.session.sm
        self.ev = Eventer()
        self.profile = None
        self.baseTitle = str(self.windowTitle())
        self.exitAfterOffline = False
        self.reconnector = None
        self.keyInfoDialog = None
        self.addContactDialog = None
        self.sm.insertCallback( self._onStateChange )
        self.connect( self.ui.createKeyButton, SIGNAL('clicked()'), self.ui.actionCreateKey.trigger )
        self.connect( self.ui.createKeyButton1, SIGNAL('clicked()'), self.ui.actionCreateKey.trigger )
        self.connect( self.ui.goOnlineButton, SIGNAL('clicked()'), self.ui.actionGoOnline.trigger )
        self.ui.contacts.setWrapping( True )
        self.connect( self.ui.contacts, SIGNAL('customContextMenuRequested(const QPoint&)'),
                self._onContactsContextMenuRequested )
        self.connect( self.ui.contacts, SIGNAL('itemDoubleClicked(QListWidgetItem*)'),
                self._onContactDoubleClicked )
        self.contextMenu = QMenu()
        self.contextMenu.addAction( self.ui.actionCheckStatus )
        self.contextMenu.addAction( self.ui.actionRemoveContact )
        self.contextMenu.addAction( self.ui.actionContactInfo )
        self.connect( self.contextMenu, SIGNAL('triggered(QAction*)'), self._onContextMenuAction )
        self.actionManager = ActionManager( self.contextMenu )
        self.appletServer = AppletServer( self.session, self.actionManager, self.reactor )
        self.statusChecker = StatusChecker( self.ui.contacts, self.session, self.ev, self.reactor )
        self.contactInfoDialogs = {}
        self.trayMenu = QMenu( self )
        self.trayMenu.addAction( self.ui.actionExit )
        if HAS_TRAY :
            self.trayIcon = TrayIcon( QPixmap(':/images/cspace_offline.png'), 'CSpace', self.trayMenu, self )
            self.connect( self.trayIcon, SIGNAL('clicked(const QPoint&,int)'), self._onTrayClicked )
            self.trayIcon.show()
        else :
            self.trayIcon = None
        self.editPermissionsDialog = None
        self.autoUpdater = AutoUpdater( self.reactor )
        self.autoUpdater.setUpdateCallback( self._onUpdateDownloaded )
        self._updateUI()
        self._doCheckSettings()

    def _setupIcons( self ) :
        def makeIcon( name ) :
            icon = QIcon()
            for res in '16 22 32'.split() :
                icon.addFile( ':/images/%s%s.png' % (name,res) )
            return icon
        actionIcons = (
                'CreateKey register',
                'GoOnline connect',
                'GoOffline disconnect',
                'Exit exit',
                'AddContact user_add',
                'RefreshStatus refresh',
                'CheckStatus refresh',
                'ContactInfo contact_info',
                'RemoveContact user_remove',
                'EditPermissions edit_permissions',
                'KeyInfo key_info' )
        for s in actionIcons :
            name,icon = s.split()
            action = getattr( self.ui, 'action%s'%name )
            action.setIcon( makeIcon(icon) )

    def _updateUI( self ) :
        state = self.sm.current()
        online = (state == self.ONLINE)
        offline = (state == self.OFFLINE)
        connecting = (state == self.CONNECTING)
        disconnecting = (state == self.DISCONNECTING)
        self.ui.actionCreateKey.setEnabled( offline )
        self.ui.actionGoOnline.setEnabled( offline )
        self.ui.actionGoOffline.setEnabled( online )
        self.ui.actionKeyInfo.setEnabled( online )
        self.ui.actionExit.setEnabled( True )
        self.ui.actionAddContact.setEnabled( online )
        self.ui.actionRefreshStatus.setEnabled( online )
        self.ui.actionCheckStatus.setEnabled( online )
        self.ui.actionContactInfo.setEnabled( online )
        self.ui.actionRemoveContact.setEnabled( online )
        self.ui.actionEditPermissions.setEnabled( online )
        self.ui.actionAboutCSpace.setEnabled( True )
        if online : msg = 'Online'
        if offline : msg = 'Offline'
        if connecting : msg = 'Going Online...'
        if disconnecting : msg = 'Going Offline...'
        if not offline :
            msg = '%s - %s' % (self.profile.name,msg)
        self.setWindowTitle( ' - '.join([msg,self.baseTitle]) )
        self.ui.createKeyButton.setEnabled( offline )
        self.ui.createKeyButton1.setEnabled( offline )
        self.ui.goOnlineButton.setEnabled( offline )
        self.ui.connectCancelButton.setEnabled( connecting or disconnecting )
        if online :
            self.ui.stack.setCurrentWidget( self.ui.contactsPage )
        elif offline :
            if self.reconnector :
                assert self.reconnector.reconnecting
                self.ui.connectCancelButton.setEnabled( True )
                self.ui.stack.setCurrentWidget( self.ui.connectingPage )
                self.ui.connectStatus.setText('<b>%s<br/>Reconnecting in %d second(s)...</b>'
                        % (self.reconnector.errorMsg, self.reconnector.timeLeft) )
            elif listProfiles() :
                self.ui.stack.setCurrentWidget( self.ui.offlinePage )
            else :
                self.ui.stack.setCurrentWidget( self.ui.offlineNoUsersPage )
        elif connecting :
            self.ui.stack.setCurrentWidget( self.ui.connectingPage )
            self.ui.connectStatus.setText( '<b>Connecting...</b>' )
        elif disconnecting :
            self.ui.stack.setCurrentWidget( self.ui.connectingPage )
            self.ui.connectStatus.setText( '<b>Disconnecting...</b>' )

    def _onStateChange( self ) :
        if self.sm.previous() == self.ONLINE :
            self.statusChecker.shutdown()
            self.appletServer.clearConnections()
            for dlg in self.contactInfoDialogs.values() :
                dlg.close()
            assert not self.contactInfoDialogs
            if self.editPermissionsDialog :
                self.editPermissionsDialog.close()
            assert not self.editPermissionsDialog
            self.ui.contacts.clear()
            if self.trayIcon is not None :
                self.trayIcon.setIcon( QPixmap(':/images/cspace_offline.png') )
                self.trayIcon.setToolTip( 'CSpace' )
        if self.sm.current() == self.OFFLINE :
            self.profile = None
            if self.reconnector :
                if self.sm.previous() == self.CONNECTING :
                    msg = 'Connect failed.'
                else :
                    msg = 'Disconnected.'
                self.reconnector.startReconnectTimer( msg )
            if self.exitAfterOffline :
                self.reactor.callLater( 0, self.ui.actionExit.trigger )
        elif self.sm.current() == self.ONLINE :
            self.ui.contacts.clear()
            for contactName in self.profile.getContactNames() :
                contact = self.profile.getContactByName( contactName )
                self._addContactItem( contact )
            self.statusChecker.initialize()
            if self.trayIcon is not None :
                self.trayIcon.setIcon( QPixmap(':/images/cspace_online.png') )
                self.trayIcon.setToolTip( 'CSpace - %s' % self.profile.name )
        self._updateUI()

    def _doCheckSettings( self ) :
        st = localSettings()
        windowWidth = st.getInt( 'Settings/WindowWidth', 0 )
        windowHeight = st.getInt( 'Settings/WindowHeight', 0 )
        if (windowWidth > 0) and (windowHeight > 0) :
            windowWidth = max( windowWidth, 100 )
            windowHeight = max( windowHeight, 100 )
            self.resize( QSize(windowWidth,windowHeight).expandedTo(self.minimumSizeHint()) )
        profiles = listProfiles()
        entries = [entry for userName,keyId,entry in profiles]
        if st.getInt('Settings/RememberKey',0) :
            entry = st.getString('Settings/SavedProfile')
            password = st.getString('Settings/SavedPassword')
            if entry and password and (entry in entries) :
                profile = loadProfile( entry, password )
                if profile :
                    self._doGoOnline( profile )

    def _sortContacts( self ) :
        self.ui.contacts.sortItems()

    def _addContactItem( self, contact ) :
        contactItem = QListWidgetItem( QIcon(':/images/user_offline.png'),
                contact.name, self.ui.contacts )
        self._sortContacts()
        self.statusChecker.check( contactItem )

    def _cancelReconnect( self ) :
        if self.reconnector :
            self.reconnector.shutdown()
            self.reconnector = None
            self._updateUI()

    @pyqtSignature( '' )
    def on_connectCancelButton_clicked( self ) :
        self._cancelReconnect()
        self.exitAfterOffline = False
        self.session.shutdown()

    @pyqtSignature( '' )
    def on_actionCreateKey_triggered( self ) :
        self._cancelReconnect()
        dlg = CreateKeyDialog( self, self.reactor )
        result = dlg.exec_()
        if result == QDialog.Rejected : return
        userName = dlg.userName
        password = dlg.password
        rsaKey = dlg.rsaKey
        keyId = dlg.keyId
        profile = createProfile( rsaKey, password, userName, keyId )
        dlg = CreateKeyDoneDialog( self, keyId )
        result = dlg.exec_()
        if result == QDialog.Rejected : return
        st = localSettings()
        if dlg.rememberKey :
            st.setInt( 'Settings/RememberKey', 1 )
            st.setString( 'Settings/SavedProfile', profile.storeEntry )
            st.setString( 'Settings/SavedPassword', password )
        else :
            st.setInt( 'Settings/RememberKey', 0 )
            st.remove( 'Settings/SavedProfile' )
            st.remove( 'Settings/SavedPassword' )
        self._updateUI()
        self._doGoOnline( profile )

    @pyqtSignature( '' )
    def on_actionGoOnline_triggered( self ) :
        self._cancelReconnect()
        dlg = GoOnlineDialog( self )
        if not dlg.profiles :
            QMessageBox.warning( self, 'No Private Keys',
                    'No Private Keys have been created. Please create your Private Key first.' )
            self.ui.actionCreateKey.trigger()
            return
        result = dlg.exec_()
        if result == QDialog.Rejected : return
        self._doGoOnline( dlg.profile )

    def _doGoOnline( self, profile ) :
        self.profile = profile
        self.session.goOnline( self.profile )
        self.reconnector = Reconnector( self.profile,
                self._onReconnectTimer, self.reactor )

    def _onReconnectTimer( self ) :
        assert self.reconnector
        if self.reconnector.timeLeft > 0 :
            self._updateUI()
            return
        self.profile = self.reconnector.profile
        self._cancelReconnect()
        self.session.goOnline( self.profile )
        self.reconnector = Reconnector( self.profile,
                self._onReconnectTimer, self.reactor )

    @pyqtSignature( '' )
    def on_actionGoOffline_triggered( self ) :
        self._cancelReconnect()
        self.session.goOffline()

    @pyqtSignature( '' )
    def on_actionKeyInfo_triggered( self ) :
        assert self.sm.current() == self.ONLINE
        if self.keyInfoDialog :
            self.keyInfoDialog.show()
            self.keyInfoDialog.activateWindow()
            return
        def onDialogClose() :
            self.keyInfoDialog = None
            self.sm.removeCallback( callbackId )
        def onStateChange() :
            self.keyInfoDialog.close()
            assert not self.keyInfoDialog
        dlg = KeyInfoDialog( self, self.profile, onDialogClose )
        dlg.show()
        self.keyInfoDialog = dlg
        callbackId = self.sm.insertCallback( onStateChange,
                src=self.ONLINE )

    @pyqtSignature( '' )
    def on_actionExit_triggered( self ) :
        self._cancelReconnect()
        if self.sm.current() == self.ONLINE :
            self.exitAfterOffline = True
            self.session.goOffline()
        else :
            self.exitAfterOffline = False
            self.appletServer.shutdown()
            self.session.shutdown()
            if self.trayIcon is not None :
                self.trayIcon.hide()
            st = localSettings()
            st.setInt( 'Settings/WindowWidth', self.width() )
            st.setInt( 'Settings/WindowHeight', self.height() )
            qApp.exit( 0 )

    @pyqtSignature( '' )
    def on_actionAddContact_triggered( self ) :
        assert self.sm.current() == self.ONLINE
        if self.addContactDialog :
            self.addContactDialog.show()
            self.addContactDialog.activateWindow()
            return
        def onDialogClose() :
            self.addContactDialog = None
            self.sm.removeCallback( callbackId )
        def onAddContact( contact ) :
            self.profile.addContact( contact )
            self._addContactItem( contact )
            saveProfileContacts( self.profile )
        def onStateChange() :
            self.addContactDialog.close()
            assert not self.addContactDialog
        dlg = AddContactDialog( self, self.reactor, self.profile,
                onAddContact, onDialogClose )
        dlg.show()
        self.addContactDialog = dlg
        callbackId = self.sm.insertCallback( onStateChange,
                src=self.ONLINE )

    @pyqtSignature( '' )
    def on_actionRefreshStatus_triggered( self ) :
        assert self.sm.current() == self.ONLINE
        for i in range(self.ui.contacts.count()) :
            item = self.ui.contacts.item( i )
            self.statusChecker.check( item )

    def _onContactsContextMenuRequested( self, pos ) :
        item = self.ui.contacts.itemAt( pos )
        if item is None : return
        curItem = self.ui.contacts.currentItem()
        if item is not curItem : return
        self.contextMenu.popup( self.ui.contacts.mapToGlobal(pos) )

    def _onContactDoubleClicked( self, item ) :
        assert self.sm.current() == self.ONLINE
        item = self.ui.contacts.currentItem()
        if item is None : return
        self.actionManager.execDefaultAction( str(item.text()) )

    def _onContextMenuAction( self, action ) :
        assert self.sm.current() == self.ONLINE
        item = self.ui.contacts.currentItem()
        if item is None : return
        self.actionManager.execAction( action, str(item.text()) )

    @pyqtSignature( '' )
    def on_actionCheckStatus_triggered( self ) :
        assert self.sm.current() == self.ONLINE
        item = self.ui.contacts.currentItem()
        if item is None : return
        self.statusChecker.check( item )

    @pyqtSignature( '' )
    def on_actionRemoveContact_triggered( self ) :
        assert self.sm.current() == self.ONLINE
        item = self.ui.contacts.currentItem()
        if item is None : return
        contact = self.profile.getContactByName( str(item.text()) )
        self.ev.trigger( 'contact.remove', item, contact )
        self.ui.contacts.takeItem( self.ui.contacts.row(item) )
        self.profile.removeContact( contact )
        saveProfileContacts( self.profile )
        permissions = self.session.getPermissions()
        permissions.removeContact( contact.name )
        if permissions.isModified() :
            permissions.savePermissions()

    @pyqtSignature( '' )
    def on_actionContactInfo_triggered( self ) :
        assert self.sm.current() == self.ONLINE
        item = self.ui.contacts.currentItem()
        if item is None : return
        dlg = self.contactInfoDialogs.get( item )
        if dlg is None :
            contact = self.profile.getContactByName( str(item.text()) )
            # FIXME: why is obj needed?
            obj = Dummy()
            def onUpdateName( newName ) :
                oldName = contact.name
                self.profile.changeContactName( oldName, newName )
                saveProfileContacts( self.profile )
                item.setText( newName )
                self._sortContacts()
                permissions = self.session.getPermissions()
                permissions.changeContactName( oldName, newName )
                if permissions.isModified() :
                    permissions.savePermissions()
            def onClose() :
                if obj.callbackId is not None :
                    self.ev.remove( obj.callbackId )
                del self.contactInfoDialogs[item]
            def onContactRemoved( removedItem, contact ) :
                if removedItem is item :
                    dlg.close()
            dlg = ContactInfoDialog( self, contact, self.profile,
                    onUpdateName, onClose )
            self.contactInfoDialogs[item] = dlg
            obj.callbackId = self.ev.register( 'contact.remove',
                    onContactRemoved )
        dlg.show()
        dlg.activateWindow()

    @pyqtSignature( '' )
    def on_actionEditPermissions_triggered( self ) :
        assert self.sm.current() == self.ONLINE
        if self.editPermissionsDialog :
            self.editPermissionsDialog.show()
            self.editPermissionsDialog.activateWindow()
            return
        def onClose() :
            self.editPermissionsDialog = None
        dlg = PermissionsDialog( self, self.session.getPermissions(),
                onClose )
        dlg.show()
        self.editPermissionsDialog = dlg

    @pyqtSignature( '' )
    def on_actionAboutCSpace_triggered( self ) :
        buildNumber = currentBuildNumber()
        listenPortMsg = ''
        if self.sm.current() == self.ONLINE :
            listenPortMsg = 'Applet Server Port: %d\n' % \
                    self.appletServer.getListenPort()
        QMessageBox.information( self, 'About CSpace',
                'CSpace Peer-to-Peer Communication Platform\n'+
                'Build %d\n' % buildNumber +
                listenPortMsg +
                '(c) Tachyon Technologies 2006',
                QMessageBox.Ok )

    def _onTrayClicked( self, pos, button ) :
        if (self.isMinimized()) or (not self.isVisible()) :
            self.showNormal()
        self.activateWindow()

    def _onUpdateDownloaded( self, updateFileName, updateFileData ) :
        def onInstall() :
            installerFile = self.autoUpdater.saveInstaller(
                    updateFileName, updateFileData )
            global execFileAfterExit
            execFileAfterExit = installerFile
            self.ui.actionExit.trigger()
            self.notifyWindow.close()
        self.notifyWindow = UpdateNotifyWindow( self.reactor,
                onInstall )

    def closeEvent( self, ev ) :
        self.showMinimized()
        if self.trayIcon is not None :
            self.hide()
        ev.ignore()

class LogFile( object ) :
    def __init__( self, settings ) :
        configDir = settings.getConfigDir()
        logFile = os.path.join( configDir, 'CSpace.log' )
        try :
            if os.path.getsize(logFile) >= 1024*1024 :
                os.remove( logFile )
        except OSError :
            pass
        self.f = file( logFile, 'a' )

    def write( self, s ) :
        self.f.write( s )
        self.f.flush()

    def flush( self ) :
        pass

def checkSettingsVersion() :
    s = localSettings()
    if not s.listEntries('') :
        s.setInt( 'SettingsVersion', SETTINGS_VERSION )
        return True
    version = s.getInt( 'SettingsVersion', -1 )
    if version == SETTINGS_VERSION : return True
    result = QMessageBox.information( None, 'Settings Update',
            'CSpace Settings format has changed. Old settings will be removed.\n' +
            'Press OK to remove data and continue.\n' +
            'Press CANCEL to exit CSpace.\n' +
            'Remove data in %s?' % s.getConfigDir(),
            QMessageBox.Ok,
            QMessageBox.Cancel | QMessageBox.Escape )
    if result != QMessageBox.Ok : return False
    for entry in s.listEntries('') :
        result = s.remove( entry )
        if not result :
            QMessageBox.critical( None, 'Error',
                    'Unable to delete entry: %s' % entry )
            return False
    s.setInt( 'SettingsVersion', SETTINGS_VERSION )
    return True

def readAddr( arg ) :
    addr = arg.split( ':' )
    addr[1] = int(addr[1])
    addr = tuple(addr)
    return addr

def main() :
    try :
        nodeAddr = readAddr( sys.argv[1] )
    except :
        nodeAddr = ('210.210.1.102',10001)
    seedNodes = [nodeAddr]
    app = QApplication( sys.argv )
    icon = QIcon()
    for iconSize in [48,32,24,16] :
        icon.addPixmap( QPixmap(':/images/cspace%d.png'%iconSize) )
    app.setWindowIcon( icon )
    app.setQuitOnLastWindowClosed( False )
    reactor = Qt4Reactor()
    if not checkSettingsVersion() :
        return
    logFile = LogFile( localSettings() )
    sys.stdout = logFile
    sys.stderr = logFile
    logging.getLogger().addHandler( logging.StreamHandler() )
    initdelaygc( reactor )
    mainWin = MainWindow( seedNodes, reactor )
    mainWin.show()
    app.exec_()
    global execFileAfterExit
    if execFileAfterExit is not None :
        p = execFileAfterExit
        args = [p]
        startingDir = os.path.split( p )[0]
        spawnProcess( p, args, os.environ, startingDir, 0 )

if __name__ == '__main__' :
    main()
