from oaipmh import common, error
from datetime import datetime

class FakeServer:
    def __init__(self):
        data = []
        for i in range(100):
            data.append((common.Header(str(i), datetime.now(), '', False),
                         common.Metadata({'title': ['Title %s' % i]}),
                         None))
        self._data = data

    def identify(self):
        return common.ServerIdentify(
            repositoryName='Fake',
            baseURL='http://www.infrae.com/oai/',
            protocolVersion="2.0",
            adminEmails=['faassen@infrae.com'],
            earliestDatestamp=datetime(2005, 1, 1),
            deletedRecord='transient',
            granularity='YYYY-MM-DDThh:mm:ssZ',
            compression=['identity'])
    
    def listIdentifiers(self, metadataPrefix=None, from_=None, until=None,
                        set=None):
        
        return [header for (header, metadata, about) in self._data]

    def listRecords(self, metadataPrefix=None, from_=None, until=None,
                    set=None):
        return self._data
    
    def getRecord(self, metadataPrefix, identifier):
        try:
            return self._data[int(identifier)]
        except IndexError:
            raise error.IdDoesNotExistError, "Id does not exist: %s" % identifier
