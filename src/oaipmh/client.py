# Copyright 2003, 2004, 2005 Infrae
# Released under the BSD license (see LICENSE.txt)
from __future__ import nested_scopes
import urllib2
from urllib import urlencode
from StringIO import StringIO
from types import SliceType
from lxml import etree
import time

from oaipmh import common

WAIT_DEFAULT = 120 # two minutes
WAIT_MAX = 5

class Error(Exception):
    pass

class MetadataSchemaRegistry:
    def __init__(self):
        self._metadata_schemas = {}
        
    def addMetadataSchema(self, metadata_schema):
        self._metadata_schemas[
            metadata_schema.getMetadataPrefix()] = metadata_schema
        
    def createMetadata(self, metadata_prefix, xpath_evaluator):
        metadata_schema = self._metadata_schemas.get(metadata_prefix)
        if metadata_schema is None:
            return None
        return metadata_schema.createMetadata(xpath_evaluator)

globalMetadataSchemaRegistry = MetadataSchemaRegistry()

addMetadataSchema = globalMetadataSchemaRegistry.addMetadataSchema

class MetadataSchema:
    def __init__(self, metadata_prefix, namespaces):
        self._metadata_prefix = metadata_prefix
        self._namespaces = namespaces
        self._descriptions = {}

    def addFieldDescription(self, field_name, field_type, xpath):
        self._descriptions[field_name] = field_type, xpath

    def createMetadata(self, xpath_evaluator):
        map = {}
        # setup any extra namespaces needed by this schema
        xpath_evaluator.registerNamespaces(self._namespaces)
        e = xpath_evaluator.evaluate
        # now extra field info according to xpath expr
        for field_name, (field_type, expr) in self._descriptions.items():
            if field_type == 'bytes':
                value = str(e(expr))
            elif field_type == 'bytesList':
                value = [str(item) for item in e(expr)]
            elif field_type == 'text':
                value = e(expr)
            elif field_type == 'textList':
                value = e(expr)
            else:
                raise Error, "Unknown field type: %s" % field_type
            map[field_name] = value
        return common.Metadata(map)

    def getMetadataPrefix(self):
        return self._metadata_prefix
    
def buildHeader(header_node, namespaces):
    e = etree.XPathEvaluator(header_node, namespaces).evaluate
    identifier = str(e('string(oai:identifier/text())'))
    datestamp = common.datestamp_to_datetime(
        str(e('string(oai:datestamp/text())')))
    setspec = [str(s) for s in e('oai:setSpec/text()')]
    deleted = e("@status = 'deleted'") 
    return common.Header(identifier, datestamp, setspec, deleted)

def buildRecords(server, metadata_prefix, namespaces, schema_registry, xml):
    tree = server.parse(xml)
    # first find resumption token if available
    evaluator = etree.XPathEvaluator(tree, namespaces)
    token = evaluator.evaluate(
        'string(/oai:OAI-PMH/*/oai:resumptionToken/text())')
    if token.strip() == '':
        token = None
    record_nodes = evaluator.evaluate(
        '/oai:OAI-PMH/*/oai:record')
    result = []
    for record_node in record_nodes:
        record_evaluator = etree.XPathEvaluator(record_node, namespaces)
        e = record_evaluator.evaluate
        # find header node
        header_node = e('oai:header')[0]
        # create header
        header = buildHeader(header_node, namespaces)
        # find metadata node
        metadata_list = e('oai:metadata')
        if metadata_list:
            metadata_node = metadata_list[0]
            metadata_evaluator = etree.XPathEvaluator(
                metadata_node, namespaces)
            # create metadata
            metadata = schema_registry.createMetadata(
                metadata_prefix, metadata_evaluator)
        else:
            metadata = None
        # XXX TODO: about, should be third element of tuple
        result.append((header, metadata, None))
    return result, token

def buildIdentifiers(server, namespaces, xml):
    tree = server.parse(xml)
    evaluator = etree.XPathEvaluator(tree, namespaces)
    # first find resumption token is available
    token = evaluator.evaluate(
        'string(/oai:OAI-PMH/oai:ListIdentifiers/oai:resumptionToken/text())')
    if token.strip() == '':
        token = None    
    header_nodes = evaluator.evaluate(
            '/oai:OAI-PMH/oai:ListIdentifiers/oai:header')            
    result = []
    for header_node in header_nodes:
        header = buildHeader(header_node, namespaces)
        result.append(header)
    return result, token

