
import unittest
from oaipmh import server, client, common
from lxml import etree

NS_OAIPMH = server.NS_OAIPMH

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
        
class ServerTestCase(unittest.TestCase):
    def setUp(self):
        pass # serlf.server = MyServer()
        
    def test_output(self):
        simple_server = server.Server(
            'TestRepository', 'http://www.infrae.com/oai',
            ['faassen@infrae.com'])
        
        xml_server = server.XMLServer(simple_server)
        print xml_server.identify()
    
        #element = etree.Element('top')
        #header = common.Header(
        #    'foo', '2003-04-29T15:57:01Z', ['a', 'b'], False)
        #server.outputHeader(element, header)
        #etree.dump(element)
        
    def test_two(self):
        pass
    

def test_suite():
    return unittest.TestSuite((unittest.makeSuite(ServerTestCase), ))

if __name__=='__main__':
    main(defaultTest='test_suite')
