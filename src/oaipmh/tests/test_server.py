import unittest
import os
import six
try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO, BytesIO
from oaipmh import server, client, common, metadata, error
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

def etree_parse(xml):
    if six.PY2:
        return etree.parse(StringIO(xml))
    return etree.parse(BytesIO(xml)) # .decode("utf-8")))

class XMLTreeServerTestCase(unittest.TestCase):
    
    def setUp(self):
        self._server = self.getXMLTreeServer()

    def getXMLTreeServer(self):
        directory = os.path.dirname(__file__)
        fake1 = os.path.join(directory, 'fake1')
        myserver = fakeclient.FakeClient(fake1)
        metadata_registry = metadata.MetadataRegistry()
        metadata_registry.registerWriter('oai_dc', server.oai_dc_writer)
        return server.XMLTreeServer(server.Resumption(myserver),
                                    metadata_registry)

    def test_getRecord(self):
        tree = self._server.getRecord(
            metadataPrefix='oai_dc', identifier='hdl:1765/315')
        self.assert_(oaischema.validate(tree))

    def test_getMetadata(self):
        tree = self._server.getMetadata(
            metadataPrefix='oai_dc', identifier='hdl:1765/315')
        self.assertEquals(tree.tag,
                          '{http://www.openarchives.org/OAI/2.0/oai_dc/}dc')
        
    def test_identify(self):
        tree = self._server.identify()
        self.assert_(oaischema.validate(tree))

    def test_listIdentifiers(self):
        tree = self._server.listIdentifiers(
            from_=datetime(2003, 4, 10),
            metadataPrefix='oai_dc')
        self.assert_(oaischema.validate(tree))
        
    def test_listMetadataFormats(self):
        tree = self._server.listMetadataFormats()
        self.assert_(oaischema.validate(tree))

    def test_listRecords(self):
        tree = self._server.listRecords(
            from_=datetime(2003, 4, 10),
            metadataPrefix='oai_dc')
        self.assert_(oaischema.validate(tree))

    def test_listSets(self):
        tree = self._server.listSets()
        self.assert_(oaischema.validate(tree))

    def test_namespaceDeclarations(self):
        # according to the spec, all namespace used in the metadata
        # element should be declared on the metadata element,
        # and not on root or ancestor elements (big sigh..)
        # this works, except for the xsi namespace which is allready declared
        # on the root element, which means lxml will not declare it again on
        # the metadata element

        tree = self._server.getRecord(
            metadataPrefix='oai_dc', identifier='hdl:1765/315')
        # ugly xml manipulation, this is probably why the requirement is in
        # the spec (yuck!)
        xml = etree.tostring(tree)
        if six.PY3:
            xml = xml.decode("utf-8")
        xml = xml.split('<metadata>')[-1].split('</metadata>')[0]
        first_el = xml.split('>')[0]
        self.assertTrue(first_el.startswith('<oai_dc:dc'))
        self.assertTrue(
            'xmlns:oai_dc="http://www.openarchives.org/OAI/2.0/oai_dc/"'
            in first_el) 
        self.assertTrue(
            'xmlns:dc="http://purl.org/dc/elements/1.1/"'
            in first_el) 
        
class ServerTestCase(unittest.TestCase):
    """
    Most of the tests are in the XMLTreeServerTestCase,
    but to test integration with XML directly (argument passing and such),
    a few test cases here.
    """
    
    def setUp(self):
        self._server = self.getServer()
        
    def getServer(self):
        directory = os.path.dirname(__file__)
        fake1 = os.path.join(directory, 'fake1')
        myserver = fakeclient.FakeClient(fake1)
        metadata_registry = metadata.MetadataRegistry()
        metadata_registry.registerWriter('oai_dc', server.oai_dc_writer)
        return server.Server(myserver, metadata_registry)

    def test_identify(self):
        xml = self._server.identify()
        tree = etree_parse(xml)
        self.assert_(oaischema.validate(tree))
        
    def test_listIdentifiers(self):
        xml = self._server.listIdentifiers(
            from_=datetime(2003, 4, 10),
            metadataPrefix='oai_dc')
        tree = etree_parse(xml)
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
        myserver = server.XMLTreeServer(
            self._server, metadata_registry)
        tree = myserver.listIdentifiers(metadataPrefix='oai_dc')
        self.assert_(oaischema.validate(tree))
        # we should find a resumptionToken element with text
        self.assert_(
            tree.xpath('//oai:resumptionToken/text()', 
                       namespaces={'oai': NS_OAIPMH} ))
        
