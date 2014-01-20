# -*- coding: utf-8 -*-
"""
This module implements the Request class which is
used to represent a request object in this project.
"""

from .common import obsolete_setter

class Request(object):
    # Attributes of body and url must be type of str, or else, will raise UnicodeEncodeError 
    # when recording an object containg Request formated by `%s` to the log file.
    # such as follows(`ascii` is the default system encoding):
    #     >>> z
    #     u'123 \u65e5\u5b98\u65b910\u4f73\u7403'
    #     >>> z.encode()
    #     Traceback (most recent call last):
    #      File "<stdin>", line 1, in <module>
    #     UnicodeEncodeError: 'ascii' codec can't encode characters in position 4-6: 
    #     ordinal not in range(128)
    #     >>> z.encode('gbk')
    #     '123 \xc8\xd5\xb9\xd9\xb7\xbd10\xbc\xd1\xc7\xf2'
    #     >>> print z.encode('gbk')
    #     123 日官方10佳球

    ATTRS = ['url', 'method', 'headers', 'body', 'calback',
             'depth', 'encoding']
    
    def __init__(self, url, callback=None, method='GET',
                 headers=None, body=None, depth=1, encoding='utf-8'):
        self._encoding = encoding
        self.method = str(method).upper()
        self._set_url(url)
        self._set_body(body)
        self.headers = headers or {}
        self.callback = callback
        self.depth = depth
    
    def _get_url(self):
        return self._url
    
    def _set_url(self, url):
        if isinstance(url, unicode):
            self._set_url(url.encode(self.encoding))
        elif isinstance(url, str):
            self._url = url
        else:
            raise TypeError('Request url must be unicode or str, got %s' % type(url).__name__)
            
        if ':' not in self._url:
            raise ValueError('Missing scheme in request url: %s' % self._url)   
    
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
            raise TypeError('Request body must be unicode or str, got %s' % type(body).__name__)
    
    body = property(_get_body, obsolete_setter(_set_body, 'body'))
    
    @property
    def encoding(self):
        return self._encoding
    
    def __str__(self):
        return "<%s %s>" % (self.method, self.url)
    
    __repr__ = __str__
    
    def copy(self):
        """return a copy of this request"""
        return self.replace()
    
    def replace(self, *args, **kws):
        """
        Create a new Request object with the same attributes 
        except for those given new values.
        """
        for x in self.ATTRS:
            kws.setdefault(x, getattr(self, x))
        cls = self.__class__
        return cls(*args, **kws)