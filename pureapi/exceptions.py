from requests.exceptions import RequestException, HTTPError

class PureAPIException(Exception):
    pass

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

class PureAPIResponseKeyError(KeyError, PureAPIResponseException):
    pass