def buildSets(server, namespaces, xml):
    tree = server.parse(xml)
    evaluator = etree.XPathEvaluator(tree, namespaces)
    # first find resumption token if available
    token = evaluator.evaluate(
        'string(/oai:OAI-PMH/oai:ListSets/oai:resumptionToken/text())')
    if token.strip() == '':
        token = None  
    set_nodes = evaluator.evaluate(
        '/oai:OAI-PMH/oai:ListSets/oai:set')
    sets = []
    for set_node in set_nodes:
        e = etree.XPathEvaluator(set_node, namespaces).evaluate
        setSpec = e('string(oai:setSpec/text())')
        setName = e('string(oai:setName/text())')
        # XXX setDescription nodes
        sets.append((setSpec, setName, None))
    return sets, token

def GetRecord(server, args, xml):
    records, token = buildRecords(
        server,
        args['metadataPrefix'],
        server.getNamespaces(),
        server.getMetadataSchemaRegistry(),
        xml
        )
    assert token is None
    return records[0]
    
def Identify(server, args, xml):
    tree = server.parse(xml)
    namespaces = server.getNamespaces()
    evaluator = etree.XPathEvaluator(tree, namespaces)
    identify_node = evaluator.evaluate(
        '/oai:OAI-PMH/oai:Identify')[0]
    identify_evaluator = etree.XPathEvaluator(identify_node, namespaces)
    e = identify_evaluator.evaluate
    
    repositoryName = e('string(oai:repositoryName/text())')
    baseURL = e('string(oai:baseURL/text())')
    protocolVersion = e('string(oai:protocolVersion/text())')
    adminEmails = e('oai:adminEmail/text()')
    earliestDatestamp = common.datestamp_to_datetime(
        e('string(oai:earliestDatestamp/text())'))
    deletedRecord = e('string(oai:deletedRecord/text())')
    granularity = e('string(oai:granularity/text())')
    compression = e('oai:compression/text()')
    # XXX description
    identify = common.ServerIdentify(repositoryName, baseURL, protocolVersion,
                                     adminEmails, earliestDatestamp,
                                     deletedRecord, granularity, compression)
    return identify

def ResumptionListGenerator(firstBatch, nextBatch):
    result, token = firstBatch()
    while 1:
        for item in result:
            yield item
        if token is None:
            break
        result, token = nextBatch(token)

def ListIdentifiers(server, args, xml):
    namespaces = server.getNamespaces()
    def firstBatch():
        return buildIdentifiers(server, namespaces, xml)
    def nextBatch(token):
        xml = server.makeRequest(verb='ListIdentifiers',
                                 resumptionToken=token)
        return buildIdentifiers(server, namespaces, xml)
    return ResumptionListGenerator(firstBatch, nextBatch)

def ListMetadataFormats(server, args, xml):
    #XXX args always thrown away?
    tree = server.parse(xml)
    namespaces = server.getNamespaces()
    evaluator = etree.XPathEvaluator(tree, namespaces)

    metadataFormat_nodes = evaluator.evaluate(
        '/oai:OAI-PMH/oai:ListMetadataFormats/oai:metadataFormat')
    metadataFormats = []
    for metadataFormat_node in metadataFormat_nodes:
        e = etree.XPathEvaluator(metadataFormat_node, namespaces).evaluate
        metadataPrefix = e('string(oai:metadataPrefix/text())')
        schema = e('string(oai:schema/text())')
        metadataNamespace = e('string(oai:metadataNamespace/text())')
        metadataFormat = (metadataPrefix, schema, metadataNamespace)
        metadataFormats.append(metadataFormat)

    return metadataFormats

