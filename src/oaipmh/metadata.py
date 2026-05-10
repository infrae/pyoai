import sys

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
        # Alias for element.xpath
        e = element.xpath
        for field_name, (field_type, expr) in list(self._fields.items()):
            try:
                # The core logic is to safely handle the result from xpath()
                raw_result = e(expr, namespaces=self._namespaces)

                value = None
                if field_type == 'bytes':
                    value = str(raw_result)
                elif field_type == 'bytesList':
                    # Ensure the result is iterable before the list comprehension
                    value = [str(item) for item in (raw_result if isinstance(raw_result, list) else [raw_result])]
                elif field_type == 'text':
                    value = text_type(raw_result)
                elif field_type == 'textList':
                    # This is the critical part to fix the error
                    if isinstance(raw_result, list):
                        # This handles the expected case: a list of elements/strings
                        value = [text_type(v) for v in raw_result]
                    elif raw_result is not None:
                        # This handles a single value being returned
                        value = [text_type(raw_result)]
                    else:
                        # Handles cases with no result (None)
                        value = []
                else:
                    raise Error("Unknown field type: %s" % field_type)

                map[field_name] = value
            except Exception as ex:
                # A robust way to prevent crashes
                print(f"Warning: Error processing field '{field_name}' with expression '{expr}': {ex}", file=sys.stderr)
                if field_type.endswith('List'):
                    map[field_name] = []
                else:
                    map[field_name] = ""

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
