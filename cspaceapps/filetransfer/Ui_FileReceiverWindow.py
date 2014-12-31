# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'FileReceiverWindow.ui'
#
# Created: Mon Oct 09 13:21:21 2006
#      by: PyQt4 UI code generator 4.0.1
#
# WARNING! All changes made in this file will be lost!

import sys
from PyQt4 import QtCore, QtGui

class Ui_FileReceiverWindow(object):
    def setupUi(self, FileReceiverWindow):
        FileReceiverWindow.setObjectName("FileReceiverWindow")
        FileReceiverWindow.resize(QtCore.QSize(QtCore.QRect(0,0,306,322).size()).expandedTo(FileReceiverWindow.minimumSizeHint()))
        FileReceiverWindow.setWindowIcon(QtGui.QIcon(":/images/cspace32.png"))

        self.vboxlayout = QtGui.QVBoxLayout(FileReceiverWindow)
        self.vboxlayout.setMargin(9)
        self.vboxlayout.setSpacing(6)
        self.vboxlayout.setObjectName("vboxlayout")

        self.status = QtGui.QLabel(FileReceiverWindow)
        self.status.setObjectName("status")
        self.vboxlayout.addWidget(self.status)

        self.fileList = QtGui.QListWidget(FileReceiverWindow)
        self.fileList.setObjectName("fileList")
        self.vboxlayout.addWidget(self.fileList)

        self.hboxlayout = QtGui.QHBoxLayout()
        self.hboxlayout.setMargin(0)
        self.hboxlayout.setSpacing(6)
        self.hboxlayout.setObjectName("hboxlayout")

        self.acceptButton = QtGui.QPushButton(FileReceiverWindow)
        self.acceptButton.setEnabled(False)
        self.acceptButton.setObjectName("acceptButton")
        self.hboxlayout.addWidget(self.acceptButton)

        self.cancelButton = QtGui.QPushButton(FileReceiverWindow)
        self.cancelButton.setObjectName("cancelButton")
        self.hboxlayout.addWidget(self.cancelButton)
        self.vboxlayout.addLayout(self.hboxlayout)

        self.retranslateUi(FileReceiverWindow)
        QtCore.QMetaObject.connectSlotsByName(FileReceiverWindow)

    def retranslateUi(self, FileReceiverWindow):
        FileReceiverWindow.setWindowTitle(QtGui.QApplication.translate("FileReceiverWindow", "Receive Files", None, QtGui.QApplication.UnicodeUTF8))
        self.status.setText(QtGui.QApplication.translate("FileReceiverWindow", "Status...", None, QtGui.QApplication.UnicodeUTF8))
        self.acceptButton.setText(QtGui.QApplication.translate("FileReceiverWindow", "&Accept", None, QtGui.QApplication.UnicodeUTF8))
        self.cancelButton.setText(QtGui.QApplication.translate("FileReceiverWindow", "&Cancel", None, QtGui.QApplication.UnicodeUTF8))
