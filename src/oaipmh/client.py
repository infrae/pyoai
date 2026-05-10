# Copyright 2003, 2004, 2005 Infrae
# Released under the BSD license (see LICENSE.txt)
from __future__ import nested_scopes
from __future__ import absolute_import

import six

try:
    import urllib.request as urllib2
    from urllib.parse import urlencode
except ImportError:
    import urllib2
    from urllib import urlencode

import base64
from lxml import etree
import time
import codecs

from oaipmh import common, metadata, validation, error
from oaipmh.datestamp import datestamp_to_datetime, datetime_to_datestamp

WAIT_DEFAULT = 120 # two minutes
WAIT_MAX = 5

class Error(Exception):
    pass


class BaseClient(common.OAIPMH):
    # retry policy on error. Default is to retry request `WAIT_MAX` times
    # on HTTP 503 errors, waiting `WAIT_DEFAULT` before each retry
    default_retry_policy = {
        # how many seconds should we wait before each retry
        'wait-default': WAIT_DEFAULT,
        # how many times should we retry
        'retry': WAIT_MAX,
        # which HTTP codes are expected
        'expected-errcodes': {503},
    }

    def __init__(self, metadata_registry=None, custom_retry_policy=None, raw_data=None):
        self._metadata_registry = (
            metadata_registry or metadata.global_metadata_registry)
        self._ignore_bad_character_hack = 0
        self._day_granularity = False
        self.retry_policy = self.default_retry_policy.copy()
        if custom_retry_policy is not None:
            self.retry_policy.update(custom_retry_policy)
        self._raw_data = raw_data

    def updateGranularity(self):
        """Update the granularity setting dependent on that the server says.
        """
        identify = self.identify()
        granularity = identify.granularity()
        if granularity == 'YYYY-MM-DD':
            self._day_granularity = True
        elif granularity == 'YYYY-MM-DDThh:mm:ssZ':
            self._day_granularity= False
        else:
            raise Error("Non-standard granularity on server: %s" % granularity)

    def handleVerb(self, verb, kw):
        # validate kw first
        validation.validateArguments(verb, kw)
        # encode datetimes as datestamps
        from_ = kw.get('from_')
        if from_ is not None:
            # turn it into 'from', not 'from_' before doing actual request
            kw['from'] = datetime_to_datestamp(from_,
                                               self._day_granularity)
        if 'from_' in kw:
            # always remove it from the kw, no matter whether it be None or not
            del kw['from_']

        until = kw.get('until')
        if until is not None:
            kw['until'] = datetime_to_datestamp(until,
                                                self._day_granularity)
        elif 'until' in kw:
            # until is None but is explicitly in kw, remove it
            del kw['until']

        # now call underlying implementation
        method_name = verb + '_impl'
        return getattr(self, method_name)(
            kw, self.makeRequestErrorHandling(verb=verb, **kw))

    def getNamespaces(self):
        """Get OAI namespaces.
        """
        return {'oai': 'http://www.openarchives.org/OAI/2.0/'}

    def getMetadataRegistry(self):
        """Return the metadata registry in use.

        Do we want to allow the returning of the global registry?
        """
        return self._metadata_registry

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
            xml = six.text_type(xml, 'UTF-8', 'replace')
            # also get rid of character code 12
            xml = xml.replace(chr(12), '?')
            xml = xml.encode('UTF-8')
        if six.PY3:
            if hasattr(xml, "encode"):
                xml = xml.encode("utf-8")
            # xml = xml.encode("utf-8")
        return etree.XML(xml)

    # implementation of the various methods, delegated here by
    # handleVerb method

    def GetRecord_impl(self, args, tree):
        records, token = self.buildRecords(
            args['metadataPrefix'],
            self.getNamespaces(),
            self._metadata_registry,
            tree
            )
        assert token is None
        return records[0]

    def GetMetadata_impl(self, args, tree):
        return tree

    def Identify_impl(self, args, tree):
        namespaces = self.getNamespaces()
        identify_node = tree.xpath(
            '/oai:OAI-PMH/oai:Identify',
            namespaces=namespaces
        )[0]
        e = identify_node.xpath

        repositoryName = e('string(oai:repositoryName/text())', namespaces=namespaces)
        baseURL = e('string(oai:baseURL/text())', namespaces=namespaces)
        protocolVersion = e('string(oai:protocolVersion/text())', namespaces=namespaces)
        adminEmails = e('oai:adminEmail/text()', namespaces=namespaces)
        earliestDatestamp = datestamp_to_datetime(
            e('string(oai:earliestDatestamp/text())', namespaces=namespaces))
        deletedRecord = e('string(oai:deletedRecord/text())', namespaces=namespaces)
        granularity = e('string(oai:granularity/text())', namespaces=namespaces)
        compression = e('oai:compression/text()', namespaces=namespaces)
        # XXX description
        identify = common.Identify(
            repositoryName, baseURL, protocolVersion,
            adminEmails, earliestDatestamp,
            deletedRecord, granularity, compression)
        return identify

    def ListIdentifiers_impl(self, args, tree):
        namespaces = self.getNamespaces()
        def firstBatch():
            return self.buildIdentifiers(namespaces, tree)
        def nextBatch(token):
            tree = self.makeRequestErrorHandling(verb='ListIdentifiers',
                                                 resumptionToken=token)
            return self.buildIdentifiers(namespaces, tree)
        return ResumptionListGenerator(firstBatch, nextBatch)

    def ListMetadataFormats_impl(self, args, tree):
        namespaces = self.getNamespaces()
        metadataFormat_nodes = tree.xpath(
            '/oai:OAI-PMH/oai:ListMetadataFormats/oai:metadataFormat',
            namespaces=namespaces
        )
        metadataFormats = []
        for metadataFormat_node in metadataFormat_nodes:
            e = metadataFormat_node.xpath
            metadataPrefix = e('string(oai:metadataPrefix/text())', namespaces=namespaces)
            schema = e('string(oai:schema/text())', namespaces=namespaces)
            metadataNamespace = e('string(oai:metadataNamespace/text())', namespaces=namespaces)
            metadataFormat = (metadataPrefix, schema, metadataNamespace)
            metadataFormats.append(metadataFormat)

        return metadataFormats

    def ListRecords_impl(self, args, tree):
        namespaces = self.getNamespaces()
        metadata_prefix = args['metadataPrefix']
        metadata_registry = self._metadata_registry
        def firstBatch():
            return self.buildRecords(
                metadata_prefix, namespaces,
                metadata_registry, tree)
        def nextBatch(token):
            tree = self.makeRequestErrorHandling(
                verb='ListRecords',
                resumptionToken=token)
            return self.buildRecords(
                metadata_prefix, namespaces,
                metadata_registry, tree)
        return ResumptionListGenerator(firstBatch, nextBatch)

    def ListSets_impl(self, args, tree):
        namespaces = self.getNamespaces()
        def firstBatch():
            return self.buildSets(namespaces, tree)
        def nextBatch(token):
            tree = self.makeRequestErrorHandling(
                verb='ListSets',
                resumptionToken=token)
            return self.buildSets(namespaces, tree)
        return ResumptionListGenerator(firstBatch, nextBatch)

    # various helper methods

    def buildRecords(self, metadata_prefix, namespaces, metadata_registry, tree):
        token = tree.xpath(
            'string(/oai:OAI-PMH/*/oai:resumptionToken/text())',
            namespaces=namespaces
        )
        if token.strip() == '' or self._raw_data:
            token = None
        record_nodes = tree.xpath('/oai:OAI-PMH/*/oai:record', namespaces=namespaces)
        result = []
        for record_node in record_nodes:
            e = record_node.xpath
            # find header node
            header_node = e('oai:header', namespaces=namespaces)[0]
            # create header
            header = buildHeader(header_node, namespaces)
            # find metadata node
            metadata_list = e('oai:metadata', namespaces=namespaces)
            if metadata_list:
                metadata_node = metadata_list[0]
                # create metadata
                metadata = metadata_registry.readMetadata(metadata_prefix,
                                                          metadata_node)
            else:
                metadata = None
            # XXX TODO: about, should be third element of tuple
            result.append((header, metadata, None))
        return result, token

    def buildIdentifiers(self, namespaces, tree):
        #'string(/oai:OAI-PMH/oai:ListIdentifiers/oai:resumptionToken/text())')
        token = tree.xpath(
            'string(/oai:OAI-PMH/*/oai:resumptionToken/text())',
            namespaces=namespaces
        )
        if token.strip() == '':
            token = None
        header_nodes = tree.xpath(
            '/oai:OAI-PMH/oai:ListIdentifiers/oai:header',
            namespaces=namespaces
        )
        result = []
        for header_node in header_nodes:
            header = buildHeader(header_node, namespaces)
            result.append(header)
        return result, token

    def buildSets(self, namespaces, tree):
        token = tree.xpath(
            'string(/oai:OAI-PMH/oai:ListSets/oai:resumptionToken/text())',
            namespaces=namespaces
        )
        if token.strip() == '':
            token = None
        set_nodes = tree.xpath(
            '/oai:OAI-PMH/oai:ListSets/oai:set',
            namespaces=namespaces
        )
        sets = []
        for set_node in set_nodes:
            e = set_node.xpath
            # make sure we get back unicode strings instead
            # of lxml.etree._ElementUnicodeResult objects.
            setSpec = six.text_type(e('string(oai:setSpec/text())', namespaces=namespaces))
            setName = six.text_type(e('string(oai:setName/text())', namespaces=namespaces))
            # XXX setDescription nodes
            sets.append((setSpec, setName, None))
        return sets, token

    def makeRequestErrorHandling(self, **kw):
        xml = self.makeRequest(**kw)
        try:
            tree = self.parse(xml)
        except SyntaxError:
            raise error.XMLSyntaxError(kw)
        # check whether there are errors first
        e_errors = tree.xpath('/oai:OAI-PMH/oai:error',
                              namespaces=self.getNamespaces())
        if e_errors:
            # XXX right now only raise first error found, does not
            # collect error info
            for e_error in e_errors:
                code = e_error.get('code')
                msg = e_error.text
                if code not in ['badArgument', 'badResumptionToken',
                                'badVerb', 'cannotDisseminateFormat',
                                'idDoesNotExist', 'noRecordsMatch',
                                'noMetadataFormats', 'noSetHierarchy']:
                    raise error.UnknownError(
                          "Unknown error code from server: %s, message: %s" % (
                        code, msg))
                # find exception in error module and raise with msg
                raise getattr(error, code[0].upper() + code[1:] + 'Error')(msg)
        return tree

    def makeRequest(self, **kw):
        raise NotImplementedError

