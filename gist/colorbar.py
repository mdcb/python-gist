# Copyright (c) 1996, 1997, The Regents of the University of California.
# All rights reserved.  See Legal.htm for full text and disclaimer.

# ed williams' colorbar stuff

import numpy
from .gistC import *
import gistfuncs

import sys # FIXME something weird's happening

def nice_levels (z, n = 8) :
    """nice_levels(z, n = 8) finds approximately n "nice values"
    between min(z) and max(z) for axis labels. n defaults to eight.
    """
    zmax = max (numpy.ravel (z))
    zmin = min (numpy.ravel (z))
    finest = abs (zmax - zmin) / float (n)
    # blows up on zmin=zmax
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
    if (abs (cmin - zmin) < 0.01 * unit) :
        cmin = cmin + unit
    cmax = unit * numpy.floor (zmax / unit)
    if (abs (cmax - zmax) < 0.01 * unit) :
        cmax = cmax - unit
    n = int ( ( (cmax - cmin) / unit + 0.5) + 1)
    # FIXME ???
    sys.stdout.flush()
    levs = gistfuncs.span (cmin, cmax, n)
    _list = numpy.nonzero(numpy.less (numpy.abs (levs), 0.1 * unit))[0]
    if len (_list) > 0 :
        gistfuncs.array_set (levs, _list, 0.0)
    return levs

def color_bar (minz, maxz, split = 0, ncol = None, ymax=0.85, ymin=0.44, xmin0=0.62, xmax0=0.64, zlabel=None, fontsize=16, font='helvetica', color='black') :
    """
    color_bar (minz, maxz) plots a color bar to the right of the plot square
    labelled by the z values from minz to maxz.

    plf (z, y, x)
    color_bar (z (min, min), z (max, max))

    or
    plf (z, y, x, cmin = MINZ, cmax = MAXZ)
    color_bar (MINZ, MAXZ)

    are typical usage
    """
    if ncol is None:
        ncol = 100 + (1 - split) * 100
    plsys (0)
    # FIXME: he wont work, see below...
    #sys.stdout.flush()
    if type (minz) == type (maxz) == int : # Do not change!!! I did ...
        plotval = numpy.reshape (numpy.arange (minz, maxz + 1, dtype = numpy.uint8),
           (maxz + 1 - minz, 1))
        pli (plotval, xmin0, ymin, xmax0, ymax) # draw bar
    elif not split :
        # FIXME ???
        sys.stdout.flush()
        d1=gistfuncs.span (0, 1, ncol)
        data=numpy.reshape(d1, (ncol, 1))
        pli (data, xmin0, ymin, xmax0, ymax) # draw bar
    else :
        pli (numpy.reshape (split_bytscl (gistfuncs.span (0, 1, ncol), 0).astype (numpy.uint8), (ncol, 1)),
           xmin0, ymin, xmax0, ymax) # draw bar
    pldj (numpy.array ( [xmin0, xmin0]), numpy.array ( [ymin, ymax]), numpy.array ( [xmax0, xmax0]),
          numpy.array ( [ymin, ymax]), color=color)
    plsys (1)
    levs = nice_levels (numpy.array ( [minz, maxz]))
    scales = []
    for i in range (len (levs)) :
        scales.append ( "% .5g" % levs [i])
    ys = ymin + (ymax - ymin) * (levs - minz) / (maxz - minz)
    llev = len (levs)
    rllev = list(range(llev))
    for i in rllev :
        plt (scales [i], xmax0+0.005, ys [i], color=color)   # labels
    xmin = numpy.zeros (llev, numpy.float32)
    xmax = numpy.zeros (llev, numpy.float32)
    xmin [0:llev] = xmin0
    xmax [0:llev] = xmax0+0.005
    plsys (0)
    pldj (xmin, ys, xmax, ys, color=color) # ticks
    plsys (1)
    # Write the max and min on bar
    xmid = (xmin0 + xmax0)/2.0
    if max (ys) > (ymax-0.01):
        plt ("% .5g" % maxz, xmid, ymax + 0.020, justify="CA",
             color=color)
    else :
        plt ("% .5g" % maxz, xmid, ymax + 0.005, justify="CA",
             color=color)
    plt ("% .5g" % minz, xmid, ymin - 0.0025, justify = "CT",
         color=color)
    if zlabel is None:
        pass
    elif zlabel != "":
        ymidpt = (ymax+ymin)/2.0
        x0 = xmax0 + 0.04
        plt(zlabel, x0, ymidpt, color=color,
               font=font, justify="CB", height=fontsize, orient=3)
