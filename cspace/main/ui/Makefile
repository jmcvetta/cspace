all : Ui_MainWindow.py Ui_CreateKeyDialog.py Ui_CreateKeyDoneDialog.py \
	Ui_GoOnlineDialog.py Ui_KeyInfoDialog.py Ui_AddContactDialog.py \
	Ui_ContactInfoDialog.py Ui_PermissionsDialog.py \
	Ui_UpdateNotifyWindow.py Ui_IncomingPromptWindow.py \
	images_rc.py

Ui_MainWindow.py : MainWindow.ui
	pyuic4 $** -o $@

Ui_CreateKeyDialog.py : CreateKeyDialog.ui
	pyuic4 $** -o $@

Ui_CreateKeyDoneDialog.py : CreateKeyDoneDialog.ui
	pyuic4 $** -o $@

Ui_GoOnlineDialog.py : GoOnlineDialog.ui
	pyuic4 $** -o $@

Ui_KeyInfoDialog.py : KeyInfoDialog.ui
	pyuic4 $** -o $@

Ui_AddContactDialog.py : AddContactDialog.ui
	pyuic4 $** -o $@

Ui_ContactInfoDialog.py : ContactInfoDialog.ui
	pyuic4 $** -o $@

Ui_PermissionsDialog.py : PermissionsDialog.ui
	pyuic4 $** -o $@

Ui_UpdateNotifyWindow.py : UpdateNotifyWindow.ui
	pyuic4 $** -o $@

Ui_IncomingPromptWindow.py : IncomingPromptWindow.ui
	pyuic4 $** -o $@

images_rc.py : images.qrc
	pyrcc4 $** -o $@
