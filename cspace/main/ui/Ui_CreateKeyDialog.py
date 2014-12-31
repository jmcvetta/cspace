# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'CreateKeyDialog.ui'
#
# Created: Mon Oct 09 13:21:16 2006
#      by: PyQt4 UI code generator 4.0.1
#
# WARNING! All changes made in this file will be lost!

import sys
from PyQt4 import QtCore, QtGui

class Ui_CreateKeyDialog(object):
    def setupUi(self, CreateKeyDialog):
        CreateKeyDialog.setObjectName("CreateKeyDialog")
        CreateKeyDialog.resize(QtCore.QSize(QtCore.QRect(0,0,379,305).size()).expandedTo(CreateKeyDialog.minimumSizeHint()))
        CreateKeyDialog.setWindowIcon(QtGui.QIcon(":/images/register32.png"))

        self.vboxlayout = QtGui.QVBoxLayout(CreateKeyDialog)
        self.vboxlayout.setMargin(0)
        self.vboxlayout.setSpacing(6)
        self.vboxlayout.setObjectName("vboxlayout")

        self.stack = QtGui.QStackedWidget(CreateKeyDialog)
        self.stack.setObjectName("stack")

        self.inputPage = QtGui.QWidget()
        self.inputPage.setObjectName("inputPage")

        self.vboxlayout1 = QtGui.QVBoxLayout(self.inputPage)
        self.vboxlayout1.setMargin(9)
        self.vboxlayout1.setSpacing(6)
        self.vboxlayout1.setObjectName("vboxlayout1")

        self.label = QtGui.QLabel(self.inputPage)
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.label.setObjectName("label")
        self.vboxlayout1.addWidget(self.label)

        self.groupBox = QtGui.QGroupBox(self.inputPage)
        self.groupBox.setObjectName("groupBox")

        self.gridlayout = QtGui.QGridLayout(self.groupBox)
        self.gridlayout.setMargin(9)
        self.gridlayout.setSpacing(6)
        self.gridlayout.setObjectName("gridlayout")

        self.password2 = QtGui.QLineEdit(self.groupBox)
        self.password2.setEchoMode(QtGui.QLineEdit.Password)
        self.password2.setObjectName("password2")
        self.gridlayout.addWidget(self.password2,2,1,1,1)

        self.label_4 = QtGui.QLabel(self.groupBox)
        self.label_4.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.label_4.setObjectName("label_4")
        self.gridlayout.addWidget(self.label_4,2,0,1,1)

        self.label_2 = QtGui.QLabel(self.groupBox)
        self.label_2.setWordWrap(True)
        self.label_2.setObjectName("label_2")
        self.gridlayout.addWidget(self.label_2,0,0,1,2)

        self.password = QtGui.QLineEdit(self.groupBox)
        self.password.setEchoMode(QtGui.QLineEdit.Password)
        self.password.setObjectName("password")
        self.gridlayout.addWidget(self.password,1,1,1,1)

        self.label_3 = QtGui.QLabel(self.groupBox)
        self.label_3.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.label_3.setObjectName("label_3")
        self.gridlayout.addWidget(self.label_3,1,0,1,1)
        self.vboxlayout1.addWidget(self.groupBox)

        self.groupBox_2 = QtGui.QGroupBox(self.inputPage)
        self.groupBox_2.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.groupBox_2.setObjectName("groupBox_2")

        self.gridlayout1 = QtGui.QGridLayout(self.groupBox_2)
        self.gridlayout1.setMargin(9)
        self.gridlayout1.setSpacing(6)
        self.gridlayout1.setObjectName("gridlayout1")

        self.userName = QtGui.QLineEdit(self.groupBox_2)
        self.userName.setObjectName("userName")
        self.gridlayout1.addWidget(self.userName,1,1,1,1)

        self.label_6 = QtGui.QLabel(self.groupBox_2)
        self.label_6.setObjectName("label_6")
        self.gridlayout1.addWidget(self.label_6,1,0,1,1)

        self.label_5 = QtGui.QLabel(self.groupBox_2)
        self.label_5.setWordWrap(True)
        self.label_5.setObjectName("label_5")
        self.gridlayout1.addWidget(self.label_5,0,0,1,2)
        self.vboxlayout1.addWidget(self.groupBox_2)

        self.hboxlayout = QtGui.QHBoxLayout()
        self.hboxlayout.setMargin(0)
        self.hboxlayout.setSpacing(6)
        self.hboxlayout.setObjectName("hboxlayout")

        spacerItem = QtGui.QSpacerItem(40,20,QtGui.QSizePolicy.Expanding,QtGui.QSizePolicy.Minimum)
        self.hboxlayout.addItem(spacerItem)

        self.createKeyButton = QtGui.QPushButton(self.inputPage)
        self.createKeyButton.setDefault(False)
        self.createKeyButton.setObjectName("createKeyButton")
        self.hboxlayout.addWidget(self.createKeyButton)

        spacerItem1 = QtGui.QSpacerItem(40,20,QtGui.QSizePolicy.Expanding,QtGui.QSizePolicy.Minimum)
        self.hboxlayout.addItem(spacerItem1)
        self.vboxlayout1.addLayout(self.hboxlayout)
        self.stack.addWidget(self.inputPage)

        self.progressPage = QtGui.QWidget()
        self.progressPage.setObjectName("progressPage")

        self.vboxlayout2 = QtGui.QVBoxLayout(self.progressPage)
        self.vboxlayout2.setMargin(9)
        self.vboxlayout2.setSpacing(6)
        self.vboxlayout2.setObjectName("vboxlayout2")

        self.msgLabel = QtGui.QLabel(self.progressPage)
        self.msgLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.msgLabel.setObjectName("msgLabel")
        self.vboxlayout2.addWidget(self.msgLabel)
        self.stack.addWidget(self.progressPage)

        self.errorPage = QtGui.QWidget()
        self.errorPage.setObjectName("errorPage")

        self.vboxlayout3 = QtGui.QVBoxLayout(self.errorPage)
        self.vboxlayout3.setMargin(9)
        self.vboxlayout3.setSpacing(6)
        self.vboxlayout3.setObjectName("vboxlayout3")

        self.label_11 = QtGui.QLabel(self.errorPage)
        self.label_11.setAlignment(QtCore.Qt.AlignCenter)
        self.label_11.setObjectName("label_11")
        self.vboxlayout3.addWidget(self.label_11)

        self.hboxlayout1 = QtGui.QHBoxLayout()
        self.hboxlayout1.setMargin(0)
        self.hboxlayout1.setSpacing(6)
        self.hboxlayout1.setObjectName("hboxlayout1")

        spacerItem2 = QtGui.QSpacerItem(40,20,QtGui.QSizePolicy.Expanding,QtGui.QSizePolicy.Minimum)
        self.hboxlayout1.addItem(spacerItem2)

        self.tryAgainButton = QtGui.QPushButton(self.errorPage)
        self.tryAgainButton.setObjectName("tryAgainButton")
        self.hboxlayout1.addWidget(self.tryAgainButton)

        spacerItem3 = QtGui.QSpacerItem(40,20,QtGui.QSizePolicy.Expanding,QtGui.QSizePolicy.Minimum)
        self.hboxlayout1.addItem(spacerItem3)
        self.vboxlayout3.addLayout(self.hboxlayout1)
        self.stack.addWidget(self.errorPage)
        self.vboxlayout.addWidget(self.stack)

        self.retranslateUi(CreateKeyDialog)
        self.stack.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(CreateKeyDialog)
        CreateKeyDialog.setTabOrder(self.password,self.password2)
        CreateKeyDialog.setTabOrder(self.password2,self.userName)
        CreateKeyDialog.setTabOrder(self.userName,self.createKeyButton)

    def retranslateUi(self, CreateKeyDialog):
        CreateKeyDialog.setWindowTitle(QtGui.QApplication.translate("CreateKeyDialog", "Create Private Key...", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("CreateKeyDialog", "<html><head><meta name=\"qrichtext\" content=\"1\" /></head><body style=\" white-space: pre-wrap; font-family:MS Shell Dlg 2; font-size:8.25pt; font-weight:400; font-style:normal; text-decoration:none;\"><p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt; font-weight:600;\">A 2048-bit RSA Key will created.</span></p></body></html>", None, QtGui.QApplication.UnicodeUTF8))
        self.groupBox.setTitle(QtGui.QApplication.translate("CreateKeyDialog", "Password", None, QtGui.QApplication.UnicodeUTF8))
        self.label_4.setText(QtGui.QApplication.translate("CreateKeyDialog", "Re-enter Password:", None, QtGui.QApplication.UnicodeUTF8))
        self.label_2.setText(QtGui.QApplication.translate("CreateKeyDialog", "The password will be used to encrypt your key before storing it on your hard disk.", None, QtGui.QApplication.UnicodeUTF8))
        self.label_3.setText(QtGui.QApplication.translate("CreateKeyDialog", "Password:", None, QtGui.QApplication.UnicodeUTF8))
        self.groupBox_2.setTitle(QtGui.QApplication.translate("CreateKeyDialog", "Username", None, QtGui.QApplication.UnicodeUTF8))
        self.label_6.setText(QtGui.QApplication.translate("CreateKeyDialog", "Username:", None, QtGui.QApplication.UnicodeUTF8))
        self.label_5.setText(QtGui.QApplication.translate("CreateKeyDialog", "The username you enter will be used only for display purposes, and is NOT A UNIQUE IDENTIFIER.\n"
        "Only lowercase alphabets(a-z), digits(0-9) and underscore(\'_\') can be used in your username.", None, QtGui.QApplication.UnicodeUTF8))
        self.createKeyButton.setText(QtGui.QApplication.translate("CreateKeyDialog", "&Create Key...", None, QtGui.QApplication.UnicodeUTF8))
        self.msgLabel.setText(QtGui.QApplication.translate("CreateKeyDialog", "Progress Message...", None, QtGui.QApplication.UnicodeUTF8))
        self.label_11.setText(QtGui.QApplication.translate("CreateKeyDialog", "<html><head><meta name=\"qrichtext\" content=\"1\" /></head><body style=\" white-space: pre-wrap; font-family:MS Shell Dlg 2; font-size:8.25pt; font-weight:400; font-style:normal; text-decoration:none;\"><p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt; font-weight:600; color:#ff0000;\">Unable to register your Public Key with the Key Server.</span></p><p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt; font-weight:600; color:#ff0000;\">Please check your internet connection.</p></body></html>", None, QtGui.QApplication.UnicodeUTF8))
        self.tryAgainButton.setText(QtGui.QApplication.translate("CreateKeyDialog", "Try Again...", None, QtGui.QApplication.UnicodeUTF8))
