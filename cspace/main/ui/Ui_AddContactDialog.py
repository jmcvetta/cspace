# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'AddContactDialog.ui'
#
# Created: Mon Oct 09 13:21:18 2006
#      by: PyQt4 UI code generator 4.0.1
#
# WARNING! All changes made in this file will be lost!

import sys
from PyQt4 import QtCore, QtGui

class Ui_AddContactDialog(object):
    def setupUi(self, AddContactDialog):
        AddContactDialog.setObjectName("AddContactDialog")
        AddContactDialog.resize(QtCore.QSize(QtCore.QRect(0,0,399,474).size()).expandedTo(AddContactDialog.minimumSizeHint()))
        AddContactDialog.setWindowIcon(QtGui.QIcon(":/images/user_add32.png"))

        self.vboxlayout = QtGui.QVBoxLayout(AddContactDialog)
        self.vboxlayout.setMargin(9)
        self.vboxlayout.setSpacing(6)
        self.vboxlayout.setObjectName("vboxlayout")

        self.groupBox = QtGui.QGroupBox(AddContactDialog)
        self.groupBox.setObjectName("groupBox")

        self.vboxlayout1 = QtGui.QVBoxLayout(self.groupBox)
        self.vboxlayout1.setMargin(9)
        self.vboxlayout1.setSpacing(6)
        self.vboxlayout1.setObjectName("vboxlayout1")

        self.keyIdStatus = QtGui.QLabel(self.groupBox)
        self.keyIdStatus.setObjectName("keyIdStatus")
        self.vboxlayout1.addWidget(self.keyIdStatus)

        self.hboxlayout = QtGui.QHBoxLayout()
        self.hboxlayout.setMargin(0)
        self.hboxlayout.setSpacing(6)
        self.hboxlayout.setObjectName("hboxlayout")

        self.label_2 = QtGui.QLabel(self.groupBox)
        self.label_2.setObjectName("label_2")
        self.hboxlayout.addWidget(self.label_2)

        self.keyId = QtGui.QLineEdit(self.groupBox)
        self.keyId.setObjectName("keyId")
        self.hboxlayout.addWidget(self.keyId)

        self.fetchKeyButton = QtGui.QPushButton(self.groupBox)
        self.fetchKeyButton.setAutoDefault(False)
        self.fetchKeyButton.setObjectName("fetchKeyButton")
        self.hboxlayout.addWidget(self.fetchKeyButton)
        self.vboxlayout1.addLayout(self.hboxlayout)
        self.vboxlayout.addWidget(self.groupBox)

        self.groupBox_2 = QtGui.QGroupBox(AddContactDialog)
        self.groupBox_2.setObjectName("groupBox_2")

        self.vboxlayout2 = QtGui.QVBoxLayout(self.groupBox_2)
        self.vboxlayout2.setMargin(9)
        self.vboxlayout2.setSpacing(6)
        self.vboxlayout2.setObjectName("vboxlayout2")

        self.publicKey = QtGui.QTextEdit(self.groupBox_2)

        font = QtGui.QFont(self.publicKey.font())
        font.setFamily("Courier New")
        font.setPointSize(10)
        font.setWeight(50)
        font.setItalic(False)
        font.setUnderline(False)
        font.setStrikeOut(False)
        font.setBold(False)
        self.publicKey.setFont(font)
        self.publicKey.setTabChangesFocus(True)
        self.publicKey.setLineWrapMode(QtGui.QTextEdit.NoWrap)
        self.publicKey.setAcceptRichText(False)
        self.publicKey.setObjectName("publicKey")
        self.vboxlayout2.addWidget(self.publicKey)
        self.vboxlayout.addWidget(self.groupBox_2)

        self.groupBox_3 = QtGui.QGroupBox(AddContactDialog)
        self.groupBox_3.setObjectName("groupBox_3")

        self.vboxlayout3 = QtGui.QVBoxLayout(self.groupBox_3)
        self.vboxlayout3.setMargin(9)
        self.vboxlayout3.setSpacing(6)
        self.vboxlayout3.setObjectName("vboxlayout3")

        self.label_3 = QtGui.QLabel(self.groupBox_3)
        self.label_3.setWordWrap(True)
        self.label_3.setObjectName("label_3")
        self.vboxlayout3.addWidget(self.label_3)

        self.hboxlayout1 = QtGui.QHBoxLayout()
        self.hboxlayout1.setMargin(0)
        self.hboxlayout1.setSpacing(6)
        self.hboxlayout1.setObjectName("hboxlayout1")

        self.label_4 = QtGui.QLabel(self.groupBox_3)
        self.label_4.setObjectName("label_4")
        self.hboxlayout1.addWidget(self.label_4)

        self.contactName = QtGui.QLineEdit(self.groupBox_3)
        self.contactName.setObjectName("contactName")
        self.hboxlayout1.addWidget(self.contactName)
        self.vboxlayout3.addLayout(self.hboxlayout1)
        self.vboxlayout.addWidget(self.groupBox_3)

        self.hboxlayout2 = QtGui.QHBoxLayout()
        self.hboxlayout2.setMargin(0)
        self.hboxlayout2.setSpacing(6)
        self.hboxlayout2.setObjectName("hboxlayout2")

        spacerItem = QtGui.QSpacerItem(40,20,QtGui.QSizePolicy.Expanding,QtGui.QSizePolicy.Minimum)
        self.hboxlayout2.addItem(spacerItem)

        self.addContactButton = QtGui.QPushButton(AddContactDialog)
        self.addContactButton.setAutoDefault(False)
        self.addContactButton.setObjectName("addContactButton")
        self.hboxlayout2.addWidget(self.addContactButton)

        self.cancelButton = QtGui.QPushButton(AddContactDialog)
        self.cancelButton.setAutoDefault(False)
        self.cancelButton.setObjectName("cancelButton")
        self.hboxlayout2.addWidget(self.cancelButton)
        self.vboxlayout.addLayout(self.hboxlayout2)

        self.retranslateUi(AddContactDialog)
        QtCore.QMetaObject.connectSlotsByName(AddContactDialog)

    def retranslateUi(self, AddContactDialog):
        AddContactDialog.setWindowTitle(QtGui.QApplication.translate("AddContactDialog", "Add Contact...", None, QtGui.QApplication.UnicodeUTF8))
        self.groupBox.setTitle(QtGui.QApplication.translate("AddContactDialog", "KeyID", None, QtGui.QApplication.UnicodeUTF8))
        self.keyIdStatus.setText(QtGui.QApplication.translate("AddContactDialog", "Enter the KeyID for your contact.", None, QtGui.QApplication.UnicodeUTF8))
        self.label_2.setText(QtGui.QApplication.translate("AddContactDialog", "KeyID:", None, QtGui.QApplication.UnicodeUTF8))
        self.fetchKeyButton.setText(QtGui.QApplication.translate("AddContactDialog", "&Fetch Public Key...", None, QtGui.QApplication.UnicodeUTF8))
        self.groupBox_2.setTitle(QtGui.QApplication.translate("AddContactDialog", "Public Key", None, QtGui.QApplication.UnicodeUTF8))
        self.groupBox_3.setTitle(QtGui.QApplication.translate("AddContactDialog", "Contact Name", None, QtGui.QApplication.UnicodeUTF8))
        self.label_3.setText(QtGui.QApplication.translate("AddContactDialog", "Enter a name for your contact. This name must be UNIQUE in your contact list. Only lowercase alphabets(a-z), digits(0-9) and underscore(\'_\') are allowed.", None, QtGui.QApplication.UnicodeUTF8))
        self.label_4.setText(QtGui.QApplication.translate("AddContactDialog", "Contact Name:", None, QtGui.QApplication.UnicodeUTF8))
        self.addContactButton.setText(QtGui.QApplication.translate("AddContactDialog", "&Add Contact", None, QtGui.QApplication.UnicodeUTF8))
        self.cancelButton.setText(QtGui.QApplication.translate("AddContactDialog", "&Cancel", None, QtGui.QApplication.UnicodeUTF8))
