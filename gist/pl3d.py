# $Id: pl3d.py 671 2007-09-18 12:58:46Z mbec $
# Copyright (c) 1996, 1997, The Regents of the University of California.
# All rights reserved.  See Legal.htm for full text and disclaimer.

import numpy
from .gistC import *
from .gistF import index_sort, array_set
from .yorick import *

#  PL3D.PY
#  Viewing transforms and other aids for 3D plotting.
#
#  $Id: pl3d.py 671 2007-09-18 12:58:46Z mbec $

#     Copyright (c) 1997.  The Regents of the University of California.
#                   All rights reserved.

'''
   General overview of module pl3d:

   (1) Viewing transform machinery.  Arguably the simplest model
       is the CAD/CAM notion that the object you see is oriented
       as you see it in the current picture.  You can then move
       it left, right, up, down, or toward or away from you,
       or you can rotate it about any of the three axes (horizontal,
       vertical, or out of the screen).  The xyz coordinates of the
       object remains unchanged throughout all of this, but this
       object coordinate system changes relative to the fixed
       xyz of the viewer, in which x is always to the right, y is
       up, and z is directed out of the screen.  Initially, the
       two coordinate systems coincide.

       rot3 (xangle,yangle,zangle)
         Rotate the object about viewer's x-axis by xangle, then
         about viewer's y-axis by yangle, then about viewer's
         z-axis by zangle
       mov3 (xchange,ychange,zchange)
         Move the object by the specified amounts.

       setz3 (zcamera)
         The 'camera' is located at (0,0,zcamera) in the viewer's
         coordinate system, looking in the minus-z direction.
         Initially, zcamera is very large, and the magnification
         factor is correspondingly large, giving an isometric view.
         Decreasing zcamera makes the perspective more extreme.
         If parts of the object are behind the camera, strange things
         may happen.

       undo3 ()
       undo3 (n)
         Undo the last N (default 1) viewpoint commands (rot3, mov3,
         or setz3).  Up to 100 viewpoint changes are remembered.
       viewpoint= save3()
       ...
       restore3 (viewpoint)
         The current viewpoint transformation can be saved and later
         restored.

       gnomon (on_off)
         Toggle the gnomon (a simple display showing the orientation
         of the xyz axes of the object).
'''

#  ------------------------------------------------------------------------


def set_draw3_ ( n ) :

    '''
    set_draw3_ ( 0 | 1 ) is used to set the global draw3_,
    which controls whether the function draw3 actually shows a drawing.
    '''

    global _draw3
    _draw3 = n

def setrot3_ (x) :

    # ZCM 2/21/97 change reflects the fact that I hadn't realized
    # that car and cdr, as functions, return the item replaced.

    global _draw3_list
    oldx = _draw3_list [0]
    _draw3_list [0] = x
    undo3_set_ (setrot3_, oldx)

def rot3 (xa = 0., ya = 0., za = 0.) :

    '''
    rot3 (xa, ya, za)
    rotate the current 3D plot by XA about viewer's x-axis,
    YA about viewer's y-axis, and ZA about viewer's z-axis.
    SEE ALSO: orient3, mov3, aim3, setz3, undo3, save3, restore3, light3
    '''

    x = numpy.array ([1.,0.,0.], numpy.float32)
    y = numpy.array ([0.,1.,0.], numpy.float32)
    z = numpy.array ([0.,0.,1.], numpy.float32)
    [x, y] = rot3_ (za, x, y)
    [z, x] = rot3_ (ya, z, x)
    [y, z] = rot3_ (xa, y, z)
    # n. b. matrixMultiply has the unfortunate effect of destroying
    # the matrix that calls it.
    gr3 = numpy.array (getrot3_ (), copy = 1)
    setrot3_ (numpy.transpose (numpy.dot (numpy.transpose (gr3), numpy.array ( [x, y, z]))))

def rot3_ (a, x, y) :
    ca = numpy.cos (a)
    sa = numpy.sin (a)
    return [numpy.multiply (ca, x) + numpy.multiply (sa, y), numpy.multiply (-sa, x) + numpy.multiply (ca, y)]

def mov3 ( xa = 0., ya = 0., za = 0. ) :

    '''
    mov3 ( [xa [, ya [, za]]])
    move the current 3D plot by XA along the viewer's x axis,
    YA along the viewer's y axis, and ZA along the viewer's z axis.
    SEE ALSO: rot3, orient3, setz3, undo3, save3, restore3, light3
    '''

    gr = numpy.dot (numpy.transpose (gr), numpy.transpose (xa))
    setorg3_ ( getorg3_ () - gr)

def aim3 ( xa = 0., ya = 0., za = 0. ) :

    '''
    aim3 ( [xa [, ya [, za]]])
    move the current 3D plot to put the point (XA, YA, ZA) in object
    coordinates at the point (0, 0, 0) -- the aim point -- in the
    viewer's coordinates. If any of the XA, YA, or ZA is nil, it defaults
    SEE ALSO: mov3, rot3, orient3, setz3, undo3, save3, restore3, light3
    '''

    setorg3_ (x)

class _ZcError(Exception):
    pass

def setz3 ( zc = None ) :

    '''
    setz3 ( [zc] )
    Set the camera position to z = ZC (x = y = 0) in the viewer's coordinate
    system. If zc is None, set the camera to infinity (default).
    SEE ALSO: rot3, orient3, undo3, save3, restore3, light3
    '''

    if not is_scalar (zc) :
        raise _ZcError('camera position must be scalar.')

    setzc3_ (zc)

