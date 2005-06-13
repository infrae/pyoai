from unittest import TestCase, TestSuite, main, makeSuite
from fakeclient import FakeClient
import os
from datetime import datetime
from oaipmh import common, metadata, validation

directory = os.path.dirname(__file__)
fake1 = os.path.join(directory, 'fake1')
fakeclient = FakeClient(fake1)

fakeclient.getMetadataRegistry().registerReader(
    'oai_dc', metadata.oai_dc_reader)

class ClientTestCase(TestCase):
    
    def test_getRecord(self):
        header, metadata, about = fakeclient.getRecord(
            metadataPrefix='oai_dc', identifier='hdl:1765/315')
        self.assertEquals(
            'hdl:1765/315',
            header.identifier())
        self.assertEquals(
            ['2:7'],
            header.setSpec())
        self.assert_(not header.isDeleted())
        
    def test_identify(self):
        identify = fakeclient.identify()
        self.assertEquals(
            'Erasmus University : Research Online',
            identify.repositoryName())
        self.assertEquals(
            'http://dspace.ubib.eur.nl/oai/',
            identify.baseURL())
        self.assertEquals(
            '2.0',
            identify.protocolVersion())
        self.assertEquals(
            ['service@ubib.eur.nl'],
            identify.adminEmails())
        self.assertEquals(
            'no',
            identify.deletedRecord())
        self.assertEquals(
            'YYYY-MM-DDThh:mm:ssZ',
            identify.granularity())
        self.assertEquals(
            ['gzip', 'compress', 'deflate'],
            identify.compression())

    def test_listIdentifiers(self):
        headers = fakeclient.listIdentifiers(from_="2003-04-10",
                                             metadataPrefix='oai_dc')
        # lazy, just test first one
        headers = list(headers)
        
        header = headers[0]
        self.assertEquals(
            'hdl:1765/308',
            header.identifier())
        self.assertEquals(
            datetime(2003, 4, 15, 10, 18, 51),
            header.datestamp())
        self.assertEquals(
            ['1:2'],
            header.setSpec())
        self.assert_(not header.isDeleted())
        self.assertEquals(16, len(headers))

    def test_listIdentifiers_argument_error(self):
        self.assertRaises(
            validation.BadArgumentError,
            fakeclient.listIdentifiers,
            foo='bar')
        
    def test_listRecords(self):
        records = fakeclient.listRecords(from_="2003-04-10",
                                         metadataPrefix='oai_dc')
        records = list(records)
        # lazy, just test first one
        header, metadata, about = records[0]
        self.assertEquals(
            'hdl:1765/308',
            header.identifier())
        self.assertEquals(
            datetime(2003, 4, 15, 10, 18, 51),
             header.datestamp())
        self.assertEquals(
            ['1:2'],
            header.setSpec())
        self.assert_(not header.isDeleted())
        # XXX need to extend metadata tests
        self.assertEquals(
            ['Kijken in het brein: Over de mogelijkheden van neuromarketing'],
            metadata.getField('title'))
            
    def test_listMetadataFormats(self):
        formats = fakeclient.listMetadataFormats()
        metadataPrefix, schema, metadataNamespace = formats[0]
        self.assertEquals(
            'oai_dc',
            metadataPrefix)
        self.assertEquals(
            'http://www.openarchives.org/OAI/2.0/oai_dc.xsd',
            schema)
        self.assertEquals(
            'http://www.openarchives.org/OAI/2.0/oai_dc/',
            metadataNamespace)

    def test_listSets(self):
        expected = [
            ('3', 'Erasmus MC (University Medical Center Rotterdam)', None),
            ('3:5', 'EUR Medical Dissertations', None),
            ]
        # lazy, just compare first two sets..
        sets = fakeclient.listSets()
        sets = list(sets)
        compare = [sets[0], sets[1]]
        self.assertEquals(
            expected,
            compare)

def test_suite():
    return TestSuite((makeSuite(ClientTestCase), ))

if __name__=='__main__':
    main(defaultTest='test_suite')
