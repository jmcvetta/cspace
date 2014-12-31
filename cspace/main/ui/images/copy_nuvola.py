import sys, os, shutil
import Image

NUVOLA_PATH = r'c:\Projects\OpenSource\nuvola'

def getSrcPath( srcName, res ) :
    return os.path.join( NUVOLA_PATH,
            '%sx%s'%(res,res),
            srcName+'.png' )

def getDestPath( destName, res, destDir ) :
    fileName = '%s%s.png' % (destName,res)
    return os.path.join( destDir, fileName )

def copyImage( srcName, destName, resolutions, destDir ) :
    for res in resolutions :
        srcPath = getSrcPath( srcName, res )
        destPath = getDestPath( destName, res, destDir )
        print 'writing %s' % destPath
        shutil.copyfile( srcPath, destPath )

def mergeImages( im, im2 ) :
    im = im.copy()
    im2 = im2.copy()
    w,h = im.size
    w2,h2 = [x/2 for x in im2.size]
    im2.thumbnail( (w2,h2), Image.ANTIALIAS )
    im.paste( im2, (w-w2,0,w,h2), im2 )
    return im

def loadImage( srcName, res ) :
    im = Image.open( getSrcPath(srcName,res) )
    if srcName == 'actions/edit_remove' :
        r,g,b,a = im.split()
        im = Image.merge( 'RGBA', (g,r,b,a) )
        im = im.point( lambda x: 1.5*x )
    return im

def copyMerged( srcName, srcName2, destName, resolutions, destDir ) :
    for res in resolutions :
        im = loadImage( srcName, res )
        im2 = loadImage( srcName2, res )
        im = mergeImages( im, im2 )
        destPath = getDestPath( destName, res, destDir )
        print 'writing %s' % destPath
        im.save( destPath )

images = (
        ('actions/connect_established','connect'),
        ('actions/connect_no','disconnect'),
        ('actions/exit','exit'),
        ('apps/kwrite','edit_permissions'),
        ('actions/reload','refresh'),
        ('actions/kgpg_gen','register'),
        ('actions/kgpg_identity','contact_info'),
        ('actions/kgpg_info','key_info')
        )

addImage = 'actions/edit_add'
removeImage = 'actions/edit_remove'
userImage = 'apps/personal'
merge_images = (
        (userImage,addImage,'user_add'),
        (userImage,removeImage,'user_remove')
        )

if __name__ == '__main__' :
    resolutions = ( '16', '22', '32' )
    destDir = '.'
    for srcName,destName in images :
        copyImage( srcName, destName, resolutions, destDir )
    for src,src2,dest in merge_images :
        copyMerged( src, src2, dest, resolutions, destDir )
