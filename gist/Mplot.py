#__all__ = ['_find_and_set', '_parse_type_arg', '_clear_global_linetype', '_append_global_linetype', '_minsqueeze', '_add_color', '_chng_font', '_remove_ticks', '_change_palette' ]

__all__ = ['histogram', 'barplot', 'errorbars', 'arrow', 'plot', 'matplot', 'stem', 'makeleg', 'twoplane', 'surf', 'scalexy', 'axes', 'bode', 'palette_write', 'palette_list', 'matview', 'imagesc', 'figure', 'subplot', 'imagesc_cb',
'palette_inspect',
'plsurf',
'legend',
#---
'stairplot',
'crosshair',
'box',
'pyg_once',
'winscape',
'movie',
'colorbar'
]

import sys, os
import numpy
from . import gistY as gist
from . import pl3d, plwf, write_style, pltitle
from .gistC import *
from .gistF import array_set
from .slice3 import split_bytscl

points = 0.0013000
inches = 72.27*points

_colornum = {'bg':-1, 'fg':-2, 'black':-3, 'white':-4,'red':-5,'green':-6,'blue':-7,'cyan':-8,'magenta':-9,'yellow':-10}
_types = {'-':'solid','|':'dash',':':'dot','-.':'dashdot','-:':'dashdotdot'}
_corder = ['B','r','m','g','c','k','y']
_colors = {'k':'black','r':'red','B':'blue','m':'magenta','g':'green','y':'yellow','c':'cyan','w':'white'}
_markers = { '+':'\2','.':'\1','*':'\3','o':'\4','x':'\5'}
_current_style='work.gs'

_rtypes = dict((v,k) for k,v in _types.items())
_rtypes['none'] = ''
_rcolors = dict((v,k) for k,v in _colors.items())
_rmarkers = dict((v,k) for k,v in _markers.items())

# TODO xwininfo
_maxwidth=1600
_maxheight=900
_dpi = 75
_maxcolors=256

gist.pldefault(dpi=_dpi,maxcolors=_maxcolors)

# directory for storing temporary *.gp and *.gs files
_user_path = os.path.join(os.environ['HOME'],'.gist')

def histogram(data,nbins=80,range=None,ntype=0,bar=1,bwidth=0.8,bcolor='fg',rval=False):
  '''Plot a histogram.

     Returns an array (nbins,2) of bin values,count.

         range -- if None, use (min,max) of the data.
         ntype -- normalization type. Use ntype == 2 to
                  compare with probability density function.

     EXAMPLE:

         z = histogram(np.random.rand(1000),range=(0.2,0.8))
  '''
  if type(bcolor) is str: bcolor=_colornum[bcolor]

  if range is None:
    dmin = numpy.minimum.reduce(data)
    dmax = numpy.maximum.reduce(data)
  else:
    dmin, dmax = range
  dmin = dmin + 0.0
  dmax = dmax + 0.0
  bin_width = (dmax - dmin)/nbins
  arr = numpy.zeros((nbins,2),numpy.float32)
  arr[:,0] = dmin + bin_width*(numpy.arange(nbins)+0.5)
  bins = dmin + bin_width*(numpy.arange(nbins+1))
  arr[:,1] = numpy.histogram(data,bins)[0]
  if ntype == 1:
    arr[:,1] = 1.0*arr[:,1] / numpy.add.reduce(arr[:,1])
  elif ntype == 2:
    arr[:,1] = 1.0/bin_width*arr[:,1] / numpy.add.reduce(arr[:,1])
  if bar:
    barplot(arr[:,0],arr[:,1],width=bwidth,color=bcolor)
  else:
    plot(arr[:,0],arr[:,1])
  if rval: return arr

def barplot(x,y,width=0.8,color='fg', horiz=False):
  '''Plot a barplot.
           
         X   X
         X   X X
       X X X X X X X

     SEE ALSO: stem, stairplot

        x --      Centers of bars
        x --      Heights of bars
        width  -- Relative width of the bars.
        color  -- Color of bars.
        horiz --  Set to True for horizontal barplot.

     EXAMPLE:

         barplot(np.arange(5),np.random.rand(5))
  '''
  if type(color) is str: color=_colornum[color]
  N = 4*numpy.ones(len(x), dtype=numpy.int32)
  x=numpy.asarray(x)
  y=numpy.asarray(y)
  hw = width * (x[1]-x[0])/ 2.0
  Xa = x-hw
  Xb = x+hw
  Ya = numpy.zeros(len(y),'d')
  Yb = y
  X = numpy.array((Xa,Xa,Xb,Xb))
  Y = numpy.array((Ya,Yb,Yb,Ya))
  X = numpy.reshape(numpy.transpose(X),(4*len(N),))
  Y = numpy.reshape(numpy.transpose(Y),(4*len(N),))
  Z = color * numpy.ones(len(N))

  if horiz: gist.plfp(Z.astype(numpy.uint8),X,Y,N)
  else: gist.plfp(Z.astype(numpy.uint8),Y,X,N)

def errorbars(x,y,err,ptcolor='r',linecolor='B',pttype='o',linetype='-',fac=0.25):
  '''Plot connected points with errorbars.

         x, y --      The points to plot.
         err --       The error in the y values.
         ptcolor --   The color for the points.
         linecolor -- The color of the connecting lines and error bars.
         pttype --    The type of point ('o', 'x', '+', '.', 'x', '*')
         linetype --  '-'  solid
                      '|'  dash
                      ':'  dot
                      '-.' dashdot
                      '-:' dashdotdot
         fac --       Adjusts how long the horizontal lines are which make the
                      top and bottom of the error bars.
  '''
  # create line arrays
  x=numpy.asarray(x)
  y=numpy.asarray(y)
  err=numpy.asarray(err)

  yb = y - err
  ye = y + err
  y = numpy.where(numpy.isfinite(y),y,0)
  gist.plg(y,x,color=_colors[ptcolor],marker=_markers[pttype],type='none')
  gist.pldj(x,yb,x,ye,color=_colors[linecolor],type=_types[linetype])
  viewp = gist.viewport()
  plotlims = gist.limits()
  conv_factorx = (viewp[1] - viewp[0]) / (plotlims[1]-plotlims[0])
  conv_factory = (viewp[3] - viewp[2]) / (plotlims[3]-plotlims[2])
  width = fac*(x[1]-x[0])
  x0 = x-width/2.0
  x1 = x+width/2.0
  gist.pldj(x0,ye,x1,ye,color=_colors[linecolor],type=_types[linetype])
  gist.pldj(x0,yb,x1,yb,color=_colors[linecolor],type=_types[linetype])

