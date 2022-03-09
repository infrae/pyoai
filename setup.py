from setuptools import setup, find_packages
from os.path import join, dirname

setup(
    name='pyoai',
    version='2.5.2pre',
    author='Infrae',
    author_email='info@infrae.com',
    url='http://www.infrae.com/download/oaipmh',
    classifiers=["Development Status :: 4 - Beta",
                 "Programming Language :: Python",
                 "License :: OSI Approved :: BSD License",
                 "Topic :: Software Development :: Libraries :: Python Modules",
                 "Environment :: Web Environment"],
    description="""The oaipmh module is a Python implementation of an "Open Archives Initiative Protocol for Metadata Harvesting" (version 2) client and server.""",
    long_description=(open(join(dirname(__file__), 'README.rst')).read()+
        '\n\n'+
        open(join(dirname(__file__), 'HISTORY.txt')).read()),
    long_description_content_type='text/x-rst',
    packages=find_packages('src'),
    package_dir = {'': 'src'},
    zip_safe=False,
    license='BSD',
    keywords='OAI-PMH xml archive',
    install_requires=['lxml', 'six'],
)
