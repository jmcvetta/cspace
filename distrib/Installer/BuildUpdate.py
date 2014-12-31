import sys, os
bn = int(file('BuildNumber.txt').read().strip())
os.system( 'echo %d > CSpaceUpdate-BuildNumber.txt' % bn )
bnf = file('CSpaceUpdate-BuildNumber.nsh','w')
print>>bnf, '!define BUILD_NUMBER %d' % bn
bnf.close()
batf = file('_tmp_update.bat','w')
print>>batf, r'"c:\Program Files\NSIS\MakeNSIS.exe" /X"SetCompressor /SOLID /FINAL lzma" CSpaceUpdate.nsi'
#print>>batf, r'"c:\Program Files\NSIS\MakeNSIS.exe" /X"SetCompressor /FINAL zlib" CSpaceUpdate.nsi'
batf.close()
os.system( '_tmp_update.bat' )
os.unlink( '_tmp_update.bat' )
os.system( 'pause' )