def legend(text,linetypes=None,lleft=None,color='fg',tfont='helvetica',fontsize=14,nobox=0):
  '''Draw a legend on the current plot.

         text      -- A list of strings which document the curves.
         linetypes -- If not given, then the text strings are associated
                      with the curves in the order they were originally
                      drawn.  Otherwise, associate the text strings with the
                      corresponding curve types given.  See plot for description.
         lleft     -- (x,y) lower left coordinates in sys=0. If not provided,
                      runs interactively.
                      prompt the user to place the legend with a mouse click.
         color     -- The legend color for box and text.

     EXAMPLE:

         gist.legend(['hello','world'],lleft=(0.290,0.696))
         gist.legend(['white dash','red dot','solid blue'],
                      linetypes=['|w',':r','-B'],color='yellow')
  '''

  if type(color) is str: color=_colornum[color]

  sys = gist.plsys()
  if sys == 0:
    gist.plsys(1)
  viewp = gist.viewport()
  gist.plsys(sys)
  DX = viewp[1] - viewp[0]
  DY = viewp[3] - viewp[2]
  width = DY / 10.0;
  if lleft is None:
    lleft = gist.mouse(0,0,'Click on point for lower left coordinate.')
    llx = lleft[0]
    lly = lleft[1]
  else:
    llx,lly = lleft[:2]

  savesys = gist.plsys()
  dx = width / 3.0
  legarr = numpy.arange(llx,llx+width,dx)
  legy = numpy.ones(legarr.shape)
  dy = fontsize*points*1.2
  deltay = fontsize*points / 2.8
  deltax = fontsize*points / 2.6 * DX / DY
  ypos = lly + deltay;
  if linetypes is None:
    linetypes = _GLOBAL_LINE_TYPES[:]  # copy them out
  gist.plsys(0)
  for k in range(len(text)):
    try: ltype =  linetypes[k] # _GLOBAL_LINE_TYPES holds the style of previous 'plot'
    except: ltype = '-' # solid
    plot(legarr,ypos*legy,ltype)
    if len(text[k]):
      gist.plt(text[k],llx+width+deltax,ypos-deltay,
               color=color,font=tfont,height=fontsize,tosys=0)
    ypos = ypos + dy
  if nobox:
    pass
  else:
    gist.plsys(0)
    maxlen = numpy.max(list(map(len,text)))
    c1 = (llx-deltax,lly-deltay)
    c2 = (llx + width + deltax + fontsize*points* maxlen/1.8 + deltax,
          lly + len(text)*dy)
    linesx0 = [c1[0],c1[0],c2[0],c2[0]]
    linesy0 = [c1[1],c2[1],c2[1],c1[1]]
    linesx1 = [c1[0],c2[0],c2[0],c1[0]]
    linesy1 = [c2[1],c2[1],c1[1],c1[1]]
    gist.pldj(linesx0,linesy0,linesx1,linesy1,color=color)
  gist.plsys(savesys)

def arrow(x0,y0,x1,y1,color='fg',ang=45.0,height=6,width=1.5,lc=None):
  '''Draw an arrow

  x0, y0 -- The beginning coordinate of the arrow
  x1, y1 -- Then end coordinate of the arrow.
  color --  The color of the arrowhead.  Number represents an index
            in the current palette or a negative number or a spelled
            out basic color.
  lc --     The color of the line (same as color by default).
  ang --    The angle of the arrowhead.
  height -- The height of the arrowhead in points.
  width --  The width of the arrow line in points.
  '''
  if lc is None:
    lc = color
  if type(lc) is str:
    lc = _colornum[lc]
  if type(color) is str:
    color = _colornum[color]
  vp = gist.viewport()
  plotlims = gist.limits()
  gist.limits(plotlims)
  conv_factorx = (vp[1]-vp[0]) / (plotlims[1]-plotlims[0])
  conv_factory = (vp[3]-vp[2]) / (plotlims[3]-plotlims[2])
  ang = ang*numpy.pi/180
  height = height*points
  hypot = height / numpy.cos(ang)
  difx = (x1 - x0) * conv_factorx
  dify = (y1 - y0) * conv_factory
  theta = numpy.arctan2(dify,difx) + numpy.pi
  tha = theta + ang
  thb = theta - ang
  x1a = x1 + hypot*numpy.cos(tha) / conv_factorx
  x1b = x1 + hypot*numpy.cos(thb) / conv_factorx
  y1a = y1 + hypot*numpy.sin(tha) / conv_factory
  y1b = y1 + hypot*numpy.sin(thb) / conv_factory
  gist.pldj([x0],[y0],[x1],[y1],color=lc,width=width)
  gist.plfp(numpy.array([color],numpy.uint8),[y1,y1a,y1b],[x1,x1a,x1b],[3])

def _find_and_set(d, s, default):
  value = default
  for k in d.keys():
    if s.find(k) >= 0:
      value = d[k]
      break
  return value

def _parse_type_arg(thearg,nowplotting):
  indx = nowplotting % len(_corder)
  if type(thearg) is type(''):
    tomark = 1
    thetype = _find_and_set(_types,thearg,'none')
    thecolor = _find_and_set(_colors,thearg,_colors[_corder[indx]])
    themarker = _find_and_set(_markers,thearg,None)
    if themarker is None:
      tomark = 0
      if thetype == 'none':
        thetype = 'solid'
    return (thetype, thecolor, themarker, tomark)
  else:  # no string this time
    return ('solid',_colors[_corder[indx]],'Z',0)

_GLOBAL_LINE_TYPES=[]
def _clear_global_linetype():
  for k in range(len(_GLOBAL_LINE_TYPES)):
    _GLOBAL_LINE_TYPES.pop()

def _append_global_linetype(arg):
  _GLOBAL_LINE_TYPES.append(arg)

def _minsqueeze(arr,min=1):
  # eliminate extra dimensions above min
  arr = numpy.asarray(arr)
  arr = numpy.squeeze(arr)
  n = len(arr.shape)
  if n < min:
    arr.shape = arr.shape + (1,)*(min-n)
  return arr

