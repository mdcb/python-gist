# Copyright (c) 1996, 1997, The Regents of the University of California.
# All rights reserved.  See Legal.htm for full text and disclaimer.
# Automatically adapted for numpy Jul 30, 2006 by numeric2numpy.py
'''
   The yorick module supplies Python versions of some common
   yorick functions: zcen_, dif_, maxelt_, minelt_,
   avg_, timer_.
'''

import os
import time
import numpy


class _ZcenError ( Exception ):
   pass

def zcen_ (x, i = 0) :

   '''
   zcen_(x, i) does the same thing as in Yorick: x(...,zcen,...)
   where zcen is the ith subscript. (works for up to 5 dimensions).
   Namely, the elements along the ith dimension of x are replaced
   by the averages of adjacent pairs, and the dimension decreases
   by one. Remember that Python sunscripts are counted from 0.
   '''

   if is_scalar (x) :
      raise _ZcenError('zcen_ must be called with an array.')
   dims = numpy.shape (x)
   ndims = len (dims)
   if i < 0 or i > ndims - 1 :
      raise _ZcenError('i <%d> is out of the range of x-dimensions <%d>.' % (i+1,ndims))
   if i == 0 :
      newx = (x [0:dims [0]-1] + x [1:dims [0]]) /2.0
   elif i == 1 :
      newx = (x [:, 0:dims [1]-1] + x[:, 1:dims [1]]) / 2.0
   elif i == 2 :
      newx = (x [:, :, 0:dims [2]-1] + x[:, :, 1:dims [2]]) / 2.0
   elif i == 3 :
      newx = (x [:, :, :, 0:dims [3]-1] + x[:, :, :, 1:dims [3]]) / 2.0
   elif i == 4 :
      newx = (x [:, :, :, :, 0:dims [4]-1] + \
              x [:, :, :, :, 0:dims [4]]) / 2.0

   return newx

class _DifError ( Exception ):
   pass

def dif_ (x, i = 0) :

   '''
   dif_(x, i) does the same thing as in Yorick: x(...,dif_,...)
   where dif_ is the ith subscript. (works for up to 5 dimensions).
   Namely, the elements along the ith dimension of x are replaced
   by the differences of adjacent pairs, and the dimension decreases
   by one. Remember that Python sunscripts are counted from 0.
   '''

   if is_scalar (x) :
      raise _DifError('dif_ must be called with an array.')
   dims = numpy.shape (x)
   ndims = len (dims)
   if i < 0 or i > ndims - 1 :
      raise _DifError('i <%d> is out of the range of x-dimensions <%d>.' % (i+1,ndims))
   if i == 0 :
      newx = x [1:dims [0]] - x [0:dims [0] - 1]
   elif i == 1 :
      newx = x [:, 1:dims [1]] - x[:, 0:dims [1] - 1]
   elif i == 2 :
      newx = x [:, :, 1:dims [2]] - x [:, :, 0:dims [2] - 1]
   elif i == 3 :
      newx = x [:, :, :, 1:dims [3]] - x [:, :, :, 0:dims [3] - 1]
   elif i == 4 :
      newx = x [:, :, :, :, 1:dims [4]] - x [:, :, :, :, 0:dims [4] - 1]
   return newx

def is_scalar(x):
   return len(numpy.shape(x)) == 0
