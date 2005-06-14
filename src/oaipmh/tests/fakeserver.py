from oaipmh import common, error
from datetime import datetime
import random

class FakeServer:
    def __init__(self):
        data = []
        
        for i in range(100):
            # create some datestamp spread
            year = 2004
            month = i % 12 + 1
            day = i % 28 + 1
            hour = i % 24
            minute = i % 60
            second = i % 60
            datestamp = datetime(year, month, day, hour, minute, second)
            data.append((common.Header(str(i), datestamp, '', False),
                         common.Metadata({'title': ['Title %s' % i]}),
                         None))
        self._data = data

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
        
    def getRecord(self, metadataPrefix, identifier):
        try:
            return self._data[int(identifier)]
        except IndexError:
            raise error.IdDoesNotExistError, "Id does not exist: %s" % identifier
    

def datestampInRange(header, from_, until):
    if from_ is not None and header.datestamp() < from_:
        return False
    if until is not None and header.datestamp() > until:
        return False
    return True