def plot(x,*args,**keywds):
  '''Plot one or more curves on the same graph.

        There can be a variable number of inputs which consist of pairs or
        triples.  The second variable is plotted against the first using the
        linetype specified by the optional third variable in the triple.  If
        only two plots are being compared, the x-axis does not have to be
        repeated.
  '''

  try: linewidth=float(keywds['width'])
  except KeyError: linewidth=1.0
  try: msize = float(keywds['msize'])
  except KeyError: msize=1.0
  savesys = gist.plsys()
  winnum = gist.window()
  if winnum < 0:
    gist.window(0)
  if savesys >= 0:
    gist.plsys(savesys)
  nargs = len(args)
  if nargs == 0:
    y = _minsqueeze(x)
    x = numpy.arange(0,len(y))
    if numpy.iscomplexobj(y):
      print('Warning: complex data plotting real part.')
      y = y.real
    y = numpy.where(numpy.isfinite(y),y,0)
    gist.plg(y,x,type='solid',color='blue',marks=0,width=linewidth)
    return
  y = args[0]
  argpos = 1
  nowplotting = 0
  _clear_global_linetype()
  while 1:
    try:
      thearg = args[argpos]
    except IndexError:
      thearg = 0
    thetype,thecolor,themarker,tomark = _parse_type_arg(thearg,nowplotting)
    if themarker == 'Z':  # args[argpos] was data or non-existent.
      pass
      _append_global_linetype(_rtypes[thetype]+_rcolors[thecolor])
    else:                 # args[argpos] was a string
      argpos = argpos + 1
      if tomark:
        _append_global_linetype(_rtypes[thetype]+_rcolors[thecolor]+_rmarkers[themarker])
      else:
        _append_global_linetype(_rtypes[thetype]+_rcolors[thecolor])
    if numpy.iscomplexobj(x) or numpy.iscomplexobj(y):
      print('Warning: complex data provided, using only real part.')
      x = numpy.real(x)
      y = numpy.real(y)
    y = numpy.where(numpy.isfinite(y),y,0)
    y = _minsqueeze(y)
    x = _minsqueeze(x)
    gist.plg(y,x,type=thetype,color=thecolor,marker=themarker,marks=tomark,msize=msize,width=linewidth)
    nowplotting = nowplotting + 1
    ## Argpos is pointing to the next potential triple of data.
    ## Now one of four things can happen:
    ##
    ##   1:  argpos points to data, argpos+1 is a string
    ##   2:  argpos points to data, end
    ##   3:  argpos points to data, argpos+1 is data
    ##   4:  argpos points to data, argpos+1 is data, argpos+2 is a string
    if argpos >= nargs: break      # no more data
    if argpos == nargs-1:          # this is a single data value.
      x = x
      y = args[argpos]
      argpos = argpos+1
    elif type(args[argpos+1]) is str:
      x = x
      y = args[argpos]
      argpos = argpos+1
    else:   # 3
      x = args[argpos]
      y = args[argpos+1]
      argpos = argpos+2

def matplot(x,y=None,axis=-1):
  '''Contribute documention
  '''
  if y is None:   # no axis data
    y = x
    x = numpy.arange(0,y.shape[axis])
  x,y = numpy.asarray(x), numpy.asarray(y)
  assert(len(y.shape)==2)
  assert(len(x)==y.shape[axis])
  otheraxis = (1+axis) % 2
  sliceobj = [slice(None)]*2

  _clear_global_linetype()
  for k in range(y.shape[otheraxis]):
    thiscolor = _colors[_corder[k % len(_corder)]]
    sliceobj[otheraxis] = k
    ysl = numpy.where(numpy.isfinite(y[sliceobj]),y[sliceobj],0)
    gist.plg(ysl,x,type='solid',color=thiscolor,marks=0)
    _append_global_linetype(_rcolors[thiscolor]+'-')

def palette_write(tofile,pal):
  pal = numpy.asarray(pal)
  if pal.dtype.char not in ['B','b','s','i','l']:
    raise ValueError('Palette data must be integer data.')
  palsize = pal.shape
  if len(palsize) > 2:
    raise TypeError('Input must be a 1-d or 2-d array')
  if len(palsize) == 2:
    if palsize[0] == 1 and palsize[1] > 1:
      pal = pal[0]
    if palsize[1] == 1 and palsize[0] > 1:
      pal = pal[:,0]
    palsize = pal.shape
  if len(palsize) == 1:
    pal = numpy.multiply.outer(pal,ones((3,),pal.dtype.char))
    palsize = pal.shape
  if not (palsize[1] == 3 or palsize[0] == 3):
    raise TypeError('If input is 2-d, the length of at least one dimension must be 3.')
  if palsize[0] == 3 and palsize[1] != 3:
    pal = numpy.transpose(pal)
    palsize = pal.shape
  if palsize[0] > 256:
    raise ValueError('Palettes should be no longer than 256.')
  fid = open(tofile,'w')
  fid.write('ncolors=%d\n\n#  r   g   b\n' % palsize[0])
  for k in range(palsize[0]):
    fid.write('%4d%4d%4d\n' % tuple(pal[k]))
  fid.close()

def palette_list(verbose=False):
  import glob
  try: gpath = os.environ['GISTPATH']
  except: gpath = gist.GISTPATH
  palettes = dict()
  for direc in gpath.split(':'):
    files = glob.glob1(direc,'*.gp')
    for f in files:
      name = f[:-3]
      fid = open(direc+'/'+f)
      lines = fid.readlines()
      desc=[]
      for l in lines:
        if not l.startswith('#'): continue
        if l.find('$Id')>0: continue
        if l[1:-1].replace(' ','') == 'rgb': continue
        desc.append(l[1:].strip())
      palettes[name]='; '.join(desc)
      fid.close()
  if verbose: return palettes
  else: return list(palettes.keys())

def _change_palette(pal):
  if pal is None: return
  if type(pal) is str:
    try: gist.palette('%s.gp' % pal)
    except gist.error:
      if len(pal) > 3 and pal[-2:] == 'gp':
        gist.palette(pal)
      else:
        raise ValueError('Palette %s not found.' % pal)
  else:
    data = numpy.transpose(numpy.asarray(pal))
    data = data.astype (numpy.uint8)
    # FIXME *xxx typo ????
    gist.palette(*numpy.transpose(data))
    #filename = os.path.join(_user_path,'_temp.gp')
    #palette_write(filename,data)
    #gist.palette(filename)

def matview(A,cmax=None,cmin=None,palette=None):
  '''Plot an image of a matrix.

    The orientation on the plot looks as follow:

    [[1,0], shows as pixels XO
     [0,0],                 OO
     [0,0]]                 OO
  '''
  A = numpy.asarray(A)
  if A.dtype.char in ['D','F']:
    print('Warning: complex array given, plotting magnitude.')
    A = numpy.abs(A)
  M,N = A.shape
  A = numpy.flipud(A)
  if cmax is None: cmax = A.max()
  if cmin is None: cmin = A.min()
  cmax = float(cmax)
  cmin = float(cmin)
  byteimage = gist.bytscl(A,cmin=cmin,cmax=cmax)
  _change_palette(palette)
  gist.window(style='nobox.gs')
  _current_style='nobox.gs'
  gist.pli(byteimage)
  gist.limits(square=1)

