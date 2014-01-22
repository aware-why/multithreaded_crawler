"""Customize a spider for search the web pages whose text contains the specific
key words.
"""
import BeautifulSoup  

from threaded_spider.http import Request
from threaded_spider.core.spider import BaseSpider
from threaded_spider.basic.util import unicode_to_str, make_utf8
from threaded_spider.keyword_item import Item

class KeyWordSpider(BaseSpider):
    """Search key words in a html document"""
    
    def __init__(self, name, start_urls=[]):
        super(KeyWordSpider, self).__init__(name, start_urls=start_urls)
     
     
    def extract_links(self, html_url, html_content):
        def canonicalize_href(base_url, href):
            if not href:
                return
            
            if href.startswith('http://'):
                return href
            elif href.startswith('/'):
                return base_url + href
            elif href.find('javascript') != -1:
                return
            else:
                return base_url + '/' + href
          
        soup = BeautifulSoup.BeautifulSoup(html_content)
        hrefs = set() 
        for link_info in soup.fetch('a'):  
            href = unicode_to_str(link_info.get('href', None))
            href = canonicalize_href(html_url, href)
            if not href or href in hrefs:
                    continue
            else:
                yield href
                hrefs.add(href)           
    
    def need_detatch(self):
        return self.crawler.stopped
    
    def parse(self, response):
        html_url = response.url
        html_content = unicode_to_str(response.body)
        depth = response.request.depth
        
        if -1 == html_content.find('</'):
            self.log('%s html has invalid header: %r', response, html_content[:200],
                     log_level='WARN')
            return
        
        if self.crawler.settings.get('MAX_DEPTH', 0) == 0:
            pass
        elif depth >= self.crawler.settings.get('MAX_DEPTH', 0):
            pass
        else: 
            for link in self.extract_links(html_url, html_content):
                print 'Schedule link: %r' % link
                yield Request(url=link, depth=depth + 1)
        
        item = Item()
        item['html_content'] = html_content
        item['depth'] = depth 
        item['self_url'] = html_url   
        yield item