class Client(BaseClient):

    def __init__(
        self,
        base_url,
        metadata_registry=None,
        credentials=None,
        local_file=False,
        force_http_get=False,
        custom_retry_policy=None,
        raw_data=None,
    ):
        BaseClient.__init__(
            self, metadata_registry, custom_retry_policy=custom_retry_policy, raw_data=raw_data
        )
        self._base_url = base_url
        self._local_file = local_file
        self._force_http_get = force_http_get
        if credentials is not None:
            self._credentials = base64.encodebytes(credentials.encode()).decode()
        else:
            self._credentials = None

    def makeRequest(self, **kw):
        if isinstance(self._raw_data, str):
            return self._raw_data.encode('ascii', 'replace')
        elif self._local_file:
            with codecs.open(self._base_url, 'r', 'utf-8') as xmlfile:
                text = xmlfile.read()
            return text.encode('ascii', 'replace')
        else:
            # XXX include From header?
            headers = {'User-Agent': 'pyoai'}
            if self._credentials is not None:
                headers['Authorization'] = 'Basic ' + self._credentials.strip()
            if self._force_http_get:
                request_url = '%s?%s' % (self._base_url, urlencode(kw))
                request = urllib2.Request(request_url, headers=headers)
            else:
                binary_data = urlencode(kw).encode('utf-8')
                request = urllib2.Request(
                    self._base_url, data=binary_data, headers=headers)

            return retrieveFromUrlWaiting(
                request,
                wait_max=self.retry_policy['retry'],
                wait_default=self.retry_policy['wait-default'],
                expected_errcodes=self.retry_policy['expected-errcodes']
            )

