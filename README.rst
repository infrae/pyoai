======
pyoai
======

.. image:: https://img.shields.io/pypi/v/pyoai.svg
    :target: https://pypi.python.org/pypi/pyoai

.. image:: https://github.com/mpasternak/pyoai/actions/workflows/run_tests.yml/badge.svg
    :target: https://github.com/mpasternak/pyoai/actions/workflows/run_tests.yml

.. image:: https://img.shields.io/badge/python-3.10%20|%203.11%20|%203.12%20|%203.13-blue
    :target: https://www.python.org/

The ``oaipmh`` module is a Python implementation of the
`Open Archives Initiative Protocol for Metadata Harvesting`_ (version 2)
client and server.

.. _Open Archives Initiative Protocol for Metadata Harvesting: http://www.openarchives.org/OAI/openarchivesprotocol.html

Installation
============

.. code-block:: bash

    pip install pyoai

Or with `uv`_::

    uv add pyoai

.. _uv: https://docs.astral.sh/uv/

Requirements
============

* Python 3.10+
* `lxml <https://lxml.de/>`_

Example
=======

A simple OAI-PMH client:

.. code-block:: python

    from oaipmh.client import Client
    from oaipmh.metadata import MetadataRegistry, oai_dc_reader

    URL = 'http://uni.edu/ir/oaipmh'

    registry = MetadataRegistry()
    registry.registerReader('oai_dc', oai_dc_reader)
    client = Client(URL, registry)

    for record in client.listRecords(metadataPrefix='oai_dc'):
        print(record)

The pyoai package also contains a generic server implementation of the
OAI-PMH protocol. It is used as the foundation of the
`MOAI Server Platform <http://pypi.python.org/pypi/MOAI>`_.

Development
===========

.. code-block:: bash

    uv sync --all-extras
    uv run pytest
