## Automatically adapted for numpy Jul 30, 2006 by numeric2numpy.py

# $Id: addPyGistTracker.py 598 2006-12-13 11:12:09Z mbec $
#  -----------------------------------------------------------------
#  LLNL-specific file
#  -----------------------------------------------------------------

from posix import system
try:
   system ( "/usr/apps/tracker/bin/tracker -s -n PYGIST -v %s" % __version__ )
except:
   pass
