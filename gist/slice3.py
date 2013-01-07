# $Id: slice3.py 671 2007-09-18 12:58:46Z mbec $
# Copyright (c) 1996, 1997, The Regents of the University of California.
# All rights reserved.  See Legal.htm for full text and disclaimer.

#  SLICE3.PY
# find 2D slices of a 3D hexahedral mesh

#  $Id: slice3.py 671 2007-09-18 12:58:46Z mbec $
#

# Change (ZCM 12/4/96) Apparently _draw3_list, which is global in
# pl3d.py, can be fetched from there, but once this has been done,
# assignments to it over there are not reflected in the copy here.
# This has been fixed by creating an access function.

import numpy
from .gistC import *
from .gistF import find_mask, construct3, array_set, interp
from .pl3d import *
from .yorick import *
import collections

def is_scalar(x):
    return len(numpy.shape(x)) == 0

#
 # Caveats:
 # (A) Performance is reasonably good, but may still be a factor of
 #     several slower than what could be achieved in compiled code.
 # (B) Only a simple in-memory mesh model is implemented here.
 #     However, hooks are supplied for more interesting possibilities,
 #     such as a large binary file resident mesh data base.
 # (C) There is a conceptual difficulty with _walk3 for the case
 #     of a quad face all four of whose edges are cut by the slicing
 #     plane.  This can only happen when two opposite corners are
 #     above and the other two below the slicing plane.  There are
 #     three possible ways to connect the four intersection points in
 #     two pairs: (1) // (2) \\ and (3) X  There is a severe problem
 #     with (1) and (2) in that a consistent decision must be made
 #     when connecting the points on the two cells which share the
 #     face - that is, each face must carry information on which way
 #     it is triangulated.  For a regular 3D mesh, it is relatively
 #     easy to come up with a consistent scheme for triangulating faces,
 #     but for a general unstructured mesh, each face itself must carry
 #     this information.  This presents a huge challenge for data flow,
 #     which I don't believe is worthwhile.  Because the X choice is
 #     unique, and I don't see why we shouldn't use it here.
 #     For contouring routines, we reject the X choice on esthetic
 #     grounds, and perhaps that will prove to be the case here as
 #     well - but I believe we should try the simple way out first.
 #     In this case, we are going to be filling these polygons with
 #     a color representing a function value in the cell.  Since the
 #     adjacent cells should have nearly the same values, the X-traced
 #     polygons will have nearly the same color, and I doubt there will
 #     be an esthetic problem.  Anyway, the slice3 implemented
 #     below produces the unique X (bowtied) polygons, rather than
 #     attempting to choose between // or \\ (non-bowtied) alternatives.
 #     Besides, in the case of contours, the trivial alternating
 #     triangulation scheme is just as bad esthetically as every
 #     zone triangulated the same way!

def plane3 (normal, point) :

    '''
    plane3(normal, point)
          or plane3([nx,ny,nz], [px,py,pz])

      returns [nx,ny,nz,pp] for the specified plane.
    '''

    # the normal doesn't really need to be normalized, but this
    # has the desirable side effect of blowing up if normal==0
    newnorm = numpy.zeros (4, numpy.float32)
    newnorm [0:3] = normal / numpy.sqrt (numpy.sum (normal*normal,axis=0))
    newnorm [3] = numpy.sum (numpy.multiply (normal, point),axis=0)
    return newnorm

class _Mesh3Error(Exception):
    pass

def mesh3 (x, y = None, z = None, ** kw) :

    '''
     mesh3(x,y,z)
          or mesh3(x,y,z, funcs = [f1,f2,...])
          or mesh3(xyz, funcs = [f1,f2,...])
          or mesh3(nxnynz, dxdydz, x0y0z0, funcs = [f1,f2,...])

      make mesh3 argument for slice3, xyz3, getv3, etc., functions.
      X, Y, and Z are each 3D coordinate arrays.  The optional F1, F2,
      etc. are 3D arrays of function values (e.g. density, temperature)
      which have one less value along each dimension than the coordinate
      arrays.  The 'index' of each zone in the returned mesh3 is
      the index in these cell-centered Fi arrays, so every index from
      one through the total number of cells indicates one real cell.
      The Fi arrays can also have the same dimensions as X, Y, or Z
      in order to represent point-centered quantities.

      If X has four dimensions and the length of the first is 3, then
      it is interpreted as XYZ (which is the quantity actually stored
      in the returned cell list).

      If X is a vector of 3 integers, it is interpreted as [nx,ny,nz]
      of a uniform 3D mesh, and the second and third arguments are
      [dx,dy,dz] and [x0,y0,z0] respectively.  (DXDYDZ represent the
      size of the entire mesh, not the size of one cell, and NXNYNZ are
      the number of cells, not the number of points.)

      Added by ZCM 1/13/97: if x, y, and z are one-dimensional of
      the same length and if the keyword verts exists and yields
      an NCELLS by 8 integer array, then we have an unstructured
      rectangular mesh, and the subscripts of cell i's vertices
      are verts[i, 0:8].

      Added by ZCM 10/10/97: if x, y, and z are one-dimensional
      of the same length or not, and verts does not exist, then
      we have a structured reectangular mesh with unequally spaced
      nodes.

      Other sorts of meshes are possible -- a mesh which lives
      in a binary file is an obvious example -- which would need
      different workers for xyz3, getv3, getc3, and iterator3
      iterator3_rect may be more general than the other three;
      as long as the cell dimensions are the car of the list
      which is the 2nd car of m3, it will work.
    '''

    dims = numpy.shape (x)
    if len (dims) == 1 and y != None and len (x) == len (y) \
       and z != None and len(x) == len (z) and 'verts' in kw :
        virtuals = [xyz3_irreg, getv3_irreg,
                    getc3_irreg, iterator3_irreg]
        dims = kw ['verts']
        if type (dims) != list :
            m3 = [virtuals, [dims, numpy.array ( [x, y, z])], []]
        else : # Irregular mesh with more than one cell type
            sizes = ()
            for nv in dims :
                sizes = sizes + (numpy.shape (nv) [0],) # no. cells of this type
            totals = [sizes [0]]
            for i in range (1, len (sizes)) :
                totals.append (totals [i - 1] + sizes [i]) #total cells so far
            m3 = [virtuals, [dims, numpy.array ( [x, y, z]), sizes, totals], []]
        if 'funcs' in kw :
            funcs = kw ['funcs']
        else :
            funcs = []
        i = 0
        for f in funcs:
            if len (f) != len (x) and len (f) != numpy.shape (dims) [0] :
                # if vertex-centered, f must be same size as x.
                # if zone centered, its length must match number of cells.
                raise _Mesh3Error('F' + repr(i) + ' is not a viable 3D cell value')
            m3 [2] = m3 [2] + [f]
            i = i + 1
        return m3

    virtuals = [xyz3_rect, getv3_rect, getc3_rect, iterator3_rect]
    if len (dims) == 4 and dims [0] == 3 and min (dims) >= 2 :
        xyz = x
        dims = dims [1:4]
    elif len (dims) == 1 and len (x) == 3 and type (x [0]) == numpy.int32 \
       and y != None and z != None and len (y) == len (z) == 3 :
        xyz = numpy.array ([y, z])
        dims = (1 + x [0], 1 + x [1], 1 + x [2])
        virtuals [0] = xyz3_unif
    elif len (dims) == 1 and y != None and z != None and len (y.shape) == 1 \
       and len (z.shape) == 1 and x.typed  == y.typed == \
       z.typed == numpy.float32 :
        # regular mesh with unequally spaced points
        dims = numpy.array ( [len (x), len (y), len (z)], numpy.int32)
        xyz = [x, y, z] # has to be a list since could be different lengths
        virtuals [0] = xyz3_unif
    else :
        if len (dims) != 3 or min (dims) < 2 or \
           y == None or len (numpy.shape (y)) != 3 or numpy.shape (y) != dims or \
           z == None or len (numpy.shape (z)) != 3 or numpy.shape (z) != dims:
            raise _Mesh3Error('X,Y,Z are not viable 3D coordinate mesh arrays')
        xyz = numpy.array ( [x, y, z])
    dim_cell = (dims [0] - 1, dims [1] - 1, dims [2] - 1)
    m3 = [virtuals, [dim_cell, xyz], []]
    if 'funcs' in kw :
        funcs = kw ['funcs']
    else :
        funcs = []
    i = 0
    for f in funcs:
        if len (f.shape) == 3 and \
           ( (f.shape [0] == dims [0] and f.shape [1] == dims [1] and
              f.shape [2] == dims [2]) or (f.shape [0] == dim_cell [0] and
              f.shape [1] == dim_cell [1] and f.shape [2] == dim_cell [2])) :
            m3 [2] = m3 [2] + [f]
            i = i + 1
        else :
            raise _Mesh3Error('F' + repr(i) + ' is not a viable 3D cell value')

    return m3

 # Ways that a list of polygons can be extracted:
 # Basic idea:
 #   (1) At each *vertex* of the cell list, a function value is defined.
 #       This is the 'slicing function', perhaps the equation of a plane,
 #       perhaps some other vertex-centered function.
 #   (2) The slice3 routine returns a list of cells for which the
 #       function value changes sign -- that is, cells for which some
 #       vertices have positive function values, and some negative.
 #       The function values and vertex coordinates are also returned.
 #   (3) The slice3 routine computes the points along the *edges*
 #       of each cell where the function value is zero (assuming linear
 #       variation along each edge).  These points will be vertices of
 #       the polygons.  The routine also sorts the vertices into cyclic
 #       order.
 #   (4) A 'color function' can be used to assign a 'color' or other
 #       value to each polygon.  If this function depends only on the
 #       coordinates of the polygon vertices (e.g.- 3D lighting), then
 #       the calculation can be done elsewhere.  There are two other
 #       possibilities:  The color function might be a cell-centered
 #       quantity, or a vertex-centered quantity (like the slicing
 #       function) on the mesh.  In these cases, slice3 already
 #       has done much of the work, since it 'knows' cell indices,
 #       edge interpolation coefficients, and the like.
 #
 # There are two particularly important cases:
 # (1) Slicing function is a plane, coloring function is either a
 #     vertex or cell centered mesh function.  Coloring function
 #     might also be a *function* of one or more of the predefined
 #     mesh functions.  If you're eventually going to sweep the whole
 #     mesh, you want to precalculate it, otherwise on-the-fly might
 #     be better.
 # (2) Slicing function is a vertex centered mesh function,
 #     coloring function is 3D shading (deferred).
 #
 # fslice(m3, vertex_list)
 # vertex_list_iterator(m3, vertex_list, mesh3)
 # fcolor(m3, vertex_list, fslice_1, fslice_2)
 #   the coloring function may need the value of fslice at the vertices
 #   in order to compute the color values by interpolation
 # two 'edge functions': one to detect edges where sign of fslice changes,
 #   second to interpolate for fcolor
 #   second to interpolate for fcolor
 #
 # slice3(m3, fslice, &nverts, &xyzverts, <fcolor>)

class _Slice3Error(Exception):
    pass


def slice3 (m3, fslice, nverts, xyzverts, * args, ** kw) :

    '''
    slice3 (m3, fslice, nverts, xyzverts)
          or color_values= slice3(m3, fslice, nverts, xyzverts, fcolor)
          or color_values= slice3(m3, fslice, nverts, xyzverts, fcolor, 1)

      slice the 3D mesh M3 using the slicing function FSLICE, returning
      the list [NVERTS, XYZVERTS, color].  Note that it is impossible to
      pass arguments as addresses, as yorick does in this routine.
      NVERTS is the number of vertices in each polygon of the slice, and
      XYZVERTS is the 3-by-sum(NVERTS,axis=0) list of polygon vertices.  If the
      FCOLOR argument is present, the values of that coloring function on
      the polygons are returned as the value of the slice3 function
      (numberof(color_values) == numberof(NVERTS) == number of polygons).

      If the slice function FSLICE is a function, it should be of the
      form:
         func fslice(m3, chunk)
      returning a list of function values on the specified chunk of the
      mesh m3.  The format of chunk depends on the type of m3 mesh, so
      you should use only the other mesh functions xyz3 and getv3 which
      take m3 and chunk as arguments.  The return value of fslice should
      have the same dimensions as the return value of getv3; the return
      value of xyz3 has an additional first dimension of length 3.

      If FSLICE is a list of 4 numbers, it is taken as a slicing plane
      with the equation FSLICE(+:1:3)*xyz(+)-FSLICE(4), as returned by
      plane3.

      If FSLICE is a single integer, the slice will be an isosurface for
      the FSLICEth variable associated with the mesh M3.  In this case,
      the keyword value= must also be present, representing the value
      of that variable on the isosurface.

      If FCOLOR is nil, slice3 returns nil.  If you want to color the
      polygons in a manner that depends only on their vertex coordinates
      (e.g.- by a 3D shading calculation), use this mode.

      If FCOLOR is a function, it should be of the form:
         func fcolor(m3, cells, l, u, fsl, fsu, ihist)
      returning a list of function values on the specified cells of the
      mesh m3.  The cells argument will be the list of cell indices in
      m3 at which values are to be returned.  l, u, fsl, fsu, and ihist
      are interpolation coefficients which can be used to interpolate
      from vertex centered values to the required cell centered values,
      ignoring the cells argument.  See getc3 source code.
      The return values should always have dimsof(cells).

      If FCOLOR is a single integer, the slice will be an isosurface for
      the FCOLORth variable associated with the mesh M3.

      If the optional argument after FCOLOR is non-nil and non-zero,
      then the FCOLOR function is called with only two arguments:
         func fcolor(m3, cells)

      The keyword argument NODE, if present and nonzero, is a signal
      to return node-centered values rather than cell-centered
      values. (ZCM 4/16/97)

    '''

    global _poly_permutations

    iso_index = None
    if not isinstance(fslice, collections.Callable):
        if 'value' not in kw and not is_scalar (fslice) and \
           len (numpy.shape (fslice)) == 1 and len (fslice) == 4 :
            normal = fslice [0:3]
            projection = fslice [3]
            fslice = _plane_slicer
        elif is_scalar (fslice) and type (fslice) == int:
            if 'value' not in kw :
                raise _Slice3Error('value= keyword required when FSLICE is mesh variable')
            _value = kw ['value']
            iso_index = fslice
            fslice = _isosurface_slicer
        else :
            raise _Slice3Error('illegal form of FSLICE argument, try help,slice3')

    if 'node' in kw :
        node = kw ['node']
    else :
        node = 0

    # will need cell list if fcolor function to be computed
    need_clist = len (args) > 0
    if len (args) > 1 :
        nointerp = args [1]
    else :
        nointerp = None

    if need_clist :
        fcolor = args [0]
        if fcolor == None :
            need_clist = 0
    else :
        fcolor = None

    # test the different possibilities for fcolor
    if need_clist and not isinstance(fcolor, collections.Callable):
        if not is_scalar (fcolor) or type (fcolor) != int :
            raise _Slice3Error('illegal form of FCOLOR argument, try help,slice3')

    # chunk up the m3 mesh and evaluate the slicing function to
    # find those cells cut by fslice==0
    # chunking avoids potentially disastrously large temporaries
    got_xyz = 0
    ntotal = 0
    # The following are used only for an irregular mesh, to
    # give the sizes of each portion of the mesh.
    ntotal8 = 0
    ntotal6 = 0
    ntotal5 = 0
    ntotal4 = 0
    # The following are used only for an irregular mesh, to
    # give the indices of the different types of chunk in the
    # results list.
    i8 = []
    i6 = []
    i5 = []
    i4 = []
    itot = [i4, i5, i6, i8]
    nchunk = 0
    results = []
    chunk = iterator3 (m3)
    cell_offsets = [0, 0, 0, 0]
    while chunk != None :

        # get the values of the slicing function at the vertices of
        # this chunk
        if fslice == _isosurface_slicer :
            fs = fslice (m3, chunk, iso_index, _value)
            # an isosurface slicer brings back a list [vals, None]
            # where vals is simply an array of the values of the
            # iso_index'th function on the vertices of the specified
            # chunk, or a triple, consisting of the array of
            # values, an array of relative cell numbers in the
            # chunk, and an offset to add to the preceding to
            # get absolute cell numbers.
        elif fslice == _plane_slicer :
            fs = fslice (m3, chunk, normal, projection)
            # In the case of a plane slice, fs is a list [vals, _xyz3]
            # (or [ [vals, clist, cell_offset], _xyz3] in the irregular case)
            # where _xyz3 is the array of vertices of the chunk. _xyz3
            # is ncells by 3 by something (in the irregular case),
            # ncells by 3 by 2 by 2 by 2 in the regular case,
            # and 3 by ni by nj by nk otherwise. vals will be
            # the values of the projections of the corresponding
            # vertex on the normal to the plane, positive if in
            # front, and negative if in back.
        else :
            fs = fslice (m3, chunk)
        if node == 1 and fcolor != None and not isinstance(fcolor, collections.Callable):
            # need vertex-centered data
            col = getv3 (fcolor, m3, chunk)
            if type (col) == list :
                col = col [0]
        else :
            col = None
        # ZCM 2/24/97 Elimination of _xyz3 as a global necessitates the following:
        # (_xyz3 comes back as the last element of the list fs)
        _xyz3 = fs [1]
        fs = fs [0]

        irregular = type (fs) == list
        if irregular :
            cell_offset = fs [2]

        # will need cell list if fslice did not compute xyz
        got_xyz = _xyz3 != None
        need_clist = need_clist or not got_xyz

        # If the m3 mesh is totally unstructured, the chunk should be
        # arranged so that fslice returns an ncells-by-2-by-2-by-2
        # (or ncells-by-3-by-2 or ncells-by-5 or ncells-by-4) array
        # of vertex values of the slicing function. Note that a
        # chunk of an irregular mesh always consists of just one
        # kind of cell.
        # On the other hand, if the mesh vertices are arranged in a
        # rectangular grid (or a few patches of rectangular grids), the
        # chunk should be the far less redundant rectangular patch.
        if (irregular) :
            # fs is a 2-sequence, of which the first element is an ncells-by-
            # 2-by-2-by-2 (by-3-by-2, by-5, or by-4) array, and the second
            # is the array of corresponding cell numbers.
            # here is the fastest way to generate the required cell list
            dims = numpy.shape (fs [0])
            dim1 = dims [0]
            slice3_precision = 0.0
            if len (dims) == 4 : # hex case
                # Note that the sum below will be between 1 and 7
                # precisely if f changes sign in the cell.
                critical_cells = numpy.bitwise_and (numpy.add.reduce \
                   (numpy.reshape (numpy.ravel (numpy.transpose (numpy.less (fs [0], slice3_precision))), \
                   (8, dim1))), 7)
                if (numpy.sum (critical_cells,axis=0) != 0) :
                    clist = numpy.take (fs [1], numpy.nonzero(critical_cells)[0],axis=0)
                    ntotal8 = ntotal8 + len (clist)
                else :
                    clist = None
                i8.append (len (results))
                cell_offsets [3] = cell_offset
            elif len (dims) == 3 : # prism case
                # Note that the sum below will be between 1 and 5
                # precisely if f changes sign in the cell.
                critical_cells = numpy.add.reduce \
                   (numpy.reshape (numpy.ravel (numpy.transpose (numpy.less (fs [0], slice3_precision))), \
                   (6, dim1)))
                critical_cells = numpy.logical_and (numpy.greater (critical_cells, 0),
                                             numpy.less (critical_cells, 6))
                if (numpy.sum (critical_cells,axis=0) != 0) :
                    clist = numpy.take (fs [1], numpy.nonzero(critical_cells)[0],axis=0)
                    ntotal6 = ntotal6 + len (clist)
                else :
                    clist = None
                i6.append (len (results))
                cell_offsets [2] = cell_offset
            elif dims [1] == 5 : # pyramid case
                # Note that the sum below will be between 1 and 4
                # precisely if f changes sign in the cell.
                critical_cells = numpy.add.reduce \
                   (numpy.reshape (numpy.ravel (numpy.transpose (numpy.less (fs [0], slice3_precision))), \
                   (5, dim1)))
                critical_cells = numpy.logical_and (numpy.greater (critical_cells, 0),
                                             numpy.less (critical_cells, 5))
                if (numpy.sum (critical_cells,axis=0) != 0) :
                    clist = numpy.take (fs [1], numpy.nonzero(critical_cells)[0],axis=0)
                    ntotal5 = ntotal5 + len (clist)
                else :
                    clist = None
                i5.append (len (results))
                cell_offsets [1] = cell_offset
            else : # tet case
                # Note that the sum below will be between 1 and 3
                # precisely if f changes sign in the cell.
                critical_cells = numpy.bitwise_and (numpy.add.reduce \
                   (numpy.reshape (numpy.ravel (numpy.transpose (numpy.less (fs [0], slice3_precision))), \
                   (4, dim1))), 3)
                if (numpy.sum (critical_cells,axis=0) != 0) :
                    clist = numpy.take (fs [1], numpy.nonzero(critical_cells)[0],axis=0)
                    ntotal4 = ntotal4 + len (clist)
                else :
                    clist = None
                i4.append (len (results))
                cell_offsets [0] = cell_offset
        else :
            dims = numpy.shape (fs)
            # fs is an ni-by-nj-by-nk array
            # result of the zcen is 0, 1/8, 2/8, ..., 7/8, or 1