def imagesc(z,cmin=None,cmax=None,xryr=None,_style='default', palette=None,
            color='fg',colormap=None):
  '''Plot an image on axes.

  z -- The data
  cmin -- Value to map to lowest color in palette (min(z) if None)
  cmax -- Value to map to highest color in palette (max(z) if None)
  xryr -- (xmin, ymin, xmax, ymax) coordinates to print
          (0, 0, z.shape[1], z.shape[0]) if None
  _style -- A 'style-sheet' to use if desired (a default one will be used
            if 'default').  If None, then no style will be imposed.
  palette -- A string for a palette previously saved in a file (see palette_write)
             or an array specifying the red-green-blue values (2-d array N x 3) or
             gray-scale values (2-d array N x 1 or 1-d array).
  color -- The color to use for the axes.
  '''
  if xryr is None:
    xryr = (0,0,z.shape[1],z.shape[0])
  try:
    _style = None
    saveval = gist.plsys(2)
    gist.plsys(saveval)
  except:
    _style = 'default'

  if _style is not None:
    if _style == 'default':
      _style=os.path.join(_user_path,'image.gs')
      system = write_style.getsys(hticpos='below',vticpos='left',frame=1,color=color)
      fid = open(_style,'w')
      fid.write(write_style.style2string(system))
      fid.close()
    gist.window(style=_style)
    _current_style=_style
  if cmax is None:
    cmax = max(numpy.ravel(z))
  if cmin is None:
    cmin = min(numpy.ravel(z))
  cmax = float(cmax)
  cmin = float(cmin)
  byteimage = gist.bytscl(z,cmin=cmin,cmax=cmax)
  if (colormap is not None): palette=colormap
  _change_palette(palette)
  gist.pli(byteimage,xryr[0],xryr[1],xryr[2],xryr[3])

def figure(n=None,style=os.path.join(_user_path,'currstyle.gs'), color='fg', frame=0, labelsize=14, labelfont='helvetica',aspect=1.618,land=0):
  global _figures
  if (aspect < 0.1) or (aspect > 10):
    aspect = 1.618
  if isinstance(color, str):
    color = _colornum[color]
  fid = open(style,'w')
  syst = write_style.getsys(color=color,frame=frame,
                           labelsize=labelsize,font=labelfont)
  if land:
    cntr = (5.5*inches,4.25*inches)  # horizontal, vertical
  else:
    cntr = (4.25*inches,5.5*inches)
  height = 4.25*inches
  width = aspect*height
  syst['viewport'] = [cntr[0]-width/2.0,cntr[0]+width/2.0,cntr[1]-height/2.0,cntr[1]+height/2.0]
  fid.write(write_style.style2string(syst,landscape=land))
  fid.close()
  if n is None:
    winnum = gist.window(style=style,width=int(width*1.25/inches*_dpi),height=int(height*1.4/inches*_dpi))
    if winnum < 0:
      gist.window(style=style,width=int(width*1.25/inches*_dpi),height=int(height*1.4/inches*_dpi))
  else:
    gist.window(n,style=style,width=int(width*1.25/inches*_dpi),height=int(height*1.4/inches*_dpi))
    _current_style = style

def _add_color(system, color, frame=0):
  try:
    system['ticks']['horiz']['tickStyle'] = {'color':color}
    system['ticks']['horiz']['gridStyle'] = {'color':color}
  except KeyError:
    system['ticks']['horiz'] = {}
    system['ticks']['horiz']['tickStyle'] = {'color':color}
    system['ticks']['horiz']['gridStyle'] = {'color':color}

  try:
    text = system['ticks']['horiz']['textStyle']
  except KeyError:
    system['ticks']['horiz']['textStyle'] = {}
  text = system['ticks']['horiz']['textStyle']
  text['color'] = color

  try:
    system['ticks']['vert']['tickStyle'] = {'color':color}
    system['ticks']['vert']['gridStyle'] = {'color':color}
  except KeyError:
    system['ticks']['vert'] = {}
    system['ticks']['vert']['tickStyle'] = {'color':color}
    system['ticks']['vert']['gridStyle'] = {'color':color}

  try:
    text = system['ticks']['vert']['textStyle']
  except KeyError:
    system['ticks']['vert']['textStyle'] = {}
  text = system['ticks']['vert']['textStyle']
  text['color'] = color

  system['ticks']['frame'] = frame
  system['ticks']['frameStyle'] = {'color':color}


def _chng_font(system, font, height):
  if height is None:
    height=14
  if font is None:
    font = 'helvetica'
  num = write_style.tfont[font]
  system['ticks'] = {
      'horiz':{
      'textStyle':{'font':num,
                   'height':height*points}
      },
      'vert':{
      'textStyle':{'font':num,
                   'height':height*points}
      }
  }

def _remove_ticks(system):
  system['ticks'] = { 'horiz': {'flags':0}, 'vert': {'flags':0}, }

def subplot(Numy,Numx,win=0,pw=None,ph=None,hsep=100,vsep=100,color='fg',frame=0,fontsize=8,font=None,ticks=1,land=1,wait=0,**kwd):
  # Use gist.plsys to change coordinate systems

  # all inputs (except fontsize) given as pixels, gist wants
  #  things in normalized device
  #  coordinate.  Window is brought up with center of window at
  #  center of 8.5 x 11 inch page: in landscape mode (5.25, 4.25)
  #  or at position (4.25,6.75) for portrait mode

  # kwd for window (... , parent=None,xpos=None,ypos=None)

  # fixme:
  #    subplot() does not handle 'contourlegend' well:
  # try
  #    gist.subplot(3,3)
  #    zoby=gist.get_style()
  #    ... zoby['contourlegend']['textStyle']
  #    gist.set_style(zoby)
  # maybe include the fix here and force things ??
  #    zoby['contourlegend']['textStyle'] = zoby['legend']['textStyle']


  msg = 1
  if pw is None:
    pw = Numx*300
    msg = 0
  if ph is None:
    ph = Numy*300
    msg = 0
  if land:
    maxwidth=min(_maxwidth,11*_dpi)
    maxheight=min(_maxheight,8.5*_dpi)
  else:
    maxwidth=min(_maxwidth,8.5*_dpi)
    maxheight=min(_maxheight,11*_dpi)

  printit = 0
  if ph > maxheight:
    ph = maxheight
    printit = 1
  if pw > maxwidth:
    pw = maxwidth
    printit = 1

  if _dpi != 100:
    fontsize = 12
  conv = inches *1.0 / _dpi  # multiply by this factor to convert pixels to NDC

  if printit and msg:
    message = 'Warning: Requested height and width too large.\n'
    message +='Changing to %d x %d' % (pw,ph)
    print(message)

  # Now we've got a suitable height and width

  if land:
    cntr = numpy.array([5.5,4.25])*_dpi  # landscape
  else:
    if sys.platform == 'win32':
      cntr = numpy.array([4.25,6.75])*_dpi  # portrait
    else:
      cntr = numpy.array([4.25,5.5])*_dpi

  Yspace = ph/float(Numy)*conv
  Xspace = pw/float(Numx)*conv

  hsep = hsep * conv
  vsep = vsep * conv
  ytop = (cntr[1]+ph/2.0)*conv
  xleft = (cntr[0]-pw/2.0)*conv

  if type(color) is str:
    color = _colornum[color]
  systems=[]
  ind = -1
  for nY in range(Numy):
    ystart = ytop - (nY+1)*Yspace
    for nX in range(Numx):
      xstart = xleft + nX*Xspace
      systems.append({})
      systems[-1]['viewport'] = [xstart+hsep/2.0,xstart+Xspace-hsep/2.0,ystart+vsep/2.0,ystart+Yspace-vsep/2.0]
      if font is not None or fontsize is not None:
        _chng_font(systems[-1],font,fontsize)
      if color != -3 or frame != 0:
        _add_color(systems[-1],color,frame=frame)
      if ticks != 1:
        _remove_ticks(systems[-1])
  _current_style=os.path.join(_user_path,'subplot%s.gs' % win)
  fid = open(_current_style,'w')
  fid.write(write_style.style2string(systems,landscape=land))
  fid.close()
  gist.winkill(win)
  gist.window(win,style=_current_style,width=int(pw),height=int(ph),wait=wait,**kwd)

