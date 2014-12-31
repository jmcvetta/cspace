# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'IncomingPromptWindow.ui'
#
# Created: Mon Oct 09 13:21:19 2006
#      by: PyQt4 UI code generator 4.0.1
#
# WARNING! All changes made in this file will be lost!

import sys
from PyQt4 import QtCore, QtGui

class Ui_IncomingPromptWindow(object):
    def setupUi(self, IncomingPromptWindow):
        IncomingPromptWindow.setObjectName("IncomingPromptWindow")
        IncomingPromptWindow.resize(QtCore.QSize(QtCore.QRect(0,0,344,130).size()).expandedTo(IncomingPromptWindow.minimumSizeHint()))
        IncomingPromptWindow.setWindowIcon(QtGui.QIcon(":/images/cspace32.png"))

        self.vboxlayout = QtGui.QVBoxLayout(IncomingPromptWindow)
        self.vboxlayout.setMargin(9)
        self.vboxlayout.setSpacing(6)
        self.vboxlayout.setObjectName("vboxlayout")

        self.prompt = QtGui.QLabel(IncomingPromptWindow)

        font = QtGui.QFont(self.prompt.font())
        font.setFamily("MS Shell Dlg")
        font.setPointSize(10)
        font.setWeight(50)
        font.setItalic(False)
        font.setUnderline(False)
        font.setStrikeOut(False)
        font.setBold(False)
        self.prompt.setFont(font)
        self.prompt.setTextFormat(QtCore.Qt.RichText)
        self.prompt.setAlignment(QtCore.Qt.AlignCenter)
        self.prompt.setWordWrap(True)
        self.prompt.setObjectName("prompt")
        self.vboxlayout.addWidget(self.prompt)

        self.hboxlayout = QtGui.QHBoxLayout()
        self.hboxlayout.setMargin(0)
        self.hboxlayout.setSpacing(6)
        self.hboxlayout.setObjectName("hboxlayout")

        spacerItem = QtGui.QSpacerItem(40,20,QtGui.QSizePolicy.Expanding,QtGui.QSizePolicy.Minimum)
        self.hboxlayout.addItem(spacerItem)

        self.allowButton = QtGui.QPushButton(IncomingPromptWindow)
        self.allowButton.setObjectName("allowButton")
        self.hboxlayout.addWidget(self.allowButton)

        self.denyButton = QtGui.QPushButton(IncomingPromptWindow)
        self.denyButton.setObjectName("denyButton")
        self.hboxlayout.addWidget(self.denyButton)

        spacerItem1 = QtGui.QSpacerItem(40,20,QtGui.QSizePolicy.Expanding,QtGui.QSizePolicy.Minimum)
        self.hboxlayout.addItem(spacerItem1)
        self.vboxlayout.addLayout(self.hboxlayout)

        self.retranslateUi(IncomingPromptWindow)
        QtCore.QMetaObject.connectSlotsByName(IncomingPromptWindow)

    def retranslateUi(self, IncomingPromptWindow):
        IncomingPromptWindow.setWindowTitle(QtGui.QApplication.translate("IncomingPromptWindow", "Incoming Connection", None, QtGui.QApplication.UnicodeUTF8))
        self.prompt.setText(QtGui.QApplication.translate("IncomingPromptWindow", "<b>Prompt</b>", None, QtGui.QApplication.UnicodeUTF8))
        self.allowButton.setText(QtGui.QApplication.translate("IncomingPromptWindow", "&Allow", None, QtGui.QApplication.UnicodeUTF8))
        self.denyButton.setText(QtGui.QApplication.translate("IncomingPromptWindow", "&Deny", None, QtGui.QApplication.UnicodeUTF8))