#        slice3_precision = max (numpy.ravel (abs (fs))) * (-1.e-12)
            slice3_precision = 0
            clist1 = numpy.ravel (zcen_ (zcen_ (zcen_
               (numpy.array (numpy.less (fs, slice3_precision), numpy.float32), 0), 1), 2))
            clist1 = numpy.logical_and (numpy.less (clist1, .9), numpy.greater (clist1, .1))
            if numpy.sum (clist1,axis=0) > 0 :
                clist = numpy.nonzero(clist1)[0]
                ntotal = ntotal + len (clist)
            else :
                clist = None
            i8.append (len (results)) # Treat regular case as hex

        if clist != None :
            #  we need to save:
            # (1) the absolute cell indices of the cells in clist
            # (2) the corresponding ncells-by-2-by-2-by-2 (by-3-by-2,
            #     by-5, or by-4) list of fslice
            #     values at the vertices of these cells
            if (irregular) :
                # extract the portions of the data indexed by clist
                fs = numpy.take (fs [0], clist,axis=0)
                if got_xyz :
                    _xyz3 = numpy.take (_xyz3, clist,axis=0)
                if col :
                    col = numpy.take (col, clist,axis=0)
            else :
                # extract the to_corners portions of the data indexed by clist
                indices = to_corners3 (clist, dims [1], dims [2])
                no_cells = numpy.shape (indices) [0]
                indices = numpy.ravel (indices)
                fs = numpy.reshape (numpy.take (numpy.ravel (fs), indices,axis=0),\
                   (no_cells, 2, 2, 2))
                if got_xyz :
                    new_xyz3 = numpy.zeros ( (no_cells, 3, 2, 2, 2), numpy.float32 )
                    new_xyz3 [:, 0, ...] = numpy.reshape (numpy.take (numpy.ravel (_xyz3 [0, ...]),\
                       indices,axis=0), (no_cells, 2, 2, 2))
                    new_xyz3 [:, 1, ...] = numpy.reshape (numpy.take (numpy.ravel (_xyz3 [1, ...]),\
                       indices,axis=0), (no_cells, 2, 2, 2))
                    new_xyz3 [:, 2, ...] = numpy.reshape (numpy.take (numpy.ravel (_xyz3 [2, ...]),\
                       indices,axis=0), (no_cells, 2, 2, 2))
                    _xyz3 = new_xyz3
                    del new_xyz3
                if col != None :
                    col = numpy.reshape (numpy.take (numpy.ravel (col), indices,axis=0), (no_cells, 2, 2, 2))
                    # NB: col represents node colors, and is only used
                    # if those are requested.
            # here, the iterator converts to absolute cell indices without
            # incrementing the chunk
            if (need_clist) :
                clist = iterator3 (m3, chunk, clist)
            else :
                clist = None
            nchunk = nchunk + 1
            need_vert_col = col != None
            results.append ( [clist, fs, _xyz3, col])
        else :
            results.append ( [None, None, None, None])
        chunk = iterator3 (m3, chunk)
        # endwhile chunk != None

    # collect the results of the chunking loop
    if not ntotal and not (ntotal8 + ntotal6 + ntotal5 + ntotal4) :
        return None
    if ntotal : # (regular mesh, but can be handled same as hex)
        ntotal8 = ntotal
        i8 = list(range(len (results)))
        itot [3] = i8
    ntot = [ntotal4, ntotal5, ntotal6, ntotal8]
    new_results = []
    for i in range (len (ntot)) :
        # This loop processes each kind of cell independently,
        # the results to be combined at the end.
        if ntot [i] == 0 : # No cells of type i
            continue
        if need_clist :
            clist = numpy.zeros (ntot [i], numpy.int32)
            fs = numpy.zeros ( (ntot [i], _no_verts [i]), numpy.float32 )
            if got_xyz :
                xyz = numpy.zeros ( (ntot [i], 3, _no_verts [i]), numpy.float32 )
            else :
                xyz = None
        if need_vert_col :
            col = numpy.zeros ( (ntot [i], _no_verts [i]), numpy.float32 )
        else :
            col = None
        k = 0

       # collect the results of the chunking loop
        for j in range (len (itot [i])) :
            l = k
            k = k + len (results [itot [i] [j]] [0])
            if need_clist :
                clist [l:k] = results [itot [i] [j]] [0]
            fs [l:k] = numpy.reshape (results [itot [i] [j]] [1], (k - l, _no_verts [i]))
            if xyz != None :
                xyz [l:k] = numpy.reshape (results [itot [i] [j]] [2],
                   (k - l, 3, _no_verts [i]))
            if col != None :
                col [l:k] = numpy.reshape (results [itot [i] [j]] [3],
                   (k - l, _no_verts [i]))
        if not got_xyz :
            # zcm 2/4/97 go to absolute cell list again
            if i > 0 and len (m3 [1]) > 2 :
                adder = m3 [1] [3] [i - 1]
            else :
                adder = 0
            xyz = numpy.reshape (xyz3 (m3, clist + adder), (ntot [i], 3, _no_verts [i]))
        # produce the lists of edge intersection points
        # -- generate (nsliced)x12 (9, 8, 6) array of edge mask values
        # (mask non-zero if edge is cut by plane)
        below = numpy.less (fs, 0.0)
        # I put the following into C for speed
        mask = find_mask (below, _node_edges [i])
        lst = numpy.nonzero(mask)[0]
        edges = numpy.array (lst, copy = 1)
        cells = edges / _no_edges [i]
        edges = edges % _no_edges [i]
        # construct edge endpoint indices in fs, xyz arrays
        # the numbers are the endpoint indices corresponding to
        # the order of the _no_edges [i] edges in the mask array
        lower = numpy.take (_lower_vert [i], edges,axis=0) + _no_verts [i] * cells
        upper = numpy.take (_upper_vert [i], edges,axis=0) + _no_verts [i] * cells
        fsl = numpy.take (numpy.ravel (fs), lower,axis=0)
        fsu = numpy.take (numpy.ravel (fs), upper,axis=0)
        # following denominator guaranteed non-zero
        denom = fsu - fsl
        fsu = fsu / denom
        fsl = fsl / denom
        new_xyz = numpy.zeros ( (len (lower), 3), numpy.float32 )
        new_xyz [:, 0] = numpy.reshape ( (numpy.take (numpy.ravel (xyz [:, 0]), lower,axis=0) * fsu - \
           numpy.take (numpy.ravel (xyz [:, 0]), upper,axis=0) * fsl), (len (lower),))
        new_xyz [:, 1] = numpy.reshape ( (numpy.take (numpy.ravel (xyz [:, 1]), lower,axis=0) * fsu - \
           numpy.take (numpy.ravel (xyz [:, 1]), upper,axis=0) * fsl), (len (lower),))
        new_xyz [:, 2] = numpy.reshape ( (numpy.take (numpy.ravel (xyz [:, 2]), lower,axis=0) * fsu - \
           numpy.take (numpy.ravel (xyz [:, 2]), upper,axis=0) * fsl), (len (lower),))
        xyz = new_xyz
        del new_xyz
        if col != None :
            # Extract subset of the data the same way
            col = numpy.take (numpy.ravel (col), lower,axis=0) * fsu - \
               numpy.take (numpy.ravel (col), upper,axis=0) * fsl
        # The xyz array is now the output xyzverts array,
        # but for the order of the points within each cell.

        # give each sliced cell a 'pattern index' between 0 and 255
        # (non-inclusive) representing the pattern of its 8 corners
        # above and below the slicing plane
        p2 = numpy.left_shift (numpy.ones (_no_verts [i], numpy.int32) , numpy.array (
           [0, 1, 2, 3, 4, 5, 6, 7], numpy.int32) [0: _no_verts [i]])
        pattern = numpy.transpose (numpy.sum (numpy.transpose (numpy.multiply (below, p2)),axis=0))

        # broadcast the cell's pattern onto each of its sliced edges
        pattern = numpy.take (pattern, lst / _no_edges [i],axis=0)
        # Let ne represent the number of edges of this type of cell,
        # and nv the number of vertices.
        # To each pattern, there corresponds a permutation of the
        # twelve edges so that they occur in the order in which the
        # edges are to be connected.  Let each such permuation be
        # stored as a list of integers from 0 to ne - 1 such that
        # sorting the integers into increasing order rearranges the edges at
        # the corresponding indices into the correct order.  (The position
        # of unsliced edges in the list is arbitrary as long as the sliced
        # edges are in the proper order relative to each other.)
        # Let these permutations be stored in a ne-by-2**nv - 2 array
        # _poly_permutations (see next comment for explanation of 4 * ne):
        pattern = numpy.take (numpy.ravel (numpy.transpose (_poly_permutations [i])),
           _no_edges [i] * (pattern - 1) + edges,axis=0) + 4 * _no_edges [i] * cells
        order = numpy.argsort (pattern)
        xyz1 = numpy.zeros ( (len (order), 3), numpy.float32 )
        xyz1 [:,0] = numpy.take (numpy.ravel (xyz [:,0]), order,axis=0)
        xyz1 [:,1] = numpy.take (numpy.ravel (xyz [:,1]), order,axis=0)
        xyz1 [:,2] = numpy.take (numpy.ravel (xyz [:,2]), order,axis=0)
        xyz = xyz1
        if col != None :
            col = numpy.take (col, order,axis=0)
        edges = numpy.take (edges, order,axis=0)
        pattern = numpy.take (pattern, order,axis=0)
        # cells(order) is same as cells by construction */

        # There remains only the question of splitting the points in
        # a single cell into multiple disjoint polygons.
        # To do this, we need one more precomputed array: poly_splits
        # should be another ne-by-2**nv - 2 array with values between 0 and 3
        # 0 for each edge on the first part, 1 for each edge on the
        # second part, and so on up to 3 for each edge on the fourth
        # part.  The value on unsliced edges can be anything, say 0.
        # With a little cleverness poly_splits can be combined with
        # _poly_permutations, by putting _poly_permutations =
        # _poly_permutations(as described above) + _no_edges [i]*poly_splits
        # (this doesn't change the ordering of _poly_permutations).
        # I assume this has been done here:
        pattern = pattern / _no_edges [i]
        # now pattern jumps by 4 between cells, smaller jumps within cells
        # get the list of places where a new value begins, and form a
        # new pattern with values that increment by 1 between each plateau
        # pattern = dif_ (pattern, 0)
        pattern = pattern[1:] - pattern[:-1]
        nz = numpy.nonzero(pattern)[0]
        lst = numpy.zeros (len (nz) + 1, numpy.int32)
        lst [1:] = nz + 1
        newpat = numpy.zeros (len (pattern) + 1, numpy.int32)
        newpat [0] = 1
        newpat [1:] = numpy.cumsum (numpy.not_equal (pattern, 0),axis=0) + 1
        pattern = newpat
        nverts = numpy.bincount (pattern) [1:]
        xyzverts = xyz

        # finally, deal with any fcolor function
        if fcolor == None :
            new_results.append ( [nverts, xyzverts, None])
            continue

        # if some polys have been split, need to split clist as well
        if len (lst) > len (clist) :
            clist = numpy.take (clist, numpy.take (cells, lst, axis=0),axis=0)
        if col == None :
            if nointerp == None :
                if isinstance(fcolor, collections.Callable):
                    col = fcolor (m3, clist + cell_offsets [i], lower, upper, fsl,
                       fsu, pattern - 1)
                else :
                    col = getc3 (fcolor, m3, clist + cell_offsets [i], lower, upper,
                       fsl, fsu, pattern - 1)
            else :
                if isinstance(fcolor, collections.Callable):
                    col = fcolor (m3, clist + cell_offsets [i])
                else :
                    col = getc3 (fcolor, m3, clist + cell_offsets [i])
        new_results.append ( [nverts, xyzverts, col])
    # New loop to consolidate the return values
    nv_n = 0
    xyzv_n = 0
    col_n = 0
    for i in range (len (new_results)) :
        nv_n = nv_n + len (new_results [i] [0])
        xyzv_n = xyzv_n + numpy.shape (new_results [i] [1]) [0]
        if new_results [i] [2] != None :
            col_n = col_n + len (new_results [i] [2])
    nverts = numpy.zeros (nv_n, numpy.int32)
    xyzverts = numpy.zeros ( (xyzv_n, 3), numpy.float32 )
    if col_n != 0 :
        col = numpy.zeros (col_n, numpy.float32 )
    else :
        col = None
    nv_n1 = 0
    xyzv_n1 = 0
    col_n1 = 0
    for i in range (len (new_results)) :
        nv_n2 = len (new_results [i] [0])
        xyzv_n2 = numpy.shape (new_results [i] [1]) [0]
        nverts [nv_n1:nv_n1 + nv_n2] = new_results [i] [0]
        xyzverts [xyzv_n1:xyzv_n1 + xyzv_n2] = new_results [i] [1]
        if new_results [i] [2] != None :
            col_n2 = len (new_results [i] [2])
            col [col_n1:col_n1 + col_n2] = new_results [i] [2]
            col_n1 = col_n1 + col_n2
        nv_n1 = nv_n1 + nv_n2
        xyzv_n1 = xyzv_n1 + xyzv_n2
    return [nverts, xyzverts, col]

 # The iterator3 function combines three distinct operations:
 # (1) If only the M3 argument is given, return the initial
 #     chunk of the mesh.  The chunk will be no more than
 #     _chunk3_limit cells of the mesh.
 # (2) If only M3 and CHUNK are given, return the next CHUNK,
 #     or [] if there are no more chunks.
 # (3) If M3, CHUNK, and CLIST are all specified, return the
 #     absolute cell index list corresponding to the index list
 #     CLIST of the cells in the CHUNK.
 #     Do not increment the chunk in this case.
 #
 # The form of the CHUNK argument and return value for cases (1)
 # and (2) is not specified, but it must be recognized by the
 # xyz3 and getv3 functions which go along with this iterator3.
 # (For case (3), CLIST and the return value are both ordinary
 #  index lists.)

class _Slice3MeshError(Exception):
    pass

def slice3mesh (xyz, * args, ** kw) :

    '''
    slice3mesh returns a triple [nverts, xyzverts, color]
     nverts is no_cells long and the ith entry tells how many
        vertices the ith cell has.
     xyzverts is sum (nverts,axis=0) by 3 and gives the vertex
        coordinates of the cells in order.
     color, if present, is len (nverts) long and contains
        a color value for each cell in the mesh.

    There are a number of ways to call slice3mesh:

       slice3mesh (z, color = None)

    z is a two dimensional array of cell function values, assumed
       to be on a uniform mesh nx by ny cells (assuming z is nx by ny)
       nx being the number of cells in the x direction, ny the number
       in the y direction.
    color, if specified, is either an nx by ny array
       of cell-centered values by which the surface is to
       be colored, or an nx +1 by ny + 1 array of vertex-
       centered values, which will be averaged over each
       cell to give cell-centered values.

       slice3mesh (nxny, dxdy, x0y0, z, color = None)

    In this case, slice3mesh accepts the specification for
    a regular 2d mesh: nxny is the number of cells in the
    x direction and the y direction; x0y0 are the initial
    values of x and y; and dxdy are the increments in the
    two directions. z is the height of a surface above
    the xy plane and must be dimensioned nx + 1 by ny + 1.
    color, if specified, is as above.

       slice3mesh (x, y, z, color = None)

    z is as above, an nx by ny array of function values
    on a mesh of the same dimensions. There are two choices
    for x and y: they can both be one-dimensional, dimensioned
    nx and ny respectively, in which case they represent a
    mesh whose edges are parallel to the axes; or else they
    can both be nx by ny, in which case they represent a
    general quadrilateral mesh.
    color, if specified, is as above.
    '''

    two_d = 0
    if 'smooth' in kw :
        smooth = kw ['smooth']
    else :
        smooth = 0
    if len (args) == 0 :
        # Only the z argument is present
        if len (numpy.shape (xyz)) != 2 :
            raise _Slice3MeshError('z must be two dimensional.')
        else :
            z = xyz
            ncx = numpy.shape (xyz) [0]
            ncy = numpy.shape (xyz) [1]
            x = numpy.arange (ncx, dtype = numpy.float32 )
            y = numpy.arange (ncy, dtype = numpy.float32 )
    elif len (args) == 3 :
        # must be the (nxny, dxdy, x0y0, z...) form
        ncx = xyz [0] + 1
        ncy = xyz [1] + 1
        x = numpy.arange (ncx, dtype = numpy.float32 ) * args [0] [0] + args [1] [0]
        y = numpy.arange (ncy, dtype = numpy.float32 ) * args [0] [1] + args [1] [1]
        z = args [2]
        if (ncx, ncy) != numpy.shape (z) :
            raise _Slice3MeshError('The shape of z must match the shape of x and y.')
    elif len (args) == 2 :
        # must be the x, y, z format
        x = xyz
        y = args [0]
        z = args [1]
        dims = numpy.shape (x)
        if len (dims) == 2 :
            two_d = 1
            if dims != numpy.shape (y) or dims != numpy.shape (z) :
                raise _Slice3MeshError('The shapes of x, y, and z must match.')
            ncx = dims [0]
            ncy = dims [1]
        elif len (dims) == 1 :
            ncx = dims [0]
            ncy = len (y)
            if (ncx, ncy) != numpy.shape (z) :
                raise _Slice3MeshError('The shape of z must match the shape of x and y.')
        else :
            raise _Slice3MeshError('Unable to decipher arguments to slice3mesh.')
    else :
        raise _Slice3MeshError('Unable to decipher arguments to slice3mesh.')

    nverts = numpy.ones ( (ncx - 1) *  (ncy - 1), numpy.int32) * 4

    ncxx = numpy.arange (ncx - 1, dtype = numpy.int32) * (ncy)
    ncyy = numpy.arange (ncy - 1, dtype = numpy.int32)

    if 'color' in kw :
        color = kw ['color']
    else :
        color = None
    if color != None :