def buildHeader(header_node, namespaces):
    e = header_node.xpath
    identifier = e('string(oai:identifier/text())', namespaces=namespaces)
    datestamp = datestamp_to_datetime(
        str(e('string(oai:datestamp/text())', namespaces=namespaces)))
    setspec = [str(s) for s in e('oai:setSpec/text()', namespaces=namespaces)]
    deleted = e("@status = 'deleted'", namespaces=namespaces)
    return common.Header(header_node, identifier, datestamp, setspec, deleted)

def ResumptionListGenerator(firstBatch, nextBatch):
    result, token = firstBatch()
    while 1:
        itemFound = False
        for item in result:
            yield item
            itemFound = True
        if token is None or not itemFound:
            break
        result, token = nextBatch(token)

def retrieveFromUrlWaiting(request,
                           wait_max=WAIT_MAX, wait_default=WAIT_DEFAULT,
                           expected_errcodes={503}):
    """Get text from URL, handling 503 Retry-After.
    """
    for i in list(range(wait_max)):
        try:
            f = urllib2.urlopen(request)
            text = f.read()
            f.close()
            # we successfully opened without having to wait
            break
        except urllib2.HTTPError as e:
            if e.code in expected_errcodes:
                try:
                    retryAfter = int(e.hdrs.get('Retry-After'))
                except TypeError:
                    retryAfter = None
                if retryAfter is None:
                    time.sleep(wait_default)
                else:
                    time.sleep(retryAfter)
            else:
                # reraise any other HTTP error
                raise
    else:
        raise Error("Waited too often (more than %s times)" % wait_max)
    return text

class ServerClient(BaseClient):
    def __init__(self, server, metadata_registry=None):
        BaseClient.__init__(self, metadata_registry)
        self._server = server

    def makeRequest(self, **kw):
        return self._server.handleRequest(kw)
