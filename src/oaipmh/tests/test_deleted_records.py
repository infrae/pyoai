from unittest import TestCase
from .fakeclient import FakeClient
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
        self.assertTrue(metadata is None)
        self.assertTrue(header.isDeleted())

    def test_getRecord_not_deleted(self):
        header, metadata, about = fakeclient.getRecord(
            metadataPrefix='oai_dc', identifier='hdl:1765/1162')
        self.assertTrue(metadata is not None)
        self.assertTrue(not header.isDeleted())

    def test_listRecords(self):
        records = fakeclient.listRecords(from_=datetime(2004, 1, 1),
                                         metadataPrefix='oai_dc')
        # lazy, just test first one
        for header, metadata, about in records:
            if header.isDeleted():
                self.assertTrue(metadata is None)
            else:
                self.assertTrue(metadata is not None)
    