def orient3 ( ** kw ) :

    '''
    orient3 ( [phi = val1, theta = val2] )
    Set the orientation of the object to (PHI, THETA). Orientations
    are a subset of the possible rotation matrices in which the z axis
    of the object appears vertical on the screen (that is, the object
    z axis projects onto the viewer y axis). The THETA angle is the
    angle from the viewer y axis to the object z axis, positive if
    the object z axis is tilted towards you (toward viewer +z). PHI is
    zero when the object x axis coincides with the viewer x axis. If
    neither PHI nor THETA is specified, PHI defaults to - pi / 4 and
    THETA defaults to pi / 6. If only PHI is specified, THETA remains
    unchanged, unless the current THETA is near pi / 2, in which case
    THETA returns to pi / 6, or unless the current orientation does
    not have a vertical z axis, in which case THETA returns to its
    default.
    Unlike rot3, orient3 is not a cumulative operation.
    '''
    # Notes with regard to global variables: (ZCM 2/21/97)
    # _orient3_phi, _orient3_theta, the default orientation angles,
    #    are known and referred to only in this routine. I have started
    #    them with an underscore, too, to make them inaccessible
    #    from outside this module.
    # phi and theta need not be global here since they are recalculated
    #    each time this routine is called.

    global _orient3_phi, _orient3_theta
    try :
        dummy = _orient3_theta
    except :
        _orient3_theta = numpy.pi / 6.

    try :
        dummy = _orient3_phi
    except :
        _orient3_phi = - numpy.pi / 4.

    if 'phi' in kw and kw ['phi'] == None :
        kw ['phi'] = _orient3_phi
    if 'theta' in kw and kw ['theta'] == None :
        kw ['theta'] = _orient3_theta
    if 'phi' not in kw and 'theta' not in kw :
        phi = _orient3_phi
        theta = _orient3_theta
    elif 'phi' not in kw or 'theta' not in kw :
        gr3 = numpy.array (getrot3_ (), copy = 1)
        z = numpy.dot (numpy.transpose (gr3), numpy.array ( [0., 0., 1.]))
        if abs (z [0]) > 1.e-6 :
            # object z-axis not aligned with viewer y-axis
            if 'theta' not in kw :
                theta = _orient3_theta
                phi = kw ['phi']
            else :
                phi = _orient3_phi
                theta = kw ['theta']
        elif 'theta' not in kw :
            phi = kw ['phi']
            if (abs (z [1]) < 1.e-6) :
                theta = _orient3_theta
            else :
                theta = numpy.arctan2 (z [2], z [1])
        else :
            theta = kw ['theta']
            y = numpy.array ( [0., z [2], -z [1]])
            x = numpy.dot (numpy.transpose (gr3), numpy.array ( [1., 0., 0.]))
            phi = numpy.arctan2 (numpy.sum (y * x,axis=0), x [0])
    else :
        phi = kw ['phi']
        theta = kw ['theta']

    x = numpy.array ( [1., 0., 0.],  numpy.float32)
    y = numpy.array ( [0., 1., 0.],  numpy.float32)
    z = numpy.array ( [0., 0., 1.],  numpy.float32)
    [y, z] = rot3_ (theta, y, z)
    [z, x] = rot3_ (phi, z, x)
    setrot3_ (numpy.array ( [x, -z, y],  numpy.float32))

import copy

def save3 ( ) :

    '''
    view = save3 ( )
      Save the current 3D viewing transformation and lighting.
      Actually, this doesn't save anything; it returns a copy
      of the current 3D viewing transformation and lighting, so
      that the user can put it aside somewhere.
    SEE ALSO: restore3, rot3, mov3, aim3, light3
    '''

    return _draw3_list [0:_draw3_n]

def restore3 ( view = None ) :

    '''
    restore3 ( view )
    Restore a previously saved 3D viewing transformation and lighting.
    If view is missing, rotate object to viewer's coordinate system.
    SEE ALSO: restore3, rot3, mov3, aim3, light3
    '''

    global _draw3_list, _draw3_view, _light3_list, _draw3_n

    if view != None :
        view = view [0:len (view)] # Copies view
    else :
        view = _draw3_view + _light3_list
    old = _draw3_list [0:_draw3_n]
    _draw3_list = view [0:_draw3_n] + _draw3_list [_draw3_n:]
    undo3_set_ (restore3, old)

class _AmbientError(Exception):
    pass

class _DiffuseError(Exception):
    pass

class _LightingError(Exception):
    pass

