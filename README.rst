.. -*- restructuredtext -*-

OAIPMH
======

.. image:: https://img.shields.io/pypi/v/pyoai.svg
        :target: https://pypi.python.org/pypi/pyoai

.. image:: https://travis-ci.org/mpasternak/pyoai.svg?branch=master
    :target: https://travis-ci.org/mpasternak/pyoai

The oaipmh module is a Python implementation of an "Open Archives
Initiative Protocol for Metadata Harvesting" (version 2) client and
server. The protocol is described here:

http://www.openarchives.org/OAI/openarchivesprotocol.html

Below is a simple implementation of an OAIPMH client:

>>> from oaipmh.client import Client
>>> from oaipmh.metadata import MetadataRegistry, oai_dc_reader

>>> URL = 'http://uni.edu/ir/oaipmh'

>>> registry = MetadataRegistry()
>>> registry.registerReader('oai_dc', oai_dc_reader)
>>> client = Client(URL, registry)

>>> for record in client.listRecords(metadataPrefix='oai_dc'):
>>>    print record


The pyoai package also contains a generic server implementation of the 
OAIPMH protocol, this is used as the foundation of the `MOAI Server Platform`_

.. _MOAI Server Platform: http://pypi.python.org/pypi/MOAI
