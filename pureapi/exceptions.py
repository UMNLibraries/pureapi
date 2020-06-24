class PureAPIException(Exception):
    pass

# Deprecate this:
class PureAPIInvalidFamilyError(ValueError, PureAPIException):
    def __init__(self, *args, family, version, **kwargs):
        super().__init__(f'Invalid family "{family}" for version "{version}"', *args, **kwargs)

# Do we need this?
class PureAPIResponseException(PureAPIException):
    pass

# This may be no longer necessary...
# Deprecate this:
class PureAPIResponseKeyError(KeyError, PureAPIResponseException):
    pass
