# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'CreateKeyDoneDialog.ui'
#
# Created: Mon Oct 09 13:21:17 2006
#      by: PyQt4 UI code generator 4.0.1
#
# WARNING! All changes made in this file will be lost!

import sys
from PyQt4 import QtCore, QtGui

class Ui_CreateKeyDoneDialog(object):
    def setupUi(self, CreateKeyDoneDialog):
        CreateKeyDoneDialog.setObjectName("CreateKeyDoneDialog")
        CreateKeyDoneDialog.resize(QtCore.QSize(QtCore.QRect(0,0,314,172).size()).expandedTo(CreateKeyDoneDialog.minimumSizeHint()))
        CreateKeyDoneDialog.setWindowIcon(QtGui.QIcon(":/images/register32.png"))

        self.vboxlayout = QtGui.QVBoxLayout(CreateKeyDoneDialog)
        self.vboxlayout.setMargin(9)
        self.vboxlayout.setSpacing(6)
        self.vboxlayout.setObjectName("vboxlayout")

        self.label = QtGui.QLabel(CreateKeyDoneDialog)
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.label.setObjectName("label")
        self.vboxlayout.addWidget(self.label)

        self.groupBox = QtGui.QGroupBox(CreateKeyDoneDialog)
        self.groupBox.setObjectName("groupBox")

        self.vboxlayout1 = QtGui.QVBoxLayout(self.groupBox)
        self.vboxlayout1.setMargin(9)
        self.vboxlayout1.setSpacing(6)
        self.vboxlayout1.setObjectName("vboxlayout1")

        self.label_2 = QtGui.QLabel(self.groupBox)
        self.label_2.setWordWrap(True)
        self.label_2.setObjectName("label_2")
        self.vboxlayout1.addWidget(self.label_2)

        self.hboxlayout = QtGui.QHBoxLayout()
        self.hboxlayout.setMargin(0)
        self.hboxlayout.setSpacing(6)
        self.hboxlayout.setObjectName("hboxlayout")

        self.label_3 = QtGui.QLabel(self.groupBox)
        self.label_3.setObjectName("label_3")
        self.hboxlayout.addWidget(self.label_3)

        self.keyId = QtGui.QLineEdit(self.groupBox)
        self.keyId.setReadOnly(True)
        self.keyId.setObjectName("keyId")
        self.hboxlayout.addWidget(self.keyId)
        self.vboxlayout1.addLayout(self.hboxlayout)
        self.vboxlayout.addWidget(self.groupBox)

        self.hboxlayout1 = QtGui.QHBoxLayout()
        self.hboxlayout1.setMargin(0)
        self.hboxlayout1.setSpacing(6)
        self.hboxlayout1.setObjectName("hboxlayout1")

        self.rememberKey = QtGui.QCheckBox(CreateKeyDoneDialog)
        self.rememberKey.setObjectName("rememberKey")
        self.hboxlayout1.addWidget(self.rememberKey)

        spacerItem = QtGui.QSpacerItem(40,20,QtGui.QSizePolicy.Expanding,QtGui.QSizePolicy.Minimum)
        self.hboxlayout1.addItem(spacerItem)

        self.goOnlineButton = QtGui.QPushButton(CreateKeyDoneDialog)
        self.goOnlineButton.setObjectName("goOnlineButton")
        self.hboxlayout1.addWidget(self.goOnlineButton)
        self.vboxlayout.addLayout(self.hboxlayout1)

        self.retranslateUi(CreateKeyDoneDialog)
        QtCore.QMetaObject.connectSlotsByName(CreateKeyDoneDialog)

    def retranslateUi(self, CreateKeyDoneDialog):
        CreateKeyDoneDialog.setWindowTitle(QtGui.QApplication.translate("CreateKeyDoneDialog", "Private Key Created", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("CreateKeyDoneDialog", "<html><head><meta name=\"qrichtext\" content=\"1\" /></head><body style=\" white-space: pre-wrap; font-family:MS Shell Dlg 2; font-size:8.25pt; font-weight:400; font-style:normal; text-decoration:none;\"><p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt; font-weight:600;\">Your RSA Private Key has been created.</span></p></body></html>", None, QtGui.QApplication.UnicodeUTF8))
        self.groupBox.setTitle(QtGui.QApplication.translate("CreateKeyDoneDialog", "KeyID", None, QtGui.QApplication.UnicodeUTF8))
        self.label_2.setText(QtGui.QApplication.translate("CreateKeyDoneDialog", "<html><head><meta name=\"qrichtext\" content=\"1\" /></head><body style=\" white-space: pre-wrap; font-family:MS Shell Dlg 2; font-size:8.25pt; font-weight:400; font-style:normal; text-decoration:none;\"><p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt; font-weight:600;\">Please send your KeyID to your friends so that they can add you to their contact list.</span></p></body></html>", None, QtGui.QApplication.UnicodeUTF8))
        self.label_3.setText(QtGui.QApplication.translate("CreateKeyDoneDialog", "KeyID:", None, QtGui.QApplication.UnicodeUTF8))
        self.rememberKey.setText(QtGui.QApplication.translate("CreateKeyDoneDialog", "&Remember password for this key", None, QtGui.QApplication.UnicodeUTF8))
        self.goOnlineButton.setText(QtGui.QApplication.translate("CreateKeyDoneDialog", "&Go Online", None, QtGui.QApplication.UnicodeUTF8))