def light3 ( * kw, ** kwds ) :

    '''
    light3 (ambient=a_level,
                     diffuse=d_level,
                     specular=s_level,
                     spower=n,
                     sdir=xyz)
      Sets lighting properties for 3D shading effects.
      A surface will be shaded according to its to its orientation
      relative to the viewing direction.

      The ambient level A_LEVEL is a light level (arbitrary units)
      that is added to every surface independent of its orientation.

      The diffuse level D_LEVEL is a light level which is proportional
      to cos(theta), where theta is the angle between the surface
      normal and the viewing direction, so that surfaces directly
      facing the viewer are bright, while surfaces viewed edge on are
      unlit (and surfaces facing away, if drawn, are shaded as if they
      faced the viewer).

      The specular level S_LEVEL is a light level proportional to a high
      power spower=N of 1+cos(alpha), where alpha is the angle between
      the specular reflection angle and the viewing direction.  The light
      source for the calculation of alpha lies in the direction XYZ (a
      3 element vector) in the viewer's coordinate system at infinite
      distance.  You can have ns light sources by making S_LEVEL, N, and
      XYZ (or any combination) be vectors of length ns (3-by-ns in the
      case of XYZ).  (See source code for specular_hook function
      definition if powers of 1+cos(alpha) aren't good enough for you.)

      With no arguments, return to the default lighting.

    EXAMPLES:
      light3 ( diffuse=.1, specular=1., sdir=[0,0,-1])
        (dramatic 'tail lighting' effect)
      light3 ( diffuse=.5, specular=1., sdir=[1,.5,1])
        (classic 'over your right shoulder' lighting)
      light3 ( ambient=.1,diffuse=.1,specular=1.,
              sdir=[[0,0,-1],[1,.5,1]],spower=[4,2])
        (two light sources combining previous effects)
    SEE ALSO: rot3, save3, restore3
    '''

    global _draw3_list, _draw3_nv
    if len (kw) > 0 : kwds = kw [0]
    old = _draw3_list [_draw3_nv:] [0:5]
    flags = 0
    if 'ambient' in kwds and kwds ['ambient'] != None :
        ambient = kwds ['ambient']
        if not is_scalar (ambient) :
            raise _AmbientError('ambient light level must be scalar.')
        flags = flags | 1
        _draw3_list [_draw3_nv] = ambient
    if 'diffuse' in kwds and kwds ['diffuse'] != None :
        diffuse = kwds ['diffuse']
        if not is_scalar (diffuse) :
            raise _DiffuseError('diffuse light level must be scalar.')
        flags = flags | 2
        _draw3_list [_draw3_nv + 1 ] = diffuse

    if 'specular' in kwds and kwds ['specular'] != None :
        specular = kwds ['specular']
        flags = flags | 4
    else :
        specular = _draw3_list [_draw3_nv + 2]
    if 'spower' in kwds and kwds ['spower'] != None :
        spower = kwds ['spower']
        flags = flags | 8
    else :
        spower = _draw3_list [_draw3_nv + 3]
    if 'sdir' in kwds and kwds ['sdir'] != None :
        sdir = kwds ['sdir']
        dims = numpy.shape (sdir)
        if dims == 0 or len (dims) == 2 and dims [1] != 3 :
            raise _LightingError('lighting direction must be 3 vector or ns-by-3 array.')
        flags = flags | 16
    else :
        sdir = _draw3_list [_draw3_nv + 4]
    if flags & 28 :
        if flags & 4 : _draw3_list [_draw3_nv + 2] = specular
        if flags & 8 : _draw3_list [_draw3_nv + 3] = spower
        if flags & 16 : _draw3_list [_draw3_nv + 4] = sdir
    if not flags :
        _draw3_list [_draw3_nv: _draw3_nv + 5] = _light3_list [0:5]
    undo3_set_ (light3_, old)

def light3_ (arg) :
    global _draw3_list, _draw3_nv

    _draw3_list [_draw3_nv:_draw3_nv + 5] = arg  [0:5]

def get3_light (xyz, * nxyz) :

    '''
    get3_light(xyz, nxyz)
       or get3_light(xyz)

      return 3D lighting for polygons with vertices XYZ.  If NXYZ is
      specified, XYZ should be sum(nxyz,axis=0)-by-3, with NXYZ being the
      list of numbers of vertices for each polygon (as for the plfp
      function).  If NXYZ is not specified, XYZ should be a quadrilateral
      mesh, ni-by-nj-by-3 (as for the plf function).  In the first case,
      the return value is len (NXYZ) long; in the second case, the
      return value is (ni-1)-by-(nj-1).

      The parameters of the lighting calculation are set by the
      light3 function.

      SEE ALSO: light3, set3_object, get3_normal, get3_centroid
      '''

    global _draw3_list, _draw3_nv
    lst = _draw3_list [_draw3_nv:]
    ambient = lst [0]
    diffuse = lst [1]
    specular = lst [2]
    spower = lst [3]
    sdir = lst [4]

    if len (nxyz) == 0 :
        normal = get3_normal (xyz)
    else :
        normal = get3_normal (xyz, nxyz [0])

    zc = getzc3_ ( )
    if ( not zc ) :
        view = numpy.array ( [0., 0., 1.],  numpy.float32)
    elif len (nxyz) == 0 :
        view = numpy.array ( [0., 0., zc],  numpy.float32) - get3_centroid (xyz)
    else :
        view = numpy.array ( [0., 0., zc],  numpy.float32) - get3_centroid (xyz, nxyz [0])
        m1 = \
           numpy.sqrt ( numpy.sum (view * view,axis=0))
        if m1 == 0. : m1 = 1.
        view = view / m1

    nv = normal [0, ...] * view [0] + normal [1, ...] * view [1] +  \
       normal [2, ...] * view [2]
    light = ambient + diffuse * abs (nv)
    if specular != 0. :
        sv = numpy.transpose (numpy.transpose (sdir) / numpy.sqrt (numpy.sum (numpy.transpose (sdir*sdir),axis=0)))
        sv = numpy.dot (sv, view)
        if len (numpy.shape (sdir)) == 1 :
            sn = numpy.sum(numpy.array([sdir[0]*normal[0],sdir[1]*normal[1],
                            sdir[2]*normal[2]]),axis=0)
            ####### I left out the specular_hook stuff.
            m1 = numpy.maximum (sn * nv -0.5 * sv + 0.5, 1.e-30)
            m1 = m1 ** spower
            light = light + (specular * m1)
        elif len (numpy.shape (sdir)) >= 2 :
            # multiple light sources
            nsrc = len (numpy.shape (sdir))
            for i in range (nsrc) :
                sn = numpy.sum(numpy.array([sdir[i,0]*normal[0],sdir[i,1]*normal[1],
                            sdir[i,2]*normal[2]]),axis=0)
                m1 = numpy.maximum (sn * nv -0.5 * sv [i] + 0.5, 1.e-30) ** spower [i]
                light = light + specular * m1
    return light

