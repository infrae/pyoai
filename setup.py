from setuptools import setup, find_packages

setup(
    name='pyoai',
    version='2.4.2',
    author='Infrae',
    author_email='jasper@infrae.com',
    url='http://www.infrae.com/download/oaipmh',
    classifiers=["Development Status :: 4 - Beta",
                 "Programming Language :: Python",
                 "License :: OSI Approved :: BSD License",
                 "Topic :: Software Development :: Libraries :: Python Modules",
                 "Environment :: Web Environment"],
    description="""\
The oaipmh module is a Python implementation of an "Open Archives
Initiative Protocol for Metadata Harvesting" (version 2) client and server.
The protocol is described here:

http://www.openarchives.org/OAI/openarchivesprotocol.html
""",
    long_description="""\
The oaipmh module is a Python implementation of an "Open Archives
Initiative Protocol for Metadata Harvesting" (version 2) client and server.
The protocol is described here:

http://www.openarchives.org/OAI/openarchivesprotocol.html

With it, you can easily harvest existing OAI-PMH compliant data providers,
as well as construct your own OAI-PMH data provider.
""",
    
    packages=find_packages('src'),
    package_dir = {'': 'src'},
    zip_safe=False,
    license='BSD',
    keywords='OAI-PMH xml archive',
    install_requires=['lxml'],
)
