import numpy
import gist

def run(arrow_scales=True):
  gist.fma()

  # generate a random field

  test_dim=10

  dx=numpy.random.rand(test_dim**2)-0.5
  dy=numpy.random.rand(test_dim**2)-0.5
  p=numpy.indices((test_dim,test_dim))
  x=p[0].ravel()
  y=p[1].ravel()

  X1=x
  Y1=y
  X2=x+dx
  Y2=y+dy
  gist.pldj(X1,Y1,X2,Y2)

  arrow_a = numpy.pi/6.
  arrow_len = .5

  slo=(Y2-Y1)/(X2-X1)
  ang=numpy.arctan(slo)
  ang1=ang+arrow_a
  ang2=ang-arrow_a

  if arrow_scales:
     ar_=numpy.sign(X2-X1)*arrow_len*((X2-X1)**2+(Y2-Y1)**2)
     aX1=X2-ar_*numpy.cos(ang1)
     aY1=Y2-ar_*numpy.sin(ang1)
     aX2=X2-ar_*numpy.cos(ang2)
     aY2=Y2-ar_*numpy.sin(ang2)
  else:
     ar_=numpy.sign(X2-X1)*arrow_len*numpy.max(((X2-X1)**2+(Y2-Y1)**2)**.5)
     aX1=X2-ar_*numpy.cos(ang1)
     aY1=Y2-ar_*numpy.sin(ang1)
     aX2=X2-ar_*numpy.cos(ang2)
     aY2=Y2-ar_*numpy.sin(ang2)

  gist.pldj(X2,Y2,aX1,aY1,color='red')
  gist.pldj(X2,Y2,aX2,aY2,color='red')
  gist.limits()

