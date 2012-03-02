#!/usr/bin/env python

import os
import sys
import numpy.distutils.system_info
import distutils
import glob

x11_info = numpy.distutils.system_info.get_info('x11')
xft_info = numpy.distutils.system_info.get_info('xft')

gistsource = glob.glob('yorick/gist/*.c')
gistsource.append('plugin/plug-hlevel.c')
gistsource.pop(gistsource.index('yorick/gist/browser.c'))
gistsource.pop(gistsource.index('yorick/gist/bench.c'))
gistsource.pop(gistsource.index('yorick/gist/cgmin.c'))

unixsource = [
  "yorick/play/unix/dir.c",
  "yorick/play/unix/files.c",
  "yorick/play/unix/fpuset.c",
  "yorick/play/unix/handler.c",
  "yorick/play/unix/pathnm.c",
  #"yorick/play/unix/pmain.c",
  "yorick/play/unix/slinks.c",
  "yorick/play/unix/stdinit.c",
  "yorick/play/unix/timeu.c",
  "yorick/play/unix/timew.c",
  "yorick/play/unix/udl.c",
  "yorick/play/unix/uevent.c",
  "yorick/play/unix/ugetc.c",
  "yorick/play/unix/uinbg.c",
  "yorick/play/unix/umain.c",
  "yorick/play/unix/usernm.c",
  "yorick/play/unix/uspawn.c",
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

def getbuildopt(gistpath,config,config_path):
  local_path=config.local_path

  extra_compile_args = ['-DGISTPATH="\\"%s\\""' % gistpath]
  extra_compile_args.append('-DPYGIST_VERSION="\\"%s\\""' % config.version)

  extra_compile_args.append("-DSTAND_ALONE") # for yorick/play/any/numfmt.c
  extra_compile_args.append("-O2")
  extra_compile_args.append('-DYLAPACK_NOALIAS')
  extra_compile_args.append('-DYCBLAS_NOALIAS')
  # TODO: patch only works for bdist_rpm
  extra_compile_args.append("-DHAVE_XFT")

  library_dirs = [os.path.join(local_path,x) for x in ['.','yorick']]
  library_dirs.extend(x11_info.get('library_dirs',[]))

  dirs = [ 'plugin','yorick/gist', 'yorick/play', 'yorick/play/unix', 'yorick/regexp',
           'yorick/matrix', 'yorick/yorick' ]
  include_dirs = [os.path.join(local_path,x) for x in dirs]
  include_dirs.extend(x11_info.get('include_dirs',[]))
  include_dirs.extend(xft_info.get('include_dirs'))

  libraries = x11_info.get('libraries',['X11'])
  libraries.extend(xft_info.get('libraries'))

  for line in file(os.path.join(config_path,"Make.cfg")):
    if line.startswith('#'): continue
    key,val=line.strip().split('=')
    if val != '':
      if key == 'MATHLIB':
        libraries.append(val.lstrip('-l'))
      elif key == 'NO_EXP10':
        extra_compile_args.append(val)
      elif key == 'XINC':
        include_dirs.append(val.lstrip('-I'))
      elif key == 'XLIB':
        libraries.append(val.lstrip('-L'))
      elif key == 'D_FPUSET':
        extra_compile_args.append(val)

  return include_dirs, library_dirs, libraries, extra_compile_args

from distutils.command.config import config
import os

class yorick_configure(config):
  def __init__(self, local_path, config_path):
    #from distutils.dist import Distribution
    #super(yorick_configure,self).__init__(self,Distribution())
    self.config_path = config_path

  def run (self):
    os.chdir('yorick')
    os.system('gmake clean config')
    os.chdir('..')
    os.system('cp yorick/Make.cfg '+self.config_path)

def configuration(parent_package='',top_path=None):
  from numpy.distutils.misc_util import Configuration
  
  config = Configuration(
    package_name='gist',
    parent_name=parent_package,
    top_path=top_path,
    package_path='gist',
    version='dev',
    description='gist for python.',
    long_description='Python plugin for gist, the yorick graphic environment.',
    url='https://github.com/mdcb/python-gist',
    author='Matthieu Bec',
    author_email='mdcb808@gmail.com',
    license='GPLv3',
    )


  
  v=file(os.path.join(config.local_path,'yorick/play/yversion.h')).readline()
  v=v.strip().split(' ')[-1]
  v=v.strip('"')
  config.version=v

  gistdata_path = os.path.join(distutils.sysconfig.get_python_lib(1),config.path_in_package,"gistdata")
  gistdata_path = gistdata_path.replace("\\",r"\\\\")

  def get_playsource(extension,build_dir):
    playsource = unixsource + x11source + anysource
    sources = [os.path.join(config.local_path,f) for f in playsource]
    config_path = os.path.join(build_dir,'confgist')
    distutils.dir_util.mkpath(config_path)
    conf = yorick_configure(config.local_path,config_path)
    #   This is repeating code, but I'm not sure how to avoid it
    #   As this gets run before overall setup does.
    # Generate Make.cfg and config.h:
    conf.run()

    inc,lib,ll,cc = getbuildopt(gistdata_path,config,config_path)

    extension.include_dirs.extend(inc)
    extension.library_dirs.extend(lib)
    extension.libraries.extend(ll)
    extension.extra_compile_args.extend(cc)
    return sources

  gistC = os.path.join(config.local_path,'./plugin/gistCmodule.c')
  sources = [os.path.join(config.local_path,f) for f in gistsource]
  sources = [gistC] + sources + [get_playsource]

  config.add_extension('gistC',sources,depends = ['yorick','.'])
  config.add_extension('gistfuncs',[os.path.join(config.local_path,'./plugin/gistfuncsmodule.c')])
  
  config.add_subpackage('',subpackage_path='gist')

  gist_data = [os.path.join('gistdata',f) for f in ('*.gs','*.gp')]
  gist_data.extend([os.path.join('yorick' ,'g',f) for f in ('*.gs','*.gp')])
  config.add_data_files (('gistdata',gist_data))

  return config

if __name__ == '__main__':
  from numpy.distutils.core import setup
  setup(name='python-',configuration=configuration)
