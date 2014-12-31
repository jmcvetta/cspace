import sys, os
bn = int(file('BuildNumber.txt').read().strip())
os.system( 'echo %d > CSpaceSetup-BuildNumber.txt' % bn )
bnf = file('CSpaceSetup-BuildNumber.nsh','w')
print>>bnf, '!define BUILD_NUMBER %d' % bn
bnf.close()
batf = file('_tmp_setup.bat','w')
print>>batf, r'"c:\Program Files\NSIS\MakeNSIS.exe" /X"SetCompressor /SOLID /FINAL lzma" CSpaceSetup.nsi'
#print>>batf, r'"c:\Program Files\NSIS\MakeNSIS.exe" /X"SetCompressor /FINAL zlib" CSpaceSetup.nsi'
batf.close()
os.system( '_tmp_setup.bat' )
os.unlink( '_tmp_setup.bat' )
os.system( 'pause' )
