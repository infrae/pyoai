from oaipmh import client
import os.path
from urllib import urlencode
from string import zfill

class FakeServerProxy(client.BaseServerProxy):
    def __init__(self, mapping_path):
        client.BaseServerProxy.__init__(self)
        self._mapping = createMapping(mapping_path)
        
    def makeRequest(self, **kw):
        # this is a complete fake, and can only deal with a number of
        # fixed requests that are mapped to files
        # sort it to get stable behavior
        return self._mapping[getRequestKey(kw)]

def getRequestKey(kw):
    """Create stable key for request dictionary to use in file.
    """
    items = kw.items()
    items.sort()
    return urlencode(items)

def createMapping(mapping_path):
    f = open(os.path.join(mapping_path, 'mapping.txt'), 'r')
    result = {}
    while 1:
        request = f.readline()
        response = f.readline()
        request = request.strip()
        response = response.strip()
        if not request or not response:
            break
        xml_f = open(os.path.join(mapping_path, response), 'r')
        text = xml_f.read()
        xml_f.close()
        result[request] = text
    return result

class FakeCreaterServerProxy(client.ServerProxy):
    def __init__(self, base_url, mapping_path):
        client.ServerProxy.__init__(self, base_url)
        self._mapping = {}
        self._mapping_path = mapping_path
        
    def makeRequest(self, **kw):
        text = client.ServerProxy.makeRequest(self, **kw)
        self._mapping[getRequestKey(kw)] = text
        return text

    def save(self):
        mapping_path = self._mapping_path
        f = open(os.path.join(mapping_path, 'mapping.txt'), 'w')
        i = 0
        for request, response in self._mapping.items():
            f.write(request)
            f.write('\n')
            filename = zfill(str(i), 5) + '.xml'
            f.write(filename)
            f.write('\n')
            response_f = open(os.path.join(mapping_path, filename), 'w')
            response_f.write(response)
            response_f.close()
            i += 1
        f.close()
