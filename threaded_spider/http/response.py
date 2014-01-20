"""This module implements the Response class which is used 
to represent a response object in this project"""

from .common import obsolete_setter

class Response(object):
    
    ATTRS = ['url', 'status', 'body', 'headers', 'request',
             'encoding']
    
    def __init__(self, url, status=200, headers=None,
                 body=None, request=None, encoding='utf-8'):
        self._encoding = encoding
        self.headers = headers or {}
        self.status = int(status)
        self._set_url(url)
        self._set_body(body)
        self.request = request
     
    @property
    def encoding(self):
        return self._encoding
        
    def _get_url(self):
        return self._url
    
    def _set_url(self, url):
        if isinstance(url, unicode):
            self._set_url(url.encode(self.encoding))
        elif isinstance(url, str):
            self._url = url
        else:
            raise TypeError('%s url must be str or unicode, got %s' 
                            % (type(self).__name__, type(url).__name__))
        
        if ':' not in self._url:
            raise ValueError('Missing scheme in Response url: %s', self._url)
    
    url = property(_get_url, obsolete_setter(_set_url, 'url'))
    
    def _get_body(self):
        return self._body
    
    def _set_body(self, body):
        if isinstance(body, unicode):
            self._body = self._set_body(body.encode(self.encoding))
        elif isinstance(body, str):
            self._body = body
        elif body is None:
            self._body = ''
        else:
            raise TypeError('Response body must be unicode or str, got %s' % type(body).__name__)
    
            
    body = property(_get_body, obsolete_setter(_set_body, 'body'))
    
    def __str__(self):
        return '<%d %s>' % (self.status, self.url)
    
    __repr__ = __str__
    
    def copy(self):
        """Create a copy of this response."""
        return self.replace()
    
    def replace(self, *args, **kws):
        """Create a new response with the same attributes
        except for the given new values"""
        for x in self.ATTRS:
            kws.setdefault(x, getattr(self, x))
        cls = self.__class__
        return cls(*args, **kws)
    