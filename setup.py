
from distutils.core import setup

f = open('version.txt', 'r')
version = f.read().strip()
f.close()

setup(name='pyoai',
      version=version,
      description='oaipmh library',
      package_dir = {'': 'src'},
      packages=['oaipmh'],
     )