def imagesc_cb(z,cmin=None,cmax=None,xryr=None,_style='default',
               zlabel=None,font='helvetica',fontsize=16,color='fg',
               palette=None):
  '''Plot an image on axes with a colorbar on the side.

  z -- The data
  cmin -- Value to map to lowest color in palette (min(z) if None)
  cmax -- Value to map to highest color in palette (max(z) if None)
  xryr -- (xmin, ymin, xmax, ymax) coordinates to print
          (0, 0, z.shape[1], z.shape[0]) if None
  _style -- A 'style-sheet' to use if desired (a default one will be used
            if 'default').  If None, then no style will be imposed.
  palette -- A string for a palette previously saved in a file (see palette_write)
             or an array specifying the red-green-blue values (2-d array N x 3) or
             gray-scale values (2-d array N x 1 or 1-d array).
  zlabel -- The label to attach to the colorbar (font, fontsize, and color
            match this).
  color -- The color to use for the ticks and frame.
  '''

  if xryr is None:
    xryr = (0,0,z.shape[1],z.shape[0])

  if _style is not None:
    if _style == 'default':
      _style=os.path.join(_user_path,'colorbar.gs')
      system = write_style.getsys(hticpos='below',vticpos='left',frame=1,color=color)
      fid = open(_style,'w')
      fid.write(write_style.style2string(system))
      fid.close()
    gist.window(style=_style)
    _current_style=_style
  cmax = float(cmax or max(numpy.ravel(z)))
  cmin = float(cmin or min(numpy.ravel(z)))

  _change_palette(palette)

  byteimage = gist.bytscl(z,cmin=cmin,cmax=cmax)
  gist.pli(byteimage,xryr[0],xryr[1],xryr[2],xryr[3])
  colorbar(cmin,cmax,ncol=240,zlabel=zlabel,font=font,fontsize=fontsize,color=color)

def stem(y, x=None, linetype='b-', mtype='mo', shift=0.013):
  '''Draw a stem plot
     
     o   o
     |   | o o
     | o | | |
    _|_|_|_|_|_

     y,x --      data points
     linetype -- type,color,marker,mark for lines
     mtype --    type,color,marker,mark for marker
  
     EXAMPLE: stem(np.random.rand(10))

     SEE ALSO: stairplot, barplot
  '''
  y0 = numpy.zeros(len(y),y.dtype.char)
  y1 = y
  x = x or numpy.arange(len(y))
  thetype,thecolor,themarker,tomark = _parse_type_arg(linetype,0)
  lcolor = thecolor
  gist.pldj(x, y0, x, y1, color=thecolor, type=thetype)
  thetype,thecolor,themarker,tomark = _parse_type_arg(mtype,0)
  if themarker not in ['o','x','.','*']:
    themarker = 'o'
  y = numpy.where(numpy.isfinite(y),y,0)
  gist.plg(y,x,color=thecolor,marker=themarker,type='none')
  gist.plg(numpy.zeros(len(x)),x,color=lcolor,marks=0)
  gist.limits()
  lims = gist.limits()
  newlims = [None]*4
  vp = gist.viewport()
  factor1 = vp[1] - vp[0]
  factor2 = vp[3] - vp[2]
  cfactx = factor1 / (lims[1] - lims[0])
  cfacty = factor2 / (lims[3] - lims[2])
  d1 = shift / cfactx
  d2 = shift / cfacty
  newlims[0] = lims[0] - d1
  newlims[1] = lims[1] + d1
  newlims[2] = lims[2] - d2
  newlims[3] = lims[3] + d2
  gist.limits(*newlims)

def makeleg(leg,pos,lenx,dd,theight=12):
  '''Contribute documention'''
  # Place legend
  x0,y0 = pos
  dx,dy = dd
  for k in range(len(leg['txt'])):
    gist.plg([y0+k*dy]*2,[x0,x0+lenx],type=leg['sym'][k][1],marks=0)
    if leg['sym'][k][0] is not None:
      gist.plg([y0+k*dy]*2,[x0,x0+lenx],type='none',marks=1,marker=leg['sym'][k][0])
    if leg['txt'][k] != '':
      gist.plt(leg['txt'][k],x0+lenx+dx,y0+k*dy,height=theight,tosys=1,justify='LH')