def get3_normal (xyz, *nxyz) :

    '''
      get3_normal(xyz, nxyz)
          or get3_normal(xyz)

      return 3D normals for polygons with vertices XYZ.  If NXYZ is
      specified, XYZ should be sum(nxyz,axis=0)-by-3, with NXYZ being the
      list of numbers of vertices for each polygon (as for the plfp
      function).  If NXYZ is not specified, XYZ should be a quadrilateral
      mesh, ni-by-nj-by-3 (as for the plf function).  In the first case,
      the return value is len(NXYZ)-by-3; in the second case, the
      return value is (ni-1)-by-(nj-1)-by-3.

      The normals are constructed from the cross product of the lines
      joining the midpoints of two edges which as nearly quarter the
      polygon as possible (the medians for a quadrilateral).  No check
      is made that these not be parallel; the returned 'normal' is
      [0,0,0] in that case.  Also, if the polygon vertices are not
      coplanar, the 'normal' has no precisely definable meaning.

      SEE ALSO: get3_centroid, get3_light
      '''

    if len (nxyz) == 0 :
        # if no polygon list is given, assume xyz is 2D mesh
        # form normal as cross product of medians
        m1 = dif_ (zcen_ (xyz, 1), 2)
        m2 = zcen_ (dif_ (xyz, 1), 2)
    else :
        # with polygon list, more elaborate calculation required
        # (1) frst subscripts the first vertex of each polygon
        frst = numpy.cumsum (nxyz [0],axis=0) - nxyz [0]

        # form normal by getting two approximate diameters
        # (reduces to above medians for quads)
        # (2) compute midpoints of first three sides
        n2 = (nxyz [0] + 1) / 2
        c0 = (numpy.take(xyz, frst, 0) + numpy.take(xyz, frst + 1, 0)) / 2.
        i = frst + n2 - 1
        c1 = (numpy.take(xyz, i, 0) + numpy.take(xyz, i + 1, 0)) / 2.
        i = n2 / 2
        c2 = (numpy.take(xyz, frst + i, 0) + numpy.take(xyz, frst + (i + 1) % nxyz [0], 0)) / 2.
        i = numpy.minimum (i + n2, nxyz [0]) - 1
        c3 = (numpy.take(xyz, frst + i, 0) + numpy.take(xyz, frst + (i + 1) % nxyz [0], 0)) / 2.
        m1 = c1 - c0
        m2 = c3 - c2

    # poly normal is cross product of two medians (or diameters)
    # normal = m1; I had to reverse the sign.
    if len (numpy.shape (xyz)) == 3 :
        n1 = m1 [2, :] * m2 [1, :] - \
                               m1 [1, :] * m2 [2, :]
        n2 = m1 [0, :] * m2 [2, :] - \
                               m1 [2, :] * m2 [0, :]
        n3 = m1 [1, :] * m2 [0, :] - \
                               m1 [0, :] * m2 [1, :]
    else :
        n1 = m1 [:, 2] * m2 [:, 1] - \
                               m1 [:, 1] * m2 [:, 2]
        n2 = m1 [:, 0] * m2 [:, 2] - \
                               m1 [:, 2] * m2 [:, 0]
        n3 = m1 [:, 1] * m2 [:, 0] - \
                               m1 [:, 0] * m2 [:, 1]
    m1 = numpy.sqrt (n1 ** 2 + n2 **2 + n3 **2)
    m1 = m1 + numpy.equal (m1, 0.0)
    normal = numpy.array([n1 / m1, n2 / m1, n3 / m1])

    return normal

def get3_centroid (xyz, * nxyz) :

    '''
      get3_centroid(xyz, *nxyz)
          or get3_centroid(xyz)

      return 3D centroids for polygons with vertices XYZ.  If NXYZ is
      specified, XYZ should be sum(nxyz,axis=0)-by-3, with NXYZ being the
      list of numbers of vertices for each polygon (as for the plfp
      function).  If NXYZ is not specified, XYZ should be a quadrilateral
      mesh, ni-by-nj-by-3 (as for the plf function).  In the first case,
      the return value is len(NXYZ) in length; in the second case, the
      return value is (ni-1)-by-(nj-1)-by-3.

      The centroids are constructed as the mean value of all vertices
      of each polygon.

      SEE ALSO: get3_normal, get3_light
    '''
    

    if len (nxyz) == 0 :
        # if no polygon list is given, assume xyz is 2D mesh
        centroid = zcen_ (zcen_ (xyz, 1), 0)
    else :
        # with polygon list, more elaborate calculation required
        last = numpy.cumsum (nxyz [0],axis=0)
        lst = numpy.bincount (1 + last) [0:-1]
        lst = numpy.cumsum (lst,axis=0)
        k = len (nxyz [0])
        l = numpy.shape (xyz) [0]
        centroid = numpy.zeros ( (k, 3))
        centroid [0:k, 0] = numpy.bincount (lst, xyz [0:l,0])
        centroid [0:k, 1] = numpy.bincount (lst, xyz [0:l,1])
        centroid [0:k, 2] = numpy.bincount (lst, xyz [0:l,2])
        fnxyz = numpy.array (nxyz [0], numpy.float32 )
        centroid = centroid / fnxyz
    return centroid

class _Get3Error(Exception):
    pass

def get3_xy (xyz, *flg) :

    '''
      get3_xy (xyz)
          or get3_xy(xyz, 1)

      Given anything-by-3 coordinates XYZ, return X and Y in viewer's
      coordinate system (set by rot3, mov3, orient3, etc.).  If the
      second argument is present and non-zero, also return Z (for use
      in sort3d or get3_light, for example).  If the camera position
      has been set to a finite distance with setz3, the returned
      coordinates will be tangents of angles for a perspective
      drawing (and Z will be scaled by 1/zc).
      Unlike the Yorick version, this function returns a 3-by-anything
      array of coordinates.
      Actually, what it returns is a 3-by-anything python array, whose
      0th element is the x array, whose 1th element is the y array, and
      whose 2th element is the z array if asked for.
      I believe that x, y, and z can be either 1d or 2d, so this
      routine is written in two cases.

    '''

    # rotate and translate to viewer's coordinate system
    shp = numpy.shape (xyz)
    if len (shp) == 3:
        # 2d mesh case is much more complex than in Yorick
        (k, l) = shp [1:3]
        go3_ = getorg3_ ()
        # Unwind xyz
        xx = numpy.ravel (xyz [0])
        yy = numpy.ravel (xyz [1])
        zz = numpy.ravel (xyz [2])
        tmpxyz = numpy.array ( [xx, yy, zz])
        gr3 = numpy.array (getrot3_ (), copy = 1)
        tmpxyz = numpy.dot (numpy.transpose (gr3),
           tmpxyz - numpy.array ( [ [go3_ [0]], [go3_ [1]], [go3_ [2]]]))