class BatchingResumptionTestCase(unittest.TestCase):
    def setUp(self):
        self._fakeserver = fakeserver.BatchingFakeServer()
        self._server = server.BatchingResumption(self._fakeserver, 10)

    def _listIdentifiers(self, resumption_server, expected_length):
        headers = []
        result, token = resumption_server.listIdentifiers(
            metadataPrefix='oai_dc')
        headers.extend(result)
        self.assert_(token is not None)
        while token is not None:
            self.assert_(result)
            self.assertEquals(expected_length, len(result))
            result, token = resumption_server.listIdentifiers(
                resumptionToken=token)
            headers.extend(result)
        self.assertEquals([str(i) for i in range(100)],
                          [header.identifier() for header in headers])

    def test_resumption(self):
        self._listIdentifiers(self._server, 10)
 
    def test_resumption_nonexact(self):
        myserver = server.BatchingResumption(self._fakeserver, 13)
        self._listIdentifiers(myserver, 13)

    def test_resumption_overflow(self):
        myserver = server.BatchingResumption(self._fakeserver, 300)
        result, token = myserver.listIdentifiers(
            metadataPrefix='oai_dc')
        self.assert_(token is None)
        self.assertEquals([str(i) for i in range(100)],
                          [header.identifier() for header in result])
        
    def test_tree_resumption(self):
        metadata_registry = metadata.MetadataRegistry()
        metadata_registry.registerWriter('oai_dc', server.oai_dc_writer)
        myserver = server.XMLTreeServer(self._server, metadata_registry)
        tree = myserver.listIdentifiers(metadataPrefix='oai_dc')
        self.assert_(oaischema.validate(tree))
        # we should find a resumptionToken element with text
        self.assert_(
            tree.xpath('//oai:resumptionToken/text()', 
                       namespaces={'oai': NS_OAIPMH} ))
        
class ClientServerTestCase(unittest.TestCase):
    def setUp(self):
        self._fakeserver = fakeserver.FakeServer()
        metadata_registry = metadata.MetadataRegistry()
        metadata_registry.registerWriter('oai_dc', server.oai_dc_writer)
        metadata_registry.registerReader('oai_dc', metadata.oai_dc_reader)
        self._server = server.Server(self._fakeserver, metadata_registry,
                                     resumption_batch_size=7)
        self._client = client.ServerClient(self._server, metadata_registry)

    def test_listIdentifiers(self):
        headers = self._client.listIdentifiers(metadataPrefix='oai_dc')
        self.assertEquals([str(i) for i in range(100)],
                          [header.identifier() for header in headers])

    def test_listRecords(self):
        records = self._client.listRecords(metadataPrefix='oai_dc')
        records = list(records)
        self.assertEquals(100, len(records))
        metadatas = [metadata for (header, metadata, about) in records]
        result = []
        for metadata in metadatas:
            result.append(metadata.getField('title')[0])
        expected = ['Title %s' % i for i in range(100)]
        self.assertEquals(expected, result)
        #for record in records:
        #    print record[0].datestamp()

    def test_listIdentifiersFromUntil(self):
        headers = self._client.listIdentifiers(metadataPrefix='oai_dc',
                                               from_=datetime(2004, 1, 1),
                                               until=datetime(2004, 7, 1))
        # we expect 52 items
        headers = list(headers)
        self.assertEquals(52, len(headers))

    def test_listIdentifiersFromUntil_nothing(self):
        self.assertRaises(error.NoRecordsMatchError,
                          self._client.listIdentifiers,
                          metadataPrefix='oai_dc', from_=datetime(2003, 1, 1),
                          until=datetime(2003, 7, 1))        
        
        
class ErrorTestCase(unittest.TestCase):
    def setUp(self):
        self._fakeserver = fakeserver.FakeServer()
        metadata_registry = metadata.MetadataRegistry()
        metadata_registry.registerWriter('oai_dc', server.oai_dc_writer)
        metadata_registry.registerReader('oai_dc', metadata.oai_dc_reader)
        self._server = server.Server(self._fakeserver, metadata_registry,
                                     resumption_batch_size=7)

    def test_badArgument(self):
        xml = self._server.handleRequest({'verb': 'Identify',
                                          'foo' : 'Bar'})
        self.assertErrors([('badArgument', 'Unknown argument: foo')],
                          xml)
        # need more tests for different variations (required, etc)

    def test_noArgument(self):
        xml = self._server.handleRequest({})
        self.assertErrors([('badVerb', 'Required verb argument not found.')],
                          xml)
        
    def test_badVerb(self):
        xml = self._server.handleRequest({'verb': 'Frotz'})
        self.assertErrors([('badVerb', 'Illegal verb: Frotz')], xml)

    def test_badResumptionToken(self):
        xml = self._server.handleRequest({'verb': 'ListRecords',
                                          'resumptionToken': 'foobar'})
        self.assertErrors(
            [('badResumptionToken',
             'Unable to decode resumption token: foobar')], xml)

    def test_cannotDisseminateFormat(self):
        xml = self._server.handleRequest({'verb': 'ListRecords',
                                          'metadataPrefix': 'nonexistent'})
        self.assertErrors(
            [('cannotDisseminateFormat',
              'Unknown metadata format: nonexistent')],
            xml)

    def test_idDoesNotExist(self):
        xml = self._server.handleRequest({'verb': 'GetRecord',
                                          'metadataPrefix': 'oai_dc',
                                          'identifier': '500'})
        self.assertErrors(
            [('idDoesNotExist',
              'Id does not exist: 500')],
            xml)

    def test_badDateArgument(self):
        xml = self._server.handleRequest({'verb': 'ListRecords',
                                          'metadataPrefix': 'oai_dc',
                                          'from': 'junk'})
        self.assertErrors(
            [('badArgument',
              "The value 'junk' of the argument 'from' is not valid.")],
            xml)
        xml = self._server.handleRequest({'verb': 'ListRecords',
                                          'metadataPrefix': 'oai_dc',
                                          'until': 'junk'})
        self.assertErrors(
            [('badArgument',
              "The value 'junk' of the argument 'until' is not valid.")],
            xml)


    def testDifferentGranularities(self):
        xml = self._server.handleRequest({'verb': 'ListRecords',
                                          'metadataPrefix': 'oai_dc',
                                          'from': '2006-01-01',
                                          'until': '2008-01-01T00:00:00Z'})
        self.assertErrors(
            [('badArgument',
              "The request has different granularities for the from"
              " and until parameters")],
            xml)
        
    
    def assertErrors(self, errors, xml):
        self.assertEquals(errors, self.findErrors(xml))
        
    def findErrors(self, xml):
        # parse
        tree = etree_parse(xml)
        # validate xml
        self.assert_(oaischema.validate(tree))
        result = []
        for e in tree.xpath(
            '//oai:error', namespaces={'oai': NS_OAIPMH}):
            result.append((e.get('code'), e.text))
        result.sort()
        return result

