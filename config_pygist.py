from distutils.command.config import config
from distutils.dist import Distribution
import os

#------------------------------------------------------------------------
# Configuration
#------------------------------------------------------------------------

class yorick_configure(config):
   def __init__(self, local_path, config_path):
      #super(yorick_configure,self).__init__(self,Distribution())
      self.config_path = config_path
      print 'yorick_configure.__init__',local_path,config_path

   def run (self):
      print 'yorick_configure.run'
      os.chdir('yorick')
      os.system('make clean config')
      os.chdir('..')
      os.system('cp yorick/Make.cfg '+self.config_path)
      
