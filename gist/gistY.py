## Automatically adapted for numpy Jul 30, 2006 by numeric2numpy.py

#  $Id: gist.py 19029 2009-03-26 22:04:16Z mdcb $
#  ---------------------------------------------------------------------
#
#  NAME:  gist.py
#
#  CHANGES:
#  11/08/04 mdh plh: Change test if color is a list; also test if array. 
#  06/16/03 mdh plh: Added a keyword (height) for font size of labels. 
#  04/07/03 mdh Modifications to plh to add labels below x-axis; removed 
#               legend and added label keyword.
#  03/19/03 llc Dave Grote reported a bug in plfc:  nc==None should be 
#               nc is None.
#  03/13/03 llc Add one NOTE on plfc.
#  03/12/03 llc Updated doc comments.
#  12/25/02 mdh Add plh to draw histograms
#  11/26/01 llc Add docstring for plmk (missing).
#  11/05/01 llc Use pydoc's help (not the one in help.py).
#  10/30/01 llc Disable is_scalar call; type(arraytype) not implemented
#               in Python.
#               Also, merge in documentation (if it exists) from gist.help 
#               after each function, so that pydoc's help can return it.
#  10/12/01 llc Re-port of gist from archived version.
#
#  ---------------------------------------------------------------------

# 'eps'
__all__ = ['hcp', 'winkill', 'pltitle', 'ylimits', 'moush', 'xytitles', 'plmk', 'plmk_default', 'plfc', 'plh', 'repl' ]

import sys, os
import numpy
from .gistC import *
from .gistF import zmin_zmax
#from mesh import * # still experimental, undebugged

# dpi=75  -> 450 pix
# dpi=100 -> 600 pix
_pix_per_dpi = 6.0
_default_dpi = 75


# Parameters used by pltitle and xytitles
#pltitle_height= 18;
#pltitle_font= 'helvetica';

# Parameters used by plmk and plmk_default
_plmk_count = 0
_plmk_msize = _plmk_color = _plmk_width = None


#  ---------------------------------------------------------------------

def hcp(filename,bw=None):
   '''hcp(filename,bw=None)

      Save a hardcopy of current window to file.
      The file name extension defines the type of image.
      Example:
         hcp('screenshot.png')

      The keyword bw= can be set to convert the image to grayscale:
        'ntsc'
        'atsc' or 'hdtv'
        'lightness'
        'average'

      SEE ALSO: rgb_read, scipy.misc.imsave
   '''
   import scipy.misc
   rgb=rgb_read()

   if bw is 'ntsc':
      # Y = 0.2989 * R + 0.5870 * G + 0.1140 * B (luminance)
      # I = 0.596  * R - 0.274  * G - 0.322  * B (hue)
      # Q = 0.211  * R -0.523   * G + 0.312  * B (saturation)
      rgb = 0.2989 * rgb[:,:,0] + 0.5870 * rgb[:,:,1] + 0.1140 * rgb[:,:,2]
   elif bw in ('atsc', 'hdtv'):
      rgb = 0.2126 * rgb[:,:,0] + 0.7152 * rgb[:,:,1] + 0.0722 * rgb[:,:,2]
   elif bw is 'lightness':
      rgb = (numpy.min(rgb,axis=2)+numpy.max(rgb,axis=2))/2
   elif bw is 'average':
      rgb = rgb.mean(axis=2)
   elif bw is not None:
      raise Exception("bw should be one of 'ntsc', 'atsc', 'hdtv', 'lightness', 'average'")

   scipy.misc.imsave(filename,rgb)


#  ---------------------------------------------------------------------

def winkill(*n):
   '''
   winkill ()
   winkill (n)
      Delete the current graphics window, or graphics window N (0-7).
   '''
   window(*n, display='', hcp='')

#  ---------------------------------------------------------------------