#     col = numpy.array (len (nverts), numpy.float32 )
        if numpy.shape (color) == (ncx - 1, ncy - 1) :
            col = color
        elif numpy.shape (color) == (ncx, ncy) and smooth == 0 :
            col = numpy.ravel (color)
            # Lower left, upper left, upper right, lower right
            col = 0.25 * (numpy.take (col, numpy.ravel (numpy.add.outer ( ncxx, ncyy)),axis=0) +
               numpy.take (col, numpy.ravel (numpy.add.outer ( ncxx, ncyy + 1)),axis=0) +
               numpy.take (col, numpy.ravel (numpy.add.outer ( ncxx + ncy, ncyy + 1)),axis=0) +
               numpy.take (col, numpy.ravel (numpy.add.outer ( ncxx + ncy, ncyy)),axis=0))
        elif numpy.shape (color) == (ncx, ncy) and smooth != 0 :
            # Node-centered colors are wanted (smooth plots)
            col = numpy.ravel (color)
            col = numpy.ravel (numpy.transpose (numpy.array ( [
               numpy.take (col, numpy.ravel (numpy.add.outer ( ncxx, ncyy)),axis=0),
               numpy.take (col, numpy.ravel (numpy.add.outer ( ncxx, ncyy + 1)),axis=0),
               numpy.take (col, numpy.ravel (numpy.add.outer ( ncxx + ncy, ncyy + 1)),axis=0),
               numpy.take (col, numpy.ravel (numpy.add.outer ( ncxx + ncy, ncyy)),axis=0)])))
        else :
            raise _Slice3MeshError('color must be cell-centered or vertex centered.')
    else :
        col = None
    xyzverts = numpy.zeros ( (4 * (ncx -1) * (ncy -1), 3), numpy.float32 )

    if not two_d :
        x1 = numpy.multiply.outer (numpy.ones (ncy - 1, numpy.float32), x [0:ncx - 1])
        x2 = numpy.multiply.outer (numpy.ones (ncy - 1, numpy.float32), x [1:ncx])
        xyzverts [:, 0] = numpy.ravel (numpy.transpose (numpy.array ([x1, x1, x2, x2])))
        del x1, x2
        y1 = numpy.multiply.outer (y [0:ncy - 1], numpy.ones (ncx - 1))
        y2 = numpy.multiply.outer (y [1:ncy], numpy.ones (ncx - 1))
        xyzverts [:, 1] = numpy.ravel (numpy.transpose (numpy.array ([y1, y2, y2, y1])))
        del y1, y2
    else :
        newx = numpy.ravel (x)
        xyzverts [:, 0] = numpy.ravel (numpy.transpose (numpy.array ( [
           numpy.take (newx, numpy.ravel (numpy.add.outer ( ncxx, ncyy)),axis=0),
           numpy.take (newx, numpy.ravel (numpy.add.outer ( ncxx, ncyy + 1)),axis=0),
           numpy.take (newx, numpy.ravel (numpy.add.outer ( ncxx + ncy, ncyy + 1)),axis=0),
           numpy.take (newx, numpy.ravel (numpy.add.outer ( ncxx + ncy, ncyy)),axis=0)])))
        newy = numpy.ravel (y)
        xyzverts [:, 1] = numpy.ravel (numpy.transpose (numpy.array ( [
           numpy.take (newy, numpy.ravel (numpy.add.outer ( ncxx, ncyy)),axis=0),
           numpy.take (newy, numpy.ravel (numpy.add.outer ( ncxx, ncyy + 1)),axis=0),
           numpy.take (newy, numpy.ravel (numpy.add.outer ( ncxx + ncy, ncyy + 1)),axis=0),
           numpy.take (newy, numpy.ravel (numpy.add.outer ( ncxx + ncy, ncyy)),axis=0)])))
    newz = numpy.ravel (z)
    xyzverts [:, 2] = numpy.ravel (numpy.transpose (numpy.array ( [
       numpy.take (newz, numpy.ravel (numpy.add.outer ( ncxx, ncyy)),axis=0),
       numpy.take (newz, numpy.ravel (numpy.add.outer ( ncxx, ncyy + 1)),axis=0),
       numpy.take (newz, numpy.ravel (numpy.add.outer ( ncxx + ncy, ncyy + 1)),axis=0),
       numpy.take (newz, numpy.ravel (numpy.add.outer ( ncxx + ncy, ncyy)),axis=0)])))

    return [nverts, xyzverts, col]

def iterator3 (m3 , chunk = None, clist = None) :

    '''
    iterator3 (m3)
    iterator3 (m3, chunk, clist)
    iterator3_rect (m3)
    iterator3_rect (m3, chunk, clist)
    iterator3_irreg (m3)
    iterator3_irreg (m3, chunk, clist)

    The iterator3 functions combine three distinct operations:
    (1) If only the M3 argument is given, return the initial
        chunk of the mesh.  The chunk will be no more than
        chunk3_limit cells of the mesh.
    (2) If only M3 and CHUNK are given, return the next CHUNK,
        or None if there are no more chunks.
    (3) If M3, CHUNK, and CLIST are all specified, return the
        absolute cell index list corresponding to the index list
        CLIST of the cells in the CHUNK.
        Do not increment the chunk in this case.

    The form of the CHUNK argument and return value for cases (1)
    and (2) is not specified, but it must be recognized by the
    xyz3 and getv3 functions which go along with this iterator3.
    (For case (3), CLIST and the return value are both ordinary
    index lists.)
    In the irregular case, it is guaranteed that the returned chunk
    consists of only one type of cell (tetrahedra, hexahedra,
    pyramids, or prisms).
    '''

    return m3 [0] [3] (m3, chunk, clist)

# biggest temporary is 3 doubles times this,
# perhaps 4 or 5 doubles times this is most at one time
_chunk3_limit = 10000

def iterator3_rect (m3, chunk, clist) :

    '''
    iterator3 (m3)
    iterator3 (m3, chunk, clist)
    iterator3_rect (m3)
    iterator3_rect (m3, chunk, clist)
    iterator3_irreg (m3)
    iterator3_irreg (m3, chunk, clist)

    The iterator3 functions combine three distinct operations:
    (1) If only the M3 argument is given, return the initial
        chunk of the mesh.  The chunk will be no more than
        chunk3_limit cells of the mesh.
    (2) If only M3 and CHUNK are given, return the next CHUNK,
        or None if there are no more chunks.
    (3) If M3, CHUNK, and CLIST are all specified, return the
        absolute cell index list corresponding to the index list
        CLIST of the cells in the CHUNK.
        Do not increment the chunk in this case.

    The form of the CHUNK argument and return value for cases (1)
    and (2) is not specified, but it must be recognized by the
    xyz3 and getv3 functions which go along with this iterator3.
    (For case (3), CLIST and the return value are both ordinary
    index lists.)
    In the irregular case, it is guaranteed that the returned chunk
    consists of only one type of cell (tetrahedra, hexahedra,
    pyramids, or prisms).
    '''

#  Note: if you look at the yorick version of this routine, you
#  will see that the significance of the subscripts is reversed.
#  This is because we do things in row-major order.

    global _chunk3_limit

    if chunk == None :
        dims = m3 [1] [0]      # [ni,nj,nk] cell dimensions
        [ni, nj, nk] = [dims [0], dims [1], dims [2]]
        njnk = nj * nk
        if _chunk3_limit <= nk :
            # stuck with 1D chunks
            ck = (nk - 1) / _chunk3_limit + 1
            cj = ci = 0
        elif _chunk3_limit <= njnk :
            # 2D chunks
            ci = ck = 0
            cj = (njnk - 1) / _chunk3_limit + 1
        else :
            # 3D chunks
            cj = ck = 0
            ci = (njnk * ni - 1) / _chunk3_limit + 1
        chunk = numpy.array ( [[ci == 0, cj == 0, ck == 0],
                         [not ci, nj * (ci != 0) + (ck != 0),
                          nk * ( (cj + ci) != 0)],
                         [ci, cj, ck], [ni, nj, nk]])
    else :
        ni = chunk [3,0]
        nj = chunk [3,1]
        nk = chunk [3,2]
        njnk = nj * nk
        offsets = numpy.array ( [njnk, nj, 1], numpy.int32)
        if clist != None :
            # add offset for this chunk to clist and return
            return numpy.sum (offsets * ( chunk [0] - 1),axis=0) + clist

    # increment to next chunk
    xi = chunk [1, 0]
    xj = chunk [1, 1]
    xk = chunk [1, 2]

    np = chunk [2, 2]
    if (np) :
        # 1D chunks
        if xk == nk :
            if xj == nj :
                if xi == ni : return None
                xi = xi + 1
                xj = 1;
            else :
                xj = xj + 1
            xk = 0
        ck = xk + 1
        step = ck / np
        frst = ck % np     # first frst steps are step+1
        if (xk < (step + 1) * frst) : step = step + 1
        xk = xk + step
        chunk [0] = numpy.array ( [xi, xj, ck])
        chunk [1] = numpy.array ( [xi, xj, xk])
    else :
        np = chunk [2, 1]
        if (np) :
            if (xj == nj) :
                if (xi == ni) : return None
                xi = xi + 1
                xj = 0
            cj = xj + 1
            step = nj / np
            frst = nj % np    # first frst steps are step+1
            if (xj < (step + 1) * frst) : step = step + 1
            xj = xj + step
            chunk [0, 0:2] = numpy.array ( [xi, cj])
            chunk [1, 0:2] = numpy.array ( [xi, xj])
        else :
            if xi == ni : return None
            ci = xi + 1
            np = chunk [2, 0]
            step = ni / np
            frst = ni % np    # first frst steps are step+1
            if (xi < (step + 1) * frst) : step = step + 1
            xi = xi + step
            chunk [0, 0] = ci
            chunk [1, 0] = xi
    return chunk

def iterator3_irreg (m3, chunk, clist) :

    '''
    iterator3 (m3)
    iterator3 (m3, chunk, clist)
    iterator3_rect (m3)
    iterator3_rect (m3, chunk, clist)
    iterator3_irreg (m3)
    iterator3_irreg (m3, chunk, clist)

    The iterator3 functions combine three distinct operations:
    (1) If only the M3 argument is given, return the initial
        chunk of the mesh.  The chunk will be no more than
        chunk3_limit cells of the mesh.
    (2) If only M3 and CHUNK are given, return the next CHUNK,
        or None if there are no more chunks.
    (3) If M3, CHUNK, and CLIST are all specified, return the
        absolute cell index list corresponding to the index list
        CLIST of the cells in the CHUNK.
        Do not increment the chunk in this case.

    The form of the CHUNK argument and return value for cases (1)
    and (2) is not specified, but it must be recognized by the
    xyz3 and getv3 functions which go along with this iterator3.
    (For case (3), CLIST and the return value are both ordinary
    index lists.)
    In the irregular case, it is guaranteed that the returned chunk
    consists of only one type of cell (tetrahedra, hexahedra,
    pyramids, or prisms).

    iterator3_irreg Does the same thing as iterator3_rect only for an
    irregular rectangular mesh. It simply splits a large mesh into smaller
    parts. Whether this is necessary I am not sure.
    Certainly it makes it easier in the irregular case to handle
    the four different types of cells separately.
    if clist is present, in the irregular case it is already
    the list of absolute cell indices, so it is simply returned.
    This and other routines to do with irregular meshes return a
    chunk which is a 2-list. The first item delimits the chunk;
    the second gives a list of corresponding cell numbers.
    '''

    global _chunk3_limit

    if clist != None:
        return clist

    dims = m3 [1] [0]     # ncells by _no_verts array of subscripts
                          # (or a list of from one to four of same)

    if type (dims) != list :
        if chunk == None:     # get the first chunk
            return [ [0, min (numpy.shape (dims) [0], _chunk3_limit)],
                     numpy.arange (0, min (numpy.shape (dims) [0], _chunk3_limit),
                     dtype = numpy.int32)]
        else :                # iterate to next chunk
            start = chunk [0] [1]
            if start >= numpy.shape(dims) [0] :
                return None
            else :
                return [ [start, min (numpy.shape (dims) [0], start + _chunk3_limit)],
                         numpy.arange (start, min (numpy.shape (dims) [0],
                                                   start + _chunk3_limit),
                         dtype = numpy.int32)]
    else :
        totals = m3 [1] [3] # cumulative totals of numbers of cells
        if chunk == None :
            return [ [0, min (totals [0], _chunk3_limit)],
                     numpy.arange (0, min (totals [0], _chunk3_limit),
                     dtype = numpy.int32)]
        else :                # iterate to next chunk
            start = chunk [0] [1]
            if start >= totals [-1] :
                return None
            else :
                for i in range (len (totals)) :
                    if start < totals [i] :
                        break
                return [ [start, min (totals [i], start + _chunk3_limit)],
                         numpy.arange (start,
                            min (totals [i], start + _chunk3_limit),
                            dtype = numpy.int32)]


def getv3 (i, m3, chunk) :

    '''
    getv3(i, m3, chunk)

      return vertex values of the Ith function attached to 3D mesh M3
      for cells in the specified CHUNK.  The CHUNK may be a list of
      cell indices, in which case getv3 returns a 2x2x2x(dimsof(CHUNK))
      list of vertex coordinates.  CHUNK may also be a mesh-specific data
      structure used in the slice3 routine, in which case getv3 may
      return a (ni)x(nj)x(nk) array of vertex values.  For meshes which
      are logically rectangular or consist of several rectangular
      patches, this is up to 8 times less data, with a concomitant
      performance advantage.  Use getv3 when writing slicing functions
      for slice3.
    '''

    return m3 [0] [1] (i, m3, chunk)

class _Getv3Error(Exception):
    pass

def getv3_rect (i, m3, chunk) :

    '''
    getv3_rect(i, m3, chunk) does the job for a regular rectangular
      mesh.
    '''

    fi = m3 [2]
    i = i - 1
    if i < 0 or is_scalar (fi) or i >= len (fi) :
        raise _Getv3Error('no such mesh function as F' + repr(i))
    dims = m3 [1] [0]
    if dims == numpy.shape (fi [i]) :
        raise _Getv3Error('mesh function F' + repr(i) + ' is not vertex-centered')
    if len (numpy.shape (chunk)) != 1 :
        c = chunk
        # The difference here is that our arrays are 0-based, while
        # yorick's are 1-based; and the last element in a range is not
        # included in the result array.
        return fi [i] [c [0, 0] - 1:1 + c [1, 0], c [0, 1] - 1:1 + c [1, 1] ,
                       c [0, 2] - 1:1 + c [1, 2]]
    else :
        # Need to create an array of fi values the same size and shape
        # as what to_corners3 returns.
        # To avoid exceedingly arcane calculations attempting to
        # go backwards to a cell list, this branch returns the list
        # [<function values>, chunk]
        # Then it is trivial for slice3 to find a list of cell
        # numbers in which fi changes sign.
        indices = to_corners3 (chunk, dims [0] + 1, dims [1] + 1)
        no_cells = numpy.shape (indices) [0]
        indices = numpy.ravel (indices)
        retval = numpy.reshape (numpy.take (numpy.ravel (fi [i]), indices,axis=0), (no_cells, 2, 2, 2))

        return [retval, chunk]

def getv3_irreg (i, m3, chunk) :

    '''
      for an irregular mesh, returns a 3-list whose elements are:
      (1) the function values for the ith function on the vertices of the
      given chunk. (The function values must have the same dimension
      as the coordinates; there is no attempt to convert zone-centered
      values to vertex-centered values.)
      (2) an array of relative cell numbers within the list of cells
      of this type.
      (3) a number that can be added to these relative numbers to gives
      the absolute cell numbers for correct access to their coordinates
      and function values.
    '''

    fi = m3 [2]
    i = i - 1
    if i < 0 or is_scalar (fi) or i >= len (fi) :
        raise _Getv3Error('no such function as F' + repr(i))
    # len (fi [i]) and the second dimension of m3 [1] [1] (xyz) should
    # be the same, i. e., there is a value associated with each coordinate.
    if len (fi [i]) != len (m3 [1] [1] [0]) :
        raise _Getv3Error('mesh function F' + repr(i) + ' is not vertex-centered.')

    verts = m3 [1] [0]
    oldstart = chunk [0] [0]
    oldfin = chunk [0] [1]
    no_cells = oldfin - oldstart

    if type (verts) != list : # Only one kind of cell in mesh
        indices = numpy.ravel (verts [oldstart:oldfin])
    else : # A list of possibly more than one kind
        sizes = m3 [1] [2]
        totals = m3 [1] [3]
        for j in range (len (totals)) :
            if oldfin <= totals [j] :
                break
        verts = verts [j]
        if j > 0 :
            start = oldstart - totals [j - 1]
            fin = oldfin - totals [j - 1]
        else :
            start = oldstart
            fin = oldfin
        indices = numpy.ravel (verts [start:fin])

    tc = numpy.shape (verts) [1]
    # ZCM 2/4/97 the array of cell numbers must be relative
    if tc == 8 : # hex cells
        return [ numpy.reshape (numpy.take (fi [i], indices,axis=0), (no_cells, 2, 2, 2)),
                numpy.arange (0, no_cells, dtype = numpy.int32), oldstart]
    elif tc == 6 : # pyramids
        return [ numpy.reshape (numpy.take (fi [i], indices,axis=0), (no_cells, 3, 2)),
                numpy.arange (0, no_cells, dtype = numpy.int32), oldstart]
    else : # tetrahedron or pyramid
        return [ numpy.reshape (numpy.take (fi [i], indices,axis=0), (no_cells, tc)),
                numpy.arange (0, no_cells, dtype = numpy.int32), oldstart]

class _Getc3Error(Exception):
    pass

def getc3 (i, m3, chunk, *args) :

    '''
    getc3(i, m3, chunk)
          or getc3(i, m3, clist, l, u, fsl, fsu, cells)

      return cell values of the Ith function attached to 3D mesh M3
      for cells in the specified CHUNK.  The CHUNK may be a list of
      cell indices, in which case getc3 returns a (dimsof(CHUNK))
      list of vertex coordinates.  CHUNK may also be a mesh-specific data
      structure used in the slice3 routine, in which case getc3 may
      return a (ni)x(nj)x(nk) array of vertex values.  There is no
      savings in the amount of data for such a CHUNK, but the gather
      operation is cheaper than a general list of cell indices.
      Use getc3 when writing colorng functions for slice3.

      If CHUNK is a CLIST, the additional arguments L, U, FSL, and FSU
      are vertex index lists which override the CLIST if the Ith attached
      function is defined on mesh vertices.  L and U are index lists into
      the (dimsof(CLIST))x2x2x2 vertex value array, say vva, and FSL
      and FSU are corresponding interpolation coefficients; the zone
      centered value is computed as a weighted average of involving these
      coefficients.  The CELLS argument is required by histogram to do
      the averaging.  See the source code for details.
      By default, this conversion (if necessary) is done by averaging
      the eight vertex-centered values.
     '''

    if len (args) == 0 :
        l = None
        u = None
        fsl = None
        fsu = None
        cells = None
    elif len (args) == 5 :
        l = args [0]
        u = args [1]
        fsl = args [2]
        fsu = args [3]
        cells = args [4]
    else :
        raise _Getc3Error('getc3 requires either three or eight parameters.')

    return m3 [0] [2] (i, m3, chunk, l, u, fsl, fsu, cells)

