# $Id: yorick.py 644 2007-08-31 17:08:46Z mbec $
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
from .shapetest import *

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

def maxelt_ (*x) :

   '''
   maxelt_ accepts a sequence of one or more possible multi-dimensional
   objects and computes their maximum. In principle these can be of
   arbitrary complexity, since the routine recurses.
   '''

   if len (x) == 0 :
      return None
   elif len (x) == 1 :
      z = x [0]
      if is_scalar (z) :
         return z
      if len (numpy.shape (z)) >= 1 :
         zz = numpy.array (z)
         return numpy.maximum.reduce (numpy.ravel (zz))
   else :
      maxelt = maxelt_ (x [0])
      for i in range (1, len (x)) :
         maxelt = max (maxelt, maxelt_ (x [i]))
      return maxelt

def minelt_ (*x) :

   '''
   minelt_ accepts a sequence of one or more possible multi-dimensional
   objects and computes their minimum. In principle these can be of
   arbitrary complexity, since the routine recurses.
   '''

   if len (x) == 0 :
      return None
   elif len (x) == 1 :
      z = x [0]
      if is_scalar (z) :
         return z
      if len (numpy.shape (z)) >= 1 :
         zz = numpy.array (z)
         return numpy.minimum.reduce (numpy.ravel (zz))
   else :
      minelt = minelt_ (x [0])
      for i in range (1, len (x)) :
         minelt = min (minelt, minelt_ (x [i]))
      return minelt

def avg_ (z) :

   '''
   avg_ (z) returns the average of all elements of its array
   argument.
   '''

   zz = numpy.array (z, copy = 1 )
   return numpy.add.reduce (numpy.ravel (zz)) / len (numpy.ravel (zz))

def sign_ (x) :
   if x >= 0 :
      return (1)
   else :
      return (- 1)

def timer_ (elapsed, *split) :

   '''
   timer (elapsed) returns a triple consisting of the times
   [cpu, system, wall].
   timer (elapsed, split) returns a sequence whose first element
   is [cpu, system, wall] and whose second element is the
   sum of split and the difference between ththe new and old values
   of 'elapsed.'
   '''

   stime = os.times ( )
   wtime = time.time ( )
   retval = numpy.array ( [stime [0], stime [1], wtime], numpy.float32 )
   if len (split) == 0 :
      return retval
   else :
      return [retval, split [0] + retval - elapsed]

