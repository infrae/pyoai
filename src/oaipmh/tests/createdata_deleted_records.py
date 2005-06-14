from fakeserver import FakeCreaterServerProxy

# tied to the server at EUR..
server = FakeCreaterServerProxy(
    'http://dspace.ubib.eur.nl/oai/',
    '/home/eric/CVS_checkouts/oai/tests/fake2')

#deleted record
print "GetRecord"
header, metadata, about = server.getRecord(
    metadataPrefix='oai_dc', identifier='hdl:1765/1160')
print "identifier:", header.identifier()
print "datestamp:", header.datestamp()
print "setSpec:", header.setSpec()
print "isDeleted:", header.isDeleted()
print

#normal record
print "GetRecord"
header, metadata, about = server.getRecord(
    metadataPrefix='oai_dc', identifier='hdl:1765/1162')
print "identifier:", header.identifier()
print "datestamp:", header.datestamp()
print "setSpec:", header.setSpec()
print "isDeleted:", header.isDeleted()
print

print "ListRecords"
for header, metadata, about in server.listRecords(
    from_=datetime(2004, 01, 01), until=datetime(2004, 02, 01),
    metadataPrefix='oai_dc'):
    print "header"
    print "identifier:", header.identifier()
    print "datestamp:", header.datestamp()
    print "setSpec:", header.setSpec()
    print "isDeleted:", header.isDeleted()
    print "metadata"
    if metadata is not None:
        for fieldname in metadata.getMap().keys():
            print "%s:" % fieldname, metadata.getField(fieldname)
    print "about"
    print about
print

server.save()