def getc3_rect (i, m3, chunk, l, u, fsl, fsu, cells) :

    '''
    getc3_rect (i, m3, chunk, l, u, fsl, fsu, cells) does the job
      for a regular rectangular mesh.
    '''

    fi = m3 [2]
    m3 = m3 [1]
    if ( i < 1 or i > len (fi)) :
        raise _Getc3Error('no such mesh function as F' + repr(i - 1))
    dims = m3 [0]
    if numpy.shape (fi [i - 1]) == dims :
        # it is a cell-centered quantity
        if len (numpy.shape (chunk)) != 1 :
            c = chunk
            # The difference here is that our arrays are 0-based, while
            # yorick's are 1-based; and the last element in a range is not
            # included in the result array.
            return fi [i - 1] [c [0, 0] - 1:1 + c [1, 0],
                               c [0, 1] - 1:1 + c [1, 1] ,
                               c [0, 2] - 1:1 + c [1, 2]]
        else :
            [k, l. m] = dims
            return numpy.reshape (numpy.take (numpy.ravel (fi [i - 1]), chunk,axis=0),
               (len (chunk), k, l, m))
    else :
        # it is vertex-centered, so we take averages to get cell quantity
        if len (numpy.shape (chunk)) != 1 :
            c = chunk
            # The difference here is that our arrays are 0-based, while
            # yorick's are 1-based; and the last element in a range is not
            # included in the result array.
            return zcen_ (zcen_( zcen_ (
                  (fi [i - 1] [c [0, 0] - 1:1 + c [1, 0],
                               c [0, 1] - 1:1 + c [1, 1] ,
                               c [0, 2] - 1:1 + c [1, 2]]), 0), 1), 2)
        else :
            indices = to_corners3 (chunk, dims [1] + 1,  dims [2] + 1)
            no_cells = numpy.shape (indices) [0]
            indices = numpy.ravel (indices)
            corners = numpy.take (numpy.ravel (fi [i - 1]), indices,axis=0)
            if l == None :
                return 0.125 * numpy.sum (numpy.transpose (numpy.reshape (corners, (no_cells, 8))),axis=0)
            else :
                # interpolate corner values to get edge values
                corners = (numpy.take (corners, l,axis=0) * fsu -
                   numpy.take (corners, u,axis=0) * fsl) / (fsu -fsl)
                # average edge values (vertex values of polys) on each poly
                return numpy.bincount (cells, corners) / numpy.bincount (cells)

def getc3_irreg (i, m3, chunk, l, u, fsl, fsu, cells) :

    '''
       Same thing as getc3_rect, i. e., returns the same type of
       data structure, but from an irregular mesh.
       m3 [1] is a 2-list; m3[1] [0] is an array whose ith element
          is an array of coordinate indices for the ith cell,
          or a list of up to four such arrays.
          m3 [1] [1] is the 3 by nverts array of coordinates.
       m3 [2] is a list of arrays of vertex-centered or cell-centered
          data.
       chunk may be a list, in which case chunk [0] is a 2-sequence
       representing a range of cell indices; or it may be a one-dimensional
       array, in which case it is a nonconsecutive set of cell indices.
       It is guaranteed that all cells indexed by the chunk are the
       same type.
    '''

    fi = m3 [2]
    if i < 1 or i > len (fi) :
        raise _Getc3Error('no such mesh function as F' + repr(i - 1))
    verts = m3 [1] [0]
    if type (verts) == list :
        sizes = m3 [1] [2]
        totals = m3 [1] [3]
    if type (verts) == list and totals [-1] == len (fi [i - 1]) or \
       type (verts) != list and numpy.shape (verts) [0] == len (fi [i - 1]) :
        # cell-centered case
        if type (chunk) == list :
            return fi [i - 1] [chunk [0] [0]:chunk [0] [1]]
        elif type (chunk) == numpy.ndarray and len (numpy.shape (chunk)) == 1 :
            return numpy.take (fi [i - 1], chunk,axis=0)
        else :
            raise _Getc3Error('chunk argument is incomprehensible.')

    if len (fi [i - 1]) != numpy.shape (m3 [1] [1]) [1] :
        raise _Getc3Error('F' + repr(i - 1) + ' has the wrong size to be ' \
           'either zone-centered or node-centered.')
    # vertex-centered case
    # First we need to pick up the vertex subscripts, which are
    # also the fi [i - 1] subscripts.
    if type (verts) != list :
        if type (chunk) == list :
            indices = verts [chunk [0] [0]:chunk [0] [1]]
        elif type (chunk) == numpy.ndarray and len (numpy.shape (chunk)) == 1 :
            indices = take (verts, chunk,axis=0)
        else :
            raise _Getc3Error('chunk argument is incomprehensible.')
    else :
        # We have a list of vertex subscripts, each for a different
        # type of cell; need to extract the correct list:
        if type (chunk) == list :
            start = chunk [0] [0]
            fin = chunk [0] [1]
            for j in range (len (totals)) :
                if fin <= totals [j] :
                    break
            verts = verts [j]
            if j > 0 :
                start = start - totals [j - 1]
                fin = fin - totals [j - 1]
            indices = verts [start:fin]
        elif type (chunk) == numpy.ndarray and len (numpy.shape (chunk)) == 1 :
            for j in range (len (totals)) :
                if chunk [-1] <= totals [j] :
                    break
            verts = verts [j]
            ch = chunk
            if j > 0 :
                ch = chunk - totals [j - 1]
            indices = numpy.take (verts, ch,axis=0)
        else :
            raise _Getc3Error('chunk argument is incomprehensible.')

    shp = numpy.shape (indices)
    no_cells = shp [0]
    indices = numpy.ravel (indices)
    corners = numpy.take (fi [i - 1], indices,axis=0)
    if l == None :
        return (1. / shp [1]) * numpy.transpose ((numpy.sum (numpy.transpose (numpy.reshape (corners,
           (no_cells, shp [1]))) [0:shp [1]],axis=0)))
    else :
        # interpolate corner values to get edge values
        corners = (numpy.take (corners, l,axis=0) * fsu -
           numpy.take (corners, u,axis=0) * fsl) / (fsu -fsl)
        # average edge values (vertex values of polys) on each poly
        return numpy.bincount (cells, corners) / numpy.bincount (cells)

_no_verts = numpy.array ( [4, 5, 6, 8])
_no_edges = numpy.array ( [6, 8, 9, 12])

# Lower and upper vertex subscripts for each edge
_lower_vert4 = numpy.array ( [0, 0, 0, 1, 2, 3], numpy.int32)
_lower_vert5 = numpy.array ( [0, 0, 0, 0, 1, 2, 3, 4], numpy.int32)
_lower_vert6 = numpy.array ( [0, 1, 0, 1, 2, 3, 0, 2, 4], numpy.int32)
_lower_vert8 = numpy.array ( [0, 1, 2, 3, 0, 1, 4, 5, 0, 2, 4, 6], numpy.int32)
_lower_vert = [_lower_vert4, _lower_vert5, _lower_vert6, _lower_vert8]
_upper_vert4 = numpy.array ( [1, 2, 3, 2, 3, 1], numpy.int32)
_upper_vert5 = numpy.array ( [1, 2, 3, 4, 2, 3, 4, 1], numpy.int32)
_upper_vert6 = numpy.array ( [4, 5, 2, 3, 4, 5, 1, 3, 5], numpy.int32)
_upper_vert8 = numpy.array ( [4, 5, 6, 7, 2, 3, 6, 7, 1, 3, 5, 7], numpy.int32)
_upper_vert = [_upper_vert4, _upper_vert5, _upper_vert6, _upper_vert8]

_node_edges8_s = numpy.array ( [ [1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0],
                        [0, 1, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0],
                        [0, 0, 1, 0, 1, 0, 0, 0, 0, 1, 0, 0],
                        [0, 0, 0, 1, 0, 1, 0, 0, 0, 1, 0, 0],
                        [1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0],
                        [0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0],
                        [0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 1],
                        [0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1]], numpy.int32)
_node_edges8 = numpy.array ( [ [0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1],
                        [0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 1],
                        [0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0],
                        [1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0],
                        [0, 0, 0, 1, 0, 1, 0, 0, 0, 1, 0, 0],
                        [0, 0, 1, 0, 1, 0, 0, 0, 0, 1, 0, 0],
                        [0, 1, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0],
                        [1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0]], numpy.int32)
_node_edges6_s = numpy.array ( [ [1, 0, 1, 0, 0, 0, 1, 0, 0],
                        [0, 1, 0, 1, 0, 0, 1, 0, 0],
                        [0, 0, 1, 0, 1, 0, 0, 1, 0],
                        [0, 0, 0, 1, 0, 1, 0, 1, 0],
                        [1, 0, 0, 0, 1, 0, 0, 0, 1],
                        [0, 1, 0, 0, 0, 1, 0, 0, 1]], numpy.int32)
_node_edges6 = numpy.array ( [ [0, 1, 0, 0, 0, 1, 0, 0, 1],
                        [1, 0, 0, 0, 1, 0, 0, 0, 1],
                        [0, 0, 0, 1, 0, 1, 0, 1, 0],
                        [0, 0, 1, 0, 1, 0, 0, 1, 0],
                        [0, 1, 0, 1, 0, 0, 1, 0, 0],
                        [1, 0, 1, 0, 0, 0, 1, 0, 0]], numpy.int32)
_node_edges4_s = numpy.array ( [ [1, 1, 1, 0, 0, 0],
                        [1, 0, 0, 1, 0, 1],
                        [0, 1, 0, 1, 1, 0],
                        [0, 0, 1, 0, 1, 1]], numpy.int32)
_node_edges4 = numpy.array ( [ [0, 0, 1, 0, 1, 1],
                        [0, 1, 0, 1, 1, 0],
                        [1, 0, 0, 1, 0, 1],
                        [1, 1, 1, 0, 0, 0]], numpy.int32)
_node_edges5_s = numpy.array ( [ [1, 1, 1, 1, 0, 0, 0, 0],
                        [1, 0, 0, 0, 1, 0, 0, 1],
                        [0, 1, 0, 0, 1, 1, 0, 0],
                        [0, 0, 1, 0, 0, 1, 1, 0],
                        [0, 0, 0, 1, 0, 0, 1, 1]], numpy.int32)
_node_edges5 = numpy.array ( [ [0, 0, 0, 1, 0, 0, 1, 1],
                        [0, 0, 1, 0, 0, 1, 1, 0],
                        [0, 1, 0, 0, 1, 1, 0, 0],
                        [1, 0, 0, 0, 1, 0, 0, 1],
                        [1, 1, 1, 1, 0, 0, 0, 0]], numpy.int32)

_node_edges = [_node_edges4_s, _node_edges5_s, _node_edges6_s, _node_edges8_s]
_node_edges3 = [_node_edges4, _node_edges5, _node_edges6, _node_edges8]

def _construct3 (itype) :
    global _node_edges
    global _no_verts
    global _no_edges
    i = numpy.arange (1, 2**_no_verts [itype] - 1, dtype = numpy.int32)
    if itype == 0 :
        below = numpy.transpose (numpy.not_equal (numpy.array ( [numpy.bitwise_and (i, 8),
                                               numpy.bitwise_and (i, 4),
                                               numpy.bitwise_and (i, 2),
                                               numpy.bitwise_and (i, 1)]), 0))
    elif itype == 1 :
        below = numpy.transpose (numpy.not_equal (numpy.array ( [numpy.bitwise_and (i, 16),
                                               numpy.bitwise_and (i, 8),
                                               numpy.bitwise_and (i, 4),
                                               numpy.bitwise_and (i, 2),
                                               numpy.bitwise_and (i, 1)]), 0))
    elif itype == 2 :
        below = numpy.transpose (numpy.not_equal (numpy.array ( [numpy.bitwise_and (i, 32),
                                               numpy.bitwise_and (i, 16),
                                               numpy.bitwise_and (i, 8),
                                               numpy.bitwise_and (i, 4),
                                               numpy.bitwise_and (i, 2),
                                               numpy.bitwise_and (i, 1)]), 0))
    elif itype == 3 :
        below = numpy.transpose (numpy.not_equal (numpy.array ( [numpy.bitwise_and (i, 128),
                                               numpy.bitwise_and (i, 64),
                                               numpy.bitwise_and (i, 32),
                                               numpy.bitwise_and (i, 16),
                                               numpy.bitwise_and (i, 8),
                                               numpy.bitwise_and (i, 4),
                                               numpy.bitwise_and (i, 2),
                                               numpy.bitwise_and (i, 1)]), 0))
    # For some reason the node edges for a cell need to be in different order
    # here than in slice3 to get the correct results. Hence _node_edges3.
    mask = find_mask (below, _node_edges3 [itype])

    return construct3 (mask, itype)

# ------------------------------------------------------------------------

_poly_permutations4 = _construct3 (0)
_poly_permutations5 = _construct3 (1)
_poly_permutations6 = _construct3 (2)
_poly_permutations8 = _construct3 (3)

_poly_permutations = [_poly_permutations4, _poly_permutations5,
                     _poly_permutations6, _poly_permutations8]

class _ContourError(Exception):
    pass

# ------------------------------------------------------------------------

def plzcont (nverts, xyzverts, contours = 8, scale = 'lin', clear = 1,
   edges = 0, color = None, cmin = None, cmax = None,
   zaxis_min = None, zaxis_max = None, split = 0) :

    '''
    plzcont (nverts, xyzverts, contours = 8, scale = 'lin', clear = 1,
    edges = 0, color = None, cmin = None, cmax = None,
    zaxis_min = None, zaxis_max = None, split = 0)

      Plot filled z contours on the specified surface. NVERTS and
      XYZVERTS arrays specify the polygons for the surface being
      drawn. CONTOURS can be one of the following:
         N, an integer: Plot N contours (therefore, N+1 colored
         components of the surface)
         CVALS, a vector of floats: draw the contours at the
         specified levels.
      SCALE can be 'lin', 'log', or 'normal' specifying the
      contour scale. (Only applicable if contours = N, of course).
      If CLEAR = 1, clear the display list first.
      If EDGES = 1, plot the edges.
      The algorithm is to apply slice2x repeatedly to the surface.
      If color == None, then bytscl the palette into N + 1 colors
      and send each of the slices to pl3tree with the appropriate color.
      If color == 'bg', will plot only the edges.
      If CMIN is given, use it instead of the minimum z actually
      being plotted in the computation of contour levels. If CMAX is given,
      use it instead of the maximum z actually being plotted in the
      computation of contour levels. This is done so that a component
      of a larger graph will have the same colors at the same levels
      as every other component, rather than its levels being based
      on its own max and min, which may lie inside those of the
      rest of the graph.
      ZAXIS_MIN and ZAXIS_MAX represent axis limits on z as expressed
      by the user. If present, ZAXIS_MIN will inhibit plotting of all
      lesser z values, and ZAXIS_MAX will inhibit the plotting of all
      greater z values.
    '''

    # 1. Get contour colors
    if type (contours) == int :
        n = contours
        if cmin != None :
            vcmin = cmin
            minz = min (xyzverts [:, 2])
        else :
            vcmin = min (xyzverts [:, 2])
            minz = vcmin
        if cmax != None :
            vcmax = cmax
            maxz = max (xyzverts [:, 2])
        else :
            vcmax = max (xyzverts [:, 2])
            maxz = vcmax
        if scale == 'lin' :
            vc = vcmin + numpy.arange (1, n + 1, dtype = numpy.float32) * \
               (vcmax - vcmin) / (n + 1)
        elif scale == 'log' :
            vc = vcmin + numpy.exp (numpy.arange (1, n + 1, dtype = numpy.float32) * \
               numpy.log (vcmax - vcmin) / (n + 1))
        elif scale == 'normal' :
            zlin = xyzverts [:, 2]
            lzlin = len (zlin)
            zbar = numpy.add.reduce (zlin) / lzlin
            zs = numpy.sqrt ( (numpy.add.reduce (zlin ** 2) - lzlin * zbar ** 2) /
                (lzlin - 1))
            z1 = zbar - 2. * zs
            z2 = zbar + 2. * zs
            diff = (z2 - z1) / (n - 1)
            vc = z1 + numpy.arange (n) * diff
        else :
            raise _ContourError('Incomprehensible scale parameter.')
    elif type (contours) == numpy.ndarray and contours.dtype == numpy.float32 :
        n = len (contours)
        vc = sort (contours)
    else :
        raise _ContourError('Incorrect contour specification.')
    if split == 0 :
        colors = (numpy.arange (n + 1, dtype = numpy.float32) * (199. / n)).astype (numpy.uint8)
    else :
        colors = (numpy.arange (n + 1, dtype = numpy.float32) * (99. / n)).astype (numpy.uint8)
    # 2. Loop through slice2x calls
    nv = numpy.array (nverts, copy = 1)
    xyzv = numpy.array (xyzverts, copy = 1)
    if clear == 1 :
        clear3 ( ) # Clear any previous plot or we're in trouble
    # find imin--contours below this number need not be computed,
    # and imax--contours at this level and above need not be computed.
    imin = imax = 0
    for i in range (n) :
        if vc [i] <= minz :
            imin = i + 1
        if vc [i] >= maxz :
            imax = i
            break
        if i == n - 1 :
            imax = n
    # now make sure that the minimum and maximum contour levels computed
    # are not outside the axis limits.
    if zaxis_min != None and zaxis_min > vc [imin] :
        for i in range (imin, imax) :
            if i + 1 < imax and zaxis_min > vc [i + 1] :
                imin = i + 1
            else :
                break
        vc [imin] = zaxis_min
    if zaxis_max != None and zaxis_max < vc [imax - 1] :
        for i in range (imax - imin) :
            if imax - 2 >= imin and zaxis_max < vc [imax - 2] :
                imax = imax - 1
            else :
                break
        vc [imax - 1] = zaxis_max
    for i in range (imin, imax) :
        [nv, xyzv, d1, nvb, xyzvb, d2] = \
           slice2x (numpy.array ( [0., 0., 1., vc [i]], numpy.float32) , nv, xyzv, None)
        if i == imin and zaxis_min != None and zaxis_min == vc [i]:
            # Don't send the 'back' surface if it's below zaxis_min.
            continue
        else:
            if color == None :
                pl3tree (nvb, xyzvb, (numpy.ones (len (nvb)) * colors [i]).astype (numpy.uint8),
                   split = 0, edges = edges)
            else :
                # N. B. Force edges to be on, otherwise the graph is empty.
                pl3tree (nvb, xyzvb, 'bg', split = 0, edges = 1)
    if zaxis_max == None or vc [imax - 1] < zaxis_max:
        # send 'front' surface if it's not beyond zaxis_max
        if color == None :
            pl3tree (nv, xyzv, (numpy.ones (len (nv)) * colors [i]).astype (numpy.uint8),
               split = 0, edges = edges)
        else :
            pl3tree (nv, xyzv, 'bg', split = 0, edges = 1)

