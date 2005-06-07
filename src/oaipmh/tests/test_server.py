import unittest
import os
from oaipmh import server, client, common
from lxml import etree
from datetime import datetime
import fakeserver

NS_OAIPMH = server.NS_OAIPMH

def fileInTestDir(name):
    _testdir = os.path.split(__file__)[0]
    return os.path.join(_testdir, name)

# load up schema
oaischema = etree.XMLSchema(etree.parse(fileInTestDir('OAI-PMH.xsd')))

class ClientServerProxy(client.BaseServerProxy):
    """A proxy that connects directly to a server object.
    """
    
    def __init__(self, server, metadataSchemaRegistry=None):
        self._server = server
        
    def makeRequest(self, **kw):
        if kw.has_key('from'):
            kw['from_'] = kw['from']
            del kw['from']
        verb = kw.pop('verb')
        verb = verb[0].lower() + verb[1:]
        return getattr(self._server, verb)(**kw)

class SimpleServer(server.Server):
    def _getEarliestDatestamp(self):
        return datetime(1953, 1, 1, 0, 0)

class ServerTestCase(unittest.TestCase):
        
    def test_identify(self):
        simple_server = SimpleServer(
            'TestRepository', 'http://www.infrae.com/oai',
            ['faassen@infrae.com'])
        
        xml_server = server.XMLServer(simple_server)
        tree = xml_server.identify_tree()
        self.assert_(oaischema.validate(tree))
        #etree.dump(tree.getroot())
        
    def test_identify2(self):
        directory = os.path.dirname(__file__)
        fake1 = os.path.join(directory, 'fake1')
        myserver = fakeserver.FakeServerProxy(fake1)

        xml_server = server.XMLServer(myserver)
        tree = xml_server.identify_tree()
        self.assert_(oaischema.validate(tree))
        #etree.dump(tree.getroot())
        
    def test_two(self):
        pass
    

def test_suite():
    return unittest.TestSuite((unittest.makeSuite(ServerTestCase), ))

if __name__=='__main__':
    main(defaultTest='test_suite')
