from oaipmh import common, error
from datetime import datetime
import random

class FakeServerCommon(object):
    def identify(self):
        return common.Identify(
            repositoryName='Fake',
            baseURL='http://www.infrae.com/oai/',
            protocolVersion="2.0",
            adminEmails=['faassen@infrae.com'],
            earliestDatestamp=datetime(2004, 1, 1),
            deletedRecord='transient',
            granularity='YYYY-MM-DDThh:mm:ssZ',
            compression=['identity'])

    def getRecord(self, metadataPrefix, identifier):
        try:
            return self._data[int(identifier)]
        except IndexError:
            raise error.IdDoesNotExistError("Id does not exist: %s" % identifier)

class FakeServerBase(FakeServerCommon):
    
    def listIdentifiers(self, metadataPrefix=None, from_=None, until=None,
                        set=None):
        result = []
        for header, metadata, about in self._data:
            if datestampInRange(header, from_, until):
                result.append(header)
        return result

    def listRecords(self, metadataPrefix=None, from_=None, until=None,
                    set=None):
        result = []
        for header, metadata, about in self._data:
            if datestampInRange(header, from_, until):
                result.append((header, metadata, about))
        return result

class BatchingFakeServerBase(FakeServerCommon):
    
    def listIdentifiers(self, metadataPrefix=None, from_=None, until=None,
                        set=None, cursor=0, batch_size=10):
        result = []
        for header, metadata, about in self._data:
            if datestampInRange(header, from_, until):
                result.append(header)
        return result[cursor:cursor + batch_size]

    def listRecords(self, metadataPrefix=None, from_=None, until=None,
                    set=None, cursor=0, batch_size=10):
        result = []
        for header, metadata, about in self._data:
            if datestampInRange(header, from_, until):
                result.append((header, metadata, about))
        return result[cursor:cursor + batch_size]

def datestampInRange(header, from_, until):
    if from_ is not None and header.datestamp() < from_:
        return False
    if until is not None and header.datestamp() > until:
        return False
    return True

def createFakeData():
    data = []
    for i in range(100):
        # create some datestamp spread
        year = 2004
        month = i % 12 + 1
        day = i % 28 + 1
        hour = i % 24
        minute = i % 60
        second = i % 60
        fake_element = None
        datestamp = datetime(year, month, day, hour, minute, second)
        data.append((common.Header(fake_element, str(i), datestamp, '', False),
                     common.Metadata(fake_element, {'title': ['Title %s' % i]}),
                     None))
    return data
    
class FakeServer(FakeServerBase):
    def __init__(self):
        self._data = createFakeData()

class BatchingFakeServer(BatchingFakeServerBase):
    def __init__(self):
        self._data = createFakeData()
    
class FakeServerWithDeletions(FakeServerBase):

    def __init__(self):
        data = []

        for i in range(0, 12):
            # create some records in a year
            year = 2005
            month = i + 1
            day = 1
            datestamp = datetime(year, month, day, 12, 30, 0)
            fake_element = None
            data.append((common.Header(fake_element, str(i), datestamp, '', False),
                         common.Metadata(fake_element, {'title': ['Title %s' % i]}),
                         None))
        self._data = data
        
    def deletionEvent(self):
        # delete half the records we store
        data = []
        # create deletion remains for these records
        for i in range(0, 6):
            year = 2006
            month = i + 1
            day = 1
            datestamp = datetime(year, month, day, 12, 35, 0)
            fake_element = None
            data.append((common.Header(fake_element, str(i), datestamp, '', True),
                         None,
                         None))
        # replace first half with deleted records
        self._data = data + self._data[6:]