##    xx = numpy.transpose (numpy.reshape (numpy.ravel (tmpxyz [0]), (k,l)))
##    yy = numpy.transpose (numpy.reshape (numpy.ravel (tmpxyz [1]), (k,l)))
##    zz = numpy.transpose (numpy.reshape (numpy.ravel (tmpxyz [2]), (k,l)))
        xx = (numpy.reshape (numpy.ravel (tmpxyz [0]), (k,l)))
        yy = (numpy.reshape (numpy.ravel (tmpxyz [1]), (k,l)))
        zz = (numpy.reshape (numpy.ravel (tmpxyz [2]), (k,l)))
        tmpxyz = numpy.array ( [xx, yy, zz])
    elif len (shp) == 2:
        go3_ = getorg3_ ()
        lm = numpy.array (getrot3_ (), copy = 1)
        rm = (xyz - numpy.array ( [ go3_ [0], go3_ [1], go3_ [2]]))
        tmpxyz = numpy.dot (rm, lm)
    else:
        raise _Get3Error('xyz has a bad numpy.shape: ' + repr(shp))

    # do optional perspective projection
    zc = getzc3_ ()
    if zc != None :
        if len (shp) == 2 :
            z = tmpxyz [:, 2]
            zc = numpy.maximum (zc - z, 1.e-35)     # protect behind camera, avoid zero divide
            tmpxyz [:, 0] = tmpxyz [:, 0] / zc
            tmpxyz [:, 1] = tmpxyz [:, 1] / zc
            if len (flg) != 0 and flg [0] != 0 :
                tmpxyz [:, 2] = tmpxyz [:, 2] / zc
        elif len (shp) == 3 :
            z = tmpxyz [:,:, 2]
            zc = numpy.maximum (zc - z, 1.e-35)     # protect behind camera, avoid zero divide
            tmpxyz [:,:, 0] = tmpxyz [:,:, 0] / zc
            tmpxyz [:,:, 1] = tmpxyz [:,:, 1] / zc
            if len (flg) != 0 and flg [0] != 0 :
                tmpxyz [:,:, 2] = tmpxyz [:,:, 2] / zc
    return tmpxyz

class _UndoError(Exception):
    pass

_in_undo3 = 0
_undo3_list = []

def undo3 (n = 1) :

    '''
      undo3 ()
          or undo3 (n)
      Undo the effects of the last N (default 1) rot3, orient3, mov3, aim3,
      setz3, or light3 commands.
    '''

    global _in_undo3, _undo3_list
    n = 2 * n
    if n < 0 or n > len (_undo3_list) :
        raise _UndoError('not that many items in undo list')
    _in_undo3 = 1     # flag to skip undo3_set_
    # perhaps should save discarded items in a redo list?
    use_list = undo3_list [-n:]
    undo3_list = undo3_list [:-n]
    while n > 0 :
        fnc = use_list_ [0]
        del use_list_ [0]
        arg = use_list_ [0]
        del use_list_ [0]
        fnc (arg)
        n = n - 2
    _in_undo3 = 0
    draw3_trigger ( )

def set3_object (fnc, arg) :

    '''
      set3_object (drawing_function, [arg1,arg2,...])

      set up to trigger a call to draw3, adding a call to the
      3D display list of the form:

         DRAWING_FUNCTION ( [ARG1, ARG2, ...]))

      When draw3 calls DRAWING_FUNCTION, the external variable draw3_
      will be non-zero, so DRAWING_FUNCTION can be written like this:

      def drawing_function(arg) :

        if (draw3_) :
           arg1= arg [0]
           arg1= arg [1]
           ...
           ...<calls to get3_xy, sort3d, get3_light, etc.>...
           ...<calls to graphics functions plfp, plf, etc.>...
           return

        ...<verify args>...
        ...<do orientation and lighting independent calcs>...
        set3_object (drawing_function, [arg1,arg2,...])

    SEE ALSO: get3_xy, get3_light, sort3d
    '''

    global _draw3_list
    _draw3_list = _draw3_list + [fnc, arg]
    draw3_trigger ()

def setorg3_ ( x ) :
    # ZCM 2/21/97 change reflects the fact that I hadn't realized
    # that car and cdr, as functions, return the item replaced.
    global _draw3_list
    oldx = _draw3_list [1]
    _draw3_list [1] = x
    undo3_set_ ( setorg3_,  oldx)

def setzc3_ (x) :
    # ZCM 2/21/97 change reflects the fact that I hadn't realized
    # that car and cdr, as functions, return the item replaced.
    global _draw3_list
    oldx = _draw3_list [2]
    _draw3_list [2] = x
    undo3_set_ ( setzc3_,  oldx)

def getrot3_ () :
    return _draw3_list [0]

def getorg3_ () :
    return _draw3_list [1]

def getzc3_ () :
    return _draw3_list [2]

def undo3_set_ (fnc, arg) :
    global _undo3_list, _in_undo3, _undo3_limit
    # arg = copy.deepcopy (arg)
    if not _in_undo3 :
        if len (_undo3_list) >= 2 * _undo3_limit :
            _undo3_list = _undo3_list [0:2 * _undo3_limit - 2]
        _undo3_list = [fnc, arg] + _undo3_list
    draw3_trigger ( )

_in_undo3 = 0         # ??????????????
_in_undo3 = 100

def do_nothing ( ) :
    pass
    return

def clear_idler ( ) :
    _idler = do_nothing ( )

def set_idler ( fnc ) :
    global _idler
    _idler = fnc

