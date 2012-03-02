## Automatically adapted for numpy Jul 30, 2006 by numeric2numpy.py

#!/usr/bin/env python
#  $Id: mesh.py 671 2007-09-18 12:58:46Z mbec $
#  -----------------------------------------------------------------
#
#  NAME:     mesh.py (incomplete, work-in-progress)
#
#  PURPOSE:  Python interface to mesh routines. 
#  
#  NOTES:
#  - Eliminate the need for PLMESH in the C module by keeping the
#    mesh at the Python level. 
#  - This layer only deals with z, y, x, ireg, tri, and mesh arguments.
#    Keyword arguments allowed by the various functions are passed
#    to the compiled function, where they are handled.
#
#  CHANGES:
#  08/7/03 llc Originated.
#
#  -----------------------------------------------------------------

import unittest
from numpy import float32, int32, int16, \
   arange, array, product, rank, reshape, shape, zeros
import gist
from gist import *

# int32 is int3232 (int)
# float32 is float3264 (double)
# int32 (short)

savedMesh = None

class InputError ( Exception ):
   """
   Used for input errors in these function calls.
   """

class Mesh:
   """
   Saves mesh information:  x, y as double array and ireg as an 
   int array.
   """
   def __init__ ( self, x=None, y=None, ireg=None, triangle=None ):

      try:
         self.x = array ( x, dtype=float32, copy=0 )
      except:
         raise TypeError, "Could not cast x to numpy ndarray"

      if not ( rank(self.x) == 2 and 
               shape(self.x)[0] >=2 and shape(self.x)[1] >= 2 ):
         raise TypeError, "x must be 2D"

      try:
         self.y = array ( y, dtype=float32, copy=0 )
      except:
         raise TypeError, "Could not cast y to numpy ndarray"
      if not ( rank(self.y) == 2 and 
               shape(self.y)[0] >=2 and shape(self.y)[1] >= 2 ):
         raise TypeError, "y must be 2D"

      if ireg is None:
         self.ireg = zeros ( shape(self.x), int32 )
         self.ireg[1:,1:] = 1
      else:
         try:
            self.ireg = array ( ireg, dtype=int32, copy=0 )
         except:
            raise TypeError, "Could not cast ireg to numpy ndarray"
         if not ( rank(self.ireg) == 2 and 
                  shape(self.ireg)[0] >=2 and shape(self.ireg)[1] >= 2 ):
            raise TypeError, "ireg must be 2D"

      if triangle is None:
         self.triangle = zeros ( shape(self.x), int32 )
      else:
         try:
            self.triangle = array ( triangle, dtype=int32, copy=0 )
         except:
            raise TypeError, "Could not cast triangle to numpy ndarray"
         if not ( rank(self.triangle) == 2 and
                  shape(self.triangle)[0] >=2 and shape(self.triangle)[1] >= 2 ):
            raise TypeError, "triangle must be 2D"

      self.shape = shape(self.x) 

   def display ( self ):
      print "mesh.x\n", self.x
      print "mesh.y\n", self.y
      print "mesh.ireg\n", self.ireg
      print "mesh.triangle\n", self.triangle

   def setReg ( self, ireg ):

      try:
         self.ireg = array ( ireg, dtype=int32, copy=0 )
      except:
         raise TypeError, "Could not cast ireg to numpy ndarray"

      if not ( rank(self.ireg) == 2 and
               shape(self.ireg)[0] >=2 and shape(self.ireg)[1] >= 2 ):
         raise TypeError, "ireg must be 2D"

      if self.shape != shape ( self.ireg ):
         raise InputError, "ireg has incompatible shape."
      
   def setTriangle ( self, triangle ):

      try:
         self.triangle = array ( triangle, dtype=int32, copy=0 )
      except:
         raise TypeError, "Could not cast triangle to numpy ndarray"

      if not ( rank(self.triangle) == 2 and
               shape(self.triangle)[0] >=2 and shape(self.triangle)[1] >= 2 ):
         raise TypeError, "triangle must be 2D"

      if self.shape != shape (self.triangle):
         raise InputError, "triangle has incompatible shape."

   def clear ( self ):
      self.x = None
      self.y = None
      self.ireg = None
      self.triangle = None

