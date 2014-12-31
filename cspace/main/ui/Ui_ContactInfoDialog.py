# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ContactInfoDialog.ui'
#
# Created: Mon Oct 09 13:21:18 2006
#      by: PyQt4 UI code generator 4.0.1
#
# WARNING! All changes made in this file will be lost!

import sys
from PyQt4 import QtCore, QtGui

class Ui_ContactInfoDialog(object):
    def setupUi(self, ContactInfoDialog):
        ContactInfoDialog.setObjectName("ContactInfoDialog")
        ContactInfoDialog.resize(QtCore.QSize(QtCore.QRect(0,0,392,363).size()).expandedTo(ContactInfoDialog.minimumSizeHint()))
        ContactInfoDialog.setWindowIcon(QtGui.QIcon(":/images/contact_info32.png"))

        self.vboxlayout = QtGui.QVBoxLayout(ContactInfoDialog)
        self.vboxlayout.setMargin(9)
        self.vboxlayout.setSpacing(6)
        self.vboxlayout.setObjectName("vboxlayout")

        self.groupBox_2 = QtGui.QGroupBox(ContactInfoDialog)
        self.groupBox_2.setObjectName("groupBox_2")

        self.hboxlayout = QtGui.QHBoxLayout(self.groupBox_2)
        self.hboxlayout.setMargin(9)
        self.hboxlayout.setSpacing(6)
        self.hboxlayout.setObjectName("hboxlayout")

        self.name = QtGui.QLineEdit(self.groupBox_2)
        self.name.setObjectName("name")
        self.hboxlayout.addWidget(self.name)

        self.updateNameButton = QtGui.QPushButton(self.groupBox_2)
        self.updateNameButton.setAutoDefault(False)
        self.updateNameButton.setObjectName("updateNameButton")
        self.hboxlayout.addWidget(self.updateNameButton)
        self.vboxlayout.addWidget(self.groupBox_2)

        self.groupBox = QtGui.QGroupBox(ContactInfoDialog)
        self.groupBox.setObjectName("groupBox")

        self.vboxlayout1 = QtGui.QVBoxLayout(self.groupBox)
        self.vboxlayout1.setMargin(9)
        self.vboxlayout1.setSpacing(6)
        self.vboxlayout1.setObjectName("vboxlayout1")

        self.publicKey = QtGui.QTextEdit(self.groupBox)

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
        self.vboxlayout1.addWidget(self.publicKey)
        self.vboxlayout.addWidget(self.groupBox)

        self.retranslateUi(ContactInfoDialog)
        QtCore.QMetaObject.connectSlotsByName(ContactInfoDialog)

    def retranslateUi(self, ContactInfoDialog):
        ContactInfoDialog.setWindowTitle(QtGui.QApplication.translate("ContactInfoDialog", "Contact Information", None, QtGui.QApplication.UnicodeUTF8))
        self.groupBox_2.setTitle(QtGui.QApplication.translate("ContactInfoDialog", "Contact Name", None, QtGui.QApplication.UnicodeUTF8))
        self.updateNameButton.setText(QtGui.QApplication.translate("ContactInfoDialog", "Update Name", None, QtGui.QApplication.UnicodeUTF8))
        self.groupBox.setTitle(QtGui.QApplication.translate("ContactInfoDialog", "RSA Public Key", None, QtGui.QApplication.UnicodeUTF8))
        self.publicKey.setHtml(QtGui.QApplication.translate("ContactInfoDialog", "<html><head><meta name=\"qrichtext\" content=\"1\" /></head><body style=\" white-space: pre-wrap; font-family:Courier New; font-size:10pt; font-weight:400; font-style:normal; text-decoration:none;\"><p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">Public Key Data...</p></body></html>", None, QtGui.QApplication.UnicodeUTF8))
