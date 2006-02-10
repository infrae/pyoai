import os
from datetime import datetime
from unittest import TestCase, TestSuite, makeSuite

from fakeclient import FakeClient
from oaipmh import metadata, error

directory = os.path.dirname(__file__)
fake3 = os.path.join(directory, 'fake3')
fakeclient = FakeClient(fake3)

fakeclient.getMetadataRegistry().registerReader(
    'oai_dc', metadata.oai_dc_reader)

class BrokenDataTestCase(TestCase):
    def test_notwellformed(self):
        self.assertRaises(error.XMLSyntaxError, fakeclient.identify)
        try:
            fakeclient.identify()
        except error.ClientError, e:
            self.assertEquals(
                {'verb': 'Identify'}, e.kw)

def test_suite():
    return TestSuite((makeSuite(BrokenDataTestCase), ))
