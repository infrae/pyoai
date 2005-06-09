import datetime
from urllib import urlencode
import cgi

class Header:
    def __init__(self, identifier, datestamp, setspec, deleted):
        self._identifier = identifier
        self._datestamp = datestamp
        self._setspec = setspec
        self._deleted = deleted
        
    def identifier(self):
        return self._identifier
    
    def datestamp(self):
        return self._datestamp

    def setSpec(self):
        return self._setspec

    def isDeleted(self):
        return self._deleted

class Metadata:
    def __init__(self, map):
        self._map = map

    def getMap(self):
        return self._map
    
    def getField(self, name):
        return self._map[name]

    __getitem__ = getField
    
class ServerIdentify:
    def __init__(self, repositoryName, baseURL, protocolVersion, adminEmails,
                 earliestDatestamp, deletedRecord, granularity, compression):
        self._repositoryName = repositoryName
        self._baseURL = baseURL
        self._protocolVersion = protocolVersion
        self._adminEmails = adminEmails
        self._earliestDatestamp = earliestDatestamp
        self._deletedRecord = deletedRecord
        self._granularity = granularity
        self._compression = compression
        # XXX description
        
    def repositoryName(self):
        return self._repositoryName

    def baseURL(self):
        return self._baseURL

    def protocolVersion(self):
        return self._protocolVersion

    def adminEmails(self):
        return self._adminEmails

    def earliestDatestamp(self):
        return self._earliestDatestamp

    def deletedRecord(self):
        return self._deletedRecord

    def granularity(self):
        return self._granularity

    def compression(self):
        return self._compression

def datetime_to_datestamp(dt):
    return dt.isoformat() + 'Z'
    
def datestamp_to_datetime(datestamp):
    splitted = datestamp.split('T')
    if len(splitted) == 2:
        d, t = splitted
        # strip off 'Z'
        t = t[:-1]
    else:
        d = splitted[0]
        t = '00:00:00'
    YYYY, MM, DD = d.split('-')
    hh, mm, ss = t.split(':')
    return datetime.datetime(
        int(YYYY), int(MM), int(DD),
        int(hh), int(mm), int(ss))

class ArgumentValidationError(Exception):
    pass

class ArgumentValidator:
    
    def __init__(self, argspec):
        self._argspec = argspec
        self._exclusive = None
        for arg_name, arg_type in argspec.items():
            if arg_type == 'exclusive':
                self._exclusive = arg_name

    def validate(self, dict):
        argspec = self._argspec
        # first filter out any local arguments, which will be returned
        local = {}
        for arg_name, arg_type in argspec.items():
            if arg_type == 'local' and dict.has_key(arg_name):
                local[arg_name] = dict[arg_name]
                del dict[arg_name]
        # check if we have unknown arguments
        for key, value in dict.items():
            if not argspec.has_key(key):
                msg = "Unknown argument: %s" % key
                raise ArgumentValidationError, msg
        # first investigate if we have exclusive argument
        if dict.has_key(self._exclusive):
            if len(dict) > 1:
                msg = ("Exclusive argument %s is used but other "
                       "arguments found." % self._exclusive)
                raise ArgumentValidationError, msg
            return local
        # if not exclusive, check for required
        for arg_name, arg_type in argspec.items(): 
            if arg_type == 'required':
                msg = "Argument required but not found: %s" % arg_name
                if not dict.has_key(arg_name):
                    raise ArgumentValidationError, msg 
        return local

class OAIMethodImpl(object):
    def __init__(self, verb, argspec):
        self._verb = verb
        self._validator = ArgumentValidator(argspec)

    def __call__(self, bound_self, **kw):
        if kw.has_key('from_'):
            kw['from'] = kw['from_']
            del kw['from_']
        local = self._validator.validate(kw)
        # reconstruct all arguments (including local)
        args = kw.copy()
        args.update(local)
        # now call handler
        return bound_self.handleVerb(self._verb, args, kw)

def OAIMethod(verb, argspec):
    obj = OAIMethodImpl(verb, argspec)
    def method(self, **kw):
        return obj(self, **kw)
    return method

