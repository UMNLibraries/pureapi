from requests.exceptions import RequestException

class PureAPIException(Exception):
  pass

class PureAPIClientException(PureAPIException):
  pass

class PureAPIClientRequestException(RequestException, PureAPIException):
  pass

class PureAPIResponseException(PureAPIException):
  pass

class PureAPIResponseKeyError(KeyError, PureAPIResponseException):
  pass
