from setuptools import setup, find_packages

setup(
    name='pyoai',
    version='2.1.4',
    author='Infrae',
    author_email='faassen@infrae.com',
    description="""\
The oaipmh module is a Python implementation of an "Open Archives
Initiative Protocol for Metadata Harvesting" (version 2) client and server.
The protocol is described here:

http://www.openarchives.org/OAI/openarchivesprotocol.html
""",
    packages=find_packages('src', exclude=['*.tests']),
    package_dir = {'': 'src'},
    zip_safe=True,
    license='BSD',
    keywords='OAI-PMH xml archive',
    install_requires=['lxml == 1.0.1'],
)
