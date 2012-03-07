#!/usr/bin/env python

patch_work_dir = './build'  # TODO - hide global

import os
import sys
import distutils
import glob
#import shutil
from distutils.core import setup, Extension
from distutils.core import Distribution, Command
from distutils.command.build import build
from distutils import log
import numpy.distutils.system_info # pkg_config

x11_info = numpy.distutils.system_info.get_info('x11')
xft_info = numpy.distutils.system_info.get_info('xft')

gistsource = glob.glob('yorick/gist/*.c')
gistsource.pop(gistsource.index('yorick/gist/browser.c'))
gistsource.pop(gistsource.index('yorick/gist/bench.c'))
gistsource.pop(gistsource.index('yorick/gist/cgmin.c'))

unixsource = [
  'yorick/play/unix/dir.c',
  'yorick/play/unix/files.c',
  'yorick/play/unix/fpuset.c',
  'yorick/play/unix/handler.c',
  'yorick/play/unix/pathnm.c',
  #'yorick/play/unix/pmain.c',
  'yorick/play/unix/slinks.c',
  'yorick/play/unix/stdinit.c',
  'yorick/play/unix/timeu.c',
  'yorick/play/unix/timew.c',
  'yorick/play/unix/udl.c',
  'yorick/play/unix/uevent.c',
  'yorick/play/unix/ugetc.c',
  'yorick/play/unix/uinbg.c',
  'yorick/play/unix/umain.c',
  'yorick/play/unix/usernm.c',
  'yorick/play/unix/uspawn.c',
  ]

x11source = glob.glob('yorick/play/x11/*.c')

anysource = glob.glob('yorick/play/any/*.c')
anysource.pop(anysource.index('yorick/play/any/hashtest.c'))
anysource.pop(anysource.index('yorick/play/any/test2d.c'))
anysource.pop(anysource.index('yorick/play/any/mmtest.c'))

anysource.extend(glob.glob('yorick/yorick/*.c'))
anysource.pop(anysource.index('yorick/yorick/fortrn.c'))
anysource.pop(anysource.index('yorick/yorick/codger.c'))
anysource.pop(anysource.index('yorick/yorick/parsre.c'))

anysource.extend(glob.glob('yorick/regexp/*.c'))
anysource.extend(glob.glob('yorick/matrix/*.c'))
anysource.extend(glob.glob('yorick/fft/*.c'))

define_macros=[]
extra_compile_args=[]

# version
version=file('yorick/play/yversion.h').readline()
version=version.strip().split(' ')[-1]
version=version.strip('"')

# GISTPATH to *.g[sp]
gistdata_path = os.path.join(distutils.sysconfig.get_python_lib(1),'gist/gistdata') # 'gist' is pkg.name
gistdata_path = gistdata_path.replace('\\',r'\\\\')

define_macros.append(('GISTPATH', '\\"%s\\"' % gistdata_path ))
define_macros.append(('PYGIST_VERSION',  '\\"%s\\"' % version))
define_macros.append(('STAND_ALONE',     None                )) # for yorick/play/any/numfmt.c
define_macros.append(('YLAPACK_NOALIAS', None                ))
define_macros.append(('YCBLAS_NOALIAS',  None                ))

gist_data=glob.glob('gistdata/*.g[sp]')
gist_data.extend(glob.glob('yorick/g/*.g[sp]'))
data_files = [(gistdata_path, gist_data),]

extra_compile_args.append('-O2')


library_dirs = x11_info.get('library_dirs',[])

dirs = [ 'yorick/gist', 'yorick/play', 'yorick/play/unix', 'yorick/regexp', 'yorick/matrix', 'yorick/yorick' ]
include_dirs = [os.path.join(patch_work_dir,x) for x in dirs]
include_dirs.extend(['plugin'])
include_dirs.extend(x11_info.get('include_dirs',[]))
include_dirs.extend(xft_info.get('include_dirs'))

libraries = x11_info.get('libraries',['X11'])
libraries.extend(xft_info.get('libraries'))

# sources
sources = unixsource + x11source + anysource + gistsource
sources = [ os.path.join(patch_work_dir,f) for f in sources]
sources.append('plugin/plug-hlevel.c')
sources.append('plugin/gistCmodule.c')

