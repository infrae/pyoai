from oaipmh import common
from datetime import datetime

class FakeServer:
    def __init__(self):
        data = []
        for i in range(100):
            data.append((common.Header(str(i), datetime.now(), '', False),
                         common.Metadata({}),
                         None))
        self._data = data

    def listIdentifiers(self, metadataPrefix=None, from_=None, until=None,
                        set=None):
        
        return [header for (header, metadata, about) in self._data]

    def listRecords(self, metadataPrefix=None, from_=None, until=None,
                    set=None):
        return self._data
    
