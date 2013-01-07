#! /usr/bin/env python
# Copyright (c) 1996, 1997, The Regents of the University of California.
# All rights reserved.  See Legal.htm for full text and disclaimer.
#  ---------------------------------------------------------------------
# 
#  NAME:    demolow.py
#  CHANGES:
#  11/08/04 mdh Fix typo on line 124 and 132. First arg should be 6.
#               Add font test #25 and a better histogram demo.
#  04/07/03 llc Add plh test.
#  03/14/03 llc Add test for plfp (test 23).
#  12/03/01 llc Correct titles for Test 12 and Test 18.  
#               Add pltitle for Test 12.
#
#  ---------------------------------------------------------------------

import time
from numpy import *
from ..gistY import *
from ..gistC import *

# low.run()
# Move the mouse to the graphcis window in-between test

__all__=['run']

def paws () :
  try: raw_input ('<Return> to continue ...\n')
  except: input ('<Return> to continue ...\n')

def grtest():

  print('\n\n         Pygist Comprehensive Graphics Test\n')
  print('This test suite is similar, but not exactly the same as yorick grtest\n')
  print('Each frame will be described at the terminal.')
  print('Compare what you see with the description, then')
  print('hit <RETURN> to see the next test, or q <RETURN> to quit.\n')
  paws()
  pldefault(marks=1, width=0, type=1, style='work.gs', dpi=100)
  winkill(0)
  print('Test 1:  Commands: window (0, wait=1, dpi=75); plg([0, 1])')
  window (0, wait=1, dpi=75)
  plg([0, 1])
  print('A small (75 dpi) window with line marked A from (1,0) to (2,1).')
  paws()
  winkill(0)

  print('Test 2:  Commands: plg([0,1])')
  plg([0,1])
  print('A large (100 dpi) window with line marked A from (1,0) to (2,1).')
  paws()
  unzoom()

  print('Test 3:  Commands: plg([1, 0])')
  plg([1, 0])
  print('Added line marked B from (1,1) to (2,0) to previous plot.')
  paws()
  unzoom()

  print('Test 4:  Commands: logxy(1, 0)')
  logxy(1, 0)
  print('X axis now a log scale.')
  paws()
  unzoom()

  print('Test 5:  Commands: logxy(0, 0)')
  logxy(0, 0)
  print('X axis back to linear scale.')
  paws()
  unzoom()

  print('Test 6:  Commands: limits(1.2, 1.8, 0.2, 0.8)')
  limits(1.2, 1.8, 0.2, 0.8)
  print('Limits changed to 1.2<x<1.8, 0.2<y<0.8.')
  paws()
  unzoom()

  ylimits(0.4, 0.6)
  print('Test 7:  Commands: ylimits(0.4, 0.6)')
  print('Limits changed to 1.2<x<1.8, 0.4<y<0.6.')
  paws()
  unzoom()

  limits()
  print('Test 8:  Commands: limits')
  print('Limits back to extreme values (1,0) to (2,1).')
  paws()
  unzoom()

  fma()
  x = 10*pi*arange(200.0)/199.0
  plg(sin(x), x)
  print('Test 9:  Commands: fma(); plg(sin(x), x)')
  print('where x = 10*pi*arange(200.0)/199.0')
  print('Five cycles of a sine wave on a new frame.')
  print('Before you continue, try clicking with the mouse buttons:')
  print('Left button zooms in, right button zooms out, middle no zoom')
  print('In each case, the point where you press the mouse button will')
  print('be translated to the point where you release the mouse button.')
  print('To zoom one axis only, click over the tick marks on that axis.')
  paws()
  unzoom()

  pledit(marks=0, width=6, type='dash')
  print('Test 10  Commands: pledit(marks=0, width=6, type=\'dash\')')
  print('Marker A on sine curve disappears, curve becomes bold dashed.')
  paws()
  unzoom()

  fma()
  x = 2*pi*arange(200.)/199.0
  for i in range(1,7):
    r = 0.5*i - (5-0.5*i)*cos(x)
    s = 'curve [' + repr(i) + ']'
    plg( r*sin(x), r*cos(x), marks=0, color=-4-i, legend = s)
  print('Test 11:  Commands: plg(r*sin(x), r*cos(x), color=-4-i)')
  print('A set of nested cardioids in the primary and secondary colors.')
  paws()
  unzoom()

  pltitle ( 'Cardioids' )
  plt ('Colored Nested Cardioids', -2.0, -3.0, orient = 1, opaque = 1, \
  tosys = 1, legend = 'Some text')
  plq()
  print('Test 12:  Commands: pltitle(\'Cardioids\'); \
  plt(\'Colored nested cardioids\',-2.,-3.,orient=1,opaque=1,tosys=1); plq()')
  print('Adds the title above the upper tick marks.')
  print('Also prints legends for the six curves at the terminal (plq).')
  paws()
  unzoom()

  print('Test 13:  Commands: pledit(color=\'fg\', type=0, marker=i)')
  for i in range(1,6): pledit(i, color='fg', type=0, marker=i)
  pledit(6, color='fg', type=0, marker='A')
  print('Changes the colors to foreground, types to no lines.')
  print('Markers are point, plus, asterisk, O, X, A.')
  paws()
  unzoom()

  print('Test 14:  Commands: pledit(marks=0, type=i)')
  for i in range(1,6): pledit(i, marks=0, type=i)
  pledit(6, color='fg', type=1, width=4)
  print('Changes line types to solid, dash, dot, dashdot, dashdotdot.')
  print('Outermost cardioid becomes a thick, solid line.')
  paws()
  unzoom()

  fma()
  limits()
  x = a3(-1, 1, 26)
  y = transpose (x)
  z = x+1j*y
  z = 5.*z/(5.+z*z)
  xx = z.real
  yy = z.imag
  print('Test 15:  Commands: plm(y, x)')
  print('Quadrilateral mesh -- round with bites out of its sides.')
  plm (yy, xx)
  paws()
  fma()
  unzoom()

  print('Test 16:  Commands: plmesh ( y, x ); plv(v, u, y, x)')
  plmesh(yy, xx)
  plv(x+.5, y-.5)
  print('Velocity vectors.  Try zooming and panning with mouse.')
  paws()
  fma()
  unzoom()

  print('Test 17:  Commands: plfc(.); plc(.); plm(y,x, boundary=1, type=2)')
  ireg = ones (xx.shape, int32)
  ireg [0, :] = 0
  ireg [:, 0] = 0
  plfc(mag(x+.5,y-.5),yy,xx,ireg,contours=8)
  plc (mag(x+.5,y-.5), marks=1)
  plm (boundary=1, type=2)
  print('Contours A-H, with mesh boundary dashed.')
  print('Contours I-P, with mesh boundary dashed.')
  paws()
  fma()
  unzoom()

  print('Test 18:  Commands: plf(z);  plfc(.); plc(z,.)')
  z = mag(x+.5,y-.5)
  plf(z)
  paws()
  fma()
  unzoom()
  
  plfc(z,yy,xx,ireg,contours=array([0.5, 1.0, 1.5]))
  plc(z, marks=0, type=2, color='bg', levs=[0.5, 1.0, 1.5])
  print('Filled mesh (color only) with three dashed contours overlayed.')
  paws()
  fma()
  unzoom()

  print('Test 19:  Commands: palette( \'<various>.gp\')')
  print('After each new palette is installed, hit <RETURN> for the next,')
  print('or q<RETURN> to begin test 20.  There are 6 palettes altogether.')
  z = mag(x+.5,y-.5)
  plf(z)
  plc(z, marks=0, type=2, color='bg', levs=[0.5, 1.0, 1.5])
  paws()
  fma ()
  plfc(z,yy,xx,ireg,contours=array([0.5, 1.0, 1.5]))
  plc(z, marks=0, type=2, color='bg', levs=[0.5, 1.0, 1.5])
  pal = ['heat.gp', 'stern.gp', 'rainbow.gp', 'gray.gp', 'yarg.gp', 'earth.gp']
  for i in range(6):
    palette (pal[i])
    print(('Palette name: ', pal[i]))
    paws()

  palette('earth.gp')
  fma()
  unzoom()

  print('Test 20:  Commands: window, style=\'<various>.gs\'')
  print('After each new style is installed, hit <RETURN> for the next,')
  print('or q<RETURN> to begin test 21.  There are 5 styles altogether.')
  pal= ['vg.gs', 'boxed.gs', 'vgbox.gs', 'nobox.gs', 'work.gs']
  for i in range(5):
    window (style=pal[i])
    plc (mag(x+.5,y-.5), marks=1)
    plm (boundary=1, type=2)
    print(('Style name: ', pal[i]))
    paws()

  window(style='work.gs')
  fma()
  unzoom()

  print('Test 21:  Commands: pli(image)')
  x = a3 (-6,6,200)
  y = transpose (x)
  r = mag(y,x)
  theta = arctan2 (y, x)
  funky = cos(r)**2 * cos(3*theta)
  pli(funky)
  print('Cell array image (color only).  Three cycles in theta, r.')
  paws()
  fma()
  unzoom()

  print('Test 22:  Commands: pldj(x0, y0, x1, y1)')
  theta = a2(0, 2*pi, 18)
  x = cos(theta)
  y = sin(theta)
  pldj(x, y, transpose (x), transpose (y))
  pltitle('Seventeen Pointed Stars')
  limits(square = 1)
  print('All 17 pointed stars.')
  paws()
  limits(square = 0)
  fma()
  unzoom()

  print('Test 23:  Commands: plfp (z, y, x, n)')