def pltitle(title,dx=0.0,dy=0.0,**kwd):
   '''
   pltitle (title, dx=0.0, dy=0.0, **kwd)
      Plot TITLE centered above the coordinate system for any of the
      standard Gist styles.  You will need to customize this for other
      plot styles.
      
      Accepts additional kwd arguments compatible with the
      plt command (e.g. font=, height=).

    To get symbol font for the next character precede by !
    To get superscript enclose with ^^
    To get subscript enclose with _<text>_

   SEE ALSO: plt
   '''
   #kwd['font'] = kwd.get('font',pltitle_font)
   kwd['justify'] = kwd.get('justify','CB')
   #kwd['height'] = kwd.get('height',pltitle_height)
   vp = viewport()
   xmidpt = (vp[0] + vp[1])/2.0 + dx
   plt( title, xmidpt, vp[3] + 0.02 + dy, **kwd)

#  ---------------------------------------------------------------------

def ylimits(ymin='u',ymax='u'): 
   '''
   ylimits (ymin='u', ymax='u')
      Set the y-axis plot limits in the current coordinate system to
      YMIN, YMAX, which may each be a number to fix the corresponding
      limit to a specified value, or the string 'e' to make the
      corresponding limit take on the extreme value of the currently
      displayed data. Arguments may be omitted only from the right. Use
      limits( xmin, xmax ) to accomplish the same function for the x-axis
      plot limits.  Note that the corresponding Yorick function for
      ylimits is ``range'' - since this word is a Python built-in function,
      I've changed the name to avoid the collision.
      SEE ALSO: plsys, limits, logxy, plg
   '''
   limits('u','u',ymin,ymax)

#  ---------------------------------------------------------------------

def moush(*arg):
   '''
   moush (y, x, ireg)
   moush (y, x)
   moush ()
      Number of args can be 0, 2, or 3.
      Returns the 1-origin zone index for the point clicked in
      for the default mesh, or for the mesh (X,Y) (region array IREG).
   '''
   narg = len(arg)
   if narg == 3: # (y, x, ireg)
      xy = mouse (-1, 0, '<Click mouse in mesh>')
      if xy == None: return None
      return mesh_loc (xy[1], xy[0], arg[0], arg[1], arg[2]);
   elif narg == 2: # (y, x)
      xy = mouse (-1, 0, '<Click mouse in mesh>')
      if xy == None: return None
      return mesh_loc (xy[1], xy[0], arg[0], arg[1]);
   elif narg == 0: # ()
      xy = mouse (-1, 0, '<Click mouse in mesh>')
      if xy == None: return None
      return mesh_loc (xy[1], xy[0]);
   else:
      print('Mouse takes 0, 2, or 3 args: ( [ y, x [ , ireg ] ] )')
      return None

##  ---------------------------------------------------------------------
##  PURPOSE:  Create an encapsulated PostScript file.  
##            Requires Ghostscript and its associated ps2epsi utility.
##  ---------------------------------------------------------------------
#
#def eps(name):
#   '''
#   eps (name)
#      Write the picture in the current graphics window to the Encapsulated
#      PostScript file NAME+'.epsi' (i.e.- the suffix .epsi is added to NAME).
#      The eps function requires the ps2epsi utility which comes with the
#      project GNU Ghostscript program.  Any hardcopy file associated with
#      the current window is first closed, but the default hardcopy file is
#      unaffected.  As a side effect, legends are turned off and color table
#      dumping is turned on for the current window.
#      The environment variable PS2EPSI_FORMAT contains the format for the
#      command to start the ps2epsi program.
#      SEE ALSO: window, fma, hcp, hcp_finish, plg
#   '''
#   import os
#   name = name + '.ps'
#   window (hcp = name, dump = 1, legends = 0)
#   hcp ()
#   window (hcp='')
#   os.system ('ps2epsi ' + name)
#   os.system ('rm ' + name)

#  ---------------------------------------------------------------------

