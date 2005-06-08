from oaipmh import common
from lxml.etree import ElementTree, Element, SubElement
from lxml import etree
from datetime import datetime

NS_OAIPMH = 'http://www.openarchives.org/OAI/2.0/'
NS_XSI = 'http://www.w3.org/2001/XMLSchema-instance'
NS_DC = 'http://www.openarchives.org/OAI/2.0/oai_dc/'

ns_resolver = etree.NsResolver(
    {None: NS_OAIPMH,
     'xsi': NS_XSI,
     'oai_dc': NS_DC})

class Server:
    """Base class for a server.

    Implement this interface (possibly subclassing this one) for your
    backend.

    A client ServerProxy can also stand in for a server.
    """
    def __init__(self, repositoryName, baseURL, adminEmails):
        self._repositoryName = repositoryName
        self._baseURL = baseURL
        self._adminEmails = adminEmails
        
    def getRecord(self, identifier, metadataPrefix):
        raise notImplementedError

    def identify(self):
        return common.ServerIdentify(
            repositoryName=self._repositoryName,
            baseURL=self._baseURL,
            protocolVersion="2.0",
            adminEmails=self._adminEmails,
            earliestDatestamp=self._getEarliestDatestamp(),
            deletedRecord='transient',
            granularity='YYYY-MM-DDThh:mm:ssZ',
            compression='identity')

    def listIdentifiers(self, metadataPrefix, from_=None, until=None, set=None,
                        resumptionToken=None):
        raise NotImplementedError

    def listMetadataFormats(self, identifier=None):
        raise NotImplementedError

    def listRecords(self, metadataPrefix, from_=None, until=None, set=None,
                    resumptionToken=None):
        raise NotImplementedError

    def listSets(self, resumptionToken=None):
        raise NotImplementedError

    def baseURL(self):
        return self._baseURL
    
    def _getEarliestDatestamp(self):
        raise NotImplementedError

