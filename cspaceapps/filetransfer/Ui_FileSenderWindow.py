# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'FileSenderWindow.ui'
#
# Created: Mon Oct 09 13:21:21 2006
#      by: PyQt4 UI code generator 4.0.1
#
# WARNING! All changes made in this file will be lost!

import sys
from PyQt4 import QtCore, QtGui

class Ui_FileSenderWindow(object):
    def setupUi(self, FileSenderWindow):
        FileSenderWindow.setObjectName("FileSenderWindow")
        FileSenderWindow.resize(QtCore.QSize(QtCore.QRect(0,0,323,304).size()).expandedTo(FileSenderWindow.minimumSizeHint()))
        FileSenderWindow.setWindowIcon(QtGui.QIcon(":/images/cspace32.png"))

        self.vboxlayout = QtGui.QVBoxLayout(FileSenderWindow)
        self.vboxlayout.setMargin(9)
        self.vboxlayout.setSpacing(6)
        self.vboxlayout.setObjectName("vboxlayout")

        self.status = QtGui.QLabel(FileSenderWindow)
        self.status.setWordWrap(True)
        self.status.setObjectName("status")
        self.vboxlayout.addWidget(self.status)

        self.hboxlayout = QtGui.QHBoxLayout()
        self.hboxlayout.setMargin(0)
        self.hboxlayout.setSpacing(6)
        self.hboxlayout.setObjectName("hboxlayout")

        self.fileList = QtGui.QListWidget(FileSenderWindow)
        self.fileList.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.fileList.setObjectName("fileList")
        self.hboxlayout.addWidget(self.fileList)

        self.vboxlayout1 = QtGui.QVBoxLayout()
        self.vboxlayout1.setMargin(0)
        self.vboxlayout1.setSpacing(6)
        self.vboxlayout1.setObjectName("vboxlayout1")

        self.addFilesButton = QtGui.QPushButton(FileSenderWindow)
        self.addFilesButton.setObjectName("addFilesButton")
        self.vboxlayout1.addWidget(self.addFilesButton)

        self.removeFilesButton = QtGui.QPushButton(FileSenderWindow)
        self.removeFilesButton.setEnabled(False)
        self.removeFilesButton.setObjectName("removeFilesButton")
        self.vboxlayout1.addWidget(self.removeFilesButton)

        self.removeAllButton = QtGui.QPushButton(FileSenderWindow)
        self.removeAllButton.setEnabled(False)
        self.removeAllButton.setObjectName("removeAllButton")
        self.vboxlayout1.addWidget(self.removeAllButton)

        spacerItem = QtGui.QSpacerItem(20,40,QtGui.QSizePolicy.Minimum,QtGui.QSizePolicy.Expanding)
        self.vboxlayout1.addItem(spacerItem)

        self.sendFilesButton = QtGui.QPushButton(FileSenderWindow)
        self.sendFilesButton.setEnabled(False)
        self.sendFilesButton.setObjectName("sendFilesButton")
        self.vboxlayout1.addWidget(self.sendFilesButton)

        self.closeButton = QtGui.QPushButton(FileSenderWindow)
        self.closeButton.setObjectName("closeButton")
        self.vboxlayout1.addWidget(self.closeButton)
        self.hboxlayout.addLayout(self.vboxlayout1)
        self.vboxlayout.addLayout(self.hboxlayout)

        self.retranslateUi(FileSenderWindow)
        QtCore.QMetaObject.connectSlotsByName(FileSenderWindow)

    def retranslateUi(self, FileSenderWindow):
        FileSenderWindow.setWindowTitle(QtGui.QApplication.translate("FileSenderWindow", "Send Files", None, QtGui.QApplication.UnicodeUTF8))
        self.status.setText(QtGui.QApplication.translate("FileSenderWindow", "<b>Status...</b>", None, QtGui.QApplication.UnicodeUTF8))
        self.addFilesButton.setText(QtGui.QApplication.translate("FileSenderWindow", "&Add Files...", None, QtGui.QApplication.UnicodeUTF8))
        self.removeFilesButton.setText(QtGui.QApplication.translate("FileSenderWindow", "&Remove File(s)", None, QtGui.QApplication.UnicodeUTF8))
        self.removeAllButton.setText(QtGui.QApplication.translate("FileSenderWindow", "Remove All", None, QtGui.QApplication.UnicodeUTF8))
        self.sendFilesButton.setText(QtGui.QApplication.translate("FileSenderWindow", "&Send Files...", None, QtGui.QApplication.UnicodeUTF8))
        self.closeButton.setText(QtGui.QApplication.translate("FileSenderWindow", "&Close", None, QtGui.QApplication.UnicodeUTF8))