def xytitles(xtitle='', ytitle='', delta=(0.,0.), **kwd):
   '''
   xytitles (xtitle='', ytitle='', delta=(0.,0.), **kwd)
     Plots title for x and y. Accepts additional kwd arguments
     compatible with the plt command (e.g. font=, height=).
    SEE ALSO: pltitle, plt
   '''
   vp = viewport()
   xmidpt = (vp[0] + vp[1])/2.0
   ymidpt = (vp[2] + vp[3])/2.0
   #kwd['font'] = kwd.get('font',pltitle_font)
   #kwd['height'] = kwd.get('height',pltitle_height)
   if len(xtitle) > 0:
      kwd['justify'] = 'CT'
      plt(xtitle, xmidpt, vp[2] - 0.035 + delta[1], **kwd)
   if len(ytitle) > 0:
      kwd['justify'] = 'CB'
      kwd['orient']=1
      plt(ytitle, vp[0] - 0.040 + delta[0], ymidpt, **kwd)

#  ---------------------------------------------------------------------

# Half-hearted attempt at span()(zcen), which returns N-1 'zone-centered'
# values in sequence (lb, ..., ub)
def _spanz(lb,ub,n):
   if n < 3: raise ValueError('3rd arg must be at least 3')
   c = 0.5*(ub - lb)/(n - 1.0)
   b = lb + c
   a = (ub - c - b)/(n - 2.0)
   return list(map(lambda x,A=a,B=b: A*x + B, numpy.arange(n-1)))

#  .. predefined markers: square, +, delta, circle, diamond, x, grad
_seq = _spanz(-numpy.pi,numpy.pi,37)
_plmk_markers = (
   numpy.array([[-1,1,1,-1],[-1,-1,1,1]])*.007,
   numpy.array([[-4,-1,-1,1,1,4,4,1,1,-1,-1,-4],
      [-1,-1,-4,-4,-1,-1,1,1,4,4,1,1]])*.007/numpy.sqrt(7),
   numpy.array([[-numpy.sqrt(3),numpy.sqrt(3),0],[-1,-1,2]])*.007/numpy.sqrt(.75*numpy.sqrt(3)),
   numpy.array([numpy.cos(_seq),numpy.sin(_seq)])*.007/(numpy.pi/4.),
   numpy.array([[-1,0,1,0],[0,-1,0,1]])*.007*numpy.sqrt(2),
   numpy.array([[-1,-2.5,-1.5,0,1.5,2.5,1,2.5,1.5,0,-1.5,-2.5],
      [0,-1.5,-2.5,-1,-2.5,-1.5,0,1.5,2.5,1,2.5,1.5]])*.007*numpy.sqrt(2)/numpy.sqrt(7),
   numpy.array([[0,numpy.sqrt(3),-numpy.sqrt(3)],[-2,1,1]])*.007/numpy.sqrt(.75*numpy.sqrt(3))
   )
del(_seq)

#  ---------------------------------------------------------------------

