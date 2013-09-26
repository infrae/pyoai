import pkg_resources

from oaipmh import error

class Header(object):
    def __init__(self, element, identifier, datestamp, setspec, deleted):
        self._element = element
        # force identifier to be a string, it might be 
        # an lxml.etree._ElementStringResult...
        try:
            self._identifier = str(identifier)
        except UnicodeEncodeError:
            self._identifier = unicode(identifier)
        self._datestamp = datestamp
        self._setspec = setspec
        self._deleted = deleted

    def element(self):
        return self._element

    def identifier(self):
        return self._identifier

    def datestamp(self):
        return self._datestamp

    def setSpec(self):
        return self._setspec

    def isDeleted(self):
        return self._deleted

class Metadata(object):
    def __init__(self, element, map):
        self._element = element
        self._map = map

    def element(self):
        return self._element

    def getMap(self):
        return self._map

    def getField(self, name):
        return self._map[name]

    __getitem__ = getField

class Identify(object):
    def __init__(self, repositoryName, baseURL, protocolVersion, adminEmails,
                 earliestDatestamp, deletedRecord, granularity, compression,
                 toolkit_description=True):
        self._repositoryName = repositoryName
        self._baseURL = baseURL
        self._protocolVersion = protocolVersion
        self._adminEmails = adminEmails
        self._earliestDatestamp = earliestDatestamp
        self._deletedRecord = deletedRecord
        self._granularity = granularity
        self._compression = compression
        self._descriptions = []
        
        if toolkit_description:
            req = pkg_resources.Requirement.parse('pyoai')
            egg = pkg_resources.working_set.find(req)
            if egg:
                version = '<version>%s</version>' % egg.version
            else:
                version = ''
            self.add_description(
                '<toolkit xsi:schemaLocation='
                '"http://oai.dlib.vt.edu/OAI/metadata/toolkit '
                'http://oai.dlib.vt.edu/OAI/metadata/toolkit.xsd" '
                'xmlns="http://oai.dlib.vt.edu/OAI/metadata/toolkit" '
                'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
                '<title>pyoai</title>'
                '%s'
                '<URL>http://infrae.com/products/oaipack</URL>'
                '</toolkit>' % version)
        
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

    def add_description(self, xml_string):
        self._descriptions.append(xml_string)

    def descriptions(self):
        return self._descriptions
    
def ResumptionTokenSpec(dict):
    dict = dict.copy()
    dict['resumptionToken'] = 'exclusive'
    return dict

class OAIMethodImpl(object):
    def __init__(self, verb):
        self._verb = verb
        
    def __call__(self, bound_self, **kw):
        return bound_self.handleVerb(self._verb, kw)
        
def OAIMethod(verb):
    obj = OAIMethodImpl(verb)
    def method(self, **kw):
        return obj(self, **kw)
    return method

class OAIPMH(object):
    """Mixin that implements the Python-level OAI-PMH interface.

    It does not include resumptionToken handling.
    
    It passes the calls on to the 'handleVerb' method, which should be
    overridden in a subclass.
    """
    def handleVerb(self, verb, kw):
        raise NotImplementedError
    
    getRecord = OAIMethod(
        'GetRecord',
        )

    getMetadata = OAIMethod(
        'GetMetadata',
        )
    
    identify = OAIMethod(
        'Identify',
        )

    listIdentifiers = OAIMethod(
        'ListIdentifiers',
        )

    listMetadataFormats = OAIMethod(
        'ListMetadataFormats',
        )

    listRecords = OAIMethod(
        'ListRecords',
        )

    listSets = OAIMethod(
        'ListSets',
        )
    
class ResumptionOAIPMH(object):
    """Mixin that implements the Resumption-capable OAI-PMH interface.

    It passes the arguments on to the 'handleVerb' method, which
    should be overridden in a subclass.

    The listIdentifiers, listSets and listRecords methods return
    tuples of a list and resumptionToken. If the resumptionToken
    returned is None, this indicates the end of the list is reached.
    """

    def handleVerb(self, verb, kw):
        raise NotImplementedError
    
    getRecord = OAIMethod(
        'GetRecord',
        )

    getMetadata = OAIMethod(
        'GetMetadata',
        )

    identify = OAIMethod(
        'Identify',
        )

    listIdentifiers = OAIMethod(
        'ListIdentifiers',
        )

    listMetadataFormats = OAIMethod(
        'ListMetadataFormats',
        )

    listRecords = OAIMethod(
        'ListRecords',
        )

    listSets = OAIMethod(
        'ListSets',
        )

def getMethodForVerb(server, verb):
    return getattr(server, verb[0].lower() + verb[1:])