# .. This duplicates the test in yorick
# .. I do not know of a way to apply a 'table lookup' in python;
# .. Hence, the temporary array.
#
# .. n = [ 5, 10, 15 ]
# .. _list = [ 1, 1, 3, 3, 2, 1, 3 ]
# .. n(_list) = [ 5, 5, 15, 15, 10, 5, 15 ] 

  n =  [3,4,5, 4, 5, 6, 5, 6, 7]
  n2 = [0,3,7,12,16,21,27,32,38]
  x0 = array ( [-2.,0.,2.]*3 )
  y0 = array ( [-2.]*3 + [0.]*3 + [2.]*3 )
  j = 1
  _list = []
  for i in n:
     _list = _list + [j]*i
     j = j + 1
  lenList = len(_list)

  nlist = arange(1,lenList+1) 
  n2list = arange(1,lenList+1) 
  phase = zeros ( (lenList), float32 ) 
  theta = zeros ( (lenList), float32 ) 
  x0List = zeros ( (lenList), float32 ) 
  y0List = zeros ( (lenList), float32 ) 

  for i in range(lenList):
     nlist[i] = n[_list[i]-1]
     n2list[i] = n2[_list[i]-1]
     x0List[i] = x0[_list[i]-1]
     y0List[i] = y0[_list[i]-1]

  phase = arange(1,lenList+1) - n2list
  theta = 2. * pi * phase / nlist
  x = cos(theta) + x0List
  y = sin(theta) + y0List

  plfp ( x0-y0, y, x, n, cmin=-4.5, cmax=4.5 )
  pltitle ( 'Three rows of three polygons' )
  limits()
  print('Three rows of three polygons.')
  paws()
  fma()
  unzoom()

  print('Test 24:  Commands: plot histogram plh(...)')
  palette('earth.gp')
  data = array([7.58, 1.67, 5.28, 6.35, 4.08, 6.83, 2.24, 5.80, 5.93, 9.42,
               2.37, 4.47, 4.91, 3.99, 5.14, 7.15, 5.69, 6.56, 1.24, 3.18])
  aminoacids = ['A', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'K', 'L',
                'M', 'N', 'P', 'Q', 'R', 'S', 'T', 'V', 'W', 'Y']
  colors = 8 * arange(1,len(data)+1)
  plh (data, labels = aminoacids, color = colors) 
  ylimits(0,10.0)
  pltitle ('Amino acid abundance (%) in SwissProt v. 36')
  paws()
  fma()
  unzoom()

  print('Test 25:  Commands: plot text plt(...)')
  window(style='nobox.gs')
  plt('Courier',0,1,tosys=1,height=20,font=0)
  plt('Courier-Bold',0,2,tosys=1,height=20,font=1)
  plt('Courier-Oblique',0,3,tosys=1,height=20,font=2)
  plt('Courier-BoldOblique',0,4,tosys=1,height=20,font=3)
  plt('Times-Roman',0,5,tosys=1,height=20,font=4)
  plt('Times-Bold',0,6,tosys=1,height=20,font=5)
  plt('Times-Italic',0,7,tosys=1,height=20,font=6)
  plt('Times-BoldItalic',0,8,tosys=1,height=20,font=7)
  plt('Helvetica',0,9,tosys=1,height=20,font=8)
  plt('Helvetica-Bold',0,10,tosys=1,height=20,font=9)
  plt('Helvetica-Oblique',0,11,tosys=1,height=20,font=10)
  plt('Helvetica-BoldOblique',0,12,tosys=1,height=20,font=11)
  plt('Symbol',0,13,tosys=1,height=20,font=12)
  plt('Symbol',0,14,tosys=1,height=20,font=13)
  plt('Symbol',0,15,tosys=1,height=20,font=14)
  plt('Symbol',0,16,tosys=1,height=20,font=15)
  plt('NewCenturySchlbk-Roman',0,17,tosys=1,height=20,font=16)
  plt('NewCenturySchlbk-Bold',0,18,tosys=1,height=20,font=17)
  plt('NewCenturySchlbk-Italic',0,19,tosys=1,height=20,font=18)
  plt('NewCenturySchlbk-BoldItalic',0,20,tosys=1,height=20,font=19)
  limits(0,2,0,22)
  paws()
  fma()
  window(style='work.gs')
  unzoom()

  print('Test 26:  Lissajous animation')
  print('First run without animation mode')
  print('Second run with animation mode')
  print('Press RETURN to continue')
  paws()
  lissajous(0)
  print('Press RETURN to continue')
  paws()
  lissajous(1)
  paws()
  unzoom()

