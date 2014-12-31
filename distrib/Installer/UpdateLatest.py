import os, sys, glob

os.chdir( '/var/www-cspace.in/setupfiles' )
files = glob.glob('*.exe') + ['LatestVersion.txt']
for f in files :
    os.system( 'cp %s tmpfile' % f )
    os.system( 'mv tmpfile ../downloads/%s' % f )
