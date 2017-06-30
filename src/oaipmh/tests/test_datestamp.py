from datetime import datetime
from unittest import TestCase, TestSuite, makeSuite
from oaipmh.datestamp import datestamp_to_datetime,\
     tolerant_datestamp_to_datetime
from oaipmh.error import DatestampError

class DatestampTestCase(TestCase):
    def test_strict_datestamp_to_datetime(self):
        self.assertEquals(
            datetime(2005, 7, 4, 14, 35, 10),
            datestamp_to_datetime('2005-07-04T14:35:10Z'))
        self.assertEquals(
            datetime(2005, 1, 24, 14, 34, 2),
            datestamp_to_datetime('2005-01-24T14:34:02Z'))
        self.assertEquals(
            datetime(2005, 7, 4),
            datestamp_to_datetime('2005-07-04'))
        self.assertRaises(DatestampError,
                          datestamp_to_datetime, '2005')
        self.assertRaises(DatestampError,
                          datestamp_to_datetime, '2005-07-04Z')
        self.assertRaises(DatestampError,
                          datestamp_to_datetime, '2005-07')
        self.assertRaises(DatestampError,
                          datestamp_to_datetime, '2005-07-04T')
        self.assertRaises(DatestampError,
                          datestamp_to_datetime, '2005-07-04T14:00Z')
        self.assertRaises(DatestampError,
                          datestamp_to_datetime, '2005-07-04T14:00:00')
        self.assertRaises(DatestampError,
                          datestamp_to_datetime, 'aaaa-bb-cc')
        self.assertRaises(DatestampError,
                          datestamp_to_datetime, 'foo')
        try:
            datestamp_to_datetime('foo')
        except DatestampError as e:
            self.assertEquals('foo', e.datestamp)

    def test_strict_datestamp_to_datetime_inclusive(self):
        # passing inclusive=True to datestamp_to_datetime
        # should default the time to 23:59:59 instead of 00:00:00
        # when only a date is supplied

        self.assertEquals(datetime(2009, 11, 16, 23, 59, 59),
                          datestamp_to_datetime('2009-11-16',
                                                inclusive=True))
        
    def test_tolerant_datestamp_to_datetime(self):
        f = tolerant_datestamp_to_datetime
        self.assertEquals(
            datetime(2005, 7, 4, 14, 35, 10),
            f('2005-07-04T14:35:10Z'))
        self.assertEquals(
            datetime(2005, 1, 24, 14, 34, 2),
            f('2005-01-24T14:34:02Z'))
        self.assertEquals(
            datetime(2005, 7, 4),
            f('2005-07-04'))
        self.assertEquals(
            datetime(2005, 1, 1),
            f('2005'))
        self.assertEquals(
            datetime(2005, 2, 1),
            f('2005-02'))
        
def test_suite():
    return TestSuite((makeSuite(DatestampTestCase), ))
