# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'GoOnlineDialog.ui'
#
# Created: Mon Oct 09 13:21:17 2006
#      by: PyQt4 UI code generator 4.0.1
#
# WARNING! All changes made in this file will be lost!

import sys
from PyQt4 import QtCore, QtGui

class Ui_GoOnlineDialog(object):
    def setupUi(self, GoOnlineDialog):
        GoOnlineDialog.setObjectName("GoOnlineDialog")
        GoOnlineDialog.resize(QtCore.QSize(QtCore.QRect(0,0,279,155).size()).expandedTo(GoOnlineDialog.minimumSizeHint()))
        GoOnlineDialog.setWindowIcon(QtGui.QIcon(":/images/connect32.png"))

        self.vboxlayout = QtGui.QVBoxLayout(GoOnlineDialog)
        self.vboxlayout.setMargin(9)
        self.vboxlayout.setSpacing(6)
        self.vboxlayout.setObjectName("vboxlayout")

        self.groupBox = QtGui.QGroupBox(GoOnlineDialog)
        self.groupBox.setObjectName("groupBox")

        self.vboxlayout1 = QtGui.QVBoxLayout(self.groupBox)
        self.vboxlayout1.setMargin(9)
        self.vboxlayout1.setSpacing(6)
        self.vboxlayout1.setObjectName("vboxlayout1")

        self.gridlayout = QtGui.QGridLayout()
        self.gridlayout.setMargin(0)
        self.gridlayout.setSpacing(6)
        self.gridlayout.setObjectName("gridlayout")

        self.password = QtGui.QLineEdit(self.groupBox)
        self.password.setEchoMode(QtGui.QLineEdit.Password)
        self.password.setObjectName("password")
        self.gridlayout.addWidget(self.password,1,1,1,1)

        self.label_2 = QtGui.QLabel(self.groupBox)
        self.label_2.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.label_2.setObjectName("label_2")
        self.gridlayout.addWidget(self.label_2,1,0,1,1)

        self.label = QtGui.QLabel(self.groupBox)
        self.label.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.label.setObjectName("label")
        self.gridlayout.addWidget(self.label,0,0,1,1)

        self.keys = QtGui.QComboBox(self.groupBox)
        self.keys.setObjectName("keys")
        self.gridlayout.addWidget(self.keys,0,1,1,1)
        self.vboxlayout1.addLayout(self.gridlayout)

        self.hboxlayout = QtGui.QHBoxLayout()
        self.hboxlayout.setMargin(0)
        self.hboxlayout.setSpacing(6)
        self.hboxlayout.setObjectName("hboxlayout")

        spacerItem = QtGui.QSpacerItem(40,20,QtGui.QSizePolicy.Expanding,QtGui.QSizePolicy.Minimum)
        self.hboxlayout.addItem(spacerItem)

        self.rememberKey = QtGui.QCheckBox(self.groupBox)
        self.rememberKey.setObjectName("rememberKey")
        self.hboxlayout.addWidget(self.rememberKey)

        spacerItem1 = QtGui.QSpacerItem(40,20,QtGui.QSizePolicy.Expanding,QtGui.QSizePolicy.Minimum)
        self.hboxlayout.addItem(spacerItem1)
        self.vboxlayout1.addLayout(self.hboxlayout)
        self.vboxlayout.addWidget(self.groupBox)

        self.hboxlayout1 = QtGui.QHBoxLayout()
        self.hboxlayout1.setMargin(0)
        self.hboxlayout1.setSpacing(6)
        self.hboxlayout1.setObjectName("hboxlayout1")

        self.goOnlineButton = QtGui.QPushButton(GoOnlineDialog)
        self.goOnlineButton.setDefault(True)
        self.goOnlineButton.setObjectName("goOnlineButton")
        self.hboxlayout1.addWidget(self.goOnlineButton)

        self.cancelButton = QtGui.QPushButton(GoOnlineDialog)
        self.cancelButton.setObjectName("cancelButton")
        self.hboxlayout1.addWidget(self.cancelButton)
        self.vboxlayout.addLayout(self.hboxlayout1)
        self.label_2.setBuddy(self.password)
        self.label.setBuddy(self.keys)

        self.retranslateUi(GoOnlineDialog)
        QtCore.QMetaObject.connectSlotsByName(GoOnlineDialog)
        GoOnlineDialog.setTabOrder(self.keys,self.password)
        GoOnlineDialog.setTabOrder(self.password,self.rememberKey)
        GoOnlineDialog.setTabOrder(self.rememberKey,self.goOnlineButton)
        GoOnlineDialog.setTabOrder(self.goOnlineButton,self.cancelButton)

    def retranslateUi(self, GoOnlineDialog):
        GoOnlineDialog.setWindowTitle(QtGui.QApplication.translate("GoOnlineDialog", "Go Online...", None, QtGui.QApplication.UnicodeUTF8))
        self.groupBox.setTitle(QtGui.QApplication.translate("GoOnlineDialog", "Select Key", None, QtGui.QApplication.UnicodeUTF8))
        self.label_2.setText(QtGui.QApplication.translate("GoOnlineDialog", "&Password:", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("GoOnlineDialog", "&Key:", None, QtGui.QApplication.UnicodeUTF8))
        self.rememberKey.setText(QtGui.QApplication.translate("GoOnlineDialog", "&Remember password for this key", None, QtGui.QApplication.UnicodeUTF8))
        self.goOnlineButton.setText(QtGui.QApplication.translate("GoOnlineDialog", "&Go Online", None, QtGui.QApplication.UnicodeUTF8))
        self.cancelButton.setText(QtGui.QApplication.translate("GoOnlineDialog", "&Cancel", None, QtGui.QApplication.UnicodeUTF8))
