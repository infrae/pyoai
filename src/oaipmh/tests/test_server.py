import unittest
import os
from oaipmh import server, client, common
from lxml import etree
from datetime import datetime
import fakeserver

NS_OAIPMH = server.NS_OAIPMH

def fileInTestDir(name):
    _testdir = os.path.split(__file__)[0]
    return os.path.join(_testdir, name)

# load up schema
oaischema = etree.XMLSchema(etree.parse(fileInTestDir('OAI-PMH.xsd')))

class ClientServerProxy(client.BaseServerProxy):
    """A proxy that connects directly to a server object.
    """
    
    def __init__(self, server, metadataSchemaRegistry=None):
        self._server = server
        
    def makeRequest(self, **kw):
        if kw.has_key('from'):
            kw['from_'] = kw['from']
            del kw['from']
        verb = kw.pop('verb')
        verb = verb[0].lower() + verb[1:]
        return getattr(self._server, verb)(**kw)

class XMLServerTestCase(unittest.TestCase):
    
    def setUp(self):
        self._server = self.getXMLTreeServer()
        
    def getXMLTreeServer(self):
        directory = os.path.dirname(__file__)
        fake1 = os.path.join(directory, 'fake1')
        myserver = fakeserver.FakeServerProxy(fake1)
        return server.XMLTreeServer(myserver)
        
    def test_identify(self):
        tree = self._server.identify()
        self.assert_(oaischema.validate(tree))
        
    def test_listIdentifiers(self):
        tree = self._server.listIdentifiers(
            from_="2003-04-10",
            metadataPrefix='oai_dc')
        self.assert_(oaischema.validate(tree))
        
    def test_metadataFormats(self):
        tree = self._server.listMetadataFormats()
        self.assert_(oaischema.validate(tree))

    def test_listRecords(self):
        tree = self._server.listRecords(
            from_="2003-04-10",
            metadataPrefix='oai_dc')
        self.assert_(oaischema.validate(tree))

def test_suite():
    return unittest.TestSuite([unittest.makeSuite(XMLServerTestCase)])

if __name__=='__main__':
    main(defaultTest='test_suite')