def call_idler ( ) :
    global _idler
    _idler ( )

def _draw3_idler ( ) :
    # I have added orientation and limits to this because they may not
    # have been set by a previous command. If the user doesn't like this,
    # he/she can write his/her own idler. (ZCM 7/1/97)
    global _default_gnomon
    orient3 ()
    if win_current () == -1 :
        window3 (0)
    else :
        window3 (win_current ())
    gnomon (_default_gnomon)
    lims = draw3 (1)
    if lims == None :
        return
    else :
        limits (lims [0], lims [1], lims [2], lims [3])

def set_default_idler ( ) :
    set_idler (_draw3_idler)

set_default_idler ( )

_draw3_changes = None

def set_multiple_components ( n = 0 ) :
    global _multiple_components
    _multiple_components = n

set_multiple_components (0)

def has_multiple_components () :
    global _multiple_components
    return _multiple_components

def draw3_trigger ( ) :
    'arrange to call draw3 when everything else is finished'
    global _draw3_changes
    global _draw3_idler
    set_idler ( _draw3_idler )
    _draw3_changes = 1

def clear3 ( ) :
    'clear3 ( ) : Clear the current 3D display list.'
    global _draw3_list, _draw3_n
    _draw3_list [_draw3_n:] = []
    set_multiple_components (0)

def window3 ( * n , **kw ) :
    '''
    window3 () or window3 (n)
    initialize style='nobox.gs' window for 3D graphics
    '''
    window (*n, wait=1, style='nobox.gs', legends=0, **kw)


def sort3d (z, npolys) :

    '''
    sort3d(z, npolys)
      given Z and NPOLYS, with len(Z)==sum(npolys,axis=0), return
      a 2-element list [LIST, VLIST] such that Z[VLIST] and NPOLYS[LIST] are
      sorted from smallest average Z to largest average Z, where
      the averages are taken over the clusters of length NPOLYS.
      Within each cluster (polygon), the cyclic order of Z[VLIST]
      remains unchanged, but the absolute order may change.

      This sorting order produces correct or nearly correct order
      for a plfp command to make a plot involving hidden or partially
      hidden surfaces in three dimensions.  It works best when the
      polys form a set of disjoint closed, convex surfaces, and when
      the surface normal changes only very little between neighboring
      polys.  (If the latter condition holds, then even if sort3d
      mis-orders two neighboring polys, their colors will be very
      nearly the same, and the mistake won't be noticeable.)  A truly
      correct 3D sorting routine is impossible, since there may be no
      rendering order which produces correct surface hiding (some polys
      may need to be split into pieces in order to do that).  There
      are more nearly correct algorithms than this, but they are much
      slower.
    SEE ALSO: get3_xy
    '''

    # first compute z, the z-centroid of every poly
    # get a list the same length as x, y, or z which is 1 for each
    # vertex of poly 1, 2 for each vertex of poly2, etc.
    # the goal is to make nlist with bincount(nlist)==npolys
    nlist = numpy.bincount(numpy.cumsum (npolys,axis=0))[0:-1]
    nlist = numpy.cumsum (nlist,axis=0)
    # now sum the vertex values and divide by the number of vertices
    z = numpy.bincount (nlist, z) / npolys

    # sort the polygons from smallest z to largest z
    lst = index_sort (z)
    # next, find the list which sorts the polygon vertices
    # first, find a list vlist such that sort(vlist) is above list
    vlist = numpy.zeros (len (lst), numpy.int32)
    array_set (vlist, lst, numpy.arange (len (lst), dtype = numpy.int32))
    # then reset the nlist values to that pre-sorted order, so that
    # sort(nlist) will be the required vertex sorting list
    nlist = numpy.take(vlist, nlist, 0)
    # the final hitch is to ensure that the vertices within each polygon
    # remain in their initial order (sort scrambles equal values)
    # since the vertices of a polygon can be cyclically permuted,
    # it suffices to add a sawtooth function to a scaled nlist to
    # produce a list in which each cluster of equal values will retain
    # the same cyclic order after the sort
    # (note that the more complicated msort routine would leave the
    #  clusters without even a cyclic permutation, if that were
    #  necessary)
    n1max = max (npolys)    # this must never be so large that
                            # numberof(npolys)*nmax > 2e9
    nmax = n1max * numpy.ones (len (nlist), numpy.int32)
    vlist = index_sort (nmax * nlist +
       numpy.arange (len (nlist), dtype = numpy.int32) % n1max)
    #         primary sort key ^            secondary key  ^
    return [lst, vlist]

_square = 1 # Global variable which tells whether to force equal axes
_xfactor = 1.
_yfactor = 1. # These globals enable one to scale one or both axes up or down

def get_factors_ ( ) :
    return [_xfactor, _yfactor]

def get_square_ ( ) :
    global _square
    return _square

def limits_ (square = 0, yfactor = 1., xfactor = 1.) :
    global _square, _xfactor, _yfactor
    _square = square
    _xfactor = xfactor
    _yfactor = yfactor

def draw3 (called_as_idler = 0, lims = None) :

    '''
       draw3 (called_as_idler = 0, lims = None):
    Draw the current 3d display list.
    Ordinarily triggered automatically when the drawing changes.
    '''
    global _draw3, _draw3_changes, _draw3_list, _draw3_n, _gnomon
    if _draw3_changes :
        if called_as_idler :
            savesys=plsys()
            fma ( )
            plsys(savesys)

        # the first _draw3_n elements of _draw3_list are the viewing
        # transforms, lighting, etc.
        # thereafter, elements are (function, argument-list) pairs
        # the _draw3 flag alerts the functions that these are the draw
        # calls rather than the interactive setup calls
        set_draw3_ (1)
        lst = _draw3_list [_draw3_n:]
        no_lims = lims == None
        first = 1
        # ZCM Feb. 1997: Because Gist command 'limits' seems to
        # misbehave and be timing dependent, I have added the kludge
        # below, which seems to make things work.
        while lst != [] :
            fnc = lst [0]
            if no_lims :
                if (first) :
                    lims = fnc (lst [1])
                    first = 0
                else :
                    fv = fnc (lst [1])
                    if fv != None and lims != None :
                        lims = [min (fv [0], lims [0]),
                                max (fv [1], lims [1]),
                                min (fv [2], lims [2]),
                                max (fv [3], lims [3])]
                    elif fv != None :
                        lims = fv
            else :
                fnc (lst [1])
            lst = lst [2:]
        if _gnomon :
            _gnomon_draw ( )
        _draw3_changes = None
        set_draw3_ (0)
        return [float(o) for o in lims]
