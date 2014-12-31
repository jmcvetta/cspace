rd /s /q build
rd /s /q dist
python setup.py py2exe
move dist\IM.exe dist\CSpaceIM.exe
move dist\FileSender.exe dist\CSpaceFileSender.exe
move dist\FileReceiver.exe dist\CSpaceFileReceiver.exe
move dist\VNCClient.exe dist\CSpaceVNCClient.exe
move dist\VNCServer.exe dist\CSpaceVNCServer.exe
copy c:\windows\system32\msvcp71.dll dist\
xcopy /e ContactActions dist\ContactActions\
xcopy /e Services dist\Services\
copy ..\cspaceapps\vnc\CSpaceVNCViewer.exe dist\
copy ..\cspaceapps\vnc\VNCHooks.dll dist\
copy ..\cspaceapps\vnc\CSpaceWinVNC.exe dist\
pause
