from gist import *
#maxwidth=1024
#maxheight=768
maxwidth=1600
maxheight=900
from Mplot import *

#
#import os, sys
#from write_style import *
#
#os.environ['GISTPATH'] = os.path.join(os.path.dirname(__file__),'gistdata')
#
#display = os.environ.get('DISPLAY')
#maxwidth=os.environ.get('XPLT_MAXWIDTH')
#maxheight=os.environ.get('XPLT_MAXHEIGHT')
#if display and (maxwidth is None or maxheight is None):
#    import commands
#    str1 = commands.getoutput('xwininfo -root')
#    # Hmmm.  errors still seem to be occuring occasionally even
#    # with the display check.  Added try block to protect against
#    # this causing import scipy to fail.
#    try:
#        ind1 = str1.find('Width:')
#        ind2 = str1.find('\n',ind1)
#        maxwidth=int(str1[ind1+6:ind2])-8
#        ind1 = str1.find('Height:')
#        ind2 = str1.find('\n',ind1)
#        maxheight=int(str1[ind1+7:ind2])-60
#        os.environ['XPLT_MAXWIDTH']=str(maxwidth)
#        os.environ['XPLT_MAXHEIGHT']=str(maxheight)
#    except ValueError:
#        pass
#
#if maxwidth is None:
#    maxwidth = 1024
#if maxheight is None:
#    maxheight = 768