def plmesh ( y=None, x=None, ireg=None, triangle=None, mesh=None ):
   """
   Return a reference to the default mesh saved 

   mesh = plmesh ( y, x, ireg, triangle=tri_array )  or
   mesh = plmesh ( mesh=myMesh )
   plmesh()
      Set the default mesh for subsequent plm, plc, plv, and plf calls.
      In the no-argument form, deletes the default mesh (until you do this,
      or switch to a new default mesh, the default mesh arrays persist and
      take up space in memory).  The Y, X, and IREG arrays should all be
      the same shape; Y and X will be converted to double, and IREG will
      be converted to int.  If IREG is omitted, it defaults to IREG(1,)=
      IREG(,1)= 0, IREG(2:,2:)=1; that is, region number 1 is the whole
      mesh.  The triangulation array TRI_ARRAY is used by plc; the
      correspondence between TRI_ARRAY indices and zone indices is the
      same as for IREG, and its default value is all zero.
      The IREG or TRI_ARRAY arguments may be supplied without Y and X or MESH
      to change the region numbering or triangulation for a given set of
      mesh coordinates.  However, a default Y and X must already have been
      defined if you do this.
      If Y is supplied, X must be supplied, and vice-versa.

   SEE ALSO: plm, plc, plv, plf, plfp
   """
   global savedMesh

   existMesh = False 

   if y is None and x is None and ireg is None and triangle is None:
      savedMesh.clear()
      savedMesh = None
      return None

   if x is not None and y is None or \
      x is None and y is not None:
      raise InputError, "If x is supplied, y must be supplied, and vice versa"

   if mesh is None:

      if x is None and y is None:
         print "Warning: using obsolete format; specify mesh or (y,x)."
         mesh = savedMesh
         existMesh = True
      else:
         savedMesh = Mesh ( x, y, ireg=ireg, triangle=triangle )

   else:

      existMesh = True
      if not ( x is None and y is None ):
         print "Warning: provided both (y,x) and mesh; will use mesh"

   if savedMesh is None:
      raise InputError, "No mesh has been specfied."

   if existMesh == True:
#     .. Allow ireg and triangle of an existing mesh to be modified
      if ireg is not None:
         mesh.setReg ( ireg ) 
      if triangle is not None:
         mesh.setTriangle ( triangle )

   print savedMesh.x
   print savedMesh.y
   print savedMesh.ireg
   return savedMesh 

def plc ( z, y=None, x=None, ireg=None, levs=None, mesh=None, **keywords ):
   """
   plc ( z, y, x, levs=z_values )  or
   plc ( z, y, x, ireg, levs=z_values ) or
   plc ( z, levs=z_values, mesh=myMesh )  or
   plc ( z, levs=z_values )
      Plot contours of Z on the mesh Y versus X.  Y, X, and IREG are
      as for plm.  The Z array must have the same shape as Y and X.
      The function being contoured takes the value Z at each point
      (X,Y) -- that is, the Z array is presumed to be point-centered.
      The Y, X, and IREG arguments may all be omitted to default to the
      mesh set by the most recent plmesh call.
      The LEVS keyword is a list of the values of Z at which you want
      contour curves.  The default is eight contours spanning the
      range of Z.
      The following keywords are legal (each has a separate help entry):

   KEYWORDS: legend, hide, region, color, type, width,
      marks, mcolor, marker, msize, mspace, mphase,
      smooth, triangle, levs

   SEE ALSO: plg, plm, plc, plv, plf, pli, plt, pldj, plfp, plmesh
             limits, logxy, ylimits, fma, hcp
   """
   global savedMesh
   _z = array ( z, float32, copy=0 )

   if mesh is None:

      if x is None and y is None and ireg is None:
         if savedMesh is None:
            raise InputError, "No mesh specified."
         else:
            print "Warning: using obsolete format; specify mesh or (y,x)."
            mesh = savedMesh
      else:
#        .. Use the passed in mesh over the default
         assert x is not None and y is not None, "x and y need to be set"
         if ireg is None:
            ireg = zeros ( shape(_z), int32 )
            ireg[1:,1:] = 1
         mesh = Mesh ( x, y, ireg=ireg )

   else:

#     .. Use the passed in mesh over the default
      if x is None and y is None and ireg is None:
#        .. Use mesh argument
         pass
      else:
         print "Warning: provided both (y,x) and mesh; will use mesh"
 
#  .. Check the dimensions of mesh
   if shape(_z) != mesh.shape:
      raise TypeError, "input mesh does not match dimensions of x"

   if levs is None:
