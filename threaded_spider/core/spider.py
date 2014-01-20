"""Base class for custom spiders"""
from threaded_spider.http import Request
from threaded_spider.basic import log

class BaseSpider(object):
    """Base class for user-defined spiders. All spiders *must*
    inherit from this class.
    """
    
    name = None
    
    def __init__(self, name=None, **kws):
        if name is not None:
            self.name = name
        elif not getattr(self, 'name', None):
            raise ValueError('%s must have a name' % type(self).__name__)
        
        self.__dict__.update(kws)
        if not hasattr(self, 'start_urls'):
            self.start_urls = []
        
    def attach_crawler(self, crawler):
        assert not hasattr(self, '_crawler'), 'Spider already bounded to %s' % self._crawler
        self._crawler = crawler
        
    @property
    def crawler(self):
        assert hasattr(self, '_crawler'), 'Spider not bounded to any crawler'
        return self._crawler
    
    def start_requests(self):
        for url in self.start_urls:
            yield self.make_request_from_url(url)
            
    def make_request_from_url(self, url):
        return Request(url)
    
    
    def log(self, _format, *args, **kws):
        """
        @type format: C{str}.
        @param format: The format specifier.
        @param args: The tuple of variable arguments to be formated.
        @param kws: The keyword arguments just like in C{..basic.log} module
            such as isError\log_level\failure\why,
            but must not be message\spider\format\system.
        """
        assert isinstance(_format, str), 'the first argumet must be format string of type str'
        message = _format % args
        kws['spider'] = self
        log.msg(message, **kws)
    
    #`parse` is the default callback after a response associated with a request is downloaded
    def parse(self, response):
        raise NotImplementedError
    
    def __str__(self):
        return '<%s %r at 0x%0x>' % (type(self).__class__, self.name, id(self)) 
    
    __repr__ = __str__