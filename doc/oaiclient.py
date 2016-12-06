import sys

from oaipmh.client import Client
from oaipmh.metadata import MetadataRegistry, oai_dc_reader

URL = sys.argv[1]
METADATA_PREFIX = sys.argv[2]
if len(sys.argv) == 4:
    SETSPEC = sys.argv[3]
else:
    SETSPEC = None
                       


registry = MetadataRegistry()
registry.registerReader('oai_dc', oai_dc_reader)
registry.registerReader(METADATA_PREFIX, oai_dc_reader)

client = Client(URL, registry)

record_count = 0
deleted_count = 0

if SETSPEC:
    records = client.listRecords(metadataPrefix=METADATA_PREFIX, set=SETSPEC)
else:
    records = client.listRecords(metadataPrefix=METADATA_PREFIX)

for num, record in enumerate(records):
    record_count += 1
    delinfo = ''
    if record[0].isDeleted():
        deleted_count += 1
        delinfo = '(deleted)'
    print('%0.6d %s %s' % (num, record[0].identifier(), delinfo))
    print('       %s' % ';'.join(record[0].setSpec()))

print('Harvested %s records, of which %s were deleted' % (record_count,
                                                          deleted_count))
    