#     _draw3 = 0

try :
    dummy = _draw3_view
except :
    _draw3_view = [numpy.array ([[1, 0, 0], [0, 1, 0], [0, 0, 1]]), [0., 0., 0.], None]
_draw3_nv = len (_draw3_view)

try :
    dummy = _draw3
except :
    set_draw3_ (0)

def get_draw3_ ( ) :
    global _draw3
    return _draw3

try :
    dummy = _light3_ambient
except :
    _light3_ambient = 0.2

try :
    dummy = _light3_diffuse
except :
    _light3_diffuse = 1.0

try :
    dummy = _light3_specular
except :
    _light3_specular = 0.0

try :
    dummy = _light3_spower
except :
    _light3_spower = 2

try :
    dummy = _light3_sdir
except :
    _light3_sdir = numpy.array ( [1.0, 0.5, 1.0]) / numpy.sqrt(2.25)

_light3_list = [_light3_ambient, _light3_diffuse, _light3_specular,
                _light3_spower, _light3_sdir]


_draw3_list = _draw3_view + _light3_list
_draw3_n = len (_draw3_list)

def get_draw3_list_ ( ) :
    global _draw3_list
    return _draw3_list

def get_draw3_n_ ( ) :
    global _draw3_n
    return _draw3_n

try :
    dummy = _gnomon
except :
    _gnomon = 0

def set_default_gnomon ( * n ) :
    # The default gnomon value is used when _draw3 is nonzero, i. e.,
    # when a plot is actually done after every plot call.
    global _default_gnomon
    if len (n) > 0 :
        _default_gnomon = n
    else :
        _default_gnomon = 0

set_default_gnomon (0)

def gnomon (* on, ** kw) :

    '''
    gnomon ()
       or gnomon (onoff)
      Toggle the gnomon display. If on is present and non-zero,
      turn on the gnomon. If zero, turn it off.

      The gnomon shows the X, Y, and Z axis directions in the
      object coordinate system. The directions are labeled.
      The gnomon is always infinitely far behind the object
      (away from the camera).

      There is a mirror-through-the-screen-plane ambiguity in the
      display which is resolved in two ways: (1) the (X, Y, Z)
      coordinate system is right-handed, and (2) If the tip of an
      axis projects into the screen, its label is drawn in opposite
      polarity to the other text in the screen.
    '''

#    (ZCM 4/4/97) Add keyword argument chr to allow specification
#    of the axis labels.

    global _gnomon, chr
    old = _gnomon
    if len (on) == 0 :
        _gnomon = 1 - _gnomon
    elif (on [0]) :
        _gnomon = 1
    else :
        _gnomon = 0
    if old != _gnomon :
        draw3_trigger ()
    if 'chr' in kw :
        chr = kw ['chr']
    else :
        chr = ['X', 'Y', 'Z']

