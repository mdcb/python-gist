#!/usr/bin/env python

from os import environ
from os.path import abspath, dirname, join
import sys
from distutils import dir_util
from distutils.sysconfig import get_python_lib
import glob


#  EXECUTE LINE:
#    python setup.py build             (optional)
#    python setup.py build -g install  (build a debug version and install)
#    python setup.py install           (does both build and install)
#    python setup.py sdist             (make a distribution version)
#    python setup.py bdist_rpm         (make an rpm version)

gistsource = glob.glob('yorick/gist/*.c')
gistsource.append('plugin/plugin-hlevel.c')
gistsource.pop(gistsource.index('yorick/gist/browser.c'))
gistsource.pop(gistsource.index('yorick/gist/bench.c'))
gistsource.pop(gistsource.index('yorick/gist/cgmin.c'))

unixsource = [
              "yorick/play/unix/dir.c",
              "yorick/play/unix/files.c",
              "yorick/play/unix/fpuset.c",
              "yorick/play/unix/handler.c",
              "yorick/play/unix/pathnm.c",
              "yorick/play/unix/pmain.c",
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


allsource = glob.glob('yorick/play/any/*.c')
allsource.pop(allsource.index('yorick/play/any/hashtest.c'))
allsource.pop(allsource.index('yorick/play/any/test2d.c'))
allsource.pop(allsource.index('yorick/play/any/mmtest.c'))
allsource.extend(glob.glob('yorick/yorick/*.c'))
allsource.pop(allsource.index('yorick/yorick/fortrn.c'))
allsource.pop(allsource.index('yorick/yorick/codger.c'))
allsource.pop(allsource.index('yorick/yorick/parsre.c'))
# STAND_ALONE
# allsource.pop(allsource.index('yorick/play/any/numfmt.c'))
allsource.extend(glob.glob('yorick/regexp/*.c'))
allsource.extend(glob.glob('yorick/matrix/*.c'))
allsource.extend(glob.glob('yorick/fft/*.c'))
allsource.append('plugin/plugin-ywrap.c')
allsource.append('plugin/plugin-yinit.c')

def getallparams(gistpath,local_path,config_path):
   from numpy.distutils.system_info import get_info
   x11_info = get_info('x11')
   extra_compile_args = ['-DGISTPATH="\\"' + gistpath + '\\""' ]
   extra_compile_args.append("-DSTAND_ALONE") # [yorick/play/any/numfmt.c]
   extra_compile_args.append("-O2")
   print 'TODO HAVE_XFT'
   #extra_compile_args.append("-DHAVE_XFT")
   extra_link_args = []
   libraries = x11_info.get('libraries',['X11'])


   include_dirs = ['plugin','yorick/gist', 'yorick/play', 'yorick/play/unix', 'yorick/regexp', 'yorick/matrix', 'yorick/yorick' ]

   library_dirs = [join(local_path,x) for x in ['.','yorick']]
   library_dirs.extend(x11_info.get('library_dirs',[]))
   library_dirs.extend('/usr/lib64')

   include_dirs = [join(local_path,x) for x in include_dirs]
   include_dirs.extend(x11_info.get('include_dirs',[]))
   xft_info = get_info('xft')
   include_dirs.extend(xft_info.get('include_dirs'))
   libraries.extend(xft_info.get('libraries'))

   inputfile = open(join(config_path,"Make.cfg"))
   lines = inputfile.readlines()
   inputfile.close()
   for line in lines:
      if line[:8]=="MATHLIB=":
         mathlib = line[8:-1] #removing the \n
         # remove the -l
         mathlib = mathlib[2:]
         libraries.append(mathlib)
      if line[:9]=="NO_EXP10=":
         no_exp10 = line[9:-1] # removing \n
         if no_exp10: extra_compile_args.append(no_exp10)
      if line[:5]=="XINC=":
         xinc = line[5:-1] # removing \n
         if xinc and sys.platform not in ['cygwin','win32']:
            # remove the -I
            xinc = xinc[2:]
            if xinc: include_dirs.append(xinc)
      if line[:5]=="XLIB=":
         xlib = line[5:-1] # removing \n
         if xlib and sys.platform not in ['cygwin','win32']:
            # remove the -L
            xlib = xlib[2:]
            library_dirs.append(xlib)
      if line.startswith('D_FPUSET='):
         fpuset=line.split('=')[1].strip()
         extra_compile_args.append(fpuset)
        
   extra_compile_args.append('-DYLAPACK_NOALIAS')
   extra_compile_args.append('-DYCBLAS_NOALIAS')
 
   return include_dirs, library_dirs, libraries, \
            extra_compile_args, extra_link_args


def configuration(parent_package='',top_path=None):
   """
      This will install *.gs and *.gp files to
      'site-packages/gist/gistdata'
   """
   from numpy.distutils.misc_util import Configuration
   from config_pygist import yorick_configure
   config = Configuration(
      package_name='gist',
      parent_name=parent_package,
      top_path=top_path,
      package_path='gist',
      version='2.2.00x',
      description='gist for python.',
      long_description='A python plugin for gist.',
      url='http://yorick.sourceforge.net',
      author='David H. Munro',
      author_email='dhmunro@pacbell.net',
      maintainer='Matthieu D.C. Bec',
      maintainer_email='mdcb808@gmail.com',
      license='GPLv3'
      )
   
   local_path = config.local_path

   gistdata_path = join(get_python_lib(1),config.path_in_package,"gistdata")
   gistdata_path = gistdata_path.replace("\\",r"\\\\")

   def get_playsource(extension,build_dir):
      playsource = unixsource + x11source + allsource
      sources = [join(local_path,n) for n in playsource]
      config_path = join(build_dir,'confpygist')
      dir_util.mkpath(config_path)
      conf = yorick_configure(local_path,config_path)
      # Look to see if compiler is set on command line and add it
      #   This is repeating code, but I'm not sure how to avoid it
      #   As this gets run before overall setup does.
      #   This is needed so that compiler can be over-ridden from the
      #   platform default in the configuration section of gist.
      for arg in sys.argv[1:]:
         if arg[:11] == '--compiler=':
            conf.compiler = arg[11:]
            break
         if arg[:2] == '-c':
            conf.compiler = arg[2:]
            break
      # Generate Make.cfg and config.h:
      conf.run()

      include_dirs, library_dirs, libraries, \
                 extra_compile_args, extra_link_args \
                 = getallparams(gistdata_path,local_path,config_path)
      ###include_dirs.insert(0,dirname(conf.config_h))

      extension.include_dirs.extend(include_dirs)
      extension.library_dirs.extend(library_dirs)
      extension.libraries.extend(libraries)
      extension.extra_compile_args.extend(extra_compile_args)
      extension.extra_link_args.extend(extra_link_args)
      return sources

   gistC = join(local_path,'./plugin/gistCmodule.c')
   sources = [join(local_path,n) for n in gistsource]
   sources = [gistC] + sources + [get_playsource]

   config.add_extension('gistC',sources,depends = ['yorick','.'])
   config.add_extension('gistfuncs',[join(local_path,'./plugin/gistfuncsmodule.c')])
   
   config.add_subpackage('',subpackage_path='gist')
   
   gist_data = [join('gistdata',x) for x in ('*.gs','*.gp')] + \
               [join('yorick' ,'g',x) for x in ('*.gs','*.gp')]
   config.add_data_files (('gistdata',gist_data))
   
   return config

if __name__ == '__main__':
   from numpy.distutils.core import setup
   setup(name='python-',configuration=configuration)