def pl4cont (nverts, xyzverts, values, contours = 8, scale = 'lin', clear = 1,
   edges = 0, color = None, cmin = None, cmax = None,
   caxis_min = None, caxis_max = None, split = 0) :

    '''
    pl4cont (nverts, xyzverts, values, contours = 8, scale = 'lin', clear = 1,
    edges = 0, color = None, cmin = None, cmax = None,
    caxis_min = None, caxis_max = None, split = 0)

      Plot filled z contours on the specified surface. VALUES is
      a node-centered array the same length as SUM (NVERTS) whose
      contours will be drawn. NVERTS and
      XYZVERTS arrays specify the polygons for the surface being
      drawn. CONTOURS can be one of the following:
         N, an integer: Plot N contours (therefore, N+1 colored
         components of the surface)
         CVALS, a vector of floats: draw the contours at the
         specified levels.
      SCALE can be 'lin', 'log', or 'normal' specifying the
      contour scale. (Only applicable if contours = N, of course).
      If CLEAR == 1, clear the display list first.
      If EDGES == 1, plot the edges.
      The algorithm is to apply slice2x repeatedly to the surface.
      If color == None, then bytscl the palette into N + 1 colors
      and send each of the slices to pl3tree with the appropriate color.
      If color == 'bg', will plot only the edges.
      If CMIN is given, use it instead of the minimum c actually
      being plotted in the computation of contour levels. If CMAX is given,
      use it instead of the maximum c actually being plotted in the
      computation of contour levels. This is done so that a component
      of a larger graph will have the same colors at the same levels
      as every other component, rather than its levels being based
      on its own max and min, which may lie inside those of the
      rest of the graph.
      CAXIS_MIN and CAXIS_MAX represent axis limits on c as expressed
      by the user. If present, CAXIS_MIN will inhibit plotting of all
      lesser c values, and CAXIS_MAX will inhibit the plotting of all
      greater c values.
    '''

    # 1. Get contour colors
    if type (contours) == int :
        n = contours
        if cmin != None :
            vcmin = cmin
            minz = min (values)
        else :
            vcmin = min (values)
            minz = vcmin
        if cmax != None :
            vcmax = cmax
            maxz = max (values)
        else :
            vcmax = max (values)
            maxz = vcmax
        if scale == 'lin' :
            vc = vcmin + numpy.arange (1, n + 1, \
               dtype = numpy.float32) * \
               (vcmax - vcmin) / (n + 1)
        elif scale == 'log' :
            vc = vcmin + exp (numpy.arange (1, n + 1, \
               dtype = numpy.float32) * \
               log (vcmax - vcmin) / (n + 1))
        elif scale == 'normal' :
            zbar = numpy.add.reduce (values) / lzlin
            zs = numpy.sqrt ( (numpy.add.reduce (values ** 2) - lzlin * zbar ** 2) /
                (lzlin - 1))
            z1 = zbar - 2. * zs
            z2 = zbar + 2. * zs
            diff = (z2 - z1) / (n - 1)
            vc = z1 + numpy.arange (n) * diff
        else :
            raise _ContourError('Incomprehensible scale parameter.')
    elif type (contours) == numpy.ndarray and contours.dtype == numpy.float32 :
        n = len (contours)
        vc = sort (contours)
    else :
        raise _ContourError('Incorrect contour specification.')
    if split == 0 :
        colors = (numpy.arange (n + 1, dtype = numpy.float32) * (199. / n)).astype (numpy.uint8)
    else :
        colors = (numpy.arange (n + 1, dtype = numpy.float32) * (99. / n)).astype (numpy.uint8)
    # 2. Loop through slice2x calls
    nv = numpy.array (nverts, copy = 1)
    xyzv = numpy.array (xyzverts, copy = 1)
    vals = numpy.array (values, copy = 1)
    if clear == 1 :
        clear3 ( ) # Clear any previous plot or we're in trouble
    # find imin--contours below this number need not be computed,
    # and imax--contours at this level and above need not be computed.
    imin = imax = 0
    for i in range (n) :
        if vc [i] <= minz :
            imin = i + 1
        if vc [i] >= maxz :
            imax = i
            break
        if i == n - 1 :
            imax = n
    # now make sure that the minimum and maximum contour levels computed
    # are not outside the axis limits.
    if caxis_min != None and caxis_min > vc [imin] :
        for i in range (imin, imax) :
            if i + 1 < imax and caxis_min > vc [i + 1] :
                imin = i + 1
            else :
                break
        vc [imin] = caxis_min
    if caxis_max != None and caxis_max < vc [imax - 1] :
        for i in range (imax - imin) :
            if imax - 2 >= imin and caxis_max < vc [imax - 2] :
                imax = imax - 1
            else :
                break
        vc [imax - 1] = caxis_max
    for i in range (n) :
        if vc [i] <= minz :
            continue
        if vc [i] >= maxz :
            break
        [nv, xyzv, vals, nvb, xyzvb, d2] = \
           slice2x (vc [i], nv, xyzv, vals)
        if i == imin and caxis_min != None and caxis_min == vc [i]:
            # Don't send the 'back' surface if it's below caxis_min.
            continue
        else:
            if color == None :
                pl3tree (nvb, xyzvb, (numpy.ones (len (nvb)) * colors [i]).astype (numpy.uint8),
                   split = 0, edges = edges)
            else :
                # N. B. Force edges to be on, otherwise the graph is empty.
                pl3tree (nvb, xyzvb, 'bg', split = 0, edges = 1)
    if caxis_max == None or vc [imax - 1] < caxis_max:
        # send 'front' surface if it's not beyond caxis_max
        if color == None :
            pl3tree (nv, xyzv, (numpy.ones (len (nv)) * colors [i]).astype (numpy.uint8),
               split = 0, edges = edges)
        else :
            pl3tree (nv, xyzv, 'bg', split = 0, edges = 1)

def slice2x (plane, nverts, xyzverts, values = None) :

    '''
    slice2x (plane, nverts, xyzverts, values)

      Slice a polygon list, retaining only those polygons or
      parts of polygons on the positive side of PLANE, that is,
      the side where xyz(+)*PLANE(+:1:3)-PLANE(4) > 0.0.
      The NVERTS, VALUES, and XYZVERTS arrays have the meanings of
      the return values from the slice3 function.
      Python returns a sextuple
      [nverts, xyzverts, values, nvertb, xyzvertb, valueb]
      with None in the place of missing or None input arguments.

    slice2_precision= precision
      Controls how slice2 (or slice2x) handles points very close to
      the slicing plane.  PRECISION should be a positive number or zero.
      Zero PRECISION means to clip exactly to the plane, with points
      exactly on the plane acting as if they were slightly on the side
      the normal points toward.  Positive PRECISION means that edges
      are clipped to parallel planes a distance PRECISION on either
      side of the given plane.  (Polygons lying entirely between these
      planes are completely discarded.)

      Default value is 0.0.

    '''

#    Note (ZCM 2/24/97) Reomved _slice2x as a global and added
#    it as a final argument to slice2.

    retval = slice2 (plane, nverts, xyzverts, values, 1)
    retval = retval + [None] * (6 - len (retval))
    return retval


class _Pl3surfError(Exception):
  pass

def pl3surf(nverts, xyzverts = None, values = None, cmin = None, cmax = None,
            lim = None, edges = 0) :
    '''
    pl3surf (nverts, xyzverts)
          or pl3surf (nverts, xyzverts, values)

      Perform simple 3D rendering of an object created by slice3
      (possibly followed by slice2).  NVERTS and XYZVERTS are polygon
      lists as returned by slice3, so XYZVERTS is sum(NVERTS,axis=0)-by-3,
      where NVERTS is a list of the number of vertices in each polygon.
      If present, the VALUES should have the same length as NVERTS;
      they are used to color the polygon.  If VALUES is not specified,
      the 3D lighting calculation set up using the light3 function
      will be carried out.  Keywords cmin= and cmax= as for plf, pli,
      or plfp are also accepted.  (If you do not supply VALUES, you
      probably want to use the ambient= keyword to light3 instead of
      cmin= here, but cmax= may still be useful.)
    '''

    _draw3 = get_draw3_ ( )
    if type (nverts) == list :
        lst = nverts
        nverts = lst [0]
        xyzverts = numpy.array (lst [1], copy = 1)
        values = lst [2]
        cmin = lst [3]
        cmax = lst [4]
        edges = lst [6]
        ## Scale xyzverts to avoid loss of accuracy
        minx = min (xyzverts [:, 0])
        maxx = max (xyzverts [:, 0])
        miny = min (xyzverts [:, 1])
        maxy = max (xyzverts [:, 1])
        minz = min (xyzverts [:, 2])
        maxz = max (xyzverts [:, 2])
        xyzverts [:, 0] = (xyzverts [:, 0] - minx) / (maxx - minx)
        xyzverts [:, 1] = (xyzverts [:, 1] - miny) / (maxy - miny)
        xyzverts [:, 2] = (xyzverts [:, 2] - minz) / (maxz - minz)
        xyztmp = get3_xy (xyzverts, 1)
        x = xyztmp [:, 0]
        y = xyztmp [:, 1]
        z = xyztmp [:, 2]
        if values == None :
#        xyzverts [:, 0] = x
#        xyzverts [:, 1] = y
#        xyzverts [:, 2] = z
            values = get3_light (xyztmp, nverts)
        [lst, vlist] = sort3d (z, nverts)
        nverts = numpy.take (nverts, lst,axis=0)
        values = numpy.take (values, lst,axis=0)
        x = numpy.take (x, vlist,axis=0)
        y = numpy.take (y, vlist,axis=0)
        _square = get_square_ ( )
        [_xfactor, _yfactor] = get_factors_ ()
        xmax = max (x)
        xmin = min (x)
        ymax = max (y)
        ymin = min (y)
        xdif = xmax - xmin
        ydif = ymax - ymin
        if _xfactor != 1. :
            xmax = xmax + (_xfactor - 1.) * xdif /2.
            xmin = xmin - (_xfactor - 1.) * xdif /2.
        if _yfactor != 1. :
            ymax = ymax + (_yfactor - 1.) * ydif /2.
            ymin = ymin - (_yfactor - 1.) * ydif /2.
        if _square :
            xdif = xmax - xmin
            ydif = ymax - ymin
            if xdif > ydif :
                dif = (xdif - ydif) / 2.
                ymin = ymin - dif
                ymax = ymax + dif
            elif ydif > xdif :
                dif = (ydif - xdif) / 2.
                xmin = xmin - dif
                xmax = xmax + dif

        plfp (values, y, x, nverts, cmin = cmin, cmax = cmax, legend = '',
           edges = edges)
        return [xmin, xmax, ymin, ymax]

    nverts = numpy.array (nverts, numpy.int32)
    xyzverts = numpy.array (xyzverts, numpy.float32 )

    if numpy.shape(xyzverts) [0] != numpy.sum(nverts,axis=0) or numpy.sum(numpy.less(nverts, 3),axis=0) or \
       nverts.dtype != numpy.int32 :
        print nverts.dtype != numpy.int32
        print numpy.sum (numpy.less (nverts, 3),axis=0)
        print numpy.shape (xyzverts) [0]
        print numpy.sum (nverts,axis=0)
        raise _Pl3surfError('illegal or inconsistent polygon list')
    if values != None and len (values) != len (nverts) :
        raise _Pl3surfError('illegal or inconsistent polygon color values')

    if values != None :
        values = numpy.array (values, numpy.float32 )

    clear3 ( )
    set3_object ( pl3surf, [nverts, xyzverts, values, cmin, cmax, lim, edges])
    if (_draw3) :
        # Plot the current list if _draw3 has been set.
        call_idler ( )
    if lim :
        tmp = get3_xy (xyzverts, 1)
        return max ( max (abs (tmp [:,0:2])))
    else :
        return None


# ------------------------------------------------------------------------

class _Pl3treeError(Exception):
    pass 

def pl3tree (nverts, xyzverts = None, values = None, plane = None,
             cmin = None, cmax = None, split = 1, edges = 0) :

    '''
    pl3tree (nverts, xyzverts = None, values = None, plane = None,
       cmin = None, cmax = None)

      Add the polygon list specified by NVERTS (number of vertices in
      each polygon) and XYZVERTS (3-by-sum(NVERTS,axis=0) vertex coordinates)
      to the currently displayed b-tree.  If VALUES is specified, it
      must have the same dimension as NVERTS, and represents the color
      of each polygon.  If VALUES is not specified, the polygons
      are assumed to form an isosurface which will be shaded by the
      current 3D lighting model; the isosurfaces are at the leaves of
      the b-tree, sliced by all of the planes.  If PLANE is specified,
      the XYZVERTS must all lie in that plane, and that plane becomes
      a new slicing plane in the b-tree.

      Each leaf of the b-tree consists of a set of sliced isosurfaces.
      A node of the b-tree consists of some polygons in one of the
      planes, a b-tree or leaf entirely on one side of that plane, and
      a b-tree or leaf on the other side.  The first plane you add
      becomes the root node, slicing any existing leaf in half.  When
      you add an isosurface, it propagates down the tree, getting
      sliced at each node, until its pieces reach the existing leaves,
      to which they are added.  When you add a plane, it also propagates
      down the tree, getting sliced at each node, until its pieces
      reach the leaves, which it slices, becoming the nodes closest to
      the leaves.

      tree is a 4-element list like this:
       [plane, back_tree, inplane_leaf, front_tree]
       plane= tree [0]  is None if this is just a leaf
                        in which case, only inplane_leaf is not None
       back_tree= tree [1]    is the part behind plane
       inplane_leaf= tree [2] is the part in the plane itself
       front_tree= tree [3]   is the part in front of plane

      This structure is relatively easy to plot, since from any
      viewpoint, a node can always be plotted in the order from one
      side, then the plane, then the other side.

      This routine assumes a 'split palette'; the colors for the
      VALUES will be scaled to fit from color 0 to color 99, while
      the colors from the shading calculation will be scaled to fit
      from color 100 to color 199.  (If VALUES is specified as a char
      array, however, it will be used without scaling.)
      You may specifiy a cmin= or cmax= keyword to affect the
      scaling; cmin is ignored if VALUES is not specified (use the
      ambient= keyword from light3 for that case).
    '''

#    (ZCM 4/23/97) Add the split keyword. This will determine
#    whether or not to split the palette (half to the isosurfaces
#    for shading and the other half to plane sections for contouring).

#    (ZCM 7/17/97) Add a calculation of the maximum and minimum
#    of everything that is put into the tree. This cures distortion
#    caused by loss of accuracy in orientation calculations.
#    What is now put on the display list is pl3tree and [tree, minmax];
#    both components are passed to _pl3tree to normalize results.

    # avoid overhead of local variables for _pl3tree and _pl3leaf
    # -- I don't know if this is such a big deal
    _draw3 = get_draw3_ ()
    if type (nverts) == list :
        _nverts = []
        for i in range (len (nverts)) :
            _nverts.append (nverts [i])
        return _pl3tree (_nverts [0], nverts [1])

    # We need copies of everything, or else arrays get clobbered.
    nverts = numpy.array (nverts, numpy.int32)
    xyzverts = numpy.array (xyzverts, numpy.float32 )
    if values == 'background' :
        values = 'bg'
    elif values != None and values != 'bg' :
        values = numpy.array (values, values.dtype)
    if plane != None :
        plane = plane.astype (numpy.float32)

    if numpy.shape(xyzverts)[0] != numpy.sum(nverts,axis=0) or numpy.sum(numpy.less (nverts, 3),axis=0) > 0 or \
       type (nverts[0]) != numpy.int32:
        print('Dim1 of xyzverts [%d], sum(nverts,axis=0) [%d], sum(less(nverts,3),axis=0) [%d], type(nverts[0]) [%s].' %
            ( numpy.shape (xyzverts) [0],
              numpy.sum (nverts,axis=0),
              numpy.sum (numpy.less (nverts, 3),axis=0),
              repr(type (nverts [0])),
            ))


        raise _Pl3treeError('illegal or inconsistent polygon list.')
    if type (values) == numpy.ndarray and len (values) != len (nverts) and \
       len (values) != numpy.sum (nverts,axis=0) :
        raise _Pl3treeError('illegal or inconsistent polygon color values')
    if type (values) == numpy.ndarray and len (values) == numpy.sum (nverts,axis=0) :
        # We have vertex-centered values, which for Gist must be
        # averaged over each cell
        lst = numpy.zeros (numpy.sum (nverts,axis=0), numpy.int32)
        array_set (lst, numpy.cumsum (nverts,axis=0) [0:-1], numpy.ones (len (nverts), numpy.int32))
        tpc = values.dtype
        values = (numpy.bincount (numpy.cumsum (lst,axis=0), values) / nverts).astype (tpc)
    if plane != None :
        if (len (numpy.shape (plane)) != 1 or numpy.shape (plane) [0] != 4) :
            raise _Pl3treeError('illegal plane format, try plane3 function')

    # Note: a leaf is going to be a list of lists.
    leaf = [ [nverts, xyzverts, values, cmin, cmax, split, edges]]

    ## max and min of current leaf
    minmax = numpy.array ( [min (xyzverts [:, 0]), max (xyzverts [:, 0]),
                      min (xyzverts [:, 1]), max (xyzverts [:, 1]),
                      min (xyzverts [:, 2]), max (xyzverts [:, 2])])

    # retrieve current b-tree (if any) from 3D display list
    _draw3_list = get_draw3_list_ ()
    _draw3_n = get_draw3_n_ ()
    try :
        tree = _draw3_list [_draw3_n:]
    except :
        tree = []
    if tree == [] or tree [0] != pl3tree :
        tree = [plane, [], leaf, []]
    else :
        oldminmax = tree [1] [1]
        tree = tree [1] [0]
        ## Find new minmax for whole tree
        minmax = numpy.array ( [min (minmax [0], oldminmax [0]),
                          max (minmax [1], oldminmax [1]),
                          min (minmax [2], oldminmax [2]),
                          max (minmax [3], oldminmax [3]),
                          min (minmax [4], oldminmax [4]),
                          max (minmax [5], oldminmax [5])])
        _pl3tree_add (leaf, plane, tree)
        set_multiple_components (1)

    tmp = has_multiple_components ()
    clear3 ()
    set_multiple_components (tmp)
#  plist (tree)
    set3_object (pl3tree, [tree, minmax])
    if (_draw3) :
        ## Plot the current list
        call_idler ( )