class DeletionTestCase(unittest.TestCase):
    def setUp(self):
        self._fakeserver = fakeserver.FakeServerWithDeletions()
        metadata_registry = metadata.MetadataRegistry()
        metadata_registry.registerWriter('oai_dc', server.oai_dc_writer)
        metadata_registry.registerReader('oai_dc', metadata.oai_dc_reader)
        self._server = server.Server(self._fakeserver, metadata_registry,
                                     resumption_batch_size=7)
        self._client = client.ServerClient(self._server, metadata_registry)

    def test_listIdentifiers(self):
        headers = self._client.listIdentifiers(metadataPrefix='oai_dc')
        # we expect 12 items
        headers = list(headers)
        self.assertEquals(12, len(headers))
        # now delete
        self._fakeserver.deletionEvent()
        # check again, we expect 12 items, but half of which is deleted
        headers = self._client.listIdentifiers(metadataPrefix='oai_dc')
        headers = list(headers)
        self.assertEquals(12, len(headers))
        deleted_count = 0
        for header in headers:
            if header.isDeleted():
                deleted_count += 1
        self.assertEquals(6, deleted_count)

    def test_listRecords(self):
        self._fakeserver.deletionEvent()
        # we expect 12 items, but half of which is deleted
        records = self._client.listRecords(metadataPrefix='oai_dc')
        records = list(records)
        self.assertEquals(12, len(records))
        deleted_count = 0
        for header, metadata, about in records:
            if header.isDeleted():
                deleted_count += 1
                self.assertEquals(None, metadata)
        self.assertEquals(6, deleted_count)

    def test_getRecord(self):
        self._fakeserver.deletionEvent()
        header, metadata, about = self._fakeserver.getRecord(
            metadataPrefix='oai_dc',
            identifier='1')
        # we try to access a deleted record
        header, metadata, about = self._client.getRecord(
            metadataPrefix='oai_dc', identifier='1')
        self.assert_(header.isDeleted())
        self.assertEquals(None, metadata)

class NsMapTestCase(unittest.TestCase):
    def setUp(self):
        self._fakeserver = fakeserver.FakeServer()
        metadata_registry = metadata.MetadataRegistry()
        metadata_registry.registerWriter('oai_dc', server.oai_dc_writer)
        metadata_registry.registerReader('oai_dc', metadata.oai_dc_reader)
        self._xmlserver = server.XMLTreeServer(
            self._fakeserver,
            metadata_registry,
            nsmap={'cow': 'http://www.cow.com'})
        self._server = server.Server(
            self._fakeserver,
            metadata_registry,
            nsmap={'cow': 'http://www.cow.com'})
        
    def test_nsmap(self):
        # if we pass another nsmap along to the server constructor, we
        # can control extra namespaces in the output envelope
        tree = self._xmlserver.identify()
        self.assertEquals(
            'http://www.cow.com',
            tree.getroot().nsmap['cow'])
        
        
def test_suite():
    return unittest.TestSuite([
        unittest.makeSuite(XMLTreeServerTestCase),
        unittest.makeSuite(ServerTestCase),
        unittest.makeSuite(ResumptionTestCase),
        unittest.makeSuite(BatchingResumptionTestCase),
        unittest.makeSuite(ClientServerTestCase),
        unittest.makeSuite(ErrorTestCase),
        unittest.makeSuite(DeletionTestCase),
        unittest.makeSuite(NsMapTestCase)])

if __name__=='__main__':
    main(defaultTest='test_suite')