def ListRecords(server, args, xml):
    namespaces = server.getNamespaces()
    metadata_prefix = args['metadataPrefix']
    metadata_schema_registry = server.getMetadataSchemaRegistry()
    def firstBatch():
        return buildRecords(
            server, metadata_prefix, namespaces,
            metadata_schema_registry, xml)
    def nextBatch(token):
        xml = server.makeRequest(
            verb='ListRecords',
            resumptionToken=token)
        return buildRecords(
            server,
            metadata_prefix, namespaces,
            metadata_schema_registry, xml)
    return ResumptionListGenerator(firstBatch, nextBatch)

def ListSets(server, args, xml):
    namespaces = server.getNamespaces()
    def firstBatch():
        return buildSets(server, namespaces, xml)
    def nextBatch(token):
        xml = server.makeRequest(
            verb='ListSets',
            resumptionToken=token)
        return buildSets(server, namespaces, xml)
    return ResumptionListGenerator(firstBatch, nextBatch)

class OAIMethodError(Exception):
    pass

class OAIMethodImpl:
    def __init__(self, verb, argspec, factory):
        self._factory = factory
        self._verb = verb
        self._argspec = argspec
        self._exclusive = None
        for arg_name, arg_type in argspec.items():
            if arg_type == 'exclusive':
                self._exclusive = arg_name

    def _processArguments(self, dict):
        argspec = self._argspec
        # first filter out any local arguments, which will be returned
        local = {}
        for key, value in argspec.items():
            if value == 'local' and dict.has_key(key):
                local[key] = dict[key]
                del dict[key]
        # check if we have unknown arguments
        for key, value in dict.items():
            if not argspec.has_key(key):
                raise OAIMethodError, "Unknown argument: %s" % key
        # first investigate if we have exclusive argument
        if dict.has_key(self._exclusive):
            if len(dict) > 1:
                raise OAIMethodError, "Exclusive argument %s is used but other arguments found." % self._exclusive
            return
        # if not exclusive, check for required
        for arg_name, arg_type in argspec.items(): 
            if arg_type == 'required':
                if not dict.has_key(arg_name):
                    raise OAIMethodError, "Argument required but not found: %s" % arg_name
        return local
    
    def __call__(self, bound_self, **kw):
        # deal with 'from' (python keyword)
        if kw.has_key('from_'):
            kw['from'] = kw['from_']
            del kw['from_']
        local = self._processArguments(kw)
        kw['verb'] = self._verb
        # reconstruct all arguments XXX hack
        args = kw.copy()
        args.update(local)
        return self._factory(bound_self, args, bound_self.makeRequest(**kw))

def OAIMethod(verb, argspec, factory):
    obj = OAIMethodImpl(verb, argspec, factory)
    def method(self, **kw):
        return obj(self, **kw)
    return method

class BaseServerProxy:
    def __init__(self, metadataSchemaRegistry=None):
        self._metadata_schema_registry = (
            metadataSchemaRegistry or globalMetadataSchemaRegistry)
        self._ignore_bad_character_hack = 0

    def addMetadataSchema(self, schema):
        """Add metadata schema to registry.
        XXX what if this is the global registry, do we want to allow that?
        """
        self._metadata_schema_registry.addMetadataSchema(schema)

    def getNamespaces(self):
        """Get OAI namespaces.
        """
        return {'oai': 'http://www.openarchives.org/OAI/2.0/'}

    def getMetadataSchemaRegistry(self):
        """Get metadata schema registry for this server.
        """
        return self._metadata_schema_registry
    
    def makeRequest(self, **kw):
        """Actually retrieve XML from the server.
        """
        raise NotImplementedError

    def ignoreBadCharacters(self, true_or_false): 	 
        """Set to ignore bad characters in UTF-8 input. 	 
        This is a hack to get around well-formedness errors of 	 
        input sources which *should* be in UTF-8 but for some reason 	 
        aren't completely. 	 
        """ 	 
        self._ignore_bad_character_hack = true_or_false 	 

    def parse(self, xml): 	 
        """Parse the XML to a lxml tree. 	 
        """
        # XXX this is only safe for UTF-8 encoded content, 	 
        # and we're basically hacking around non-wellformedness anyway,
        # but oh well
        if self._ignore_bad_character_hack: 	 
            xml = unicode(xml, 'UTF-8', 'replace') 	 
            # also get rid of character code 12 	 
            xml = xml.replace(chr(12), '?')
        else:
            xml = unicode(xml, 'UTF-8')
        return etree.XML(xml)

    getRecord = OAIMethod(
        'GetRecord',
        {'identifier':'required',
        'metadataPrefix':'required'},
        GetRecord
        )
    
    identify = OAIMethod(
        'Identify',
        {},
        Identify
        )

    listIdentifiers = OAIMethod(
        'ListIdentifiers',
        {'from':'optional',
         'until':'optional',
         'metadataPrefix':'required',
         'set':'optional',
         'resumptionToken':'exclusive',
         },
        ListIdentifiers
        )

    listMetadataFormats = OAIMethod(
        'ListMetadataFormats',
        {'identifier':'optional'},
        ListMetadataFormats
        )

    listRecords = OAIMethod(
        'ListRecords',
        {'from':'optional',
         'until':'optional',
         'set':'optional',
         'resumptionToken':'exclusive',
         'metadataPrefix':'required',
         },
        ListRecords
        )

    listSets = OAIMethod(
        'ListSets',
        {'resumptionToken':'exclusive',
         },
        ListSets
        )
    