palette_dict = {
   'earth.gp' :
      [numpy.array ([0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 2, 2, 3, 4, 5, 5, 6, 7, 8,
               8, 9, 10, 11, 11, 12, 13, 14, 15, 15, 16, 17, 18, 18, 19,
               20, 21, 22, 22, 23, 24, 25, 26, 26, 27, 28, 29, 30, 31, 31,
               32, 33, 34, 35, 36, 36, 37, 38, 39, 40, 41, 41, 42, 43, 44,
               45, 46, 47, 48, 48, 48, 49, 49, 50, 50, 51, 51, 52, 52, 53,
               53, 54, 54, 55, 55, 56, 56, 57, 57, 58, 58, 59, 59, 60, 61,
               61, 62, 62, 63, 63, 64, 64, 65, 65, 66, 67, 67, 68, 68, 69,
               69, 70, 71, 73, 76, 78, 81, 83, 86, 88, 91, 94, 96, 99, 101,
               104, 106, 109, 111, 114, 117, 119, 121, 122, 124, 126, 128,
               129, 131, 133, 135, 136, 138, 140, 141, 143, 145, 147, 149,
               150, 152, 154, 156, 157, 159, 161, 163, 165, 166, 168, 170,
               172, 174, 175, 177, 179, 181, 183, 183, 184, 184, 185, 185,
               186, 186, 187, 187, 187, 188, 188, 189, 189, 190, 190, 190,
               191, 191, 192, 192, 193, 195, 196, 197, 198, 199, 201, 202,
               203, 204, 205, 207, 208, 209, 210, 211, 213, 214, 215, 216,
               217, 219, 220, 221, 222, 223, 225, 226, 227, 228, 229, 231,
               232, 233, 234, 235, 237, 238, 239, 240, 241, 243, 244, 245,
               246, 247, 249, 250, 251, 252, 253, 255], 'B'),
      numpy.array ( [0, 0, 0, 0, 0, 0, 0, 0, 3, 6, 8, 11, 13, 16, 18, 21, 23, 26,
               28, 31, 33, 36, 38, 41, 43, 45, 48, 50, 52, 55, 57, 59, 61,
               64, 66, 68, 70, 72, 74, 77, 79, 81, 83, 85, 87, 89, 91, 93,
               95, 97, 99, 100, 102, 104, 106, 108, 109, 111, 113, 115,
               116, 118, 120, 121, 123, 125, 126, 128, 128, 129, 129, 130,
               131, 131, 132, 133, 133, 134, 134, 135, 136, 136, 137, 138,
               138, 139, 140, 140, 141, 141, 142, 143, 143, 144, 145, 145,
               146, 146, 147, 148, 148, 149, 150, 150, 151, 151, 152, 153,
               153, 154, 155, 155, 156, 156, 157, 158, 158, 159, 160, 160,
               161, 161, 162, 163, 163, 164, 165, 165, 166, 166, 167, 168,
               168, 168, 169, 169, 170, 170, 171, 171, 172, 172, 172, 173,
               173, 174, 174, 175, 175, 175, 176, 176, 177, 177, 178, 178,
               179, 179, 179, 180, 180, 181, 181, 182, 182, 183, 183, 182,
               181, 181, 180, 179, 178, 177, 176, 175, 174, 173, 172, 171,
               170, 169, 168, 167, 166, 165, 164, 163, 163, 164, 164, 165,
               165, 166, 167, 167, 168, 169, 170, 171, 172, 173, 174, 175,
               176, 177, 178, 179, 181, 182, 184, 185, 187, 188, 190, 192,
               194, 196, 198, 200, 202, 204, 206, 208, 211, 213, 215, 218,
               221, 223, 226, 229, 232, 235, 238, 241, 244, 248, 251, 255],
               'B'),
      numpy.array ( [0, 46, 58, 69, 81, 92, 104, 116, 116, 116, 116, 116, 117,
               117, 117, 117, 117, 118, 118, 118, 118, 118, 119, 119, 119,
               119, 119, 120, 120, 120, 120, 120, 121, 121, 121, 121, 121,
               122, 122, 122, 122, 122, 123, 123, 123, 123, 123, 124, 124,
               124, 124, 124, 125, 125, 125, 125, 125, 126, 126, 126, 126,
               126, 127, 127, 127, 127, 127, 128, 126, 125, 124, 123, 122,
               120, 119, 118, 117, 115, 114, 113, 111, 110, 109, 108, 106,
               105, 104, 102, 101, 100, 98, 97, 96, 94, 93, 92, 90, 89, 88,
               86, 85, 84, 82, 81, 80, 78, 77, 76, 74, 73, 71, 70, 71, 72,
               72, 73, 73, 74, 75, 75, 76, 76, 77, 77, 78, 79, 79, 80, 80,
               81, 82, 82, 82, 83, 83, 83, 84, 84, 84, 85, 85, 85, 86, 86,
               86, 87, 87, 87, 88, 88, 88, 89, 89, 89, 90, 90, 90, 91, 91,
               91, 92, 92, 92, 93, 93, 93, 94, 94, 94, 95, 95, 95, 96, 96,
               97, 97, 97, 98, 98, 98, 99, 99, 99, 100, 100, 100, 101, 101,
               104, 106, 108, 111, 113, 116, 118, 121, 123, 126, 129, 131,
               134, 137, 139, 142, 145, 148, 150, 153, 156, 159, 162, 165,
               168, 170, 173, 176, 179, 182, 185, 189, 192, 195, 198, 201,
               204, 207, 211, 214, 217, 220, 224, 227, 230, 234, 237, 241,
               244, 248, 251, 255] , 'B')],
   'gray.gp' : [
      numpy.array ( [
               0, 1, 2, 3, 4, 5, 6, 7, 9, 10, 11, 12, 13, 14, 15, 16, 17,
               18, 19, 20, 21, 22, 23, 25, 26, 27, 28, 29, 30, 31, 32, 33,
               34, 35, 36, 37, 38, 39, 41, 42, 43, 44, 45, 46, 47, 48, 49,
               50, 51, 52, 53, 54, 55, 57, 58, 59, 60, 61, 62, 63, 64, 65,
               66, 67, 68, 69, 70, 71, 73, 74, 75, 76, 77, 78, 79, 80, 81,
               82, 83, 84, 85, 86, 87, 89, 90, 91, 92, 93, 94, 95, 96, 97,
               98, 99, 100, 101, 102, 103, 105, 106, 107, 108, 109, 110,
               111, 112, 113, 114, 115, 116, 117, 118, 119, 121, 122, 123,
               124, 125, 126, 127, 128, 129, 130, 131, 132, 133, 134, 135,
               137, 138, 139, 140, 141, 142, 143, 144, 145, 146, 147, 148,
               149, 150, 151, 153, 154, 155, 156, 157, 158, 159, 160, 161,
               162, 163, 164, 165, 166, 167, 169, 170, 171, 172, 173, 174,
               175, 176, 177, 178, 179, 180, 181, 182, 183, 185, 186, 187,
               188, 189, 190, 191, 192, 193, 194, 195, 196, 197, 198, 199,
               201, 202, 203, 204, 205, 206, 207, 208, 209, 210, 211, 212,
               213, 214, 215, 217, 218, 219, 220, 221, 222, 223, 224, 225,
               226, 227, 228, 229, 230, 231, 233, 234, 235, 236, 237, 238,
               239, 240, 241, 242, 243, 244, 245, 246, 247, 249, 250, 251,
               252, 253, 254, 255
              ] , 'B'),
      numpy.array ( [
               0, 1, 2, 3, 4, 5, 6, 7, 9, 10, 11, 12, 13, 14, 15, 16, 17,
               18, 19, 20, 21, 22, 23, 25, 26, 27, 28, 29, 30, 31, 32, 33,
               34, 35, 36, 37, 38, 39, 41, 42, 43, 44, 45, 46, 47, 48, 49,
               50, 51, 52, 53, 54, 55, 57, 58, 59, 60, 61, 62, 63, 64, 65,
               66, 67, 68, 69, 70, 71, 73, 74, 75, 76, 77, 78, 79, 80, 81,
               82, 83, 84, 85, 86, 87, 89, 90, 91, 92, 93, 94, 95, 96, 97,
               98, 99, 100, 101, 102, 103, 105, 106, 107, 108, 109, 110,
               111, 112, 113, 114, 115, 116, 117, 118, 119, 121, 122, 123,
               124, 125, 126, 127, 128, 129, 130, 131, 132, 133, 134, 135,
               137, 138, 139, 140, 141, 142, 143, 144, 145, 146, 147, 148,
               149, 150, 151, 153, 154, 155, 156, 157, 158, 159, 160, 161,
               162, 163, 164, 165, 166, 167, 169, 170, 171, 172, 173, 174,
               175, 176, 177, 178, 179, 180, 181, 182, 183, 185, 186, 187,
               188, 189, 190, 191, 192, 193, 194, 195, 196, 197, 198, 199,
               201, 202, 203, 204, 205, 206, 207, 208, 209, 210, 211, 212,
               213, 214, 215, 217, 218, 219, 220, 221, 222, 223, 224, 225,
               226, 227, 228, 229, 230, 231, 233, 234, 235, 236, 237, 238,
               239, 240, 241, 242, 243, 244, 245, 246, 247, 249, 250, 251,
               252, 253, 254, 255
              ] , 'B'),
      numpy.array ( [
               0, 1, 2, 3, 4, 5, 6, 7, 9, 10, 11, 12, 13, 14, 15, 16, 17,
               18, 19, 20, 21, 22, 23, 25, 26, 27, 28, 29, 30, 31, 32, 33,
               34, 35, 36, 37, 38, 39, 41, 42, 43, 44, 45, 46, 47, 48, 49,
               50, 51, 52, 53, 54, 55, 57, 58, 59, 60, 61, 62, 63, 64, 65,
               66, 67, 68, 69, 70, 71, 73, 74, 75, 76, 77, 78, 79, 80, 81,
               82, 83, 84, 85, 86, 87, 89, 90, 91, 92, 93, 94, 95, 96, 97,
               98, 99, 100, 101, 102, 103, 105, 106, 107, 108, 109, 110,
               111, 112, 113, 114, 115, 116, 117, 118, 119, 121, 122, 123,
               124, 125, 126, 127, 128, 129, 130, 131, 132, 133, 134, 135,
               137, 138, 139, 140, 141, 142, 143, 144, 145, 146, 147, 148,
               149, 150, 151, 153, 154, 155, 156, 157, 158, 159, 160, 161,
               162, 163, 164, 165, 166, 167, 169, 170, 171, 172, 173, 174,
               175, 176, 177, 178, 179, 180, 181, 182, 183, 185, 186, 187,
               188, 189, 190, 191, 192, 193, 194, 195, 196, 197, 198, 199,
               201, 202, 203, 204, 205, 206, 207, 208, 209, 210, 211, 212,
               213, 214, 215, 217, 218, 219, 220, 221, 222, 223, 224, 225,
               226, 227, 228, 229, 230, 231, 233, 234, 235, 236, 237, 238,
               239, 240, 241, 242, 243, 244, 245, 246, 247, 249, 250, 251,
               252, 253, 254, 255
              ] , 'B')
      ],
   'heat.gp' : [
      numpy.array ( [
               0, 1, 2, 4, 5, 7, 8, 10, 11, 13, 15, 17, 18, 20, 21, 23, 24,
               26, 27, 28, 30, 31, 33, 34, 36, 37, 39, 40, 42, 43, 46, 47,
               49, 50, 52, 53, 55, 56, 57, 59, 60, 62, 63, 65, 66, 68, 69,
               70, 72, 73, 76, 78, 79, 81, 82, 84, 85, 86, 88, 89, 92, 94,
               95, 97, 98, 99, 101, 102, 104, 105, 108, 110, 111, 113, 114,
               115, 117, 118, 120, 121, 123, 124, 126, 127, 128, 130, 131,
               133, 134, 136, 139, 140, 141, 143, 144, 146, 147, 149, 150,
               152, 153, 155, 156, 157, 159, 160, 162, 163, 165, 166, 169,
               170, 172, 173, 175, 176, 178, 179, 181, 182, 185, 186, 188,
               189, 191, 192, 194, 195, 197, 198, 201, 202, 204, 205, 207,
               208, 210, 211, 212, 214, 215, 217, 218, 220, 221, 223, 224,
               226, 227, 228, 231, 233, 234, 236, 237, 239, 240, 241, 243,
               244, 246, 247, 249, 250, 252, 253, 255, 255, 255, 255, 255,
               255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255,
               255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255,
               255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255,
               255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255,
               255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255,
               255, 255, 255, 255, 255, 255, 255, 255, 255
              ] , 'B'),
      numpy.array ( [
               0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
               0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
               0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
               0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
               0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
               0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 3, 5, 7, 9, 11,
               15, 17, 18, 20, 22, 24, 26, 28, 30, 32, 35, 37, 39, 41, 43,
               45, 47, 49, 51, 52, 54, 56, 58, 60, 62, 64, 66, 68, 69, 71,
               75, 77, 79, 81, 83, 85, 86, 88, 90, 92, 94, 96, 98, 100,
               102, 103, 105, 107, 109, 111, 115, 117, 119, 120, 122, 124,
               126, 128, 130, 132, 136, 137, 139, 141, 143, 145, 147, 149,
               151, 153, 156, 158, 160, 162, 164, 166, 168, 170, 171, 173,
               175, 177, 179, 181, 183, 185, 187, 188, 190, 192, 196, 198,
               200, 202, 204, 205, 207, 209, 211, 213, 215, 217, 219, 221,
               222, 224, 226, 228, 230, 232, 236, 238, 239, 241, 243, 245,
               247, 249, 251, 253
              ] , 'B'),
      numpy.array ( [
               0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
               0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
               0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
               0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
               0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
               0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
               0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
               0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
               0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
               7, 11, 15, 19, 23, 27, 31, 35, 39, 43, 51, 54, 58, 62, 66,
               70, 74, 78, 82, 86, 90, 94, 98, 102, 105, 109, 113, 117,
               121, 125, 133, 137, 141, 145, 149, 153, 156, 160, 164, 168,
               172, 176, 180, 184, 188, 192, 196, 200, 204, 207, 215, 219,
               223, 227, 231, 235, 239, 243, 247, 251
              ] , 'B')
      ],
   'rainbow.gp' : [
      numpy.array ( [
               255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255,
               255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255,
               255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255,
               255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255,
               255, 255, 255, 255, 255, 245, 240, 235, 229, 224, 219, 213,
               208, 202, 197, 192, 186, 181, 175, 170, 159, 154, 149, 143,
               138, 132, 127, 122, 116, 111, 106, 100, 95, 89, 84, 73, 68,
               63, 57, 52, 46, 41, 36, 30, 25, 19, 14, 9, 3, 0, 0, 0, 0,
               0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
               0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
               0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
               0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
               0, 0, 0, 0, 0, 2, 7, 18, 24, 29, 34, 40, 45, 50, 56, 61, 67,
               72, 77, 83, 88, 93, 104, 110, 115, 120, 126, 131, 136, 142,
               147, 153, 158, 163, 169, 174, 180, 190, 196, 201, 206, 212,
               217, 223, 228, 233, 239, 244, 249, 255, 255, 255, 255, 255,
               255, 255, 255, 255, 255
              ] , 'B'),
      numpy.array ( [
               0, 0, 0, 0, 0, 0, 0, 0, 5, 11, 16, 22, 27, 32, 38, 43, 48,
               54, 59, 65, 70, 75, 81, 91, 97, 102, 108, 113, 118, 124,
               129, 135, 140, 145, 151, 156, 161, 167, 178, 183, 188, 194,
               199, 204, 210, 215, 221, 226, 231, 237, 242, 247, 253, 255,
               255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255,
               255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255,
               255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255,
               255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255,
               255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255,
               255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255,
               255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255,
               255, 255, 255, 255, 250, 239, 234, 228, 223, 218, 212, 207,
               201, 196, 191, 185, 180, 174, 169, 164, 153, 148, 142, 137,
               131, 126, 121, 115, 110, 105, 99, 94, 88, 83, 78, 67, 62,
               56, 51, 45, 40, 35, 29, 24, 18, 13, 8, 2, 0, 0, 0, 0, 0, 0,
               0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
               0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
               0, 0, 0, 0, 0, 0, 0, 0
              ] , 'B'),
      numpy.array ( [
               42, 36, 31, 26, 20, 15, 10, 4, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
               0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
               0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
               0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
               0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1,
               12, 17, 23, 28, 33, 39, 44, 49, 55, 60, 66, 71, 76, 82, 87,
               98, 103, 109, 114, 119, 125, 130, 135, 141, 146, 152, 157,
               162, 168, 173, 184, 189, 195, 200, 205, 211, 216, 222, 227,
               232, 238, 243, 248, 254, 255, 255, 255, 255, 255, 255, 255,
               255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255,
               255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255,
               255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255,
               255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255,
               255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255,
               255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255,
               255, 255, 255, 255, 255, 255, 255, 255, 255, 254, 249, 243,
               233, 227, 222, 217, 211, 206, 201
              ] , 'B')
      ],
   'stern.gp' : [
      numpy.array ( [
               0, 18, 36, 54, 72, 90, 108, 127, 145, 163, 199, 217, 235,
               254, 249, 244, 239, 234, 229, 223, 218, 213, 208, 203, 197,
               192, 187, 182, 177, 172, 161, 156, 151, 146, 140, 135, 130,
               125, 120, 115, 109, 104, 99, 94, 89, 83, 78, 73, 68, 63, 52,
               47, 42, 37, 32, 26, 21, 16, 11, 6, 64, 65, 66, 67, 68, 69,
               70, 71, 72, 73, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85,
               86, 87, 88, 89, 90, 91, 92, 93, 94, 96, 97, 98, 99, 100,
               101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112,
               113, 114, 115, 117, 118, 119, 120, 121, 122, 123, 124, 125,
               126, 128, 129, 130, 131, 132, 133, 134, 135, 136, 137, 139,
               140, 141, 142, 143, 144, 145, 146, 147, 148, 149, 150, 151,
               152, 153, 154, 155, 156, 157, 158, 160, 161, 162, 163, 164,
               165, 166, 167, 168, 169, 170, 171, 172, 173, 174, 175, 176,
               177, 178, 179, 181, 182, 183, 184, 185, 186, 187, 188, 189,
               190, 192, 193, 194, 195, 196, 197, 198, 199, 200, 201, 203,
               204, 205, 206, 207, 208, 209, 210, 211, 212, 213, 214, 215,
               216, 217, 218, 219, 220, 221, 222, 224, 225, 226, 227, 228,
               229, 230, 231, 232, 233, 234, 235, 236, 237, 238, 239, 240,
               241, 242, 243, 245, 246, 247, 248, 249, 250, 251, 252, 253,
               254
              ] , 'B'),
      numpy.array ( [
               0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 11, 12, 13, 14, 15, 16, 17, 18,
               19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 32, 33, 34,
               35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49,
               50, 51, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 64, 65, 66,
               67, 68, 69, 70, 71, 72, 73, 75, 76, 77, 78, 79, 80, 81, 82,
               83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 96, 97, 98,
               99, 100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110,
               111, 112, 113, 114, 115, 117, 118, 119, 120, 121, 122, 123,
               124, 125, 126, 128, 129, 130, 131, 132, 133, 134, 135, 136,
               137, 139, 140, 141, 142, 143, 144, 145, 146, 147, 148, 149,
               150, 151, 152, 153, 154, 155, 156, 157, 158, 160, 161, 162,
               163, 164, 165, 166, 167, 168, 169, 170, 171, 172, 173, 174,
               175, 176, 177, 178, 179, 181, 182, 183, 184, 185, 186, 187,
               188, 189, 190, 192, 193, 194, 195, 196, 197, 198, 199, 200,
               201, 203, 204, 205, 206, 207, 208, 209, 210, 211, 212, 213,
               214, 215, 216, 217, 218, 219, 220, 221, 222, 224, 225, 226,
               227, 228, 229, 230, 231, 232, 233, 234, 235, 236, 237, 238,
               239, 240, 241, 242, 243, 245, 246, 247, 248, 249, 250, 251,
               252, 253, 254
              ] , 'B'),
      numpy.array ( [
               0, 1, 3, 5, 7, 9, 11, 13, 15, 17, 21, 23, 25, 27, 29, 31,
               33, 35, 37, 39, 41, 43, 45, 47, 49, 51, 53, 55, 57, 59, 63,
               65, 67, 69, 71, 73, 75, 77, 79, 81, 83, 85, 87, 89, 91, 93,
               95, 97, 99, 101, 105, 107, 109, 111, 113, 115, 117, 119,
               121, 123, 127, 129, 131, 133, 135, 137, 139, 141, 143, 145,
               149, 151, 153, 155, 157, 159, 161, 163, 165, 167, 169, 171,
               173, 175, 177, 179, 181, 183, 185, 187, 191, 193, 195, 197,
               199, 201, 203, 205, 207, 209, 211, 213, 215, 217, 219, 221,
               223, 225, 227, 229, 233, 235, 237, 239, 241, 243, 245, 247,
               249, 251, 255, 251, 247, 243, 238, 234, 230, 226, 221, 217,
               209, 204, 200, 196, 192, 187, 183, 179, 175, 170, 166, 162,
               158, 153, 149, 145, 141, 136, 132, 128, 119, 115, 111, 107,
               102, 98, 94, 90, 85, 81, 77, 73, 68, 64, 60, 56, 51, 47, 43,
               39, 30, 26, 22, 17, 13, 9, 5, 0, 3, 7, 15, 19, 22, 26, 30,
               34, 38, 41, 45, 49, 57, 60, 64, 68, 72, 76, 79, 83, 87, 91,
               95, 98, 102, 106, 110, 114, 117, 121, 125, 129, 137, 140,
               144, 148, 152, 156, 159, 163, 167, 171, 175, 178, 182, 186,
               190, 194, 197, 201, 205, 209, 216, 220, 224, 228, 232, 235,
               239, 243, 247, 251
              ] , 'B')
      ],
   'yarg.gp' : [
      numpy.array ( [
               255, 254, 253, 252, 251, 250, 249, 248, 246, 245, 244, 243,
               242, 241, 240, 239, 238, 237, 236, 235, 234, 233, 232, 230,
               229, 228, 227, 226, 225, 224, 223, 222, 221, 220, 219, 218,
               217, 216, 214, 213, 212, 211, 210, 209, 208, 207, 206, 205,
               204, 203, 202, 201, 200, 198, 197, 196, 195, 194, 193, 192,
               191, 190, 189, 188, 187, 186, 185, 184, 182, 181, 180, 179,
               178, 177, 176, 175, 174, 173, 172, 171, 170, 169, 168, 166,
               165, 164, 163, 162, 161, 160, 159, 158, 157, 156, 155, 154,
               153, 152, 150, 149, 148, 147, 146, 145, 144, 143, 142, 141,
               140, 139, 138, 137, 136, 134, 133, 132, 131, 130, 129, 128,
               127, 126, 125, 124, 123, 122, 121, 120, 118, 117, 116, 115,
               114, 113, 112, 111, 110, 109, 108, 107, 106, 105, 104, 102,
               101, 100, 99, 98, 97, 96, 95, 94, 93, 92, 91, 90, 89, 88,
               86, 85, 84, 83, 82, 81, 80, 79, 78, 77, 76, 75, 74, 73, 72,
               70, 69, 68, 67, 66, 65, 64, 63, 62, 61, 60, 59, 58, 57, 56,
               54, 53, 52, 51, 50, 49, 48, 47, 46, 45, 44, 43, 42, 41, 40,
               38, 37, 36, 35, 34, 33, 32, 31, 30, 29, 28, 27, 26, 25, 24,
               22, 21, 20, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8, 6,
               5, 4, 3, 2, 1, 0
              ] , 'B'),
      numpy.array ( [
               255, 254, 253, 252, 251, 250, 249, 248, 246, 245, 244, 243,
               242, 241, 240, 239, 238, 237, 236, 235, 234, 233, 232, 230,
               229, 228, 227, 226, 225, 224, 223, 222, 221, 220, 219, 218,
               217, 216, 214, 213, 212, 211, 210, 209, 208, 207, 206, 205,
               204, 203, 202, 201, 200, 198, 197, 196, 195, 194, 193, 192,
               291, 190, 189, 188, 187, 186, 185, 184, 182, 181, 180, 179,
               278, 177, 176, 175, 174, 173, 172, 171, 170, 169, 168, 166,
               265, 164, 163, 162, 161, 160, 159, 158, 157, 156, 155, 154,
               253, 152, 150, 149, 148, 147, 146, 145, 144, 143, 142, 141,
               240, 139, 138, 137, 136, 134, 133, 132, 131, 130, 129, 128,
               127, 126, 125, 124, 123, 122, 121, 120, 118, 117, 116, 115,
               114, 113, 112, 111, 110, 109, 108, 107, 106, 105, 104, 102,
               101, 100, 99, 98, 97, 96, 95, 94, 93, 92, 91, 90, 89, 88, 86,
               85, 84, 83, 82, 81, 80, 79, 78, 77, 76, 75, 74, 73, 72, 70,
               69, 68, 67, 66, 65, 64, 63, 62, 61, 60, 59, 58, 57, 56, 54,
               53, 52, 51, 50, 49, 48, 47, 46, 45, 44, 43, 42, 41, 40, 38,
               37, 36, 35, 34, 33, 32, 31, 30, 29, 28, 27, 26, 25, 24, 22,
               21, 20, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8, 6, 5,
               4, 3, 2, 1, 0
              ] , 'B'),
      numpy.array ( [
               255, 254, 253, 252, 251, 250, 249, 248, 246, 245, 244, 243,
               242, 241, 240, 239, 238, 237, 236, 235, 234, 233, 232, 230,
               229, 228, 227, 226, 225, 224, 223, 222, 221, 220, 219, 218,
               217, 216, 214, 213, 212, 211, 210, 209, 208, 207, 206, 205,
               204, 203, 202, 201, 200, 198, 197, 196, 195, 194, 193, 192,
               191, 190, 189, 188, 187, 186, 185, 184, 182, 181, 180, 179,
               178, 177, 176, 175, 174, 173, 172, 171, 170, 169, 168, 166,
               165, 164, 163, 162, 161, 160, 159, 158, 157, 156, 155, 154,
               153, 152, 150, 149, 148, 147, 146, 145, 144, 143, 142, 141,
               140, 139, 138, 137, 136, 134, 133, 132, 131, 130, 129, 128,
               127, 126, 125, 124, 123, 122, 121, 120, 118, 117, 116, 115,
               114, 113, 112, 111, 110, 109, 108, 107, 106, 105, 104, 102,
               101, 100, 99, 98, 97, 96, 95, 94, 93, 92, 91, 90, 89, 88,
               86, 85, 84, 83, 82, 81, 80, 79, 78, 77, 76, 75, 74, 73, 72,
               70, 69, 68, 67, 66, 65, 64, 63, 62, 61, 60, 59, 58, 57, 56,
               54, 53, 52, 51, 50, 49, 48, 47, 46, 45, 44, 43, 42, 41, 40,
               38, 37, 36, 35, 34, 33, 32, 31, 30, 29, 28, 27, 26, 25, 24,
               22, 21, 20, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8,
               6, 5, 4, 3, 2, 1, 0
              ] , 'B')
      ]
   }

