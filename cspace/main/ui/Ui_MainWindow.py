# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'MainWindow.ui'
#
# Created: Mon Oct 09 13:21:16 2006
#      by: PyQt4 UI code generator 4.0.1
#
# WARNING! All changes made in this file will be lost!

import sys
from PyQt4 import QtCore, QtGui

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(QtCore.QSize(QtCore.QRect(0,0,283,376).size()).expandedTo(MainWindow.minimumSizeHint()))
        MainWindow.setWindowIcon(QtGui.QIcon(":/images/cspace32.png"))
        MainWindow.setIconSize(QtCore.QSize(24,24))

        self.centralwidget = QtGui.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")

        self.vboxlayout = QtGui.QVBoxLayout(self.centralwidget)
        self.vboxlayout.setMargin(0)
        self.vboxlayout.setSpacing(0)
        self.vboxlayout.setObjectName("vboxlayout")

        self.stack = QtGui.QStackedWidget(self.centralwidget)
        self.stack.setObjectName("stack")

        self.contactsPage = QtGui.QWidget()
        self.contactsPage.setObjectName("contactsPage")

        self.vboxlayout1 = QtGui.QVBoxLayout(self.contactsPage)
        self.vboxlayout1.setMargin(0)
        self.vboxlayout1.setSpacing(0)
        self.vboxlayout1.setObjectName("vboxlayout1")

        self.contacts = QtGui.QListWidget(self.contactsPage)
        self.contacts.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.contacts.setIconSize(QtCore.QSize(24,24))
        self.contacts.setResizeMode(QtGui.QListView.Adjust)
        self.contacts.setObjectName("contacts")
        self.vboxlayout1.addWidget(self.contacts)
        self.stack.addWidget(self.contactsPage)

        self.offlinePage = QtGui.QWidget()
        self.offlinePage.setObjectName("offlinePage")

        self.vboxlayout2 = QtGui.QVBoxLayout(self.offlinePage)
        self.vboxlayout2.setMargin(0)
        self.vboxlayout2.setSpacing(0)
        self.vboxlayout2.setObjectName("vboxlayout2")

        self.hboxlayout = QtGui.QHBoxLayout()
        self.hboxlayout.setMargin(0)
        self.hboxlayout.setSpacing(6)
        self.hboxlayout.setObjectName("hboxlayout")

        spacerItem = QtGui.QSpacerItem(40,20,QtGui.QSizePolicy.Expanding,QtGui.QSizePolicy.Minimum)
        self.hboxlayout.addItem(spacerItem)

        self.goOnlineButton = QtGui.QPushButton(self.offlinePage)
        self.goOnlineButton.setObjectName("goOnlineButton")
        self.hboxlayout.addWidget(self.goOnlineButton)

        spacerItem1 = QtGui.QSpacerItem(40,20,QtGui.QSizePolicy.Expanding,QtGui.QSizePolicy.Minimum)
        self.hboxlayout.addItem(spacerItem1)
        self.vboxlayout2.addLayout(self.hboxlayout)

        self.hboxlayout1 = QtGui.QHBoxLayout()
        self.hboxlayout1.setMargin(0)
        self.hboxlayout1.setSpacing(6)
        self.hboxlayout1.setObjectName("hboxlayout1")

        spacerItem2 = QtGui.QSpacerItem(40,20,QtGui.QSizePolicy.Expanding,QtGui.QSizePolicy.Minimum)
        self.hboxlayout1.addItem(spacerItem2)

        self.createKeyButton = QtGui.QPushButton(self.offlinePage)
        self.createKeyButton.setObjectName("createKeyButton")
        self.hboxlayout1.addWidget(self.createKeyButton)

        spacerItem3 = QtGui.QSpacerItem(40,20,QtGui.QSizePolicy.Expanding,QtGui.QSizePolicy.Minimum)
        self.hboxlayout1.addItem(spacerItem3)
        self.vboxlayout2.addLayout(self.hboxlayout1)
        self.stack.addWidget(self.offlinePage)

        self.offlineNoUsersPage = QtGui.QWidget()
        self.offlineNoUsersPage.setObjectName("offlineNoUsersPage")

        self.vboxlayout3 = QtGui.QVBoxLayout(self.offlineNoUsersPage)
        self.vboxlayout3.setMargin(0)
        self.vboxlayout3.setSpacing(0)
        self.vboxlayout3.setObjectName("vboxlayout3")

        self.hboxlayout2 = QtGui.QHBoxLayout()
        self.hboxlayout2.setMargin(0)
        self.hboxlayout2.setSpacing(0)
        self.hboxlayout2.setObjectName("hboxlayout2")

        spacerItem4 = QtGui.QSpacerItem(40,20,QtGui.QSizePolicy.Expanding,QtGui.QSizePolicy.Minimum)
        self.hboxlayout2.addItem(spacerItem4)

        self.createKeyButton1 = QtGui.QPushButton(self.offlineNoUsersPage)
        self.createKeyButton1.setObjectName("createKeyButton1")
        self.hboxlayout2.addWidget(self.createKeyButton1)

        spacerItem5 = QtGui.QSpacerItem(40,20,QtGui.QSizePolicy.Expanding,QtGui.QSizePolicy.Minimum)
        self.hboxlayout2.addItem(spacerItem5)
        self.vboxlayout3.addLayout(self.hboxlayout2)
        self.stack.addWidget(self.offlineNoUsersPage)

        self.connectingPage = QtGui.QWidget()
        self.connectingPage.setObjectName("connectingPage")

        self.vboxlayout4 = QtGui.QVBoxLayout(self.connectingPage)
        self.vboxlayout4.setMargin(9)
        self.vboxlayout4.setSpacing(6)
        self.vboxlayout4.setObjectName("vboxlayout4")

        spacerItem6 = QtGui.QSpacerItem(20,40,QtGui.QSizePolicy.Minimum,QtGui.QSizePolicy.Expanding)
        self.vboxlayout4.addItem(spacerItem6)

        self.hboxlayout3 = QtGui.QHBoxLayout()
        self.hboxlayout3.setMargin(0)
        self.hboxlayout3.setSpacing(6)
        self.hboxlayout3.setObjectName("hboxlayout3")

        spacerItem7 = QtGui.QSpacerItem(40,20,QtGui.QSizePolicy.Expanding,QtGui.QSizePolicy.Minimum)
        self.hboxlayout3.addItem(spacerItem7)

        self.vboxlayout5 = QtGui.QVBoxLayout()
        self.vboxlayout5.setMargin(0)
        self.vboxlayout5.setSpacing(6)
        self.vboxlayout5.setObjectName("vboxlayout5")

        self.connectStatus = QtGui.QLabel(self.connectingPage)
        self.connectStatus.setAlignment(QtCore.Qt.AlignCenter)
        self.connectStatus.setObjectName("connectStatus")
        self.vboxlayout5.addWidget(self.connectStatus)

        self.connectCancelButton = QtGui.QPushButton(self.connectingPage)
        self.connectCancelButton.setObjectName("connectCancelButton")
        self.vboxlayout5.addWidget(self.connectCancelButton)
        self.hboxlayout3.addLayout(self.vboxlayout5)

        spacerItem8 = QtGui.QSpacerItem(40,20,QtGui.QSizePolicy.Expanding,QtGui.QSizePolicy.Minimum)
        self.hboxlayout3.addItem(spacerItem8)
        self.vboxlayout4.addLayout(self.hboxlayout3)

        spacerItem9 = QtGui.QSpacerItem(20,40,QtGui.QSizePolicy.Minimum,QtGui.QSizePolicy.Expanding)
        self.vboxlayout4.addItem(spacerItem9)
        self.stack.addWidget(self.connectingPage)
        self.vboxlayout.addWidget(self.stack)
        MainWindow.setCentralWidget(self.centralwidget)

        self.menubar = QtGui.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0,0,283,21))
        self.menubar.setObjectName("menubar")

        self.menu_Help = QtGui.QMenu(self.menubar)
        self.menu_Help.setObjectName("menu_Help")

        self.menuC_ontacts = QtGui.QMenu(self.menubar)
        self.menuC_ontacts.setObjectName("menuC_ontacts")

        self.menu_CSpace = QtGui.QMenu(self.menubar)
        self.menu_CSpace.setObjectName("menu_CSpace")

        self.menuO_ptions = QtGui.QMenu(self.menubar)
        self.menuO_ptions.setObjectName("menuO_ptions")
        MainWindow.setMenuBar(self.menubar)

        self.statusbar = QtGui.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.toolBar = QtGui.QToolBar(MainWindow)
        self.toolBar.setOrientation(QtCore.Qt.Horizontal)
        self.toolBar.setIconSize(QtCore.QSize(32,32))
        self.toolBar.setObjectName("toolBar")
        MainWindow.addToolBar(self.toolBar)

        self.actionCreateKey = QtGui.QAction(MainWindow)
        self.actionCreateKey.setIcon(QtGui.QIcon(":/images/register32.png"))
        self.actionCreateKey.setObjectName("actionCreateKey")

        self.actionGoOnline = QtGui.QAction(MainWindow)
        self.actionGoOnline.setIcon(QtGui.QIcon(":/images/connect32.png"))
        self.actionGoOnline.setObjectName("actionGoOnline")

        self.actionGoOffline = QtGui.QAction(MainWindow)
        self.actionGoOffline.setIcon(QtGui.QIcon(":/images/disconnect32.png"))
        self.actionGoOffline.setObjectName("actionGoOffline")

        self.actionExit = QtGui.QAction(MainWindow)
        self.actionExit.setIcon(QtGui.QIcon(":/images/exit32.png"))
        self.actionExit.setObjectName("actionExit")

        self.actionAddContact = QtGui.QAction(MainWindow)
        self.actionAddContact.setIcon(QtGui.QIcon(":/images/user_add32.png"))
        self.actionAddContact.setObjectName("actionAddContact")

        self.actionRefreshStatus = QtGui.QAction(MainWindow)
        self.actionRefreshStatus.setIcon(QtGui.QIcon(":/images/refresh32.png"))
        self.actionRefreshStatus.setObjectName("actionRefreshStatus")

        self.actionCheckStatus = QtGui.QAction(MainWindow)
        self.actionCheckStatus.setIcon(QtGui.QIcon(":/images/refresh32.png"))
        self.actionCheckStatus.setObjectName("actionCheckStatus")

        self.actionContactInfo = QtGui.QAction(MainWindow)
        self.actionContactInfo.setIcon(QtGui.QIcon(":/images/contact_info32.png"))
        self.actionContactInfo.setObjectName("actionContactInfo")

        self.actionRemoveContact = QtGui.QAction(MainWindow)
        self.actionRemoveContact.setIcon(QtGui.QIcon(":/images/user_remove32.png"))
        self.actionRemoveContact.setObjectName("actionRemoveContact")

        self.actionEditPermissions = QtGui.QAction(MainWindow)
        self.actionEditPermissions.setIcon(QtGui.QIcon(":/images/edit_permissions32.png"))
        self.actionEditPermissions.setObjectName("actionEditPermissions")

        self.actionAboutCSpace = QtGui.QAction(MainWindow)
        self.actionAboutCSpace.setIcon(QtGui.QIcon(":/images/cspace32.png"))
        self.actionAboutCSpace.setObjectName("actionAboutCSpace")

        self.actionKeyInfo = QtGui.QAction(MainWindow)
        self.actionKeyInfo.setIcon(QtGui.QIcon(":/images/key_info32.png"))
        self.actionKeyInfo.setObjectName("actionKeyInfo")
        self.menu_Help.addAction(self.actionAboutCSpace)
        self.menuC_ontacts.addAction(self.actionAddContact)
        self.menuC_ontacts.addAction(self.actionRefreshStatus)
        self.menu_CSpace.addAction(self.actionGoOnline)
        self.menu_CSpace.addAction(self.actionGoOffline)
        self.menu_CSpace.addAction(self.actionKeyInfo)
        self.menu_CSpace.addSeparator()
        self.menu_CSpace.addAction(self.actionCreateKey)
        self.menu_CSpace.addSeparator()
        self.menu_CSpace.addAction(self.actionExit)
        self.menuO_ptions.addAction(self.actionEditPermissions)
        self.menubar.addAction(self.menu_CSpace.menuAction())
        self.menubar.addAction(self.menuC_ontacts.menuAction())
        self.menubar.addAction(self.menuO_ptions.menuAction())
        self.menubar.addAction(self.menu_Help.menuAction())
        self.toolBar.addAction(self.actionGoOnline)
        self.toolBar.addAction(self.actionCreateKey)
        self.toolBar.addAction(self.actionGoOffline)
        self.toolBar.addAction(self.actionExit)
        self.toolBar.addSeparator()
        self.toolBar.addAction(self.actionAddContact)
        self.toolBar.addAction(self.actionRefreshStatus)

        self.retranslateUi(MainWindow)
        self.stack.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QtGui.QApplication.translate("MainWindow", "CSpace", None, QtGui.QApplication.UnicodeUTF8))
        self.contacts.clear()

        item = QtGui.QListWidgetItem(self.contacts)
        item.setText(QtGui.QApplication.translate("MainWindow", "Item 1", None, QtGui.QApplication.UnicodeUTF8))
        item.setIcon(QtGui.QIcon(":/images/user_online.png"))

        item1 = QtGui.QListWidgetItem(self.contacts)
        item1.setText(QtGui.QApplication.translate("MainWindow", "Item 2", None, QtGui.QApplication.UnicodeUTF8))
        item1.setIcon(QtGui.QIcon(":/images/user_offline.png"))

        item2 = QtGui.QListWidgetItem(self.contacts)
        item2.setText(QtGui.QApplication.translate("MainWindow", "Item 3", None, QtGui.QApplication.UnicodeUTF8))
        item2.setIcon(QtGui.QIcon(":/images/user_online.png"))

        item3 = QtGui.QListWidgetItem(self.contacts)
        item3.setText(QtGui.QApplication.translate("MainWindow", "Item 4", None, QtGui.QApplication.UnicodeUTF8))
        item3.setIcon(QtGui.QIcon(":/images/user_offline.png"))
        self.goOnlineButton.setText(QtGui.QApplication.translate("MainWindow", "Go Online...", None, QtGui.QApplication.UnicodeUTF8))
        self.createKeyButton.setText(QtGui.QApplication.translate("MainWindow", "Create Private Key...", None, QtGui.QApplication.UnicodeUTF8))
        self.createKeyButton1.setText(QtGui.QApplication.translate("MainWindow", "Create Private Key...", None, QtGui.QApplication.UnicodeUTF8))
        self.connectStatus.setText(QtGui.QApplication.translate("MainWindow", "<html><head><meta name=\"qrichtext\" content=\"1\" /></head><body style=\" white-space: pre-wrap; font-family:MS Shell Dlg; font-size:8.25pt; font-weight:400; font-style:normal; text-decoration:none;\"><p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-weight:600;\">Connect failed.</span></p><p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt; font-weight:600;\">Reconnecting in 30 second(s)...</p></body></html>", None, QtGui.QApplication.UnicodeUTF8))
        self.connectCancelButton.setText(QtGui.QApplication.translate("MainWindow", "Cancel", None, QtGui.QApplication.UnicodeUTF8))
        self.menu_Help.setTitle(QtGui.QApplication.translate("MainWindow", "&Help", None, QtGui.QApplication.UnicodeUTF8))
        self.menuC_ontacts.setTitle(QtGui.QApplication.translate("MainWindow", "C&ontacts", None, QtGui.QApplication.UnicodeUTF8))
        self.menu_CSpace.setTitle(QtGui.QApplication.translate("MainWindow", "&CSpace", None, QtGui.QApplication.UnicodeUTF8))
        self.menuO_ptions.setTitle(QtGui.QApplication.translate("MainWindow", "O&ptions", None, QtGui.QApplication.UnicodeUTF8))
        self.actionCreateKey.setText(QtGui.QApplication.translate("MainWindow", "&Create Private Key...", None, QtGui.QApplication.UnicodeUTF8))
        self.actionCreateKey.setIconText(QtGui.QApplication.translate("MainWindow", "Create Private Key", None, QtGui.QApplication.UnicodeUTF8))
        self.actionCreateKey.setToolTip(QtGui.QApplication.translate("MainWindow", "Create Private Key", None, QtGui.QApplication.UnicodeUTF8))
        self.actionGoOnline.setText(QtGui.QApplication.translate("MainWindow", "&Go Online...", None, QtGui.QApplication.UnicodeUTF8))
        self.actionGoOffline.setText(QtGui.QApplication.translate("MainWindow", "Go &Offline", None, QtGui.QApplication.UnicodeUTF8))
        self.actionExit.setText(QtGui.QApplication.translate("MainWindow", "E&xit", None, QtGui.QApplication.UnicodeUTF8))
        self.actionAddContact.setText(QtGui.QApplication.translate("MainWindow", "&Add Contact...", None, QtGui.QApplication.UnicodeUTF8))
        self.actionAddContact.setIconText(QtGui.QApplication.translate("MainWindow", "Add Contact", None, QtGui.QApplication.UnicodeUTF8))
        self.actionAddContact.setToolTip(QtGui.QApplication.translate("MainWindow", "Add Contact", None, QtGui.QApplication.UnicodeUTF8))
        self.actionRefreshStatus.setText(QtGui.QApplication.translate("MainWindow", "Refresh &Status", None, QtGui.QApplication.UnicodeUTF8))
        self.actionCheckStatus.setText(QtGui.QApplication.translate("MainWindow", "&Check Status", None, QtGui.QApplication.UnicodeUTF8))
        self.actionContactInfo.setText(QtGui.QApplication.translate("MainWindow", "Contact &Information...", None, QtGui.QApplication.UnicodeUTF8))
        self.actionRemoveContact.setText(QtGui.QApplication.translate("MainWindow", "Remove Contact", None, QtGui.QApplication.UnicodeUTF8))
        self.actionEditPermissions.setText(QtGui.QApplication.translate("MainWindow", "&Edit Permissions...", None, QtGui.QApplication.UnicodeUTF8))
        self.actionAboutCSpace.setText(QtGui.QApplication.translate("MainWindow", "&About CSpace...", None, QtGui.QApplication.UnicodeUTF8))
        self.actionKeyInfo.setText(QtGui.QApplication.translate("MainWindow", "Key Information...", None, QtGui.QApplication.UnicodeUTF8))