#     .. Default is 8 evenly spaced contours
#     .. First, flatten the array to get the min and max
      zz = reshape ( _z, (product(shape(_z)),) )
      zmin = min ( zz )
      zmax = max ( zz )
      zdel = ( zmax - zmin ) / 7.0
      _levels = arange ( zmin, zmax, zdel )
   else:
      _levels = array ( levs, int32, copy = 0 )

   print mesh.x
   print mesh.y
   print mesh.ireg
   print _levels
   gist.plc( _z, mesh.y, mesh.x, mesh.ireg, _levels )

def plf ( z, y=None, x=None, ireg=None, mesh=None, **keywords ):
   """
   Plot a filled mesh. z has the same shape as x and y. 

   plf ( z, y, x )  or
   plf ( z, y, x, ireg )  or
   plf ( z, mesh=myMesh )
   plf ( z )
      Plot a filled mesh Y versus X.  Y, X, and IREG are as for plm.
      The Z array must have the same shape as Y and X, or one smaller
      in both dimensions.  If Z is of type char, it is used `as is',
      otherwise it is linearly scaled to fill the current palette, as
      with the bytscl function.
      (See the bytscl function for explanation of top, cmin, cmax.)
      The mesh is drawn with each zone in the color derived from the Z
      function and the current palette; thus Z is interpreted as a
      zone-centered array.
      The Y, X, and IREG arguments may all be omitted to default to the
      mesh set by the most recent plmesh call.
      A solid edge can optionally be drawn around each zone by setting
      the EDGES keyword non-zero.  ECOLOR and EWIDTH determine the edge
      color and width.  The mesh is drawn zone by zone in order from
      IREG(2+imax) to IREG(jmax*imax) (the latter is IREG(imax,jmax)),
      so you can achieve 3D effects by arranging for this order to
      coincide with back-to-front order.  If Z is nil, the mesh zones
      are filled with the background color, which you can use to
      produce 3D wire frames.
      The following keywords are legal (each has a separate help entry):

   KEYWORDS: legend, hide, region, top, cmin, cmax, edges, ecolor, ewidth

   SEE ALSO: plg, plm, plc, plv, plf, pli, plt, pldj, plfp, plmesh,
             limits, logxy, ylimits, fma, hcp, palette, bytscl, histeq_scale
   """ 
   global savedMesh
   _z = array ( z, float32, copy=0 )

   if mesh is None:

      if x is None and y is None and ireg is None:
         print "Warning: using obsolete format; specify mesh or (y,x)."
         mesh = savedMesh
      else:
         assert x is not None and y is not None, "x and y need to be set"
         if ireg is None:
            ireg = zeros ( shape(_z), int32 )
            ireg[1:,1:] = 1
         mesh = Mesh ( x, y, ireg=ireg )

   else:

      if x is None and y is None and ireg is None:
#        .. Use mesh argument
         pass
      else:
         print "Warning: provided both (y,x) and mesh; will use mesh"
 
#  .. Check the dimensions of mesh
   if shape(_z) != mesh.shape:
      raise TypeError, "input mesh does not match dimensions of x"

   print mesh.x
   print mesh.y
   print mesh.ireg
   gist.plf( _z, mesh.y, mesh.x, mesh.ireg )

def plm ( y=None, x=None, ireg=None, mesh=None ):
   """
   plm ( y, x, boundary=0/1, inhibit=0/1/2 )  or
   plm ( y, x, ireg, boundary=0/1, inhibit=0/1/2 )  or
   plm ( boundary=0/1, inhibit=0/1/2, mesh=myMesh )
   plm ( boundary=0/1, inhibit=0/1/2 )

      Plot a mesh of Y versus X.  Y and X must be 2D arrays with equal
      dimensions.  If present, IREG must be a 2D region number array
      for the mesh, with the same dimensions as X and Y.  The values of
      IREG should be positive region numbers, and zero for zones which do
      not exist.  The first row and column of IREG never correspond to any
      zone, and should always be zero.  The default IREG is 1 everywhere
      else.  If present, the BOUNDARY keyword determines whether the
      entire mesh is to be plotted (boundary=0, the default), or just the
      boundary of the selected region (boundary=1).  If present, the
      INHIBIT keyword causes the (X(,j),Y(,j)) lines to not be plotted
      (inhibit=1), or the (X(i,),Y(i,)) lines to not be plotted (inhibit=2).
      By default (inhibit=0), mesh lines in both logical directions are
      plotted.
      The Y, X, and IREG arguments may all be omitted to default to the
      mesh set by the most recent plmesh call.
      The following keywords are legal (each has a separate help entry):

    KEYWORDS: legend, hide, color, type, width, region, boundary, inhibit

    SEE ALSO: plg, plm, plc, plv, plf, pli, plt, pldj, plfp, plmesh,
              limits, logxy, ylimits, fma, hcp
   """
   global savedMesh

   if mesh is None:

      if x is None and y is None and ireg is None:
         print "Warning: using obsolete format; specify mesh or (y,x)."
         mesh = savedMesh
      else:
         assert x is not None and y is not None, "x and y need to be set"
         _x = array ( x, float32 )
         if ireg is None:
            ireg = zeros ( shape(_x), int32 )
            ireg[1:,1:] = 1
         mesh = Mesh ( x, y, ireg=ireg )

   else:

      if x is None and y is None and ireg is None:
#        .. Use mesh argument
         pass
      else:
         print "Warning: provided both (y,x) and mesh; will use mesh"
 
   print mesh.x
   print mesh.y
   print mesh.ireg
   gist.plm( mesh.y, mesh.x, mesh.ireg ) 

def plv ( vy, vx, y=None, x=None, ireg=None, mesh=None, **keywords ):
   """
   plv ( vy, vx, y, x, scale=dt )  or
   plv ( vy, vx, y, x, ireg, scale=dt )  or
   plv ( vy, vx, scale=dt, mesh=myMesh )  or
   plv ( vy, vx, scale=dt )

     Plot a vector field (VX,VY) on the mesh (X,Y).  Y, X, and IREG are
     as for plm.  The VY and VX arrays must have the same shape as Y and X.
     The Y, X, and IREG arguments may all be omitted to default to the
     mesh set by the most recent plmesh call.
     The SCALE keyword is the conversion factor from the units of
     (VX,VY) to the units of (X,Y) -- a time interval if (VX,VY) is a velocity
     and (X,Y) is a position -- which determines the length of the
     vector `darts' plotted at the (X,Y) points.  If omitted, SCALE is
     chosen so that the longest ray arrows have a length comparable
     to a `typical' zone size.
     You can use the scalem keyword in pledit to make adjustments to the
     SCALE factor computed by default.
     The following keywords are legal (each has a separate help entry):

   KEYWORDS: legend, hide, region, color, hollow, width, aspect, scale

   SEE ALSO: plg, plm, plc, plv, plf, pli, plt, pldj, plfp, plmesh, pledit,
             limits, logxy, ylimits, fma, hcp
   """ 
   global savedMesh
   _vx = array ( vx, float32, copy=0 )
   _vy = array ( vy, float32, copy=0 )

   if shape(_vx) != shape(_vy):
      raise InputError, "Shapes of vx and vy are not the same."

   if mesh is None:

      if x is None and y is None and ireg is None:
         print "Warning: using obsolete format; specify mesh or (y,x)."
         mesh = savedMesh
      else:
         assert x is not None and y is not None, "x and y need to be set"
         if ireg is None:
            ireg = zeros ( shape(x), int32 )
            ireg[1:,1:] = 1
         mesh = Mesh ( x, y, ireg=ireg )

   else:

      if x is None and y is None and ireg is None:
#        .. Use mesh argument
         pass
      else:
         print "Warning: provided both (y,x) and mesh; will use mesh"
 
#  .. Check the dimensions of mesh
   if shape(_vx) != mesh.shape:
      raise TypeError, "input mesh does not match dimensions of x"

   print mesh.x 
   print mesh.y 
   print mesh.ireg 
   gist.plv( _vy, _vx, mesh.y, mesh.x, mesh.ireg )

class TestPLMESH ( unittest.TestCase ):

   def setUp ( self ):
      self.x = [ [ 1., 2., 3.], [ 1., 2., 3.], [ 1., 2., 3.] ]
      self.y = [ 3*[1.], 3*[2.], 3*[3.] ]
      self.ireg = [ 3*[0], [0, 4, 4], [0, 4, 4] ]
      self.triangle = [ 3*[0], [0, 2, 2], [0, 2, 2] ]
      self.m = Mesh ( self.x, self.y, self.ireg )

   def testPLMESH ( self ):

      print "... plmesh ( self.y, self.x, self.ireg )"
      myMesh = plmesh ( self.y, self.x, self.ireg )

      print "... plmesh ( self.y, self.x, mesh=myMesh )"
      myMesh = plmesh ( self.y, self.x, mesh=myMesh )

      print "... plmesh ( self.y, self.x )"
      myMesh = plmesh ( self.y, self.x )

      print "... plmesh ( ireg=self.ireg )"
      myMesh = plmesh ( ireg=self.ireg, triangle=self.triangle )

      print "... plmesh ()"
      myMesh = plmesh ()

   def tearDown ( self ):
      del self.m

