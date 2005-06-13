import unittest
import os
from StringIO import StringIO
from oaipmh import server, client, common, metadata
from lxml import etree
from datetime import datetime
import fakeclient
import fakeserver

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
        self.assert_(oaischema.validate(tree))

    def test_listSets(self):
        tree = self._server.listSets()
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

class ResumptionTestCase(unittest.TestCase):
    def setUp(self):
        self._fakeserver = fakeserver.FakeServer()
        self._server = server.Resumption(self._fakeserver, 10)

    def test_resumption(self):
        headers = []
        result, token = self._server.listIdentifiers(metadataPrefix='oai_dc')
        headers.extend(result)
        while token is not None:
            result, token = self._server.listIdentifiers(resumptionToken=token)
            headers.extend(result)
        self.assertEquals([str(i) for i in range(100)],
                          [header.identifier() for header in headers])

    def test_tree_resumption(self):
        metadata_registry = metadata.MetadataRegistry()
        metadata_registry.registerWriter('oai_dc', server.oai_dc_writer)
        myserver = server.XMLTreeServer(self._fakeserver, metadata_registry)
        tree = myserver.listIdentifiers(metadataPrefix='oai_dc')
        self.assert_(oaischema.validate(tree))
        # we should find a resumptionToken element with text
        self.assert_(
            tree.xpath('//oai:resumptionToken/text()', {'oai': NS_OAIPMH} ))

class ServerClient(client.BaseClient):
    def __init__(self, server, metadata_registry=None):
        client.BaseClient.__init__(self, metadata_registry)
        self._server = server
        
    def makeRequest(self, **kw):
        verb = kw.pop('verb')
        method = common.getMethodForVerb(self._server, verb)
        return method(**kw)
        
class ClientServerTestCase(unittest.TestCase):
    def setUp(self):
        self._fakeserver = fakeserver.FakeServer()
        metadata_registry = metadata.MetadataRegistry()
        metadata_registry.registerWriter('oai_dc', server.oai_dc_writer)
        metadata_registry.registerReader('oai_dc', metadata.oai_dc_reader)
        self._server = server.XMLServer(self._fakeserver, metadata_registry,
                                        resumption_batch_size=7)
        self._client = ServerClient(self._server, metadata_registry)

    def test_listIdentifiers(self):
        headers = self._client.listIdentifiers(metadataPrefix='oai_dc')
        self.assertEquals([str(i) for i in range(100)],
                          [header.identifier() for header in headers])

    def test_listRecords(self):
        records = self._client.listRecords(metadataPrefix='oai_dc')
        metadatas = [metadata for (header, metadata, about) in records]
        result = []
        for metadata in metadatas:
            result.append(metadata.getField('title')[0])
        expected = ['Title %s' % i for i in range(100)]
        self.assertEquals(expected, result)

class ErrorTestCase(unittest.TestCase):
    def setUp(self):
        self._fakeserver = fakeserver.FakeServer()
        metadata_registry = metadata.MetadataRegistry()
        metadata_registry.registerWriter('oai_dc', server.oai_dc_writer)
        metadata_registry.registerReader('oai_dc', metadata.oai_dc_reader)
        self._server = server.XMLServer(self._fakeserver, metadata_registry,
                                        resumption_batch_size=7)

    def test_badArgument(self):
        xml = self._server.handleRequest({'verb': 'Identify',
                                          'foo' : 'Bar'})
        self.assertErrors([('badArgument', 'Unknown argument: foo')],
                          xml)

    def test_badVerb(self):
        xml = self._server.handleRequest({'verb': 'Frotz'})
        self.assertErrors([('badVerb', 'Illegal verb: Frotz')], xml)
        
    def assertErrors(self, errors, xml):
        self.assertEquals(errors, self.findErrors(xml))
        
    def findErrors(self, xml):
        result = []
        for e in etree.parse(StringIO(xml)).xpath(
            '//oai:error', {'oai': NS_OAIPMH}):
            result.append((e.get('code'), e.text))
        result.sort()
        return result
    
def test_suite():
    return unittest.TestSuite([
        unittest.makeSuite(XMLTreeServerTestCase),
        unittest.makeSuite(XMLServerTestCase),
        unittest.makeSuite(ResumptionTestCase),
        unittest.makeSuite(ClientServerTestCase),
        unittest.makeSuite(ErrorTestCase)])

if __name__=='__main__':
    main(defaultTest='test_suite')