def twoplane(DATA,slice1,slice2,dx=[1,1,1],cmin=None,cmax=None,xb=None,xe=None,
             xlab='',ylab='',zlab='',clab='',titl='',
             totalheight=0.5,space=0.02, medfilt=5,
             font='helvetica',fontsize=16,color='fg',lcolor='bg',
             fcolor='fg',  cb=1, line=1, palette=None):
  '''Visualize a 3d volume as a two connected slices.
  
  The slices are given in the 2-tuple slice1 and slice2.

  These give the dimension and corresponding slice numbers to plot.
  The unchosen slice is the common dimension in the images.

  twoplane(img3d,(0,12),(2,60)) plots two images with a common 'x'-axis
  as the first dimension.  The lower plot is img3d[12,:,:] with a line
  through row 60 corresponding to the slice transpose(img3d[:,:,60])
  plotted above this first plot.
  '''
  if xb is None:
    xb = [0,0,0]
  if xe is None:
    xe = DATA.shape
  # get two image slices
  # make special style file so that pixels are square
  getdx = numpy.array([1,1,1])
  imgsl1 = [slice(None,None),slice(None,None),slice(None,None)]
  imgsl1[slice1[0]] = slice1[1]
  img1 = DATA[imgsl1]
  getdx1 = getdx.__copy__()
  getdx1[slice1[0]] = 0
  dx1 = numpy.compress(getdx1,dx,axis=-1)
  xb1 = numpy.compress(getdx1,xb,axis=-1)
  xe1 = numpy.compress(getdx1,xe,axis=-1)

  imgsl2 = [slice(None,None),slice(None,None),slice(None,None)]
  imgsl2[slice2[0]] = slice2[1]
  img2 = DATA[imgsl2]
  getdx2 = getdx.__copy__()
  getdx2[slice2[0]] = 0
  dx2 = numpy.compress(getdx2,dx,axis=-1)
  xb2 = numpy.compress(getdx2,xb,axis=-1)
  xe2 = numpy.compress(getdx2,xe,axis=-1)

  if (slice1[0] == slice2[0]):
    raise ValueError('Same slice dimension..')

  for k in range(3):
    if k not in [slice1[0],slice2[0]]:
      samedim = k
      break
  if samedim == 2:
    pass
  elif samedim == 1:
    if samedim > slice1[0]:
      img1 = numpy.transpose(img1)
      dx1 = dx1[::-1]
      xb1 = xb1[::-1]
      xe1 = xe1[::-1]
    if samedim > slice2[0]:
      img2 = numpy.transpose(img2)
      dx2 = dx2[::-1]
      xb2 = xb2[::-1]
      xe2 = xe2[::-1]
  else:
    img1 = numpy.transpose(img1)
    dx1 = dx1[::-1]
    xb1 = xb1[::-1]
    xe1 = xe1[::-1]
    img2 = numpy.transpose(img2)
    dx2 = dx2[::-1]
    xb2 = xb2[::-1]
    xe2 = xe2[::-1]

  assert(img1.shape[1] == img2.shape[1])
  units = totalheight - space
  totaldist = img1.shape[0]*dx1[0] + img2.shape[0]*dx2[0]
  convfactor = units / float(totaldist)
  height1 = img1.shape[0]*dx1[0] * convfactor
  xwidth = img1.shape[1]*dx1[1]*convfactor
  if xwidth > 0.6:
    rescale = 0.6 / xwidth
    xwidth = rescale * xwidth
    height1 = rescale * height1
    totalheight = totalheight * rescale
    print(xwidth, height1)
  else:
    print(xwidth)
  ystart = 0.5 - totalheight / 2
  ypos1 = [ystart, ystart+height1]
  ypos2 = [ystart+height1+space,ystart+totalheight]
  xpos = [0.395-xwidth/2.0, 0.395+xwidth/2.0]

  systems = []
  system = write_style.getsys(hticpos='', vticpos='left')
  system['viewport'] = [xpos[0],xpos[1],ypos2[0],ypos2[1]]
  if fcolor not in ['black',None]:
    _add_color(system, _colornum[color])
  systems.append(system)
  system = write_style.getsys(hticpos='below', vticpos='left')
  system['viewport'] = [xpos[0],xpos[1],ypos1[0],ypos1[1]]
  if fcolor not in ['black',None]:
    _add_color(system, _colornum[color])
  systems.append(system)

  the_style = os.path.join(_user_path,'two-plane.gs')
  write_style.writestyle(the_style,systems)

  gist.window(style=the_style)
  _current_style = the_style
  _change_palette(palette)
  gist.plsys(1)
  if medfilt > 1:
    import scipy.signal
    img1 = scipy.signal.medfilt(img1,[medfilt,medfilt])
    img2 = scipy.signal.medfilt(img2,[medfilt,medfilt])
  if cmax is None:
    cmax = max(max(numpy.ravel(img1)),max(numpy.ravel(img2)))
  if cmin is None:
    cmin = min(min(numpy.ravel(img1)),min(numpy.ravel(img2)))
  cmax = float(cmax)
  cmin = float(cmin)
  byteimage = gist.bytscl(img2,cmin=cmin,cmax=cmax)
  gist.pli(byteimage,xb2[1],xb2[0],xe2[1],xe2[0])
  gist.xytitles(ytitle=zlab,color=color)
  if titl != '':
    pltitle(titl,color=color)
  if line:
    xstart = xb2[1]
    xstop = xe2[1]
    yval = slice1[1]*(xe2[0] - xb2[0])/(img2.shape[0]) + xb2[0]
    gist.pldj([xstart],[yval],[xstop],[yval],type='dash',width=2,color='bg')

  gist.plsys(2)
  gist.xytitles(xlab,ylab,color=color)
  byteimage = gist.bytscl(img1,cmin=cmin,cmax=cmax)
  gist.pli(byteimage,xb1[1],xb1[0],xe1[1],xe1[0])
  if line:
    xstart = xb1[1]
    xstop = xe1[1]
    yval = slice2[1]*(xe1[0] - xb1[0])/(img1.shape[0]) + xb1[0]
    gist.pldj([xstart],[yval],[xstop],[yval],type='dash',width=2,color='bg')

  if cb:
    colorbar(cmin,cmax,ncol=240,zlabel=clab,font=font,fontsize=fontsize,color=color,ymin=ystart,ymax=ystart+totalheight,xmin0=xpos[1]+0.02,xmax0=xpos[1]+0.04)

def surf(z,x=None,y=None,win=None,shade=0,edges=1,edge_color='fg',phi=-45.0,
         theta=30.0,zscale=1.0,palette=None,gnomon=0):
  '''Plot a three-dimensional wire-frame (surface): z=f(x,y)
  '''
  if win is None:
    pl3d.window3()
  else:
    pl3d.window3(win)
  pl3d.set_draw3_(0)
  phi0 = phi*numpy.pi/180.0
  theta0 = theta*numpy.pi/180.0
  pl3d.orient3(phi=phi0,theta=theta0)
  pl3d.light3()
  _change_palette(palette)
  sz = numpy.shape(z)
  if len(sz) != 2:
    raise ValueError('Input must be a 2-d array --- a surface.')
  N,M = sz
  if x is None:
    x = numpy.arange(0,N)
  if y is None:
    y = numpy.arange(0,M)
  x = numpy.squeeze(x)
  y = numpy.squeeze(y)
  if (len(numpy.shape(x)) == 1):
    x = x[:,newaxis]*numpy.ones((1,M))
  if (len(numpy.shape(y)) == 1):
    y = numpy.ones((N,1))*y[newaxis,:]
  plwf.plwf(z,y,x,shade=shade,edges=edges,ecolor=edge_color,scale=zscale)
  lims = pl3d.draw3(1)
  gist.limits(lims[0],lims[1],lims[2],lims[3])
  pl3d.gnomon(gnomon)

