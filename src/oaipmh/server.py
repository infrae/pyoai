from oaipmh import common
from lxml.etree import ElementTree, Element, SubElement
from lxml import etree
from datetime import datetime

NS_OAIPMH = 'http://www.openarchives.org/OAI/2.0/'
NS_XSI = 'http://www.w3.org/2001/XMLSchema-instance'

ns_resolver = etree.NsResolver({None: NS_OAIPMH, 'xsi': NS_XSI})

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
     
class XMLServer:
    """A server that responds to messages by returning OAI-PMH compliant XML.

    Takes a server object.
    """
    def __init__(self, server):
        self._server = server
        
    def getRecord(self, identifier, metadataPrefix):
        pass
    
    def identify(self):
        return etree.tostring(self.identify_tree().getroot())

    def identify_tree(self):
        envelope = self._outputEnvelope(verb='Identify')
        self._outputIdentify(envelope.getroot(), self._server.identify())
        return envelope
    
    def listIdentifiers(self, metadataPrefix, from_=None, until=None, set=None,
                        resumptionToken=None):
        pass

    def listMetadataFormats(self, identifier=None):
        pass

    def listRecords(self, metadataPrefix, from_=None, until=None, set=None,
                    resumptionToken=None):
        pass
    

    def listSets(self, resumptionToken=None):
        pass

    def _outputEnvelope(self, **kw):
        e_oaipmh = Element(nsoai('OAI-PMH'), ns_resolver=ns_resolver)
        e_tree = ElementTree(element=e_oaipmh)
        e_oaipmh.set('{%s}schemaLocation' % NS_XSI,
                     ('http://www.openarchives.org/OAI/2.0/ '
                      'http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd'))
        e_responseDate = SubElement(e_oaipmh, nsoai('responseDate'))
        # XXX should date be now or calculated at latest possible moment?
        e_responseDate.text = common.datetime_to_datestamp(
            datetime.utcnow().replace(microsecond=0))
        e_request = SubElement(e_oaipmh, nsoai('request'))
        # XXX shouldn't output this if we had an error
        for key, value in kw.items():
            e_request.set(key, value)
        # XXX this is potentially slow..
        e_request.text = self._server.identify().baseURL()
        return e_tree

    def _outputIdentify(self, tree, identify):
        e_identify = SubElement(tree, nsoai('Identify'))
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
        # XXX fake
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
                
    def _outputHeader(self, tree, header):
        e_header = SubElement(tree, nsoai('header'))
        e_identifier = SubElement(e_header, nsoai('identifier'))
        e_identifier.text = header.identifier()
        e_datestamp = SubElement(e_header, nsoai('datestamp'))
        e_datestamp.text = header.datestamp()
        for set in header.setSpec():
            e = SubElement(e_header, nsoai('setSpec'))
            e.text = set
        tree.append(e_header)
    
def nsoai(name):
    return '{%s}%s' % (NS_OAIPMH, name)

def outputHeader(tree, header):
    """Given a header build XML representation.
    """
    e_header = Element('{%s}header' % NS_OAIPMH, ns_resolver=ns_resolver)
    e_identifier = SubElement(e_header, '{%s}identifier' % NS_OAIPMH)
    e_identifier.text = header.identifier()
    e_datestamp = SubElement(e_header, '{%s}datestamp' % NS_OAIPMH)
    e_datestamp.text = header.datestamp()
    for set in header.setSpec():
        e = SubElement(e_header, '{%s}setSpec' % NS_OAIPMH)
        e.text = set
    tree.append(e_header)

def outputRecord(tree, record):
    """Given a record build XML representation.
    """
    header, metadata, about = record
    e_record = Element('{%s}record' % NS_OAIPMH, ns_resolver=ns_resolver)
    e_record.append(outputHeader(header))
    e_metadata = SubElement(e_record, '{%s}metadata' % NS_OAIPMH)
    # XXX ignore about for now
    tree.append(e_record)
    
## def outputRecords(records, batch_size=None):
##     """Given an iterable of records, return iterable.

##     batch_size is size of individual batch, or None for no batching.
    
##     Returns iterable of xml for each batch, including resumption
##     token information.
##     """
##     c = 0
##     for record in records:
##         e_records = Element(
##         if batch_size is not None and c >= batch_size:
##             c = 0
##             yield e_records
##         c += 1
##     yield e_records
    
    
def outputServerIdentify(tree, identify):
    """Given an identify builds an XML representation.
    """
    pass