class OAIPMH:
    """Mixin that implements the Python-level OAI-PMH interface.

    It does not include resumptionToken handling.

    It validates method calls and passes them on to the 'handleVerb'
    method, which should be overridden in a subclass.
    """
    def handleVerb(self, verb, args, kw):
        raise NotImplementedError

    getRecord = OAIMethod(
        'GetRecord',
        {'identifier':'required',
        'metadataPrefix':'required'},
        )
    
    identify = OAIMethod(
        'Identify',
        {},
        )

    listIdentifiers = OAIMethod(
        'ListIdentifiers',
        {'from':'optional',
         'until':'optional',
         'metadataPrefix':'required',
         'set':'optional',
         },
        )

    listMetadataFormats = OAIMethod(
        'ListMetadataFormats',
        {'identifier':'optional'},
        )

    listRecords = OAIMethod(
        'ListRecords',
        {'from':'optional',
         'until':'optional',
         'set':'optional',
         'metadataPrefix':'required',
         },
        )

    listSets = OAIMethod(
        'ListSets',
        {},
        )

class ResumptionOAIPMH:
    """Mixin that implements the Resumption-capable OAI-PMH interface.

    It validates method calls and passes them on to the 'handleVerb'
    method, which should be overridden in a subclass.

    The listIdentifiers, listSets and listRecords methods return
    tuples of a list and resumptionToken. If the resumptionToken
    returned is None, this indicates the end of the list is reached.
    """

    def handleVerb(self, verb, args, kw):
        raise NotImplementedError
    
    getRecord = OAIMethod(
        'GetRecord',
        {'identifier':'required',
        'metadataPrefix':'required'},
        )
    
    identify = OAIMethod(
        'Identify',
        {},
        )

    listIdentifiers = OAIMethod(
        'ListIdentifiers',
        {'from':'optional',
         'until':'optional',
         'metadataPrefix':'required',
         'set':'optional',
         'resumptionToken':'exclusive',
         },
        )

    listMetadataFormats = OAIMethod(
        'ListMetadataFormats',
        {'identifier':'optional'},
        )

    listRecords = OAIMethod(
        'ListRecords',
        {'from':'optional',
         'until':'optional',
         'set':'optional',
         'resumptionToken':'exclusive',
         'metadataPrefix':'required',
         },
        )

    listSets = OAIMethod(
        'ListSets',
        {'resumptionToken':'exclusive',
         },
        )

class Resumption(ResumptionOAIPMH):
    """There are two interfaces:

    OAIPMH

    ResumptionOAIPMH

    The Resumption class can turn a plain OAIPMH interface into
    a ResumptionOAIPMH interface

    This implementation is not particularly efficient for large
    result sets, as the complete result set needs to be reconstructed each
    time.
    """
    def __init__(self, server, batch_size=10):
        self._server = server
        self._batch_size = batch_size

    def encodeResumptionToken(self, kw, cursor):
        kw = kw.copy()
        kw['cursor'] = str(cursor)
        return urlencode(kw)

    def decodeResumptionToken(self, token):
        kw = cgi.parse_qs(token, True)
        result = {}
        for key, value in kw.items():
            result[key] = value[0]
        cursor = int(result.pop('cursor'))
        return result, cursor
    
    def handleVerb(self, verb, args, kw):
        # do original query
        method_name = verb[0].lower() + verb[1:]
        # if we're handling a resumption token
        if 'resumptionToken' in kw:
            kw, cursor = self.decodeResumptionToken(
                kw['resumptionToken'])
            end_batch = cursor + self._batch_size
            # do query again with original parameters
            result = getattr(self._server, method_name)(**kw)
            # XXX defeat laziness of any generators..
            result = list(result)
            if end_batch < len(result):
                resumptionToken = self.encodeResumptionToken(
                    kw, end_batch)
            else:
                resumptionToken = None
            return result[cursor:end_batch], resumptionToken
        # we're not handling resumption token, so do request
        result = getattr(self._server, method_name)(**kw)
        # now handle resumption system
        if verb in ['ListSets', 'ListIdentifiers', 'ListRecords']:
            # XXX defeat the laziness effect of any generators..
            result = list(result)
            end_batch = self._batch_size
            if end_batch < len(result):
                resumptionToken = self.encodeResumptionToken(
                    kw, end_batch)
            else:
                resumptionToken = None
            return result[0:end_batch], resumptionToken
        return result