def split_palette ( * name) :

    '''
    split_palette
    split_palette ('palette_name.gp')
      split the current palette or the specified palette into two
      parts; colors 0 to 99 will be a compressed version of the
      original, while colors 100 to 199 will be a gray scale.
    '''

    if len (name) > 0 :
        dum = palette (name [0])
        del dum
    r = numpy.zeros (240, 'B')
    g = numpy.zeros (240, 'B')
    b = numpy.zeros (240, 'B')
    dum = palette (r, g, b, query = 1)
    del dum
    try : # r may be all zeros, in which case the following will fail:
        n = max (numpy.nonzero(r)[0]) + 1 # (Figure out how many entries there are)
    except :
        n = 0
    if n < 100 :
        dum = palette ('earth.gp')
        dum = palette (r, g, b, query = 1)
        del dum
        n = max (max (numpy.nonzero(r)[0]), max (numpy.nonzero(g)[0]),
                 max (numpy.nonzero(b)[0])) + 1
    newr = numpy.zeros (200, 'B')
    newg = numpy.zeros (200, 'B')
    newb = numpy.zeros (200, 'B')
    newr [0:100] = interp (r [0:n].astype (numpy.float32), numpy.arange (n, dtype = numpy.float32 ),
       numpy.arange (100, dtype = numpy.float32 ) * n / 100).astype (numpy.uint8)
    newg [0:100] = interp (g [0:n].astype (numpy.float32), numpy.arange (n, dtype = numpy.float32 ),
       numpy.arange (100, dtype = numpy.float32 ) * n / 100).astype (numpy.uint8)
    newb [0:100] = interp (b [0:n].astype (numpy.float32), numpy.arange (n, dtype = numpy.float32 ),
       numpy.arange (100, dtype = numpy.float32 ) * n / 100).astype (numpy.uint8)
    newr [100:200] = (numpy.arange (100, dtype = numpy.int32) * 255 / 99).astype (numpy.uint8)
    newg [100:200] = (numpy.arange (100, dtype = numpy.int32) * 255 / 99).astype (numpy.uint8)
    newb [100:200] = (numpy.arange (100, dtype = numpy.int32) * 255 / 99).astype (numpy.uint8)
    palette (newr, newg, newb)

def split_bytscl (x, upper, cmin = None, cmax = None) :

    '''bytscl but scale to the lower half of a split
      palette (0-99, normally the color scale) if the second parameter
      is zero or nil, or the upper half (100-199, normally the gray
      scale) if the second parameter is non-zero.
    '''

    x = bytscl (x, cmin = cmin, cmax = cmax, top = 99).astype (numpy.uint8)

    if upper :
        x = x + 100
    return x

def _pl3tree (tree, minmax) :
    #  tree is a 4-element list like this:
    #  [plane, back_tree, inplane_leaf, front_tree]
    #   plane= tree [0]  is None if this is just a leaf
    #                    in which case, only inplane_leaf is not None
    #   back_tree= tree [1]    is the part behind plane
    #   inplane_leaf= tree [2] is the part in the plane itself
    #   front_tree= tree [3]   is the part in front of plane
    if tree == None or tree == [] :
        return None
    if tree [0] == None or tree [0] == [] :
        # only the leaf is non-nil (but not a plane)
        return _pl3leaf ( tree [2], 1, minmax)

    # apply the 3D coordinate transform to two points along the
    # normal of the splitting plane to judge which is in front
    xyz = get3_xy (numpy.array ( [ [0., 0., 0.],
                   [tree [0] [0], tree [0] [1], tree [0] [2]]], numpy.float32), 1)
    [x, y, z] = [xyz [:, 0], xyz [:, 1], xyz [:, 2]]

    # plot the parts in order toward the current viewpoint
    if z [1] >= z [0] :
        q1 = _pl3tree (tree [1], minmax)
        q2 = _pl3leaf (tree [2], 0, minmax)
        q3 = _pl3tree (tree [3], minmax)
    else :
        q1 = _pl3tree (tree [3], minmax)
        q2 = _pl3leaf (tree [2], 0, minmax)
        q3 = _pl3tree (tree [1], minmax)
    if q1 != None :
        if q2 != None and q3 == None :
            return [min (q2 [0], q1 [0]),
                    max (q2 [1], q1 [1]),
                    min (q2 [2], q1 [2]),
                    max (q2 [3], q1 [3])]
        elif q2 == None and q3 != None :
            return [min (q3 [0], q1 [0]),
                    max (q3 [1], q1 [1]),
                    min (q3 [2], q1 [2]),
                    max (q3 [3], q1 [3])]
        elif q2 != None and q3 != None :
            return [min (q3 [0], q2 [0], q1 [0]),
                    max (q3 [1], q2 [1], q1 [1]),
                    min (q3 [2], q2 [2], q1 [2]),
                    max (q3 [3], q2 [3], q1 [3])]
        else :
            return q1
    elif q2 != None :
        if q3 == None :
            return q2
        else :
            return [min (q2 [0], q3 [0]),
                    max (q2 [1], q3 [1]),
                    min (q2 [2], q3 [2]),
                    max (q2 [3], q3 [3])]
    elif q3 != None :
        return q3
    else :
        return None

## from lp import *

def _pl3leaf (leaf, not_plane, minmax) :

    # count number of polys, number of vertices
    _nverts = _xyzverts = 0
    if type (leaf) == list and type (leaf [0]) == list :
        for i in range (len (leaf)) :
            [_nverts, _xyzverts] = _pl3tree_count ( leaf [i], _nverts, _xyzverts )
    else :
        [_nverts, _xyzverts] = _pl3tree_count ( leaf , _nverts, _xyzverts)

    # accumulate polys and vertices into a single polygon list
    # The type of array required for palettes is 'Py_GpColor',
    # which translates to 'PyArray_UBYTE', which is selected
    # with a second argument of 'B' to the zeros() function.
## _values = numpy.zeros (_nverts, 'B') # See below
    old_nverts = _nverts
    _nverts = numpy.zeros (_nverts, numpy.int32)
    _x = numpy.zeros (_xyzverts, numpy.float32 )
    _y = numpy.zeros (_xyzverts, numpy.float32 )
    if (not_plane) :
        # Not just straight assignment; make _z a separate copy
        _z = numpy.zeros (_xyzverts, numpy.float32 )
    else :
        _z = None
    _list = 1
    _vlist = 1
    if type (leaf) == list and type (leaf [0]) == list :
        if leaf [0] [2] != 'bg' :
            _values = numpy.zeros (old_nverts, 'B')
        else :
            _values = 'bg'
        for i in range (len (leaf)) :
            [_list, _vlist, _edges] = _pl3tree_accum ( leaf [i] , not_plane,
               _x, _y, _z, _list, _vlist, _values, _nverts, minmax)
    else :
        if leaf [2] != 'bg' :
            _values = numpy.zeros (old_nverts, 'B')
        else :
            _values = 'bg'
        [_list, _vlist, _edges] = _pl3tree_accum ( leaf , not_plane,
           _x, _y, _z, _list, _vlist, _values, _nverts, minmax)

    # sort the single polygon list
    if not_plane :
        [_list, _vlist] = sort3d (_z, _nverts)
        _nverts = numpy.take (_nverts, _list,axis=0)
        if _values != 'bg' :
            _values = numpy.take (_values, _list,axis=0)
        _x = numpy.take (_x, _vlist,axis=0)
        _y = numpy.take (_y, _vlist,axis=0)

    _square = get_square_ ( )
    [_xfactor, _yfactor] = get_factors_ ()
    xmax = max (_x)
    xmin = min (_x)
    ymax = max (_y)
    ymin = min (_y)
    xdif = xmax - xmin
    ydif = ymax - ymin
    if _xfactor != 1. :
        xmax = xmax + (_xfactor - 1.) * xdif /2.
        xmin = xmin - (_xfactor - 1.) * xdif /2.
    if _yfactor != 1. :
        ymax = ymax + (_yfactor - 1.) * ydif /2.
        ymin = ymin - (_yfactor - 1.) * ydif /2.
    if _square :
        xdif = xmax - xmin
        ydif = ymax - ymin
        if xdif > ydif :
            dif = (xdif - ydif) / 2.
            ymin = ymin - dif
            ymax = ymax + dif
        elif ydif > xdif :
            dif = (ydif - xdif) / 2.
            xmin = xmin - dif
            xmax = xmax + dif

    if _values == 'bg' :
        _values = None
    plfp (_values, _y, _x, _nverts, legend = '', edges = _edges)
    return [xmin, xmax, ymin, ymax]

def _pl3tree_count (item, _nverts, _xyzverts) :
    return [_nverts + len (item [0]), _xyzverts  + len (numpy.ravel (item [1])) / 3]

def _pl3tree_accum (item, not_plane, _x, _y, _z, _list, _vlist, _values,
   _nverts, minmax) :
    # (ZCM 2/24/97) Add _x, _y, _z , _list, _vlist, _nverts as parameters to
    # avoid use of globals. return the new values of _list, _vlist.
    # (ZCM 7/16/97) Return item [6] (whether to show edges)
    # (ZCM 7/17/97) Add parameter minmax to normalize values

    # N. B.:
    # item [0] is nverts
    # item [1] is xyzverts
    # item [2] is values   (if present)
    # item [3] is cmin   (if present)
    # item [4] is cmax   (if present)
    # item [5] is split (1 = split the palette, 0 = do not split)
    # item [6] is edges (1 = show edges, 0 = do not show edges)
    # I have cleaned up what I think is extremely obscure Yorick code
    # apparently designed to avoid some overhead.
    # N. B. avoid splitting the palette if split is 0. (ZCM 4/23/97)

    _xyzverts = numpy.array (item [1], copy = 1) # protect copy in tree
    # Normalize copy  (I'm only going to do this if it's an
    # isosurface or is not a plane or has multiple components.
    # There is a real problem here.
    # You get bad distortion without doing this if one coordinate
    # is many orders of magnitude larger than the others but the
    # others have significant figues. You also get bad distortion
    # by doing this in the case of a single plane section
    # when one coordinate is insignificant with
    # respect to the others and doesn't have significant digits.
    # It is awfully hard to come up with a numerical criterion for this.)
    if item [2] == None or not_plane or has_multiple_components ():
        minx = minmax [0]
        maxx = minmax [1]
        miny = minmax [2]
        maxy = minmax [3]
        minz = minmax [4]
        maxz = minmax [5]
        _xyzverts [:, 0] = (_xyzverts [:, 0] - minx) / (maxx - minx)
        _xyzverts [:, 1] = (_xyzverts [:, 1] - miny) / (maxy - miny)
        _xyzverts [:, 2] = (_xyzverts [:, 2] - minz) / (maxz - minz)
    if  item [2] == None :
        # this is an isosurface to be shaded (no values specified)
        _xyzverts = get3_xy (_xyzverts, 1)
        # accumulate nverts and values
        incr = len (item [0])
        _nverts [ _list - 1: _list - 1 + incr] = item [0]
        if item [5] != 0 :
            _values [ _list - 1: _list - 1 + incr] = split_bytscl (
               get3_light (_xyzverts, item [0]), 1, cmin = 0.0,
               cmax = item [4]).astype (numpy.uint8)
        else : # no split
            _values [ _list - 1: _list - 1 + incr] = bytscl (
               get3_light (_xyzverts, item [0]), cmin = 0.0,
               cmax = item [4]).astype (numpy.uint8)
        _list = _list + incr
        # accumulate x, y, and z
        incr = numpy.shape (_xyzverts) [0]
        _x [_vlist - 1:_vlist - 1 + incr] = _xyzverts [:, 0]
        _y [_vlist - 1:_vlist - 1 + incr] = _xyzverts [:, 1]
        if not_plane :
            _z [_vlist - 1:_vlist - 1 + incr] = _xyzverts [:, 2]
        _vlist = _vlist + incr
    else :
        # this is to be pseudo-colored since values are given
        if (not_plane) :
            __xyz = get3_xy (_xyzverts, 1)
        else :
            __xyz = get3_xy (_xyzverts, 0)
        # accumulate nverts and values
        incr = len (item [0])
        _nverts [ _list - 1: _list - 1 + incr] = item [0]
        if item [2] != 'bg' :
            if (item [2]).dtype.char != 'B' :
                if item [5] != 0 :
                    _values [ _list - 1: _list - 1 + incr] = split_bytscl (
                       item [2], 0, cmin = item [3], cmax = item [4]).astype (numpy.uint8)
                else :
                    _values [ _list - 1: _list - 1 + incr] = bytscl (
                       item [2], cmin = item [3], cmax = item [4]).astype (numpy.uint8)
            else :
                _values [ _list - 1: _list - 1 + incr] = item [2]
        _list = _list + incr
        # accumulate x, y, and z
        incr = numpy.shape (__xyz) [0]
        _x [_vlist - 1:_vlist - 1 + incr] = __xyz [:, 0]
        _y [_vlist - 1:_vlist - 1 + incr] = __xyz [:, 1]
        if not_plane :
            _z [_vlist - 1:_vlist - 1 + incr] = __xyz [:, 2]
        _vlist = _vlist + incr

    return [_list, _vlist, item [6]]

