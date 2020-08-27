class PureAPIException(Exception):
    '''Base class for pureapi exceptions.client.'''
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