def plmk(y,x=None,marker=None,width=None,color=None,msize=None):
   '''
   plmk (y,x=None,marker=None,width=None,color=None,msize=None)
     Make a scatter plot of the points Y versus X.  If X is nil,
     it defaults to indgen(numberof(Y)).  By default, the marker
     cycles through 7 predefined marker shapes.  You may specify a shape
     using the marker= keyword, line width using the width= keyword (you
     get solid fills for width>=10), color using the color= keyword.
     You can also use the msize= keyword to scale the marker (default
     msize=1.0).  You can change the default width, color, or msize
     using the plmk_default function.

   The predefined marker= values are:

   marker=
      1        square
      2        cross
      3        triangle
      4        circle
      5        diamond
      6        cross (rotated 45 degrees)
      7        triangle (upside down)

   You may also put marker=[xm,ym] where xm and ym are vectors
   of NDC coordinates to design your own custom marker shapes.

   SEE ALSO: plmk_default, plg (type=0 keyword)
   '''

   global _plmk_count
   global _plmk_color, _plmk_width, _plmk_msize
   color_dict = { 'bg':-1, 'fg':-2, 'black':-3, 'white':-4, 'red':-5,
      'green':-6, 'blue':-7, 'cyan':-8, 'magenta':-9, 'yellow':-10 }

   z = None

   if marker == None:
      marker = _plmk_markers[(_plmk_count)%7]
      _plmk_count = _plmk_count + 1
   elif type(marker) == type(0):
      marker = _plmk_markers[marker-1];

   xm = marker[0]
   ym = marker[1]
   if not msize: msize = _plmk_msize;
   if msize:
      xm = xm * msize;
      ym = ym * msize;

   if not color: color = _plmk_color;
   ecolor = color;
   if type(color) == str:
      color = color_dict[color];
  
   if not width: width = _plmk_width;
   if width >= 10:
      width = None
   if not color:
      color = ecolor = -2 # magic number for 'fg'

   z = numpy.ones(1+len(y)) * color
   z = z.astype(numpy.uint8) # convert array to type <unsigned char>

   n = numpy.ones(1+len(y),numpy.int64);
   n[0] = len(ym);
   if not x: x = 1 + numpy.arange(len(y));
   
   plfp( z, numpy.concatenate((ym,y)), numpy.concatenate((xm,x)),n,
      edges=1, ewidth=width, ecolor=ecolor)

#  ---------------------------------------------------------------------


def plmk_default(color=None, msize=None, width=None):
   '''
   plmk_default (color=None, msize=None, width=None)
     Set default color, msize, and width values for plmk.  Use
     width=10 to get solid fills.  With no parameters, plmk_default
     restores the initial default values.
   '''
   global _plmk_color, _plmk_width, _plmk_msize
   if color: _plmk_color = color
   if width: _plmk_width = width
   if msize: _plmk_msize = msize
   if not (color or width or msize):
      _plmk_msize = _plmk_color = _plmk_width = None

class _ContourError(Exception):
    pass

#  ---------------------------------------------------------------------

