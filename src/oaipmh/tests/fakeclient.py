from oaipmh import client, common
import os.path
from datetime import datetime
try:
    from urllib.parse import urlencode
except ImportError:
    from urllib import urlencode


class FakeClient(client.BaseClient):
    def __init__(self, mapping_path, custom_retry_policy=None):
        client.BaseClient.__init__(self, custom_retry_policy=custom_retry_policy)
        self._mapping = createMapping(mapping_path)

    def makeRequest(self, **kw):
        # this is a complete fake, and can only deal with a number of
        # fixed requests that are mapped to files
        # sort it to get stable behavior
        return self._mapping[getRequestKey(kw)]

class TestError(Exception):
    def __init__(self, kw):
        self.kw = kw

class GranularityFakeClient(client.BaseClient):
    def __init__(self, granularity):
        client.BaseClient.__init__(self)
        self._granularity = granularity

    def makeRequest(self, **kw):
        # even more fake, we'll simply raise an exception with the request
        # this can be caught by the test to see whether the request uses
        # day granularity..
        raise TestError(kw)

    def identify(self):
        return common.Identify(
            'Foo', 'http://test.info', '2.0', ['foo@bar.com'],
            datetime(2005, 1, 1), 'no', self._granularity,
            None)

def getRequestKey(kw):
    """Create stable key for request dictionary to use in file.
    """
    items = list(kw.items())
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

class FakeCreaterClient(client.Client):
    def __init__(self, base_url, mapping_path, metadata_registry):
        client.Client.__init__(self, base_url, metadata_registry)
        self._mapping = {}
        self._mapping_path = mapping_path

    def makeRequest(self, **kw):
        text = client.Client.makeRequest(self, **kw)
        self._mapping[getRequestKey(kw)] = text
        return text

    def save(self):
        mapping_path = self._mapping_path
        f = open(os.path.join(mapping_path, 'mapping.txt'), 'w')
        i = 0
        for request, response in self._mapping.items():
            f.write(request)
            f.write('\n')
            filename = str(i).zfill(5) + ".xml"
            f.write(filename)
            f.write('\n')
            response_f = open(os.path.join(mapping_path, filename), 'w')
            response_f.write(response)
            response_f.close()
            i += 1
        f.close()
