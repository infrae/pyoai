
#
class BadArgumentError(Exception):
    pass

def validate(argspec, dict):
    exclusive = None
    for arg_name, arg_type in argspec.items():
        if arg_type == 'exclusive':
            exclusive = arg_name
    # check if we have unknown arguments
    for key, value in dict.items():
        if not argspec.has_key(key):
            msg = "Unknown argument: %s" % key
            raise BadArgumentError, msg
    # first investigate if we have exclusive argument
    if dict.has_key(exclusive):
        if len(dict) > 1:
            msg = ("Exclusive argument %s is used but other "
                   "arguments found." % exclusive)
            raise BadArgumentError, msg
        return
    # if not exclusive, check for required
    for arg_name, arg_type in argspec.items(): 
        if arg_type == 'required':
            msg = "Argument required but not found: %s" % arg_name
            if not dict.has_key(arg_name):
                raise BadArgumentError, msg 
    return
        
class ValidationSpec(object):
    GetRecord = {
        'identifier':'required',
        'metadataPrefix':'required'
        }
    
    Identify = {
        }

    ListIdentifiers = {
        'from_':'optional',
        'until':'optional',
        'metadataPrefix':'required',
        'set':'optional',
        }

    ListMetadataFormats = {
        'identifier':'optional'
        }

    ListRecords = {
        'from_':'optional',
        'until':'optional',
        'set':'optional',
        'metadataPrefix':'required',
        }

    ListSets = {
        }

class ResumptionValidationSpec(ValidationSpec):

    ListIdentifiers = {
        'from_':'optional',
        'until':'optional',
        'metadataPrefix':'required',
        'set':'optional',
        'resumptionToken':'exclusive',
        }
    
    ListRecords = {
        'from_':'optional',
        'until':'optional',
        'set':'optional',
        'metadataPrefix':'required',
        'resumptionToken':'exclusive',
        }

    ListSets = {
        'resumptionToken':'exclusive',
        }

def validateArguments(verb, kw):
    validate(getattr(ValidationSpec, verb), kw)

def validateResumptionArguments(verb, kw):
    validate(getattr(ResumptionValidationSpec, verb), kw)
    
