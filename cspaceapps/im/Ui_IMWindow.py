# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'IMWindow.ui'
#
# Created: Mon Oct 09 13:21:20 2006
#      by: PyQt4 UI code generator 4.0.1
#
# WARNING! All changes made in this file will be lost!

import sys
from PyQt4 import QtCore, QtGui

class Ui_IMWindow(object):
    def setupUi(self, IMWindow):
        IMWindow.setObjectName("IMWindow")
        IMWindow.resize(QtCore.QSize(QtCore.QRect(0,0,401,308).size()).expandedTo(IMWindow.minimumSizeHint()))
        IMWindow.setWindowIcon(QtGui.QIcon(":/images/cspace32.png"))

        self.vboxlayout = QtGui.QVBoxLayout(IMWindow)
        self.vboxlayout.setMargin(9)
        self.vboxlayout.setSpacing(6)
        self.vboxlayout.setObjectName("vboxlayout")

        self.chatLogView = QtGui.QTextEdit(IMWindow)

        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Policy(7),QtGui.QSizePolicy.Policy(7))
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(4)
        sizePolicy.setHeightForWidth(self.chatLogView.sizePolicy().hasHeightForWidth())
        self.chatLogView.setSizePolicy(sizePolicy)

        font = QtGui.QFont(self.chatLogView.font())
        font.setFamily("MS Shell Dlg")
        font.setPointSize(10)
        font.setWeight(50)
        font.setItalic(False)
        font.setUnderline(False)
        font.setStrikeOut(False)
        font.setBold(False)
        self.chatLogView.setFont(font)
        self.chatLogView.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.chatLogView.setReadOnly(True)
        self.chatLogView.setObjectName("chatLogView")
        self.vboxlayout.addWidget(self.chatLogView)

        self.chatInputEdit = QtGui.QTextEdit(IMWindow)

        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Policy(7),QtGui.QSizePolicy.Policy(7))
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(self.chatInputEdit.sizePolicy().hasHeightForWidth())
        self.chatInputEdit.setSizePolicy(sizePolicy)

        font = QtGui.QFont(self.chatInputEdit.font())
        font.setFamily("MS Shell Dlg")
        font.setPointSize(10)
        font.setWeight(50)
        font.setItalic(False)
        font.setUnderline(False)
        font.setStrikeOut(False)
        font.setBold(False)
        self.chatInputEdit.setFont(font)
        self.chatInputEdit.setAcceptRichText(False)
        self.chatInputEdit.setObjectName("chatInputEdit")
        self.vboxlayout.addWidget(self.chatInputEdit)

        self.statusLabel = QtGui.QLabel(IMWindow)
        self.statusLabel.setObjectName("statusLabel")
        self.vboxlayout.addWidget(self.statusLabel)

        self.retranslateUi(IMWindow)
        QtCore.QMetaObject.connectSlotsByName(IMWindow)
        IMWindow.setTabOrder(self.chatInputEdit,self.chatLogView)

    def retranslateUi(self, IMWindow):
        IMWindow.setWindowTitle(QtGui.QApplication.translate("IMWindow", "CSpace IM", None, QtGui.QApplication.UnicodeUTF8))
