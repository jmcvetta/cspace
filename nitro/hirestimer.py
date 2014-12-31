import sys
from time import time, clock

if sys.platform == 'win32' :
    seconds = clock
else :
    seconds = time