def plsurf(z,x=None,y=None,win=None,shade=0,edges=1,edge_color='fg',phi=-45.0,
         theta=30.0,zscale=1.0,palette=None,gnomon=0,animate=False,limits=True, ireg=None):
  '''Plot a 3-D wire-frame surface z=f(x,y)
  '''
  if win is None:
    pass
    #pl3d.window3()
  else:
    pl3d.window3(win)
  pl3d.set_draw3_(0)
  phi0 = phi*numpy.pi/180.0
  theta0 = theta*numpy.pi/180.0
  pl3d.orient3(phi=phi0,theta=theta0)
  pl3d.light3()
  _change_palette(palette)
  sz = numpy.shape(z)
  if len(sz) != 2:
    raise ValueError('Input must be a 2-d array --- a surface.')
  N,M = sz
  if x is None:
    x = numpy.arange(0,N)
  if y is None:
    y = numpy.arange(0,M)
  x = numpy.squeeze(x)
  y = numpy.squeeze(y)
  if (len(numpy.shape(x)) == 1):
    x = x[:,newaxis]*numpy.ones((1,M))
  if (len(numpy.shape(y)) == 1):
    y = numpy.ones((N,1))*y[newaxis,:]
  plwf.plwf(z,y,x,shade=shade,edges=edges,ecolor=edge_color,scale=zscale, ireg=ireg)
  # if animate, the application is responsible to fma
  lims = pl3d.draw3(not animate)
  if limits:
    gist.limits(lims[0],lims[1],lims[2],lims[3])
  pl3d.gnomon(gnomon)

def scalexy(xscale,yscale=None):
  '''Expand the limits by a certain scale factor. 
  '''
  if yscale is None:
    yscale = xscale
  xmin, xmax, ymin, ymax, flag = gist.limits()
  dx = (xmax-xmin)*(xscale-1.0)/2.0
  dy = (ymax-ymin)*(yscale-1.0)/2.0
  gist.limits(xmin-dx,xmax+dx,ymin-dy,ymax+dy)

def axes(type='b|'):
  '''Do axes'''
  vals = gist.limits()
  v0,v1,v2,v3 = vals[:4]
  x0 = numpy.r_[v0:v1:5j]
  y0 = 5*[0]
  x1 = 5*[0]
  y1 = numpy.r_[v2:v3:5j]
  plot(x0,y0,type,x1,y1,type,hold=1)
  gist.limits(v0,v1,v2,v3)


def bode(w,H,win=0,frame=0,lcolor='blue',color='bg',tcolor='fg',freq='rad'):
  '''Plot a bode plot of the transfer function H as a function of w.
  '''

  if type(tcolor) is str: tcolor=_colornum[tcolor]

  if freq == 'Hz':
    w = w /2.0 / numpy.pi
  subplot(2,1,win,hsep=120,frame=frame,color=color)
  gist.plsys(1)
  gist.plg(20*numpy.log10(abs(H)),w,type='solid',color=lcolor,marks=0)
  gist.logxy(1,0)
  gist.gridxy(1,1)
  if freq == 'Hz':
    gist.xytitles('Frequency (Hz)',color=tcolor,delta=(0,-0.005))
  else:
    xytitles('Frequency (rad/s)',color=tcolor,delta=(0,-0.005))
  xytitles(ytitle='Magnitude (dB)',color=tcolor,delta=(-0.005,0))
  pltitle('Bode Plot',color=tcolor)
  gist.plsys(2)
  gist.plg(180/numpy.pi*numpy.unwrap(numpy.angle(H)),w,type='solid',color=lcolor,marks=0)
  gist.logxy(1,0)
  gist.gridxy(1,1)
  if freq == 'Hz':
    gist.xytitles('Frequency (Hz)',color=tcolor,delta=(0,-0.005))
  else:
    gist.xytitles('Frequency (rad/s)',color=tcolor,delta=(0,-0.005))
  xytitles(ytitle='Phase (deg.)',color=tcolor,delta=(-0.005,0))

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

def stairplot(a,*arg,**kwd):
  '''Draw a stairplot.
           _
       _  | |_
      | |_|   |_
     _|         |_

     SEE ALSO: stem, barplot
  '''
  if type(a)==numpy.ndarray and len(a.shape)==2:
    xs=a[:,0]
    ys=a[:,1]
  else:
    xs = numpy.arange(len(a))
    ys = a

  gist.pldj(xs[:-1],ys[:-1],xs[1:],ys[:-1],*arg,**kwd)
  gist.pldj(xs[1:],ys[:-1],xs[1:],ys[1:],*arg,**kwd)
  #
  gist.plg((ys[-1],ys[-1]),(xs[-1],2*xs[-1]-xs[-2]),*arg,**kwd)

  #n=len(a)
  #gist.pldj(numpy.arange(n-1)+1,a[:-1],numpy.arange(n-1)+2,a[:-1],*arg,**kwd)
  #gist.pldj(numpy.arange(n-1)+2,a[0:-1],numpy.arange(n-1)+2,a[1:],*arg,**kwd)

def crosshair(x,y,szx=None,szy=None,*arg,**kwd):
  '''Draws a field of crosshair

        x,y     -- coordinate of the center(s)
        szx,szy -- size(s) of the crosshair

     EXAMPLE:
        crosshair(0, 0, 1)
        crosshair([0,1],[0,1], 0.2)
        crosshair(np.arange(10),np.arange(10),np.arange(10),np.arange(10))

     SEE ALSO: pldj
  '''
  x,y = [numpy.array([o]) for o in (x,y)]
  if szx==None:
    _szx=(x.max()-x.min())/ 100.
  else:
    _szx=numpy.array(szx)
  if szy==None:
    if szx==None:
      _szy=(y.max()-y.min())/ 100.
    else:
      _szy=_szx
  else:
    _szy=numpy.array([szy])

  gist.pldj(x+_szx,y,x-_szx,y,*arg,**kwd)
  gist.pldj(x,y+_szy,x,y-_szy,*arg,**kwd)

def pyg_once():
  '''Trigger an update inside the gist event loop.

     Use to integrate gist within a GUI toolkit.

     For finer granulatiy, use pyg_pending (flush gist event)
     and pyg_idler (force a redraw).

     EXAMPLE:

       def gtk_gist_pending (*args):
         # pyg_once equivalent
         gist.pyg_pending() # flush gist event queue (mouse events, etc.)
         gist.pyg_idler()   # force gist redraw
         return True

       def gtk_gist_connect(dis, fd):
         if dis == 0:
           # listen for gist events
           glib.io_add_watch(fd,glib.IO_IN,gtk_gist_pending,None)
         else:
           # stop listening
           pass

       def gtk_gist_keyhandle(msg):
         print 'gtk_gist_keyhandler', msg

       gist.pyg_register(gtk_gist_connect,gtk_gist_keyhandle)

     NOTE: for fast animation in animate(1), it is best to only
     invoke gist.pyg_pending() on gtk_gist_onpending, and force
     gist.pyg_idler within the gist.fma() loop.

     SEE ALSO: pyg_pending, pyg_idler, pyg_register
         ALSO: pyg_inputhook, pyg_inputunhook, pyg_unhook
  '''
  gist.pyg_pending() # Handle any new events
  gist.pyg_idler()   # Redraw window after changes from events



