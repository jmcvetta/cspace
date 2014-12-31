# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'PermissionsDialog.ui'
#
# Created: Mon Oct 09 13:21:19 2006
#      by: PyQt4 UI code generator 4.0.1
#
# WARNING! All changes made in this file will be lost!

import sys
from PyQt4 import QtCore, QtGui

class Ui_PermissionsDialog(object):
    def setupUi(self, PermissionsDialog):
        PermissionsDialog.setObjectName("PermissionsDialog")
        PermissionsDialog.resize(QtCore.QSize(QtCore.QRect(0,0,569,414).size()).expandedTo(PermissionsDialog.minimumSizeHint()))
        PermissionsDialog.setWindowIcon(QtGui.QIcon(":/images/edit_permissions32.png"))
        PermissionsDialog.setSizeGripEnabled(False)

        self.vboxlayout = QtGui.QVBoxLayout(PermissionsDialog)
        self.vboxlayout.setMargin(9)
        self.vboxlayout.setSpacing(6)
        self.vboxlayout.setObjectName("vboxlayout")

        self.groupBox = QtGui.QGroupBox(PermissionsDialog)
        self.groupBox.setObjectName("groupBox")

        self.vboxlayout1 = QtGui.QVBoxLayout(self.groupBox)
        self.vboxlayout1.setMargin(9)
        self.vboxlayout1.setSpacing(6)
        self.vboxlayout1.setObjectName("vboxlayout1")

        self.label = QtGui.QLabel(self.groupBox)
        self.label.setWordWrap(False)
        self.label.setObjectName("label")
        self.vboxlayout1.addWidget(self.label)

        self.predefinedPermissions = QtGui.QTextEdit(self.groupBox)

        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Policy(5),QtGui.QSizePolicy.Policy(5))
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.predefinedPermissions.sizePolicy().hasHeightForWidth())
        self.predefinedPermissions.setSizePolicy(sizePolicy)

        font = QtGui.QFont(self.predefinedPermissions.font())
        font.setFamily("Courier New")
        font.setPointSize(10)
        font.setWeight(50)
        font.setItalic(False)
        font.setUnderline(False)
        font.setStrikeOut(False)
        font.setBold(False)
        self.predefinedPermissions.setFont(font)
        self.predefinedPermissions.setTabChangesFocus(True)
        self.predefinedPermissions.setLineWrapMode(QtGui.QTextEdit.NoWrap)
        self.predefinedPermissions.setReadOnly(True)
        self.predefinedPermissions.setObjectName("predefinedPermissions")
        self.vboxlayout1.addWidget(self.predefinedPermissions)
        self.vboxlayout.addWidget(self.groupBox)

        self.groupBox_2 = QtGui.QGroupBox(PermissionsDialog)
        self.groupBox_2.setObjectName("groupBox_2")

        self.vboxlayout2 = QtGui.QVBoxLayout(self.groupBox_2)
        self.vboxlayout2.setMargin(9)
        self.vboxlayout2.setSpacing(6)
        self.vboxlayout2.setObjectName("vboxlayout2")

        self.status = QtGui.QLabel(self.groupBox_2)
        self.status.setObjectName("status")
        self.vboxlayout2.addWidget(self.status)

        self.permissions = QtGui.QTextEdit(self.groupBox_2)

        font = QtGui.QFont(self.permissions.font())
        font.setFamily("Courier New")
        font.setPointSize(10)
        font.setWeight(50)
        font.setItalic(False)
        font.setUnderline(False)
        font.setStrikeOut(False)
        font.setBold(False)
        self.permissions.setFont(font)
        self.permissions.setTabChangesFocus(True)
        self.permissions.setLineWrapMode(QtGui.QTextEdit.NoWrap)
        self.permissions.setAcceptRichText(False)
        self.permissions.setObjectName("permissions")
        self.vboxlayout2.addWidget(self.permissions)
        self.vboxlayout.addWidget(self.groupBox_2)

        self.hboxlayout = QtGui.QHBoxLayout()
        self.hboxlayout.setMargin(0)
        self.hboxlayout.setSpacing(6)
        self.hboxlayout.setObjectName("hboxlayout")

        spacerItem = QtGui.QSpacerItem(40,20,QtGui.QSizePolicy.Expanding,QtGui.QSizePolicy.Minimum)
        self.hboxlayout.addItem(spacerItem)

        self.applyButton = QtGui.QPushButton(PermissionsDialog)
        self.applyButton.setEnabled(False)
        self.applyButton.setDefault(True)
        self.applyButton.setObjectName("applyButton")
        self.hboxlayout.addWidget(self.applyButton)

        self.closeButton = QtGui.QPushButton(PermissionsDialog)
        self.closeButton.setObjectName("closeButton")
        self.hboxlayout.addWidget(self.closeButton)

        spacerItem1 = QtGui.QSpacerItem(40,20,QtGui.QSizePolicy.Expanding,QtGui.QSizePolicy.Minimum)
        self.hboxlayout.addItem(spacerItem1)
        self.vboxlayout.addLayout(self.hboxlayout)

        self.retranslateUi(PermissionsDialog)
        QtCore.QMetaObject.connectSlotsByName(PermissionsDialog)

    def retranslateUi(self, PermissionsDialog):
        PermissionsDialog.setWindowTitle(QtGui.QApplication.translate("PermissionsDialog", "Modify Permissions", None, QtGui.QApplication.UnicodeUTF8))
        self.groupBox.setTitle(QtGui.QApplication.translate("PermissionsDialog", "Predefined rules", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("PermissionsDialog", "These rules are hard coded, and may not be modified.", None, QtGui.QApplication.UnicodeUTF8))
        self.groupBox_2.setTitle(QtGui.QApplication.translate("PermissionsDialog", "User defined rules", None, QtGui.QApplication.UnicodeUTF8))
        self.status.setText(QtGui.QApplication.translate("PermissionsDialog", "<html><head><meta name=\"qrichtext\" content=\"1\" /></head><body style=\" white-space: pre-wrap; font-family:MS Shell Dlg 2; font-size:8.25pt; font-weight:400; font-style:normal; text-decoration:none;\"><p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt; font-weight:600;\">Set user defined rules to override predefined rules, and to define new rules.</span></p></body></html>", None, QtGui.QApplication.UnicodeUTF8))
        self.applyButton.setText(QtGui.QApplication.translate("PermissionsDialog", "&Apply", None, QtGui.QApplication.UnicodeUTF8))
        self.closeButton.setText(QtGui.QApplication.translate("PermissionsDialog", "&Close", None, QtGui.QApplication.UnicodeUTF8))