class TestPLM ( unittest.TestCase ):

   def setUp ( self ):
      self.x = [ [ 1., 2., 3.], [ 1., 2., 3.], [ 1., 2., 3.] ]
      self.y = [ 3*[1.], 3*[2.], 3*[3.] ]
      self.ireg = [ 3*[0], [0, 4, 4], [0, 4, 4] ]
      self.m = Mesh ( self.x, self.y, self.ireg )

   def testPLM ( self ):
      print "plm ( self.y, self.x, self.ireg )"
      plm ( self.y, self.x, self.ireg )
      print "plm ( mesh = self.m )"
      plm ( mesh = self.m )
      print "plm ( self.y, self.x, mesh = self.m )"
      plm ( self.y, self.x, mesh = self.m )

   def tearDown ( self ):
      del self.m

class TestPLC ( unittest.TestCase ):

   def setUp ( self ):
      self.x = [ [ 1., 2., 3.], [ 1., 2., 3.], [ 1., 2., 3.] ]
      self.y = [ 3*[1.], 3*[2.], 3*[3.] ]
      self.z = [ 3*[10.], 3*[20.], 3*[30.] ]
      self.ireg = [ 3*[0], [0, 4, 4], [0, 4, 4] ]
      self.levels = [ 5., 15., 28., 35. ]
      self.m = Mesh ( self.x, self.y, self.ireg )

   def testPLC ( self ):
      print "plmesh ( self.y, self.x, self.ireg )"
      plmesh ( self.y, self.x, self.ireg )
      print "plc ( self.z, self.y, self.x )"
      plc ( self.z, self.y, self.x )
      print "plc ( self.z, mesh = self.m, levs = self.levels )"
      plc ( self.z, mesh = self.m, levs = self.levels )
      print "plc ( self.z, levs = self.levels )"
      plc ( self.z, levs = self.levels )

   def tearDown ( self ):
      del self.m
      
class TestPLF ( unittest.TestCase ):

   def setUp ( self ):
      self.x = [ [ 1., 2., 3.], [ 1., 2., 3.], [ 1., 2., 3.] ]
      self.y = [ 3*[1.], 3*[2.], 3*[3.] ]
      self.z = [ 3*[10.], 3*[20.], 3*[30.] ]
      self.ireg = [ 3*[0], [0, 4, 4], [0, 4, 4] ]
      self.levels = [ 5., 15., 28., 35. ]
      self.m = Mesh ( self.x, self.y, self.ireg )

   def testPLF ( self ):
      print "plmesh ( self.y, self.x, self.ireg )"
      plmesh ( self.y, self.x, self.ireg )
      print "plf ( self.z, self.y, self.x )"
      plf ( self.z, self.y, self.x )
      print "plf ( self.z, mesh = self.m )"
      plf ( self.z, mesh = self.m )
      print "plf ( self.z )"
      plf ( self.z )

   def tearDown ( self ):
      del self.m

class TestPLV ( unittest.TestCase ):

   def setUp ( self ):
      self.x = [ [ 1., 2., 3.], [ 1., 2., 3.], [ 1., 2., 3.] ]
      self.y = [ 3*[1.], 3*[2.], 3*[3.] ]
      self.vx = [ 3*[10.], 3*[20.], 3*[30.] ]
      self.vy = [ 3*[50.], 3*[55.], 3*[60.] ]
      self.ireg = [ 3*[0], [0, 4, 4], [0, 4, 4] ]
      self.m = Mesh ( self.x, self.y, self.ireg )

   def testPLV ( self ):
      print "plmesh ( self.y, self.x, self.ireg )"
      plmesh ( self.y, self.x, self.ireg )
      print "plv ( self.vy, self.vx, self.y, self.x )"
      plv ( self.vy, self.vx, self.y, self.x )
      print "plv ( self.vy, self.vx, mesh = self.m, scale=.5 )"
      plv ( self.vy, self.vx, mesh = self.m, scale=.5 )
      print "plv ( self.vy, self.vx )"
      plv ( self.vy, self.vx )

   def tearDown ( self ):
      del self.m

if (__name__=="__main__"):
   unittest.main()
