import os, sys, StringIO, sha

def digestFile( f ) :
    return sha.new(file(f,'rb').read()).hexdigest()

def digestList( fileList ) :
    out = []
    for f in fileList :
        if not os.path.isfile(f) : continue
        d = digestFile( f )
        out.append( (f,d) )
    return out

def main() :
    fileList = sys.argv[1:]
    for f,d in digestList(fileList) :
        print '%s %s' % (f,d)

if __name__ == '__main__' :
    main()
