
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

class IdDoesNotExistError(ErrorBase):
    pass

class NoRecordsMatchError(ErrorBase):
    pass

class NoMetadataFormatsError(ErrorBase):
    pass

class NoSetHierarchyError(ErrorBase):
    pass