def lissajous(animation):

#  DOCUMENT lissajous
#     runs the Yorick equivalent of an old graphics performance test
#     used to compare PLAN, ALMA, and Basis with LTSS TMDS graphics.
#   SEE ALSO: testg, grtest
#
#  Two figures with (x,y)= (cx,cy) + size*(cos(na*t), sin(nb*t+phase))
#  -- the centers describe semi-circular arcs of radius rc. 

   import os
   t= 2*pi*arange(400.0)/399.0
   na1= 1
   nb1= 5
   na2= 2
   nb2= 7
   rc1= 40.
   rc2= 160.
   size= 40.
   phase= theta= 0.

   n = 200;   #/* number of frames in animation */
   dtheta= pi/(n-1)
   dphase= 2*pi/(n-1)

   if animation == 1:
      animate(1)
   else:
      animate(0)

   fma()

   t0 = os.times()

   for i in range(n):
      cost= cos(theta)
      sint= sin(theta)
      x= rc1*cost+size*cos(na1*t)
      y= rc1*sint+size*sin(nb1*t+phase);
      plg( y, x)
      x= rc2*cost+size*cos(na2*t)
      y= rc2*sint+size*sin(nb2*t+phase);
      plg( y, x)
      fma()
      theta= theta + dtheta;
      phase= phase + dphase;
  
   t1 = os.times()
   print('Timing summary for Lissajous')
   print(('Wall clock:', t1[4] - t0[4]))
   print(('User cpu:', t1[0] - t0[0]))
   print(('Sys cpu:', t1[1] - t0[1]))

   if animation == 1:
      #/* turn off animation and pop up final frame again */
      animate(0)
      x= -rc1+size*cos(na1*t)
      y= size*sin(nb1*t);
      plg(y, x)
      x= -rc2+size*cos(na2*t)
      y= size*sin(nb2*t);
      plg(y, x)

# (nr X nc) array, each row an integer in the sequence [0, 1, ... ]
def a1(nr,nc):
   return reshape (array(concat1(nr,nc), float32), (nr,nc))

# (n-1) square array, with each row == spanz(lb,ub,n)
def a2(lb,ub,n):
   return reshape (array((n-1)*spanz(lb,ub,n), float32), (n-1,n-1))
  
# (n) square array, with each row == linspace(lb,ub,n)
def a3(lb,ub,n):
   return tile(linspace(lb,ub,n), n).reshape(n,n)
  
# Half-hearted attempt at linspace()(zcen), which returns N-1 'zone-centered'
# values in sequence (lb, ..., ub)
def spanz(lb,ub,n):
   if n < 3: raise ValueError('3rd arg must be at least 3')
   c = 0.5*(ub - lb)/(n - 1.0)
   b = lb + c
   a = (ub - c - b)/(n - 2.0)
   return list(map(lambda x,A=a,B=b: A*x + B, list(range(n-1))))

# magnitude or distance function
def mag(*args):
   r = 0
   for i in range(len(args)):
      r = r + args[i]*args[i]
   return sqrt(r)

def run():
   grtest()

if __name__ == '__main__': 
   run()
