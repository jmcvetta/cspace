# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'UpdateNotifyWindow.ui'
#
# Created: Mon Oct 09 13:21:19 2006
#      by: PyQt4 UI code generator 4.0.1
#
# WARNING! All changes made in this file will be lost!

import sys
from PyQt4 import QtCore, QtGui

class Ui_UpdateNotifyWindow(object):
    def setupUi(self, UpdateNotifyWindow):
        UpdateNotifyWindow.setObjectName("UpdateNotifyWindow")
        UpdateNotifyWindow.resize(QtCore.QSize(QtCore.QRect(0,0,364,110).size()).expandedTo(UpdateNotifyWindow.minimumSizeHint()))
        UpdateNotifyWindow.setWindowIcon(QtGui.QIcon(":/images/cspace32.png"))

        self.vboxlayout = QtGui.QVBoxLayout(UpdateNotifyWindow)
        self.vboxlayout.setMargin(9)
        self.vboxlayout.setSpacing(6)
        self.vboxlayout.setObjectName("vboxlayout")

        self.hboxlayout = QtGui.QHBoxLayout()
        self.hboxlayout.setMargin(0)
        self.hboxlayout.setSpacing(6)
        self.hboxlayout.setObjectName("hboxlayout")

        self.label = QtGui.QLabel(UpdateNotifyWindow)
        self.label.setPixmap(QtGui.QPixmap(":/images/cspace48.png"))
        self.label.setObjectName("label")
        self.hboxlayout.addWidget(self.label)

        self.label_2 = QtGui.QLabel(UpdateNotifyWindow)

        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Policy(5),QtGui.QSizePolicy.Policy(5))
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_2.sizePolicy().hasHeightForWidth())
        self.label_2.setSizePolicy(sizePolicy)
        self.label_2.setWordWrap(True)
        self.label_2.setObjectName("label_2")
        self.hboxlayout.addWidget(self.label_2)
        self.vboxlayout.addLayout(self.hboxlayout)

        self.hboxlayout1 = QtGui.QHBoxLayout()
        self.hboxlayout1.setMargin(0)
        self.hboxlayout1.setSpacing(6)
        self.hboxlayout1.setObjectName("hboxlayout1")

        spacerItem = QtGui.QSpacerItem(40,20,QtGui.QSizePolicy.Expanding,QtGui.QSizePolicy.Minimum)
        self.hboxlayout1.addItem(spacerItem)

        self.installUpdateButton = QtGui.QPushButton(UpdateNotifyWindow)
        self.installUpdateButton.setObjectName("installUpdateButton")
        self.hboxlayout1.addWidget(self.installUpdateButton)

        spacerItem1 = QtGui.QSpacerItem(40,20,QtGui.QSizePolicy.Expanding,QtGui.QSizePolicy.Minimum)
        self.hboxlayout1.addItem(spacerItem1)
        self.vboxlayout.addLayout(self.hboxlayout1)

        self.retranslateUi(UpdateNotifyWindow)
        QtCore.QMetaObject.connectSlotsByName(UpdateNotifyWindow)

    def retranslateUi(self, UpdateNotifyWindow):
        UpdateNotifyWindow.setWindowTitle(QtGui.QApplication.translate("UpdateNotifyWindow", "CSpace Update", None, QtGui.QApplication.UnicodeUTF8))
        self.label_2.setText(QtGui.QApplication.translate("UpdateNotifyWindow", "<html><head><meta name=\"qrichtext\" content=\"1\" /></head><body style=\" white-space: pre-wrap; font-family:MS Shell Dlg; font-size:8.25pt; font-weight:400; font-style:normal; text-decoration:none;\"><p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-weight:600;\">A new version of CSpace has been downloaded and is ready to install.</span><br /><span style=\" font-weight:600;\">Click the button below after closing all CSpace windows</span></p></body></html>", None, QtGui.QApplication.UnicodeUTF8))
        self.installUpdateButton.setText(QtGui.QApplication.translate("UpdateNotifyWindow", "Stop CSpace, Install Update, and Restart CSpace", None, QtGui.QApplication.UnicodeUTF8))