class patch_cmd(Command):
  description = 'apply patches prior to build'
  
  #user_options = [('name=', 'n', 'option name abreviated by n'),]
  
  boolean_options = ['xft_patch','zeroborder_patch']
  #negative_opt = {'no-patch-bool-flag': 'patch-bool-flag'}

  def initialize_options(self):
    self.xft_patch = True
    self.zeroborder_patch = True

  def finalize_options(self):
    pass

  def run(self):
    log.info('preparing patch tree copy')
    if not os.path.isdir(patch_work_dir): self.mkpath(patch_work_dir)
    patchdir=os.path.join(patch_work_dir,'yorick')
    #if os.path.isdir(patchdir): shutil.rmtree(patchdir)
    self.mkpath(patchdir)
    self.copy_tree('yorick', patchdir)
    log.info('applying patches')
    if self.xft_patch:
      os.system('cd %s && patch -p1 < ../../patch/xft.patch' % patchdir)
      for ext in self.distribution.ext_modules:
        ext.define_macros.append(('HAVE_XFT', None))
    if self.zeroborder_patch: os.system('cd %s && patch -p1 < ../../patch/yorick-cvs-pwin-border.patch' % patchdir)

class mkconfig_cmd(Command):
  description = 'configure yorick prior to build'
 
  def initialize_options(self):
    pass

  def finalize_options(self):
    pass

  def run(self):
    log.info('making config')
    patchdir=os.path.join(patch_work_dir,'yorick')
    os.system('cd %s; gmake clean config;' % patchdir)
    log.info('parse config')
    libraries=[]
    define_macros=[]
    #include_dirs=[]
    for line in file(os.path.join(patch_work_dir,'yorick/Make.cfg')):
      if line.startswith('#'): continue
      key,val=line.strip().split('=')
      if val != '':
        if key == 'MATHLIB':
          libraries.append(val.lstrip('-l'))
        elif key == 'NO_EXP10':
          define_macros.append((val.lstrip('-D'), None))
        elif key == 'D_FPUSET':
          define_macros.append((val.lstrip('-D'), None))
        #elif key == 'XINC':
        #  include_dirs.append(val.lstrip('-I'))
        #elif key == 'XLIB':
        #  libraries.append(val.lstrip('-L'))
    # update our build_ext(s)
    for ext in self.distribution.ext_modules:
      ext.libraries.extend(libraries)
      ext.define_macros.extend(define_macros)
      #ext.include_dirs.extend(include_dirs)

class gist_build(build):
  description = 'build python gist.'
  
  def __init__(self, dist):
    build.__init__(self, dist)

  def has_patches(self):
    # TODO return self.distribution.has_patches()
    return True
  
  sub_commands = [
      ('patch',     has_patches      ),
      ('mkconfig',  lambda self:True ),
    ]

  sub_commands.extend(build.sub_commands)
  
class Gist_dist(Distribution):
  def __init__ (self, attrs=None):
    #super(Gist_dist,self).__init__(attrs)
    Distribution.__init__(self, attrs)
    self.cmdclass = {
      'build':          gist_build,    # override
      'patch':          patch_cmd,
      'mkconfig':       mkconfig_cmd,
    }

long_description='''The Python Gist Scientific Graphics Package is a module for production of general scientific graphics. Gist is the graphic frontend for Yorick, written by David H. Munro of Lawrence Livermore National Laboratory. The library is small, portable, efficient, and full-featured. It produces x-vs-y plots with ``good'' tick marks and tick labels, 2-D quadrilateral mesh plots with contours, vector fields, or pseudocolor maps on such meshes, and a selection of 3-D plots.'''

setup(
  name='python-gist',
  distclass=Gist_dist,
  version=version,
  description='gist for python.',
  long_description=long_description,
  author='Matthieu Bec',
  author_email='mdcb808@gmail.com',
  url='https://github.com/mdcb/python-gist',
  license='GPLv3',
  ext_modules=[
     Extension(
        name='gist.gistC',
        sources=sources,
        include_dirs=include_dirs,
        #undef_macros=undef_macros,
        define_macros=define_macros,
        library_dirs=library_dirs,
        libraries=libraries,
        #runtime_library_dirs = ['xxx','yyy'],
        extra_compile_args = extra_compile_args,
        ),
     Extension(
        name='gist.gistfuncs',
        sources=['plugin/gistfuncsmodule.c'],
        include_dirs=include_dirs,
        #undef_macros=undef_macros,
        define_macros=define_macros,
        library_dirs=library_dirs,
        libraries=libraries,
        #runtime_library_dirs = ['xxx','yyy'],
        extra_compile_args = extra_compile_args,
        ),
     ],
  packages = ['gist'],
  package_dir = {'gist': 'gist'},
  install_path = 'gist',
  data_files=data_files,
  )