def box(x,y,u,v=None,color='fg',width=1,ltype='-',center=False,*args,**kwd):
  '''Draw a box, or field of boxes.

     center
        x,y -- center coordinates
        u   -- width
        v   -- height. If not specified, draw square box(es).
     
     not center
        x,y -- bottom left corner
        u,v -- top right corner


        ltype -- '-'  solid
                 '|'  dash
                 ':'  dot
                 '-.' dashdot
                 '-:' dashdotdot
     EXAMPLE:
        box(0,1,2,3)
        box([0,10],[1,11],[2,12],[3,13])
        box([0,10],[1,11],[5,10],center=True)

     SEE ALSO: pldj
  '''
  if type(color) is str: color=_colornum[color]
  linetype = _types[ltype]
  if center:
    if v is None: v=u
    cx,cy,w,h=[numpy.array(o) for o in (x,y,u,v)]
    w2=w/2.
    h2=h/2.
    x0=(cx+w2,cx-w2,cx-w2,cx+w2)
    y0=(cy+h2,cy+h2,cy-h2,cy-h2)
    x1=(cx-w2,cx-w2,cx+w2,cx+w2)
    y1=(cy+h2,cy-h2,cy-h2,cy+h2)
  else:
    x0=(x,u,u,x)
    y0=(y,y,v,v)
    x1=(u,u,x,x)
    y1=(y,v,v,y)

#  boxx1=numpy.array([x,   x+w,  x+w,  x     ])
#  boxy1=numpy.array([y,   y,    y+h,  y+h   ])
#  boxx2=numpy.array([x+w, x+w,  x,    x     ])
#  boxy2=numpy.array([y,   y+h,  y+h,  y     ])
#  gist.pldj(boxx1,boxy1,boxx2,boxy2,*args,**kwd)



  gist.pldj(x0,y0,x1,y1,color=color,type=linetype,
            width=width,*args,**kwd)


def winscape(*args, **kwd):
  '''Open a large landscape window.
  '''
  gist.window(*args,width=900,dpi=120,style='winscape.gs',**kwd)
  gist.pldefault(height=10) # more dpi, smaller fonts (axis_t.height = 0.010 ~> font 7.7)

def palette_inspect(p=None):
  '''Inspect current or designated palette inside a new window.
  '''
  for i in range(7):
    if not gist.win_exists(i): break
  gist.window(i)
  if (p): gist.palette(p)
  gist.fma()
  c=0
  for i in range(10):
    for j in range(36):
      if c>255: break
      gist.plt('%03d'%c,0.767-0.129-i*0.030,0.372+j*0.015, color=c, height=11)
      c+=1
  # negative color = bg,fg,8primary, then the pallette      0-255
  c=0
  for i in range(10):
    for j in range(36):
      if c>255: break
      gist.plt('%04d'%-c,0.129+i*0.030,0.372+j*0.015, color=-c, height=11)
      c+=1

def movie (draw_func, min_interframe = 0.0, lims = None) :

   '''Run a movie based on the given DRAW_FUNC function.  The movie
     stops when the DRAW_FUNC function returns zero.

     If MIN_INTERFRAME is specified, a pause will be added as
     necessary to slow down the movie.  MIN_INTERFRAME is a time
     in seconds (default 0).

     If every frame of your movie has the same limits, use the
     limits command to fix the limits before you call movie.
   '''

   gist.window (wait = 1, style = 'nobox.gs') # make sure window is ready to draw
   gist.fma ()
   gist.animate (1)
   i = 0
   while True:
      more = draw_func(i)
      if lims != None:
         gist.limits(*lims[:4])
      else:
         gist.limits(square=1)
      gist.fma()
      if min_interframe: gist.pause(min_interframe*1000.)
      i += 1
      if not more: break
   gist.animate (0)

def _nice_levels (z, n = 8) :
    '''Find approximately n 'nice values'
    between min(z) and max(z) for axis labels.
    '''
    zmax = numpy.max(z)
    zmin = numpy.min(z)
    finest = numpy.abs (zmax - zmin) / float (n)
    unit = 10. ** numpy.floor (numpy.log10 (finest))
    finest = finest / unit
    if finest > 5.0 :
        finest = 10.
    elif finest > 2. :
        finest = 5.
    elif finest > 1. :
        finest = 2.
    unit = unit * finest
    cmin = unit * numpy.ceil (zmin / unit)
    if (numpy.abs (cmin - zmin) < 0.01 * unit) :
        cmin = cmin + unit
    cmax = unit * numpy.floor (zmax / unit)
    if (numpy.abs (cmax - zmax) < 0.01 * unit) :
        cmax = cmax - unit
    n = int ( ( (cmax - cmin) / unit + 0.5) + 1)
    levs = numpy.linspace (cmin, cmax, n)
    _list = numpy.nonzero(numpy.less (numpy.abs (levs), 0.1 * unit))[0]
    if len (_list) > 0 :
        array_set (levs, _list, 0.0)
    return levs

def colorbar (minz, maxz, ncol = 255, ymax=0.85, ymin=0.44, xmin0=0.62, xmax0=0.64, zlabel=None, fontsize=12, font='helvetica', color='fg') :
    '''Plot a color bar to the right of the plot square
       labelled by the z values from minz to maxz.

    EXAMPLE:
        plf (z,y,x)
        colorbar (z.min(), z.max())

        plf (z, y, x, cmin = MINZ, cmax = MAXZ)
        colorbar (MINZ, MAXZ)

    '''
    # colorbar & box
    plsys (0)
    data=numpy.linspace(0, 1, ncol)
    pli(data.reshape((-1, 1)), xmin0, ymin, xmax0, ymax)
    pldj((xmin0, xmin0),(ymin, ymax),(xmax0, xmax0),(ymin, ymax),color=color)
    
    # scale text
    plsys (1)
    levs = _nice_levels(numpy.array([minz, maxz]))
    scales = ['% .5g' % l for l in levs]
    ys = ymin + (ymax - ymin) * (levs - minz) / (maxz - minz)
    for s,y in zip(scales,ys):
        plt(s, xmax0+0.005, y, color=color) # labels
    xmin = numpy.zeros_like(levs)+ xmin0
    xmax = numpy.zeros_like(levs) + xmax0 + 0.005
    plsys(0)
    pldj(xmin, ys, xmax, ys, color=color) # ticks
    # max and min on bar
    plsys(1)
    xmid = (xmin0 + xmax0)/2.0
    if max(ys) > ymax-0.01:
        plt ('% .5g' % maxz, xmid, ymax + 0.020, justify='CA', color=color)
    else :
        plt ('% .5g' % maxz, xmid, ymax + 0.005, justify='CA', color=color)
    plt ('% .5g' % minz, xmid, ymin - 0.0025, justify = 'CT', color=color)
    if zlabel:
        ymidpt = (ymax+ymin)/2.0
        plt(zlabel, xmin0, ymidpt, color=color,font=font, justify='CB', height=fontsize, orient=1)


