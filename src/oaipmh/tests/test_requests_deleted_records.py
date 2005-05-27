from unittest import TestCase, TestSuite, main, makeSuite
from fakeserver import FakeServerProxy
import os
from oaipmh.client import register_oai_dc

directory = os.path.dirname(__file__)
fake2 = os.path.join(directory, 'fake2')
fakeserver = FakeServerProxy(fake2)

register_oai_dc(fakeserver)

class RequestTestCase(TestCase):
    def test_getRecord_deleted(self):
        header, metadata, about = fakeserver.getRecord(
            metadataPrefix='oai_dc', identifier='hdl:1765/1160')
        self.assert_(metadata is None)
        self.assert_(header.isDeleted())

    def test_getRecord_not_deleted(self):
        header, metadata, about = fakeserver.getRecord(
            metadataPrefix='oai_dc', identifier='hdl:1765/1162')
        self.assert_(metadata is not None)
        self.assert_(not header.isDeleted())

    def test_listRecords(self):
        records = fakeserver.listRecords(from_="2004-01-01",
                                         metadataPrefix='oai_dc')
        # lazy, just test first one
        for header, metadata, about in records:
            if header.isDeleted():
                self.assert_(metadata is None)
            else:
                self.assert_(metadata is not None)
    
def test_suite():
    return TestSuite((makeSuite(RequestTestCase), ))

if __name__=='__main__':
    main(defaultTest='test_suite')
