
class ErrorBase(Exception):
    def oainame(self):
        name = self.__class__.__name__
        # strip off 'Error' part
        name = name[:-5]
        # lowercase error name
        name = name[0].lower() + name[1:]
        return name

class BadArgumentError(ErrorBase):
    pass

class BadVerbError(ErrorBase):
    pass

class BadResumptionTokenError(ErrorBase):
    pass

class CannotDisseminateFormatError(ErrorBase):
    pass

class IdDoesNotExist(ErrorBase):
    pass

class NoRecordsMatch(ErrorBase):
    pass

class NoMetadataFormats(ErrorBase):
    pass

class NoSetHierarchy(ErrorBase):
    pass