def plfc (z, y, x, ireg, contours = 8, colors = None, region = 0,
   triangle = None, scale = 'lin') :
   '''
   plfc (z, y, x, ireg, contours = 8, colors = None, region = 0,
      triangle = None, scale = 'lin')

      Fills contours of Z on the mesh Y versus X.  Y, X, and IREG are
      as for plm.  The Z array must have the same shape as Y and X.
      The function being contoured takes the value Z at each point
      (X, Y) -- that is, the Z array is presumed to be point-centered.

      NOTE:  The ireg argument was not in the Yorick Gist plfc.

      The CONTOURS keyword can be an integer specifying the number of
      contours desired, or a list of the values of Z at which you want
      contour curves.  These curves divide the mesh into len(CONTOURS+1)
      regions, each of which is filled with a solid color.  If CONTOURS is
      None or not given, 8 'nice' equally spaced level values spanning the
      range of Z are selected.

      If you specify CONTOURS, you may also specify COLORS, an array of
      color numbers (Python dtype 'B', np.uint8, integers between 0 and the
      length of the current palette - 1, normally 199) of length
      len(CONTOURS)+1. If you do not specify them, equally
      spaced colors are chosen.

      If CONTOURS is an integer, SCALE expresses how contour levels
      are determined.  SCALE may be 'lin', 'log', or 'normal'
      specifying linearly, logarithmically, or normally spaced
      contours. Note that unlike Yorick's plfc, this routine does
      not use spann to compute its contours. Neither, apparently,
      does plc, which uses a third algorithm which matches neither
      the one we use nor the one spann uses. So if you plot filled
      contours and then plot contour lines, the contours will in
      general not coincide exactly.

      Note that you may use spann to calculate your contour levels
      if you wish.

      The following keywords are legal (each has a separate help entry):
    KEYWORDS: triangle, region
    SEE ALSO: plg, plm, plc, plv, plf, pli, plt, pldj, plfp, plmesh
              colorbar, contour, limits, logxy, range, fma, hcp
   '''
   # 1. Get contour colors

   (vcmin, vcmax) = zmin_zmax (z, ireg)
   if type (contours) == int :
      n = contours
      vc = numpy.zeros (n + 2, numpy.float32)
      vc [0] = vcmin
      vc [n + 1] = vcmax
      if scale == 'lin' or scale == None :
          # This stuff is in lieu of the spann stuff in Yorick.
          vc [1:n + 1] = vcmin + numpy.arange (1, n + 1) * \
             (vcmax - vcmin) / (n + 1)
      elif scale == 'log' :
          vc [1:n + 1] = vcmin + exp (numpy.arange (1, n + 1) * \
             log (vcmax - vcmin) / (n + 1))
      elif scale == 'normal' :
          zlin = numpy.ravel (z)
          lzlin = len (zlin)
          zbar = numpy.add.reduce (zlin) / lzlin
          zs = numpy.sqrt ( (numpy.add.reduce (zlin ** 2) - lzlin * zbar ** 2) /
              (lzlin - 1))
          z1 = zbar - 2. * zs
          z2 = zbar + 2. * zs
          diff = (z2 - z1) / (n - 1)
          vc [1:n + 1] = z1 + numpy.arange (n) * diff
      else :
          raise _ContourError('Incomprehensible scale parameter.')
   elif type (contours) == numpy.ndarray and contours.dtype.type == numpy.float64 :
      n = len (contours)
      vc = numpy.zeros (n + 2, numpy.float32)
      vc [0] = vcmin
      vc [n + 1] = vcmax
      vc [1:n + 1] = numpy.sort (contours)
   else :
      raise _ContourError('Incorrect contour specification.')
   if colors == None :
      colors = (numpy.arange (n + 1) * (199. / n)).astype(numpy.uint8)
   else :
      colors = numpy.array (colors)
      if len (colors) != n + 1 :
         raise Exception('PLFC_Error, colors must specify one more color than contours.')
      if colors.dtype != numpy.uint8 :
         colors = bytscl (colors)

   if triangle == None :
      triangle = numpy.zeros (z.shape, numpy.int32)

  # Set mesh first
   plmesh (y, x, ireg, triangle = triangle)
   for i in range (n + 1) :
      [nc, yc, xc] = contour (numpy.array ( [vc [i], vc [i + 1]]), z)
      if nc == 0 or nc is None:
         continue
      plfp ( (numpy.ones (len (nc)) * colors [i]).astype(numpy.uint8),
         yc, xc, nc, edges = 0)

