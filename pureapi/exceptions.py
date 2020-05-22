from requests.exceptions import RequestException, HTTPError

class PureAPIException(Exception):
    pass

class PureAPIMissingDomainError(ValueError, PureAPIException):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

class PureAPIInvalidCollectionError(ValueError, PureAPIException):
    def __init__(self, *args, collection, version, **kwargs):
        super().__init__(f'Invalid collection "{collection}" for version "{version}"')

class PureAPIInvalidFamilyError(ValueError, PureAPIException):
    def __init__(self, *args, family, version, **kwargs):
        super().__init__(f'Invalid family "{family}" for version "{version}"')

class PureAPIInvalidVersionError(ValueError, PureAPIException):
    def __init__(self, *args, version, **kwargs):
        message = f'Invalid version "{version}"'
        if 'extra_message' in kwargs:
            message = f'{message} {kwargs["extra_message"]}'
        super().__init__(message)

class PureAPIClientException(PureAPIException):
    pass

class PureAPIClientHTTPError(HTTPError, PureAPIException):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

class PureAPIClientRequestException(RequestException, PureAPIException):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

class PureAPIResponseException(PureAPIException):
    pass

# This may be no longer necessary...
class PureAPIResponseKeyError(KeyError, PureAPIResponseException):
    pass
