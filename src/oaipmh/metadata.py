import sys

from lxml import etree
from lxml.etree import SubElement
from oaipmh import common

if sys.version_info[0] == 3:
    text_type = str
else:
    text_type = unicode

class MetadataRegistry(object):
    """A registry that contains readers and writers of metadata.

    a reader is a function that takes a chunk of (parsed) XML and
    returns a metadata object.

    a writer is a function that takes a takes a metadata object and
    produces a chunk of XML in the right format for this metadata.
    """
    def __init__(self):
        self._readers = {}
        self._writers = {}
        
    def registerReader(self, metadata_prefix, reader):
        self._readers[metadata_prefix] = reader

    def registerWriter(self, metadata_prefix, writer):
        self._writers[metadata_prefix] = writer

    def hasReader(self, metadata_prefix):
        return metadata_prefix in self._readers
    
    def hasWriter(self, metadata_prefix):
        return metadata_prefix in self._writers
    
    def readMetadata(self, metadata_prefix, element):
        """Turn XML into metadata object.

        element - element to read in

        returns - metadata object
        """
        return self._readers[metadata_prefix](element)

    def writeMetadata(self, metadata_prefix, element, metadata):
        """Write metadata as XML.
        
        element - ElementTree element to write under
        metadata - metadata object to write
        """
        self._writers[metadata_prefix](element, metadata)

global_metadata_registry = MetadataRegistry()

class Error(Exception):
    pass

class MetadataReader(object):
    """A default implementation of a reader based on fields.
    """
    def __init__(self, fields, namespaces=None):
        self._fields = fields
        self._namespaces = namespaces or {}

    def __call__(self, element):
        map = {}
        # create XPathEvaluator for this element
        xpath_evaluator = etree.XPathEvaluator(element, 
                                               namespaces=self._namespaces)
        
        e = xpath_evaluator.evaluate
        # now extra field info according to xpath expr
        for field_name, (field_type, expr) in list(self._fields.items()):
            if field_type == 'bytes':
                value = str(e(expr))
            elif field_type == 'bytesList':
                value = [str(item) for item in e(expr)]
            elif field_type == 'text':
                # make sure we get back unicode strings instead
                # of lxml.etree._ElementUnicodeResult objects.
                value = text_type(e(expr))
            elif field_type == 'textList':
                # make sure we get back unicode strings instead
                # of lxml.etree._ElementUnicodeResult objects.
                value = [text_type(v) for v in e(expr)]
            else:
                raise Error("Unknown field type: %s" % field_type)
            map[field_name] = value
        return common.Metadata(element, map)

oai_dc_reader = MetadataReader(
    fields={
    'title':       ('textList', 'oai_dc:dc/dc:title/text()'),
    'creator':     ('textList', 'oai_dc:dc/dc:creator/text()'),
    'subject':     ('textList', 'oai_dc:dc/dc:subject/text()'),
    'description': ('textList', 'oai_dc:dc/dc:description/text()'),
    'publisher':   ('textList', 'oai_dc:dc/dc:publisher/text()'),
    'contributor': ('textList', 'oai_dc:dc/dc:contributor/text()'),
    'date':        ('textList', 'oai_dc:dc/dc:date/text()'),
    'type':        ('textList', 'oai_dc:dc/dc:type/text()'),
    'format':      ('textList', 'oai_dc:dc/dc:format/text()'),
    'identifier':  ('textList', 'oai_dc:dc/dc:identifier/text()'),
    'source':      ('textList', 'oai_dc:dc/dc:source/text()'),
    'language':    ('textList', 'oai_dc:dc/dc:language/text()'),
    'relation':    ('textList', 'oai_dc:dc/dc:relation/text()'),
    'coverage':    ('textList', 'oai_dc:dc/dc:coverage/text()'),
    'rights':      ('textList', 'oai_dc:dc/dc:rights/text()')
    },
    namespaces={
    'oai_dc': 'http://www.openarchives.org/OAI/2.0/oai_dc/',
    'dc' : 'http://purl.org/dc/elements/1.1/'}
    )

oai_edm_reader = MetadataReader(
    fields={
    'identifier': ('textList', 'rdf:RDF/edm:ProvidedCHO/dc:identifier/text()'),
    'language': ('textList', 'rdf:RDF/edm:ProvidedCHO/dc:language/text()'),
    'rights': ('textList', 'rdf:RDF/edm:ProvidedCHO/dc:rights/text()'),
    'description': ('textList', 'rdf:RDF/edm:ProvidedCHO/dc:description/text()'),
    'publisher': ('textList', 'rdf:RDF/edm:ProvidedCHO/dc:publisher/text()'),
    'subject': ('textList', 'rdf:RDF/skos:Concept[@rdf:about=//edm:ProvidedCHO/dc:subject/@rdf:resource]/skos:prefLabel/text()'),
    'type': ('textList', 'rdf:RDF/skos:Concept[@rdf:about=//edm:ProvidedCHO/dc:type/@rdf:resource]/skos:prefLabel/text()'),
    'temporal': ('textList', 'rdf:RDF/edm:TimeSpan[@rdf:about=//edm:ProvidedCHO/dcterms:temporal/@rdf:resource]/skos:prefLabel/text()'),
    'file': ('textList', 'rdf:RDF/ore:Aggregation/edm:isShownBy/@rdf:resource'),
    'title': ('textList', 'rdf:RDF/edm:ProvidedCHO/dc:title/text()'),
    'creator': ('textList', 'rdf:RDF/edm:Agent[@rdf:about=//edm:ProvidedCHO/dc:creator/@rdf:resource]/skos:prefLabel/text()')
    },
    namespaces={
    'dc' : 'http://purl.org/dc/elements/1.1/',
    'edm': 'http://www.europeana.eu/schemas/edm/',
    'oai_edm': 'http://www.europeana.eu/schemas/edm/',
    'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
    'rdfs': 'http://www.w3.org/2000/01/rdf-schema#',
    'skos': 'http://www.w3.org/2004/02/skos/core#',
    'ore': 'http://www.openarchives.org/ore/terms/',
    'wgs84': 'http://www.w3.org/2003/01/geo/wgs84_pos#',
    'owl': 'http://www.w3.org/2002/07/owl#',
    'rdaGr2': 'http://rdvocab.info/ElementsGr2/',
    'ns13': 'http://www.w3.org/ns/odrl/2/',
    'ns12': 'http://xmlns.com/foaf/0.1/',
    'ns11': 'http://rdfs.org/sioc/services#',
    'ns10': 'http://www.ebu.ch/metadata/ontologies/ebucore/ebucore#',
    'dcterms': 'http://purl.org/dc/terms/',
    'ns16': 'http://www.europeana.eu/schemas/edm/enrichment/',
    'ns15': 'http://usefulinc.com/ns/doap#',
    'ns14': 'http://creativecommons.org/ns#',
    'dc': 'http://purl.org/dc/elements/1.1/'
    }