def plh (y, x=None, width=1, hide=0, color=None, labels=None, height=None):
   '''
   plh ( y, [x, labels, <keylist>])

      Draws a histogram, where the height of the bars is given
      by Y. If X is None, the bars in the histogram have a
      width equal to unity. If X is a single real number, the
      widths of the bars are all equal to this number. If X is
      a one-dimensional array with an equal number of elements
      as the Y array, then X is interpreted as the widths of
      the bars. In all of these cases, the histogram starts at
      the origin. However, if X is a one-dimensional array
      with one element more than Y, then X is interpreted as
      the locations of the start and end points of the bars in
      the histogram. If X is a one-dimensional array with twice
      as many elements as Y, then X represents the start and
      end points for each bar separately.
      The keyword color is either a single color, representing
      the fill color of the bars, or a list of colors, one for
      each bar.
      If the keyword labels is given, then the horizontal tick
      marks and numerical labels are switched off. The keyword
      labels should then consist of a list of strings, with the
      same number of elements as Y. These labels are then drawn
      below the horizontal axis. The keyword height, if given,
      specifies the font height for the labels.
      To switch the tick marks and labels back on for subsequent
      plots, you can execute
      window(style='work.gs')
      which will reset the window to the usual work.gs style sheet.
      
      
      The following keywords are legal (each has a separate help entry):
    KEYWORDS: width, hide, color, height
    SEE ALSO: plg, plm, plc, plv, plf, pli, plt, pldj, plfp, plmesh
              colorbar, contour, limits, logxy, range, fma, hcp
   '''

   color_dict = { 'bg':-1, 'fg':-2, 'black':-3, 'white':-4, 'red':-5,
      'green':-6, 'blue':-7, 'cyan':-8, 'magenta':-9, 'yellow':-10 }
   n = len(y)
   barx = [[]] * n
   if x==None:
      for i in range(n):
         barx[i] = numpy.array([i,i,i+1,i+1])
   else:
      if type(x) == int or type(x) == numpy.float32:
         # x denotes the width of the bars, which are all equal
         for i in range(n-1):
            barx[i] = numpy.array([i,i,i+1,i+1]) * x
      elif type(x) == list or type(x) == numpy.ndarray:
         if len(x) == n:
            # x denotes the width of the bars, which can be different
            offset = 0
            for i in range(n):
               barx[i] = offset + numpy.array([0,0,1,1]) * x[i]
               offset = offset + x[i]
         elif len(x) == n + 1:
            for i in range(n):
               barx[i] = numpy.array([x[i],x[i],x[i+1],x[i+1]])
         elif len(x) == 2*n:
            for i in range(n):
               barx[i] = numpy.array([x[2*i],x[2*i],x[2*i+1],x[2*i+1]])
         else:
            raise Exception('plh error: inconsistent length of X')
   bary = [[]] * n
   for i in range(n):
      bary[i] = numpy.array([0,y[i],y[i],0])
   if labels:
      if win_current() < 0:
         window(style='boxed.gs',legends=0)
      style = get_style()
      if style['systems'][0]['ticks']['horizontal']['flags'] & 99:
         # We need to switch off tick marks and labels here
         window(style='boxed.gs', legends=0)
         style = get_style()
         flags = style['systems'][0]['ticks']['horizontal']['flags']
         flags = flags & ( ~ 99) # Switch off horizontal tick marks, labels
         style['systems'][0]['ticks']['horizontal']['flags'] = flags
         set_style(style)
   if color != None:
      if type(color) != list and type(color) != numpy.ndarray:
         color = [color] * n
      for i in range(n):
         z = color[i]
         if type(z) == str: z = color_dict[z]
         plfp(numpy.array([z],numpy.uint8),bary[i],barx[i],[4])
   for i in range(n):
      plg(bary[i],barx[i],width=width,hide=hide,marks=0)
   if labels:
      [left,right,bottom,top] = viewport()
      hticks = style['systems'][0]['ticks']['horizontal']
      scale = (right-left)/(barx[-1][-1]-barx[0][0])
      y = bottom - hticks['labelOff'] + hticks['tickLen'][0] + hticks['tickOff']
      if height:
         for i in range(n):
            x = left + scale * ((barx[i][0]+barx[i][-1])/2. - barx[0][0])
            plt(labels[i],x,y,justify='CT',height=height)
      else:
         for i in range(n):
            x = left + scale * ((barx[i][0]+barx[i][-1])/2. - barx[0][0])
            plt(labels[i],x,y,justify='CT')

def repl ():
   '''
   repl()

   brings you back to the repl interactive mode.
   '''
   try: import os; execfile(os.environ['PYTHONSTARTUP'])
   except: import os; exec(compile(open(os.environ['PYTHONSTARTUP']).read(), 'PYTHONSTARTUP', 'exec'))
   import code, inspect
   # uplevel hack
   frame_obj, file_name, line_num, func_name, lines_of_context, index_in_current_line = inspect.stack()[1]
   lcls=frame_obj.f_locals
   code.interact(local=lcls,banner='welcome back!')