class ServerProxy(BaseServerProxy):
    def __init__(self, base_url, metadataSchemaRegistry=None):
        BaseServerProxy.__init__(self, metadataSchemaRegistry)
        self._base_url = base_url
        
    def makeRequest(self, **kw):
        """Actually retrieve XML from the server.
        """
        # XXX include From header?
        headers = {'User-Agent': 'Infrae-oaipmh',
                   }
        request = urllib2.Request(self._base_url, urlencode(kw), headers)
        return retrieveFromUrlWaiting(request)

def retrieveFromUrlWaiting(request,
                           wait_max=WAIT_MAX, wait_default=WAIT_DEFAULT):
    """Get text from URL, handling 503 Retry-After.
    """
    for i in range(wait_max):
        try:
            f = urllib2.urlopen(request)
            text = f.read()
            f.close()
            # we successfully opened without having to wait
            break
        except urllib2.HTTPError, e:
            if e.code == 503:
                try:
                    retryAfter = int(e.hdrs.get('Retry-After'))
                except ValueError:
                    retryAfter = None
                if retryAfter is None:
                    time.sleep(wait_default)
                else:
                    time.sleep(retryAfter)
            else:
                # reraise any other HTTP error
                raise
    else:
        raise Error, "Waited too often (more than %s times)" % wait_max
    return text

def register_oai_dc(server_proxy=None):
    """Register OAI DC with server proxy, or global registry.
    """
    oai_dc = MetadataSchema(
        'oai_dc',
        {'oai_dc': 'http://www.openarchives.org/OAI/2.0/oai_dc/',
         'dc' : 'http://purl.org/dc/elements/1.1/'}
        )
    
    fields = [
        ('title', 'oai_dc:dc/dc:title/text()'),
        ('creator', 'oai_dc:dc/dc:creator/text()'),
        ('subject', 'oai_dc:dc/dc:subject/text()'),
        ('description', 'oai_dc:dc/dc:description/text()'),
        ('publisher', 'oai_dc:dc/dc:publisher/text()'),
        ('contributor', 'oai_dc:dc/dc:contributor/text()'),
        ('date', 'oai_dc:dc/dc:date/text()'),
        ('type', 'oai_dc:dc/dc:type/text()'),
        ('format', 'oai_dc:dc/dc:format/text()'),
        ('identifier', 'oai_dc:dc/dc:identifier/text()'),
        ('source', 'oai_dc:dc/dc:source/text()'),
        ('language', 'oai_dc:dc/dc:language/text()'),
        ('relation', 'oai_dc:dc/dc:relation/text()'),
        ('coverage', 'oai_dc:dc/dc:coverage/text()'),
        ('rights', 'oai_dc:dc/dc:rights/text()')
        ]
    
    for name, xpath in fields:
        oai_dc.addFieldDescription(name, 'textList', xpath)

    if server_proxy is not None:
        server_proxy.addMetadataSchema(oai_dc)
    else:
        addMetadataSchema(oai_dc)

