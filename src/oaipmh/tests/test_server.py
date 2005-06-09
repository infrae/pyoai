import unittest
import os
from StringIO import StringIO
from oaipmh import server, client, common, metadata
from lxml import etree
from datetime import datetime
import fakeclient

NS_OAIPMH = server.NS_OAIPMH

def fileInTestDir(name):
    _testdir = os.path.split(__file__)[0]
    return os.path.join(_testdir, name)

# load up schema
oaischema = etree.XMLSchema(etree.parse(fileInTestDir('OAI-PMH.xsd')))

class XMLTreeServerTestCase(unittest.TestCase):
    
    def setUp(self):
        self._server = self.getXMLTreeServer()

    def getXMLTreeServer(self):
        directory = os.path.dirname(__file__)
        fake1 = os.path.join(directory, 'fake1')
        myserver = fakeclient.FakeClient(fake1)
        metadata_registry = metadata.MetadataRegistry()
        metadata_registry.registerWriter('oai_dc', server.oai_dc_writer)
        return server.XMLTreeServer(myserver, metadata_registry)

    def test_getRecord(self):
        tree = self._server.getRecord(
            metadataPrefix='oai_dc', identifier='hdl:1765/315')
        self.assert_(oaischema.validate(tree))
        
    def test_identify(self):
        tree = self._server.identify()
        self.assert_(oaischema.validate(tree))

    def test_listIdentifiers(self):
        tree = self._server.listIdentifiers(
            from_="2003-04-10",
            metadataPrefix='oai_dc')
        self.assert_(oaischema.validate(tree))
        
    def test_listMetadataFormats(self):
        tree = self._server.listMetadataFormats()
        self.assert_(oaischema.validate(tree))

    def test_listRecords(self):
        tree = self._server.listRecords(
            from_="2003-04-10",
            metadataPrefix='oai_dc')
        f = open('outm.xml', 'w')
        tree.write(f)
        f.close()
        self.assert_(oaischema.validate(tree))

class XMLServerTestCase(unittest.TestCase):
    """
    Most of the tests are in the XMLTreeServerTestCase,
    but to test integration with XML directly (argument passing and such),
    a few test cases here.
    """
    
    def setUp(self):
        self._server = self.getXMLServer()
        
    def getXMLServer(self):
        directory = os.path.dirname(__file__)
        fake1 = os.path.join(directory, 'fake1')
        myserver = fakeclient.FakeClient(fake1)
        metadata_registry = metadata.MetadataRegistry()
        metadata_registry.registerWriter('oai_dc', server.oai_dc_writer)
        return server.XMLServer(myserver, metadata_registry)

    def test_identify(self):
        xml = self._server.identify()
        tree = etree.parse(StringIO(xml))
        self.assert_(oaischema.validate(tree))
        
    def test_listIdentifiers(self):
        xml = self._server.listIdentifiers(
            from_="2003-04-10",
            metadataPrefix='oai_dc')
        tree = etree.parse(StringIO(xml))
        self.assert_(oaischema.validate(tree))
        
def test_suite():
    return unittest.TestSuite([
        unittest.makeSuite(XMLTreeServerTestCase),
        unittest.makeSuite(XMLServerTestCase)])

if __name__=='__main__':
    main(defaultTest='test_suite')
