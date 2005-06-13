import datetime

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
    # ignore microsends
    dt = dt.replace(microsecond=0)
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

class BadArgumentError(Exception):
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
                raise BadArgumentError, msg
        # first investigate if we have exclusive argument
        if dict.has_key(self._exclusive):
            if len(dict) > 1:
                msg = ("Exclusive argument %s is used but other "
                       "arguments found." % self._exclusive)
                raise BadArgumentError, msg
            return local
        # if not exclusive, check for required
        for arg_name, arg_type in argspec.items(): 
            if arg_type == 'required':
                msg = "Argument required but not found: %s" % arg_name
                if not dict.has_key(arg_name):
                    raise BadArgumentError, msg 
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

def getMethodForVerb(server, verb):
    return getattr(server, verb[0].lower() + verb[1:])

