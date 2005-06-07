import datetime

class Header:
    def __init__(self, identifier, datestamp, setspec, deleted):
        self._identifier = identifier
        self._datestamp = datestamp
        self._setspec = setspec
        self._deleted = deleted
        
    def identifier(self):
        return self._identifier
    
    def datestamp(self):
        return self._datestamp

    def setSpec(self):
        return self._setspec

    def isDeleted(self):
        return self._deleted

class Metadata:
    def __init__(self, map):
        self._map = map

    def getMap(self):
        return self._map
    
    def getField(self, name):
        return self._map[name]

    __getitem__ = getField
    
class ServerIdentify:
    def __init__(self, repositoryName, baseURL, protocolVersion, adminEmails,
                 earliestDatestamp, deletedRecord, granularity, compression):
        self._repositoryName = repositoryName
        self._baseURL = baseURL
        self._protocolVersion = protocolVersion
        self._adminEmails = adminEmails
        self._earliestDatestamp = earliestDatestamp
        self._deletedRecord = deletedRecord
        self._granularity = granularity
        self._compression = compression
        # XXX description
        
    def repositoryName(self):
        return self._repositoryName

    def baseURL(self):
        return self._baseURL

    def protocolVersion(self):
        return self._protocolVersion

    def adminEmails(self):
        return self._adminEmails

    def earliestDatestamp(self):
        return self._earliestDatestamp

    def deletedRecord(self):
        return self._deletedRecord

    def granularity(self):
        return self._granularity

    def compression(self):
        return self._compression

def datetime_to_datestamp(dt):
    return dt.isoformat() + 'Z'
    
def datestamp_to_datetime(datestamp):
    splitted = datestamp.split('T')
    if len(splitted) == 2:
        d, t = splitted
        # strip off 'Z'
        t = t[:-1]
    else:
        d = splitted[0]
        t = '00:00:00'
    YYYY, MM, DD = d.split('-')
    hh, mm, ss = t.split(':')
    return datetime.datetime(
        int(YYYY), int(MM), int(DD),
        int(hh), int(mm), int(ss))

        
