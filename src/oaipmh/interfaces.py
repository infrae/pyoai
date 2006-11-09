class IOAI:
    def getRecord(metadataPrefix, identifier):
        """Get a record for a metadataPrefix and identifier.

        metadataPrefix - identifies metadata set to retrieve
        identifier - repository-unique identifier of record
        
        Should raise error.CannotDisseminateFormatError if
        metadataPrefix is unknown or not supported by identifier.
        
        Should raise error.IdDoesNotExistError if identifier is
        unknown or illegal.

        Returns a header, metadata, about tuple describing the record.
        """

    def identify():
        """Retrieve information about the repository.

        Returns an Identify object describing the repository.
        """

    def listIdentifiers(metadataPrefix, set=None, from_=None, until=None):
        """Get a list of header information on records.

        metadataPrefix - identifies metadata set to retrieve
        set - set identifier; only return headers in set (optional)
        from_ - only retrieve headers from from_ date forward (optional)
        until - only retrieve headers with dates up to and including
                until date (optional)

        Should raise error.CannotDisseminateFormatError if metadataPrefix
        is not supported by the repository.

        Should raise error.NoSetHierarchyError if the repository does not
        support sets.
        
        Returns an iterable of headers.
        """
        
    def listMetadataFormats(identifier=None):
        """List metadata formats supported by repository or record.

        identifier - identify record for which we want to know all
                     supported metadata formats. if absent, list all metadata
                     formats supported by repository. (optional)


        Should raise error.IdDoesNotExistError if record with
        identifier does not exist.
        
        Should raise error.NoMetadataFormatsError if no formats are
        available for the indicated record.

        Returns an iterable of metadataPrefix, schema, metadataNamespace
        tuples (each entry in the tuple is a string).
        """
        
    def listRecords(metadataPrefix, set=None, from_=None, until=None):
        """Get a list of header, metadata and about information on records.

        metadataPrefix - identifies metadata set to retrieve
        set - set identifier; only return records in set (optional)
        from_ - only retrieve records from from_ date forward (optional)
        until - only retrieve records with dates up to and including
                until date (optional)

        Should raise error.CannotDisseminateFormatError if metadataPrefix
        is not supported by the repository.

        Should raise error.NoSetHierarchyError if the repository does not
        support sets.

        Returns an iterable of header, metadata, about tuples.
        """

    def listSets():
        """Get a list of sets in the repository.

        Should raise error.NoSetHierarchyError if the repository does not
        support sets.

        Returns an iterable of setSpec, setName tuples (strings).
        """
        
class IBatchingOAI:
    """Very similar to IOAI, but the implementation can be batch-aware.

    Methods that support resumption will get two extra arguments,
    cursor and batch_size, which indicate the batch currently being
    requested.
    """
    
    def getRecord(metadataPrefix, identifier):
        pass
    
    def identify():
        pass
    
    def listIdentifiers(metadataPrefix, set=None, from_=None, until=None,
                        cursor=0, batch_size=10):
        pass
    
    def listMetadataFormats(identifier=None):
        pass
    
    def listRecords(metadataPrefix, set=None, from_=None, until=None,
                    cursor=0, batch_size=10):
        pass
    
    def listSets():
        pass
    
class IIdentify:
    def repositoryName():
        """Name of repository.
        """

    def baseURL():
        """Base URL for OAI-PMH requests.
        """

    def protocolVersion():
        """OAI-PMH protocol version (should always be '2.0')
        """

    def adminEmails():
        """List of email addresses of repository administrators.
        """

    def earliestDateStamp():
        """The datetime (datestamp) of the earliest record in repository.
        """

    def deletedRecord():
        """Way the repository handles deleted records.

        Either 'no', 'transient' or 'persistent'.
        """

    def granularity():
        """Datetime granularity of datestamps in repository.

        Either YYYY-MM-DD or YYYY-MM-DDThh:mm:ssZ
        """

    def compression():
        """List of types of compression schemes supported by repository.

        'identity' is the 'do-nothing' scheme.
        """
        
class IHeader:
    def identifier():
        """Repository-unique identifier of this record.
        """

    def datestamp():
        """Datetime of creation, last modification or deletion of the record.

        This can be used for selective harvesting.
        """

    def setSpec():
        """A list of sets this record is a member of.
        """

    def isDeleted():
        """If true, record has been deleted.
        """
