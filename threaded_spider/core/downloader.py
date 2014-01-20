"""Downloader to send a request to get a response."""
import urllib2
import socket
socket.setdefaulttimeout(60)
import gzip

from threaded_spider import logger
from threaded_spider.basic.compat import NativeStringIO
from threaded_spider.http import Response, Request

class Downloader(object):
    
    def __init__(self, crawler):
        self.settings = crawler.settings
        self.active = []
    
    def fetch(self, request, spider):
        try:
            self.active.append(request)
            response = self._download(request)
            return response
        except Exception, e:
            logger.error(why='@downloader, fetch %s failed' % request, spider=spider)
        finally:
            self.active.remove(request)
        
    def _download(self, request):
        # Exceed the depth limit for crawler settings, return None to ignore.
        if self.settings.get('MAX_DEPTH', 0) == 0:
            pass
        elif request.depth > self.settings.get('MAX_DEPTH', 0):
            return None
        
        url_file = urllib2.urlopen(request.url)
        is_gzip = False
        cont_encode = url_file.headers.get('content-encoding', False)
        if cont_encode == 'gzip':
            is_gzip = True
            
        data = url_file.read()
        if is_gzip:
            data = self._ungzip(data)
        
        resp = Response(url_file.geturl(), status=url_file.getcode(), 
                        headers=dict(url_file.headers.items()),
                        body=data, request=request
                        )
        return resp
        
    def _ungzip(self, data): 
        stream = NativeStringIO()
        stream.write(data)
        stream.seek(0)
        gzipper = gzip.GzipFile(fileobj=stream)
        data = gzipper.read()
        return data
    
    def has_pending_download(self):
        return len(self.active) 