def _pl3tree_add (leaf, plane, tree) :
    if tree != None and tree != [] and \
       not is_scalar (tree) and tree [0] != None :
        # tree has slicing plane, slice new leaf or plane and descend
        [back, leaf1] = _pl3tree_slice (tree [0], leaf)
        if back :
            if len (tree) >= 2 and tree [1] != None and tree [1] != [] :
                _pl3tree_add (back, plane, tree [1])
            else :
                tree [1] = [None, [], back, []]
        if (leaf1) :
            if len (tree) >= 4 and tree [3] != None and tree [3] != [] :
                _pl3tree_add (leaf1, plane, tree [3])
            else :
                tree [3] = [None, [], leaf1, []]

    elif plane != None :
        # tree is just a leaf, but this leaf has slicing plane
        tree [0] = plane
        tmp = tree [2]
        tree [2] = leaf
        leaf = tmp   # swap new leaf with original leaf
        [back, leaf1] = _pl3tree_slice (plane, leaf)
        if (back) :
            tree [1] = [None, [], back, []]
        if (leaf1) :
            tree [3] = [None, [], leaf1, []]
    else :
        # tree is just a leaf and this leaf has no slicing plane
        tree [2] = leaf + tree [2]
    return

def _pl3tree_slice (plane, leaf) :
    back = frnt = None
    for ll in leaf :
        # each item in the leaf list is itself a list
        nvf = ll [0]
        if nvf != None :
            nvb = numpy.array (nvf, copy = 1)
        else :
            nvb = None
        xyzf = ll [1]
        if xyzf != None :
            xyzb = numpy.array (xyzf, copy = 1)
        else :
            xyzb = None
        valf = ll [2]
        if valf != None :
            tpc = valf.dtype.char
            valb = numpy.array (valf, copy = 1)
        else :
            valb = None
        if len (ll) > 4 :
            ll4 = ll [4]
        else :
            ll4 = None
        if len (ll) > 5 :
            ll5 = ll [5]
        else :
            ll5 = 1
        if len (ll) > 6 :
            ll6 = ll [6]
        else :
            ll6 = 0
        [nvf, xyzf, valf, nvb, xyzb, valb] = \
           slice2x (plane, nvf, xyzf, valf)
        if valf != None:
            valf = valf.astype (tpc)
        if valb != None:
            valb = valb.astype (tpc)
        if nvf != None :
            if frnt != None :
                frnt = [ [nvf, xyzf, valf, ll [3], ll4, ll5, ll6]] + frnt
            else :
                frnt = [ [nvf, xyzf, valf, ll [3], ll4, ll5, ll6]]
        if nvb != None :
            if back != None :
                back = [ [nvb, xyzb, valb, ll [3], ll4, ll5, ll6]] + back
            else :
                back = [ [nvb, xyzb, valb, ll [3], ll4, ll5, ll6]]
    return [back, frnt]

class _Pl3tree_prtError(Exception):
    pass

def pl3tree_prt () :
    _draw3_list = get_draw3_list_ ()
    _draw3_n = get_draw3_n_ ()
    if len (_draw3_list) >= _draw3_n :
        tree = _draw3_list [_draw3_n:]
        if tree == None or tree == [] or tree [0] != pl3tree :
            print('<current 3D display not a pl3tree>')
#        raise _Pl3tree_prtError, '<current 3D display not a pl3tree>'
        else :
            tree = tree [1] [0]
            _pl3tree_prt (tree, 0)

def pl3_other_prt(tree = None):
    if tree == None:
        pl3tree_prt ()
    else :
        if tree == None or tree == []:
            print('<current 3D display not a pl3tree>')
        else :
            _pl3tree_prt (tree, 0)

def _pl3tree_prt (tree, depth) :
    if tree == None or tree == [] :
        return
    indent = (' ' * (1 + 2 * depth)) [0:-1]
    print((indent + '+DEPTH= ' + repr(depth)))
    if len (tree) != 4 :
        print((indent + '***error - not a tree'))
    print((indent + 'plane= ' + repr(tree [0])))
    back = tree [1]
    lst = tree [2]
    frnt = tree [3]
    if back == None or back == [] :
        print((indent + 'back = []'))
    else :
        _pl3tree_prt (back, depth + 1)

    for leaf in lst :
        print((indent + 'leaf length= ' + repr(len (leaf))))
        print((indent + 'npolys= ' + repr(len (leaf [0])) + \
           ', nverts= ' + repr(numpy.sum (leaf [0],axis=0)) + ', max= ' + repr(max (leaf [0]))))
        print((indent + 'nverts= ' + repr(numpy.shape (leaf [1]) [0]) + \
           ', nvals= ' + repr(len (leaf [2]))))

    if frnt == None or frnt == [] :
        print((indent + 'frnt = []'))
    else :
        _pl3tree_prt (frnt, depth + 1)
    print((indent + '+DEPTH= ' + repr(depth)))

# ------------------------------------------------------------------------

def _isosurface_slicer (m3, chunk, iso_index, _value) :
#  Have to remember here that getv3 can either return an array of
#  values, or a 2-list consisting of values and the corresponding cell
#  indices, the latter in the case of an irregular grid.
# Note: (ZCM 2/24/97) I have fixed slicers to return the vertex
# information and what used to be the global _xyz3, or None. Hence
# returning the tuple [tmp, None].

    tmp = getv3 (iso_index, m3, chunk)
    if type (tmp) == list :
        tmp[0] = tmp [0] - _value
    else :
        tmp = tmp - _value
    return [tmp, None]

def _plane_slicer (m3, chunk, normal, projection) :
    # (ZCM 2/24/97) In all cases, return x as the last element of
    # the tuple. This eliminates the global _xyz3.

    x = xyz3(m3,chunk)
    irregular = type (chunk) == list and len (chunk) == 2 \
       or type (chunk) == numpy.ndarray and len (numpy.shape (chunk)) == 1 \
       and type (chunk [0]) == int
    if irregular :
        # Need to return a list, the first component being the x's,
        # the second being the relative cell list, and the third an offset
        verts = m3 [1] [0]
        cell_offset = 0
        if type (verts) == list :
            totals = m3 [1] [3]
            if type (chunk) == list :
                fin = chunk [0] [1]
            else :
                fin = chunk [-1]
            for j in range (len (verts)) :
                if fin <= totals [j] :
                    break
            if j > 0 :
                cell_offset = totals [j - 1]
        if type (chunk) == list :
            clist = numpy.arange (0, chunk [0] [1] - chunk [0] [0], dtype = numpy.int32)
        else :
            clist = chunk - cell_offset
        # In the irregular case we know x is ncells by 3 by something
        return [ [x [:,0] * normal [0] + x [:,1] * normal [1] + \
           x [:,2] * normal [2] - projection, clist, cell_offset], x]
    elif len (numpy.shape (x)) == 5 : # It's ncells X 3 X 2 X 2 X 2
        return [x [:,0] * normal [0] + x [:,1] * normal [1] + \
           x [:,2] * normal [2] - projection, x]
    else :                    # It's 3 X ni X nj X nk
        return [x [0] * normal [0] + x [1] * normal [1] + x [2] * normal [2] -\
           projection, x]

def xyz3 (m3, chunk) :

    '''
    xyz3 (m3, chunk)

      return vertex coordinates for CHUNK of 3D mesh M3.  The CHUNK
      may be a list of cell indices, in which case xyz3 returns a
      (dimsof(CHUNK))x3x2x2x2 list of vertex coordinates.  CHUNK may
      also be a mesh-specific data structure used in the slice3
      routine, in which case xyz3 may return a 3x(ni)x(nj)x(nk)
      array of vertex coordinates.  For meshes which are logically
      rectangular or consist of several rectangular patches, this
      is up to 8 times less data, with a concomitant performance
      advantage.  Use xyz3 when writing slicing functions or coloring
      functions for slice3.
    '''

    xyz = m3 [0] [0] (m3, chunk)
    return xyz

def xyz3_rect (m3, chunk) :
    m3 = m3 [1]
    if len (numpy.shape (chunk)) != 1 :
        c = chunk
        # The difference here is that our arrays are 0-based, while
        # yorick's are 1-based; and the last element in a range is not
        # included in the result array.
        return m3 [1] [:,c [0, 0] - 1:1 + c [1, 0], c [0, 1] - 1:1 + c [1, 1] ,
                       c [0, 2] - 1:1 + c [1, 2]]
    else :
        # Need to create an array of m3 [1] values the same size and shape
        # as what to_corners3 returns.
        # To avoid exceedingly arcane calculations attempting to
        # go backwards to a cell list, this branch returns the list
        # [<function values>, chunk]
        # ???????????? ^^^^^^^^^^^^
        # Then it is trivial for slice3 to find a list of cell
        # numbers in which fi has a negative value.
        dims = m3 [0]
        indices = to_corners3 (chunk, dims [1] + 1, dims [2] + 1)
        no_cells = numpy.shape (indices) [0]
        indices = numpy.ravel (indices)
        retval = numpy.zeros ( (no_cells, 3, 2, 2, 2), numpy.float32 )
        m30 = numpy.ravel (m3 [1] [0, ...])
        retval [:, 0, ...] = numpy.reshape (numpy.take (m30, indices,axis=0), (no_cells, 2, 2, 2))
        m31 = numpy.ravel (m3 [1] [1, ...])
        retval [:, 1, ...] = numpy.reshape (numpy.take (m31, indices,axis=0), (no_cells, 2, 2, 2))
        m32 = numpy.ravel (m3 [1] [2, ...])
        retval [:, 2, ...] = numpy.reshape (numpy.take (m32, indices,axis=0), (no_cells, 2, 2, 2))
        return retval

class _xyz3Error(Exception):
    pass

def xyz3_irreg (m3, chunk) :
    xyz = m3 [1] [1]
    if type (chunk) == list and len (chunk) == 2 :
        no_cells = chunk [0] [1] - chunk [0] [0]
        if type (m3 [1] [0]) == list :
            totals = m3 [1] [3]
            start = chunk [0] [0]
            fin = chunk [0] [1]
            for i in range (len (totals)) :
                if fin <= totals [i] :
                    break
            verts = m3 [1] [0] [i]
            if i > 0 :
                start = start - totals [i - 1]
                fin = fin - totals [i - 1]
            ns = verts [start:fin]
            shp = numpy.shape (verts)
        else :
            ns = m3 [1] [0] [chunk [0] [0]:chunk [0] [1]]   # This is a kXnv numpy.array
            shp = numpy.shape (m3 [1] [0])
    elif type (chunk) == numpy.ndarray and len (numpy.shape (chunk)) == 1 and \
       type (chunk [0]) == int :
        # chunk is an absolute cell list
        no_cells = len (chunk)
        if type (m3 [1] [0]) == list :
            totals = m3 [1] [3]
            fin = max (chunk)
            for i in range (len (totals)) :
                if fin <= totals [i] :
                    break
            verts = m3 [1] [0] [i]
            if i > 0 :
                start = totals [i - 1]
            else :
                start = 0
            verts = m3 [1] [0] [i]
            ns = numpy.take (verts, chunk - start,axis=0)
            shp = numpy.shape (verts)
        else :
            ns = numpy.take (m3 [1] [0], chunk,axis=0)
            shp = numpy.shape (m3 [1] [0])
    else :
        raise _xyz3Error('chunk parameter has the wrong type.')
    if shp [1] == 8 : # hex
        retval = numpy.zeros ( (no_cells, 3, 2, 2, 2), numpy.float32)
        retval [:, 0] = \
           numpy.reshape (numpy.take (xyz [0], numpy.ravel (ns),axis=0), (no_cells, 2, 2, 2))
        retval [:, 1] = \
           numpy.reshape (numpy.take (xyz [1], numpy.ravel (ns),axis=0), (no_cells, 2, 2, 2))
        retval [:, 2] = \
           numpy.reshape (numpy.take (xyz [2], numpy.ravel (ns),axis=0), (no_cells, 2, 2, 2))
    elif shp [1] == 6 : # prism
        retval = numpy.zeros ( (no_cells, 3, 3, 2), numpy.float32)
        retval [:, 0] = \
           numpy.reshape (numpy.take (xyz [0], numpy.ravel (ns),axis=0), (no_cells, 3, 2))
        retval [:, 1] = \
           numpy.reshape (numpy.take (xyz [1], numpy.ravel (ns),axis=0), (no_cells, 3, 2))
        retval [:, 2] = \
           numpy.reshape (numpy.take (xyz [2], numpy.ravel (ns),axis=0), (no_cells, 3, 2))
    elif shp [1] == 5 : # pyramid
        retval = numpy.zeros ( (no_cells, 3, 5), numpy.float32)
        retval [:, 0] = \
           numpy.reshape (numpy.take (xyz [0], numpy.ravel (ns),axis=0), (no_cells, 5))
        retval [:, 1] = \
           numpy.reshape (numpy.take (xyz [1], numpy.ravel (ns),axis=0), (no_cells, 5))
        retval [:, 2] = \
           numpy.reshape (numpy.take (xyz [2], numpy.ravel (ns),axis=0), (no_cells, 5))
    elif shp [1] == 4 : # tet
        retval = numpy.zeros ( (no_cells, 3, 4), numpy.float32)
        retval [:, 0] = \
           numpy.reshape (numpy.take (xyz [0], numpy.ravel (ns),axis=0), (no_cells, 4))
        retval [:, 1] = \
           numpy.reshape (numpy.take (xyz [1], numpy.ravel (ns),axis=0), (no_cells, 4))
        retval [:, 2] = \
           numpy.reshape (numpy.take (xyz [2], numpy.ravel (ns),axis=0), (no_cells, 4))
    else :
        raise _xyz3Error('Funny number of cell faces: ' + repr(shp [1]))
    return retval

def xyz3_unif (m3, chunk) :
    m3 = m3 [1]
    n = m3 [1]
    if len (chunk.shape) != 1 :
        c = chunk
        i = c [0] - 1
        dn = c [1] + 1 - i
        xyz = numpy.zeros ( (3, dn [0], dn [1], dn [2]), numpy.float32)
    else :
        dims = m3 [0]
        nj = dims [1]
        nk = dims [2]
        njnk = nj * nk
        zchunk = chunk % nk
        ychunk = chunk / nk % nj
        xchunk = chunk / njnk
        xyz = numpy.zeros ( (len (chunk), 3, 2, 2, 2), numpy.float32 )
        ijk0 = numpy.array ( [numpy.zeros ( (2, 2), numpy.int32 ), numpy.ones ( (2, 2), numpy.int32 )])
        ijk1 = numpy.array ( [ [0, 0], [1, 1]], numpy.int32 )
        ijk1 = numpy.array ( [ijk1, ijk1] , numpy.int32 )
        ijk2 = numpy.array ( [ [0, 1], [0, 1]], numpy.int32 )
        ijk2 = numpy.array ( [ijk2, ijk2] , numpy.int32 )
    if len (n) == 2: # we have dxdydz and x0y0z0
        dxdydz = n [0]
        x0y0z0 = n [1]
        if len (numpy.shape (chunk)) != 1:
            # Convert the increment and size into array coordinates
            # -- consecutive values
            xx = numpy.arange (dn [0], dtype = numpy.float32 ) * dxdydz [0] / (dn [0] - 1)
            yy = numpy.arange (dn [1], dtype = numpy.float32 ) * dxdydz [1] / (dn [1] - 1)
            zz = numpy.arange (dn [2], dtype = numpy.float32 ) * dxdydz [2] / (dn [2] - 1)
            xyz [0] = x0y0z0 [0] + i [0] * dxdydz [0] + numpy.multiply.outer (
               numpy.multiply.outer ( xx, numpy.ones (dn [1], numpy.float32 )),
               numpy.ones (dn [2], numpy.float32 ))
            xyz [1] = x0y0z0 [1] + i [1] * dxdydz [0] + \
               numpy.multiply.outer ( numpy.ones (dn [0], numpy.float32 ), \
               numpy.multiply.outer ( yy, numpy.ones (dn [2], numpy.float32 )))
            xyz [2] = x0y0z0 [2] + i [2] * dxdydz [0] + \
               numpy.multiply.outer ( numpy.ones (dn [0], numpy.float32 ), \
               numpy.multiply.outer ( numpy.ones (dn [1], numpy.float32 ), zz))
        else :
            # -- nonconsecutive values
            xyz [:, 0] = numpy.add.outer ( xchunk, ijk0) * dxdydz [0] + x0y0z0 [0]
            xyz [:, 1] = numpy.add.outer ( ychunk, ijk1) * dxdydz [1] + x0y0z0 [1]
            xyz [:, 2] = numpy.add.outer ( zchunk, ijk2) * dxdydz [2] + x0y0z0 [2]
    elif type (n) == list and len (n) == 3: # We have three one-dimensional arrays.
        xx = n [0]
        yy = n [1]
        zz = n [2]
        n0 = len (xx)
        n1 = len (yy)
        n2 = len (zz)
        if len (numpy.shape (chunk)) != 1:
            # Convert the increment and size into array coordinates
            # -- consecutive values
            xyz [0] = numpy.multiply.outer (
               numpy.multiply.outer ( xx [i [0]:i [0] + n0],  numpy.ones (n1, numpy.float32 )), \
               numpy.ones (n2, numpy.float32 ))
            xyz [1] =  numpy.multiply.outer ( numpy.ones (n0, numpy.float32 ), \
               numpy.multiply.outer ( yy [i [1]: i[1] + n1], numpy.ones (n2, numpy.float32 )))
            xyz [2] = numpy.multiply.outer ( numpy.ones (n0, numpy.float32 ), \
               numpy.multiply.outer ( numpy.ones (n1, numpy.float32 ), zz [i [2]: i[2] + n2]))
        else :
            # -- nonconsecutive values
            xyz [:, 0] = numpy.reshape (numpy.take (xx, numpy.ravel (numpy.add.outer (xchunk, ijk0)),axis=0),
               (len (chunk),  2, 2, 2))
            xyz [:, 1] = numpy.reshape (numpy.take (yy, numpy.ravel (numpy.add.outer (ychunk, ijk1)),axis=0),
               (len (chunk),  2, 2, 2))
            xyz [:, 2] = numpy.reshape (numpy.take (zz, numpy.ravel (numpy.add.outer (zchunk, ijk2)),axis=0),
               (len (chunk),  2, 2, 2))
    return xyz

def to_corners3 (lst, nj, nk) :

    '''
    to_corners3(lst, nj, nk)
      convert an array of cell indices in an (ni-1)-by-(NJ-1)-by-(NK-1)
      logically rectangular grid of cells into the list of
      len(LIST)-by-2-by-2-by-2 cell corner indices in the
      corresponding ni-by-NJ-by-NK array of vertices.
      Note that this computation in Yorick gives an absolute offset
      for each cell quantity in the grid. In Yorick it is legal to
      index a multidimensional array with an absolute offset. In
      Python it is not. However, an array can be flattened if
      necessary.
      Other changes from Yorick were necessitated by row-major
      order and 0-origin indices, and of course the lack of
      Yorick array facilities.
    '''

    njnk = nj * nk
    kk = lst / (nk - 1)
    lst = lst + kk + nk * (kk / (nj - 1))
    adder = numpy.array ( [ [ [0, 1], [nk, nk + 1]],
                      [ [njnk, njnk + 1], [nk + njnk, nk + njnk + 1]]])
    res = numpy.zeros ( (len (lst), 2, 2, 2), numpy.int32)
    for i in range (len(lst)):
        res [i] = adder + lst [i]
    return res
