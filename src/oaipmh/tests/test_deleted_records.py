from unittest import TestCase, TestSuite, main, makeSuite
from fakeclient import FakeClient
import os
from oaipmh import metadata
from datetime import datetime

directory = os.path.dirname(__file__)
fake2 = os.path.join(directory, 'fake2')
fakeclient = FakeClient(fake2)

fakeclient.getMetadataRegistry().registerReader(
    'oai_dc', metadata.oai_dc_reader)

class DeletedRecordsTestCase(TestCase):
    def test_getRecord_deleted(self):
        header, metadata, about = fakeclient.getRecord(
            metadataPrefix='oai_dc', identifier='hdl:1765/1160')
        self.assert_(metadata is None)
        self.assert_(header.isDeleted())

    def test_getRecord_not_deleted(self):
        header, metadata, about = fakeclient.getRecord(
            metadataPrefix='oai_dc', identifier='hdl:1765/1162')
        self.assert_(metadata is not None)
        self.assert_(not header.isDeleted())

    def test_listRecords(self):
        records = fakeclient.listRecords(from_=datetime(2004, 1, 1),
                                         metadataPrefix='oai_dc')
        # lazy, just test first one
        for header, metadata, about in records:
            if header.isDeleted():
                self.assert_(metadata is None)
            else:
                self.assert_(metadata is not None)
    
def test_suite():
    return TestSuite((makeSuite(DeletedRecordsTestCase), ))

if __name__=='__main__':
    main(defaultTest='test_suite')
