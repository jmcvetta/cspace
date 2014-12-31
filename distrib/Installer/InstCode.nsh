!macro CheckCSpace NS
Function ${NS}CheckCSpace
    Push $0
    Push $1
    Push $R0
    StrCpy $1 5
again:
    Processes::FindProcess "CSpace.exe"
    StrCmp $R0 "1" 0 notfound
    Sleep 1000
    IntOp $1 $1 - 1
    StrCmp $1 0 0 again
    
    StrCpy $0 "installation"
    StrCmp "${NS}" "" isinstall
    StrCpy $0 "uninstallation"
isinstall:
    MessageBox MB_OKCANCEL "CSpace.exe appears to be running.$\r$\n \
    Press OK to terminate it and continue $0.$\r$\n \
    Press CANCEL to stop the $0." IDOK terminateit
    Abort
terminateit:
    KillProcDLL::KillProc "CSpace.exe"
    Sleep 1000
notfound:
    Pop $R0
    Pop $1
    Pop $0
FunctionEnd
!macroend

!macro KillApplets NS
Function ${NS}KillApplets
    Push $R0
    KillProcDLL::KillProc "CSpaceIM.exe"
    KillProcDLL::KillProc "CSpaceFileSender.exe"
    KillProcDLL::KillProc "CSpaceFileReceiver.exe"
    KillProcDLL::KillProc "CSpacePhotoSender.exe"
    KillProcDLL::KillProc "CSpacePhotoReceiver.exe"
    KillProcDLL::KillProc "CSpaceVNCClient.exe"
    KillProcDLL::KillProc "CSpaceVNCServer.exe"
    KillProcDLL::KillProc "CSpaceVNCViewer.exe"
    KillProcDLL::KillProc "CSpaceWinVNC.exe"
    Pop $R0
FunctionEnd
!macroend


