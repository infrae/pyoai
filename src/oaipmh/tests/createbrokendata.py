from fakeclient import FakeCreaterClient
from datetime import datetime
from oaipmh import metadata

registry = metadata.MetadataRegistry()
registry.registerReader('oai_dc', metadata.oai_dc_reader)
# tied to the server at EUR..
client = FakeCreaterClient(
    'http://ep.eur.nl/oai/request',
    '/home/faassen/tmp/fake3',
    registry
    )

#print "GetRecord"
#header, metadata, about = client.getRecord(
#    metadataPrefix='oai_dc', identifier='hdl:1765/315')
#print "identifier:", header.identifier()
#print "datestamp:", header.datestamp()
#print "setSpec:", header.setSpec()
#print "isDeleted:", header.isDeleted()
#print

print "Identify"
identify = client.identify()
print "repositoryName:", identify.repositoryName()
print "baseURL:", identify.baseURL()
print "protocolVerson:", identify.protocolVersion()
print "adminEmails:", identify.adminEmails()
print "earliestDatestamp:", identify.earliestDatestamp()
print "deletedRecords:", identify.deletedRecord()
print "granularity:", identify.granularity()
print "compression:", identify.compression()
print

print "ListIdentifiers"
headers = client.listIdentifiers(from_=datetime(2006, 02, 8),
                                 metadataPrefix='oai_dc')
for header in headers:
    print "identifier:", header.identifier()
    print "datestamp:", header.datestamp()
    print "setSpec:", header.setSpec()
    print "isDeleted:", header.isDeleted()
print

print "ListMetadataFormats"
for prefix, schema, ns in client.listMetadataFormats():
    print "metadataPrefix:", prefix
    print "schema:", schema
    print "metadataNamespace:", ns
print

print "ListRecords"
for header, metadata, about in client.listRecords(
    from_=datetime(2006, 02, 8), metadataPrefix='oai_dc'):
    print "header"
    print "identifier:", header.identifier()
    print "datestamp:", header.datestamp()
    print "setSpec:", header.setSpec()
    print "isDeleted:", header.isDeleted()
    #print "metadata"
    #for fieldname in fieldnames:
    #    print "%s:" % fieldname, metadata.getField(fieldname)
    print "about"
    print about
print

print "ListSets"
for setSpec, setName, setDescription in client.listSets():
    print "setSpec:", setSpec
    print "setName:", setName
    print "setDescription:", setDescription
print

client.save()