def _gnomon_draw ( ) :
    global chr
    o = numpy.array ( [0., 0., 0.],  numpy.float32)
    x1 = numpy.array ( [1., 0., 0.],  numpy.float32)
    y1 = numpy.array ( [0., 1., 0.],  numpy.float32)
    z1 = numpy.array ( [0., 0., 1.],  numpy.float32)
    xyz1 = numpy.array (getrot3_ ( ), copy = 1)
    xyz2 = numpy.array([[o,x1],[o,y1],[o,z1]])
    s1 = numpy.shape ( xyz1 )
    s2 = numpy.shape ( xyz2 )
    xyz = numpy.zeros ( (s2 [1], s2 [0], s1 [1] ), numpy.float32)
    xyz [0, :, :] = numpy.dot (numpy.transpose (xyz1), xyz2 [:, 0, :])
    xyz [1, :, :] = numpy.dot (numpy.transpose (xyz1), xyz2 [:, 1, :])
    xyz = .0013 * _gnomon_scale * xyz
    x1 = xyz [0:2, 0, 0:3]
    y1 = xyz [0:2, 1, 0:3]
    z1 = xyz [1, 2, 0:3]
    x0 = x1 [0]
    x1 = x1 [1]
    y0 = y1 [0]
    y1 = y1 [1]
    wid = min (_gnomon_scale / 18., 6.)
    if ( wid < 0.5 ) : wid = 0.
    savesys = plsys (0)
    pldj (x0 + _gnomon_x, y0 + _gnomon_y, x1 + _gnomon_x, y1 + _gnomon_y,
          width = wid, type = 1, legend = '')
    plsys (savesys)

    # Compute point size of labels (1/3 of axis length)
    pts = [8, 10, 12, 14, 18, 24] [numpy.digitize (_gnomon_scale / 3.0,
          numpy.array ([9, 11, 13, 16, 21], numpy.int32))]

    if _gnomon_scale < 21.0 :
        x1 = x1 * 21. / _gnomon_scale
        y1 = y1 * 21. / _gnomon_scale
    # label positions: first find shortest axis
    xy = numpy.sqrt (x1 * x1 + y1 * y1)
    xysum = numpy.add.reduce (xy)
    i = argmin (xy,axis=-1)          # mnx (xy)
    jk = [ [1, 2], [2, 0], [0, 1]] [i]
    j = jk [0]
    k = jk [1]
    if xy [i] < 1.e-7 * xysum : # guarantee not exactly zero
        x1 [i] = -1.e-6 * (x1 [j] + x1 [k] )
        y1 [i] = -1.e-6 * (y1 [j] + y1 [k] )
        xy [i] = numpy.sqrt (x1 [i] * x1 [i] + y1 [i] * y1 [i])
    xyi = xy [i]
    # next find axis nearest to shortest
    if abs (x1 [j] * y1 [i] - y1 [j] * x1 [i]) * xy [k] > \
       abs (x1 [k] * y1 [i] - y1 [k] * x1 [i]) * xy [j] :
        jk = j
        j = k
        k = jk
    # furthest axis first--move perpendicular to nearest axis
    xk = - y1 [j]
    yk = x1 [j]
    xy = numpy.sqrt (xk * xk + yk * yk)
    xk = xk / xy
    yk = yk / xy
    if (xk * x1 [k] + yk * y1 [k] < 0.0 ) :
        xk = - xk
        yk = - yk
    # nearer axis next--move perpendicular to furthest axis
    xj = - y1 [k]
    yj = x1 [k]
    xy = numpy.sqrt (xj * xj + yj * yj)
    xj = xj / xy
    yj = yj / xy
    if (xj * x1[j] + yj * y1 [j] < 0.0 ) :
        xj = - xj
        yj = - yj
    # shortest axis last -- move perpendicular to nearer
    xi = - y1 [j]
    yi = x1 [j]
    xy = numpy.sqrt (xi * xi + yi * yi)
    xi = xi / xy
    yi = yi / xy
    if (xi *x1 [i] + yi * y1 [i] < 0.0) :
        xi = - xi
        yi = - yi

    # shortest axis label may need adjustment
    d = 0.0013 * pts
    if xyi < d :
        # just center it in correct quadrant
        jk = numpy.sign (xi * xj + yi * yj) or 1
        yi = numpy.sign (xi * xk + yi * yk) or 1
        xi = jk * xj + yi * xk
        yi = jk * yj + yi * yk
        jk = numpy.sqrt (xi * xi + yi * yi)
        xi = xi / jk
        yi = yi / jk
    x = numpy.zeros (3, numpy.float32)
    y = numpy.zeros (3, numpy.float32)
    x [i] = xi
    x [j] = xj
    x [k] = xk
    y [i] = yi
    y [j] = yj
    y [k] = yk
    x = x * d
    y = y * d
    x = x + x1 + _gnomon_x
    y = y + y1 + _gnomon_y
    try :
        dum = chr
    except :
        chr = ['X', 'Y', 'Z']
    gnomon_text_ (chr [i], x [i], y [i], pts, z1 [i] < 1.e-6)
    gnomon_text_ (chr [j], x [j], y [j], pts, z1 [j] < 1.e-6)
    gnomon_text_ (chr [k], x [k], y [k], pts, z1 [k] < 1.e-6)

try :
    dummy = _gnomon_scale
except :
    _gnomon_scale = 30.       # axes lengths in points
try :
    dummy = _gnomon_x
except :
    _gnomon_x = 0.18          # gnomon origin in system 0 coordinates
try :
    dummy = _gnomon_y
except :
    _gnomon_y = 0.42

def gnomon_text_ (chr, x, y, pts, invert) :
    # pts = 8, 10, 12, 14, 18, or 24
    col = 'fg'
    if invert :
        savesys = plsys (0)
        print(('savesys',savesys))
        plg (numpy.array ( [y, y]), numpy.array ( [x, x]), type = 1, width = 2.2 * pts,
             color = col, marks = 0, legend = '')
        plsys (savesys)
        col = 'bg'
    plt (chr, x, y, justify = 'CH', color = col, height = pts,
         font = 'helvetica', opaque = 0)

g_nframes = 30

def spin3 (nframes = 30, axis = numpy.array ([-1, 1, 0],  numpy.float32), 
   dtmin = 0.0, lims = None, angle = 2. * numpy.pi) :

    '''
    spin3 ( ) or spin3 (nframes) os spin3 (nframes, axis)
      Spin the current 3D display list about AXIS over NFRAMES.  Keywords
      dtmin= the minimum allowed interframe time in seconds (default 0.0),

      The default AXIS is [-1,1,0] and the default NFRAMES is 30.
    SEE ALSO: rot3
    '''

    from .Mplot import movie

    # Note on global variables (ZCM 2/21/97):
    # I see no better way of sharing these between spin3 and _spin3
    #   than making them global. Otherwise one would have to pass
    #   them to movie, which would then send them as arguments to
    #   _spin3. But because movie may call other routines, every one
    #   of them would have to have these values, necessary or not.
    #   So I have started their names with underscores; at least
    #   this makes them inaccessible outside this module.
    global _phi, _theta, _dtheta
    global _g_nframes
    _g_nframes = nframes
    _dtheta = angle / (nframes - 1)
    _theta = numpy.arccos (axis [2] / numpy.sqrt (axis [0] * axis [0] + axis [1] * axis [1] +
                    axis [2] * axis [2]))
    inc = axis [0] == axis [1] == 0
    _phi = numpy.arctan2 (axis [1], axis [0] + inc)
    orig = save3 ( )
    movie (_spin3, dtmin, lims)
    restore3 (orig)

def _spin3 (i) :
    global _g_nframes
    global _phi, _theta, _dtheta
    if i >= _g_nframes:
        return 0
    rot3 (za = -_phi)
    rot3 (ya = -_theta, za = _dtheta)
    rot3 (ya = _theta, za = _phi)
    lims = draw3 ( )
    # fixme, gistC does not cast numpy.float64 to float
    limits (float(lims [0]), float(lims [1]), float(lims [2]), float(lims [3]))
    return 1

#--

def is_scalar(x):
    return len(numpy.shape(x)) == 0


