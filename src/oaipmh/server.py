from lxml.etree import ElementTree, Element, SubElement
from lxml import etree
from datetime import datetime

from oaipmh import common, metadata

NS_OAIPMH = 'http://www.openarchives.org/OAI/2.0/'
NS_XSI = 'http://www.w3.org/2001/XMLSchema-instance'
NS_OAIDC = 'http://www.openarchives.org/OAI/2.0/oai_dc/'
NS_DC = "http://purl.org/dc/elements/1.1/"

nsmap = {
    None: NS_OAIPMH,
    'xsi': NS_XSI,
    'oai_dc': NS_OAIDC,
    'dc': NS_DC
    }

class XMLTreeServer:
    """A server that responds to messages by returning XML trees.

    This is an implementation class that normally would not be exposed
    to the outside world.

    Takes an object conforming to the ResumptionOAIPMH API.
    """
    def __init__(self, server, metadata_registry):
        self._server = server
        self._metadata_registry = (
            metadata_registry or metadata.global_metadata_registry)
        
    def getRecord(self, **kw):
        envelope, e_getRecord = self._outputEnvelope(
            verb='GetRecord', **kw)
        record = self._server.getRecord(**kw)
        header, metadata, about = self._server.getRecord(**kw)
        e_record = SubElement(e_getRecord, nsoai('record'))
        self._outputHeader(e_record, header)   
        self._outputMetadata(e_record, kw['metadataPrefix'], metadata)
        return envelope
    
    def identify(self):
        envelope, e_identify = self._outputEnvelope(verb='Identify')
        identify = self._server.identify()
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

    def listMetadataFormats(self, **kw):
        envelope, e_listMetadataFormats = self._outputEnvelope(
            verb="ListMetadataFormats", **kw)
        for (metadataPrefix, schema,
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

    def listIdentifiers(self, **kw):
        envelope, e_listIdentifiers = self._outputEnvelope(
            verb='ListIdentifiers', **kw)
        def outputFunc(element, headers):
            for header in headers:
                self._outputHeader(element, header)
        self._outputResuming(
            e_listIdentifiers,
            self._server.listIdentifiers,
            outputFunc,
            kw)
        return envelope
    
    def listRecords(self, **kw):
        envelope, e_listRecords = self._outputEnvelope(
            verb="ListRecords", **kw)
        metadataPrefix = kw['metadataPrefix']
        def outputFunc(element, records):
            for header, metadata, about in records:
                e_record = SubElement(e_listRecords, nsoai('record'))
                self._outputHeader(e_record, header)   
                self._outputMetadata(e_record, metadataPrefix, metadata)
                # XXX about
        self._outputResuming(
            e_listRecords,
            self._server.listRecords,
            outputFunc,
            kw)
        return envelope

    def listSets(self, **kw):
        # XXX
        raise NotImplementedError

    def _outputEnvelope(self, **kw):
        e_oaipmh = Element(nsoai('OAI-PMH'), nsmap=nsmap)
        e_oaipmh.set('{%s}schemaLocation' % NS_XSI,
                     ('http://www.openarchives.org/OAI/2.0/ '
                      'http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd'))
        e_tree = ElementTree(element=e_oaipmh)
        e_responseDate = SubElement(e_oaipmh, nsoai('responseDate'))
        # date should be first possible moment
        e_responseDate.text = common.datetime_to_datestamp(
            datetime.utcnow().replace(microsecond=0))
        e_request = SubElement(e_oaipmh, nsoai('request'))
        # XXX shouldn't output this if we had an error
        for key, value in kw.items():
            if key == 'from_':
                key = 'from'
            e_request.set(key, value)
        # XXX this is potentially slow..
        e_request.text = self._server.identify().baseURL()
        e_element = SubElement(e_oaipmh, nsoai(kw['verb']))
        return e_tree, e_element
    
    def _outputResuming(self, element, input_func, output_func, kw):
        if 'resumptionToken' in kw:
            result, token = input_func(resumptionToken=kw['resumptionToken'])
        else:
            result, token = input_func(**kw)
        output_func(element, result)
        if token is not None:
            e_resumptionToken = SubElement(element, nsoai('resumptionToken'))
            e_resumptionToken.text = token
            
    def _outputHeader(self, element, header):
        e_header = SubElement(element, nsoai('header'))
        e_identifier = SubElement(e_header, nsoai('identifier'))
        e_identifier.text = header.identifier()
        e_datestamp = SubElement(e_header, nsoai('datestamp'))
        e_datestamp.text = common.datetime_to_datestamp(header.datestamp())
        for set in header.setSpec():
            e = SubElement(e_header, nsoai('setSpec'))
            e.text = set
        
    def _outputMetadata(self, element, metadata_prefix, metadata):
        e_metadata = SubElement(element, nsoai('metadata'))
        self._metadata_registry.writeMetadata(
            metadata_prefix, e_metadata, metadata)
        
class XMLServer(common.ResumptionOAIPMH):
    """A server that responds to messages by returning OAI-PMH compliant XML.

    Takes a server object.
    """
    def __init__(self, server, metadata_registry=None):
        self._tree_server = XMLTreeServer(server, metadata_registry)

    def handleVerb(self, verb, args, kw):
        method_name = verb[0].lower() + verb[1:]
        return etree.tostring(
            getattr(self._tree_server, method_name)(**kw).getroot())
    
def oai_dc_writer(element, metadata):
    e_dc = SubElement(element, nsoaidc('dc'))
    e_dc.set('{%s}schemaLocation' % NS_XSI,
             '%s http://www.openarchives.org/OAI/2.0/oai_dc.xsd' % NS_DC)
    map = metadata.getMap()
    for name in [
        'title', 'creator', 'subject', 'description', 'publisher',
        'contributor', 'date', 'type', 'format', 'identifier',
        'source', 'language', 'relation', 'coverage', 'rights']:
        for value in map.get(name, []):
            e = SubElement(e_dc, nsdc(name))
            e.text = value
               
def nsoai(name):
    return '{%s}%s' % (NS_OAIPMH, name)

def nsoaidc(name):
    return '{%s}%s' % (NS_OAIDC, name)

def nsdc(name):
    return '{%s}%s' % (NS_DC, name)