class XMLTreeServer:
    """A server that responds to messages by returning XML trees.

    This is an implementation class that normally would not be exposed
    to the outside world.

    Takes an object conforming to the server API.
    """
    def __init__(self, server):
        self._server = server

    def getRecord(self, identifier, metadataPrefix):
        pass

    def identify(self):
        envelope = self._outputEnvelope(verb='Identify')
        identify = self._server.identify()
        e_identify = SubElement(envelope.getroot(), nsoai('Identify'))
        e_repositoryName = SubElement(e_identify, nsoai('repositoryName'))
        e_repositoryName.text = identify.repositoryName()
        e_baseURL = SubElement(e_identify, nsoai('baseURL'))
        e_baseURL.text = identify.baseURL()
        e_protocolVersion = SubElement(e_identify, nsoai('protocolVersion'))
        e_protocolVersion.text = identify.protocolVersion()
        for adminEmail in identify.adminEmails():
            e = SubElement(e_identify, nsoai('adminEmail'))
            e.text = adminEmail
        e_earliestDatestamp = SubElement(e_identify,
                                         nsoai('earliestDatestamp'))
        e_earliestDatestamp.text = common.datetime_to_datestamp(
            identify.earliestDatestamp())
        e_deletedRecord = SubElement(e_identify,
                                     nsoai('deletedRecord'))
        e_deletedRecord.text = identify.deletedRecord()
        e_granularity = SubElement(e_identify, nsoai('granularity'))
        e_granularity.text = identify.granularity()
        compressions = identify.compression()
        if compressions != ['identity']:
            for compression in compressions:
                e_compression = SubElement(e_identify, nsoai('compression'))
                e_compression.text = compression
        return envelope
    
    def listIdentifiers(self, metadataPrefix, from_=None, until=None, set=None,
        resumptionToken=None):
        envelope = self._outputEnvelope(verb='ListIdentifiers', from_=from_,
                                        metadataPrefix=metadataPrefix,
                                        until=until, set=set,
                                        resumptionToken=resumptionToken)

        e_listIdentifiers = SubElement(envelope.getroot(),
                                       nsoai('ListIdentifiers'))
        kw = {}
        kw['metadataPrefix'] = metadataPrefix
        if from_ is not None:
            kw['from_'] = from_
        if until is not None:
            kw['until'] = until
        if set is not None:
            kw['set'] = set
        if resumptionToken is not None:
            kw['resumptionToken'] = resumptionToken
        for header in self._server.listIdentifiers(**kw):
            self._outputHeader(e_listIdentifiers, header)
        return envelope

    def listMetadataFormats(self, identifier=None):
        envelope = self._outputEnvelope(verb="ListMetadataFormats",
                                        identifier=identifier)
        e_listMetadataFormats = SubElement(envelope.getroot(),
                                           nsoai('ListMetadataFormats'))
        kw = {}
        if identifier is not None:
            kw['identifier'] = identifier
        for (metadataPrefix,
             schema,
             metadataNamespace) in self._server.listMetadataFormats(**kw):
            e_metadataFormat = SubElement(e_listMetadataFormats,
                                          nsoai('metadataFormat'))
            e_metadataPrefix = SubElement(e_metadataFormat,
                                          nsoai('metadataPrefix'))
            e_metadataPrefix.text = metadataPrefix
            e_schema = SubElement(e_metadataFormat,
                                  nsoai('schema'))
            e_schema.text = schema
            e_metadataNamespace = SubElement(e_metadataFormat,
                                             nsoai('metadataNamespace'))
            e_metadataNamespace.text = metadataNamespace
        return envelope            

    def listRecords(self, metadataPrefix, from_=None, until=None, set=None,
                    resumptionToken=None):
        envelope = self._outputEnvelope(verb="ListRecords",
                                        metadataPrefix=metadataPrefix,
                                        from_=from_,
                                        until=until,
                                        set=set,
                                        resumptionToken=resumptionToken)
        e_listRecords = SubElement(envelope.getroot(),
                                   nsoai('ListRecords'))
        kw = {}
        kw['metadataPrefix'] = metadataPrefix
        if from_ is not None:
            kw['from_'] = from_
        if until is not None:
            kw['until'] = until
        if set is not None:
            kw['set'] = set
        if resumptionToken is not None:
            kw['resumptionToken'] = resumptionToken
        for header, metadata, about in self._server.listRecords(**kw):
            e_record = SubElement(e_listRecords, nsoai('record'))
            self._outputHeader(e_record, header)   
            self._outputMetadata(e_record, metadata)
            # XXX about
        return envelope

    def _outputEnvelope(self, **kw):
        e_oaipmh = Element(nsoai('OAI-PMH'), ns_resolver=ns_resolver)
        e_oaipmh.set('{%s}schemaLocation' % NS_XSI,
                     ('http://www.openarchives.org/OAI/2.0/ '
                      'http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd'))
        e_tree = ElementTree(element=e_oaipmh)
        e_responseDate = SubElement(e_oaipmh, nsoai('responseDate'))
        # XXX should date be now or calculated at latest possible moment?
        e_responseDate.text = common.datetime_to_datestamp(
            datetime.utcnow().replace(microsecond=0))
        e_request = SubElement(e_oaipmh, nsoai('request'))
        # XXX shouldn't output this if we had an error
        for key, value in kw.items():
            if value is not None:
                if key == 'from_':
                    key = 'from'
                e_request.set(key, value)
        # XXX this is potentially slow..
        e_request.text = self._server.identify().baseURL()
        return e_tree

    def _outputHeader(self, tree, header):
        e_header = SubElement(tree, nsoai('header'))
        e_identifier = SubElement(e_header, nsoai('identifier'))
        e_identifier.text = header.identifier()
        e_datestamp = SubElement(e_header, nsoai('datestamp'))
        e_datestamp.text = common.datetime_to_datestamp(header.datestamp())
        for set in header.setSpec():
            e = SubElement(e_header, nsoai('setSpec'))
            e.text = set
        
    def _outputMetadata(self, tree, metadata):
        e_metadata = SubElement(tree, nsoai('metadata'))
        e_dc = SubElement(e_metadata, nsdc('dc'))
        #e_dc.set('{%s}schemaLocation' % NS_XSI,
        #         ('http://www.openarchives.org/OAI/2.0/oai_dc/'
        #          'http://www.openarchives.org/OAI/2.0/oai_dc.xsd'))
 
        
class XMLServer(object):
    """A server that responds to messages by returning OAI-PMH compliant XML.

    Takes a server object.
    """
    def __init__(self, server):
        self._tree_server = XMLTreeServer(server)
        
    def getRecord(self, **kw):
        return etree.tostring(self._tree_server.getRecord(**kw).getroot())
    
    def identify(self, **kw):
        return etree.tostring(self._tree_server.identify(**kw).getroot())

    def listIdentifiers(self, **kw):
        return etree.tostring(
            self._tree_server.listIdentifiers(**kw).getroot())
        
    def listMetadataFormats(self, **kw):
        return etree.tostring(
            self._tree_server.listMetadataFormats(**kw).getroot())
            
    def listRecords(self, **kw):
        return etree.tostring(
            self._tree_server.listRecords(**kw).getroot())

    def listSets(self, resumptionToken=None):
        return etree.tostring(
            self._tree_server.listSets(**kw).getroot())

def nsoai(name):
    return '{%s}%s' % (NS_OAIPMH, name)

def nsdc(name):
    return '{%s}%s' % (NS_DC, name)

