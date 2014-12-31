# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'KeyInfoDialog.ui'
#
# Created: Mon Oct 09 13:21:17 2006
#      by: PyQt4 UI code generator 4.0.1
#
# WARNING! All changes made in this file will be lost!

import sys
from PyQt4 import QtCore, QtGui

class Ui_KeyInfoDialog(object):
    def setupUi(self, KeyInfoDialog):
        KeyInfoDialog.setObjectName("KeyInfoDialog")
        KeyInfoDialog.resize(QtCore.QSize(QtCore.QRect(0,0,425,353).size()).expandedTo(KeyInfoDialog.minimumSizeHint()))
        KeyInfoDialog.setWindowIcon(QtGui.QIcon(":/images/key_info32.png"))

        self.vboxlayout = QtGui.QVBoxLayout(KeyInfoDialog)
        self.vboxlayout.setMargin(9)
        self.vboxlayout.setSpacing(6)
        self.vboxlayout.setObjectName("vboxlayout")

        self.groupBox = QtGui.QGroupBox(KeyInfoDialog)
        self.groupBox.setObjectName("groupBox")

        self.vboxlayout1 = QtGui.QVBoxLayout(self.groupBox)
        self.vboxlayout1.setMargin(9)
        self.vboxlayout1.setSpacing(6)
        self.vboxlayout1.setObjectName("vboxlayout1")

        self.label = QtGui.QLabel(self.groupBox)
        self.label.setWordWrap(True)
        self.label.setObjectName("label")
        self.vboxlayout1.addWidget(self.label)

        self.hboxlayout = QtGui.QHBoxLayout()
        self.hboxlayout.setMargin(0)
        self.hboxlayout.setSpacing(6)
        self.hboxlayout.setObjectName("hboxlayout")

        self.label_2 = QtGui.QLabel(self.groupBox)
        self.label_2.setObjectName("label_2")
        self.hboxlayout.addWidget(self.label_2)

        self.keyId = QtGui.QLineEdit(self.groupBox)
        self.keyId.setReadOnly(True)
        self.keyId.setObjectName("keyId")
        self.hboxlayout.addWidget(self.keyId)
        self.vboxlayout1.addLayout(self.hboxlayout)
        self.vboxlayout.addWidget(self.groupBox)

        self.groupBox_2 = QtGui.QGroupBox(KeyInfoDialog)
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
        self.publicKey.setLineWrapMode(QtGui.QTextEdit.NoWrap)
        self.publicKey.setReadOnly(True)
        self.publicKey.setAcceptRichText(False)
        self.publicKey.setObjectName("publicKey")
        self.vboxlayout2.addWidget(self.publicKey)
        self.vboxlayout.addWidget(self.groupBox_2)

        self.retranslateUi(KeyInfoDialog)
        QtCore.QMetaObject.connectSlotsByName(KeyInfoDialog)

    def retranslateUi(self, KeyInfoDialog):
        KeyInfoDialog.setWindowTitle(QtGui.QApplication.translate("KeyInfoDialog", "Key Information", None, QtGui.QApplication.UnicodeUTF8))
        self.groupBox.setTitle(QtGui.QApplication.translate("KeyInfoDialog", "KeyID", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("KeyInfoDialog", "Send your KeyID to your friends so that they can add you to their contact list.", None, QtGui.QApplication.UnicodeUTF8))
        self.label_2.setText(QtGui.QApplication.translate("KeyInfoDialog", "KeyID:", None, QtGui.QApplication.UnicodeUTF8))
        self.groupBox_2.setTitle(QtGui.QApplication.translate("KeyInfoDialog", "RSA Public Key", None, QtGui.QApplication.UnicodeUTF8))
        self.publicKey.setHtml(QtGui.QApplication.translate("KeyInfoDialog", "<html><head><meta name=\"qrichtext\" content=\"1\" /></head><body style=\" white-space: pre-wrap; font-family:Courier New; font-size:10pt; font-weight:400; font-style:normal; text-decoration:none;\"><p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">Public Key Data...</p></body></html>", None, QtGui.QApplication.UnicodeUTF8))
