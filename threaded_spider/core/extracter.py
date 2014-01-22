"""After downloaded, spider parse the response from which items are extracted 
and then items are processed by the ItemProcessor.
"""

from threaded_spider.basic.util import load_object 
from threaded_spider.http import Request
from threaded_spider.core.item import BaseItem
from threaded_spider import logger

class Extracter(object):
    
    def __init__(self, crawler):
        itemproc_cls = load_object(crawler.settings.get('ITEM_PROCESSOR'))
        self.itemproc = itemproc_cls.from_crawler(crawler)
        self.crawler = crawler
        self.active_response = []
    
    def attach_spider(self, spider):
        self.itemproc.attach_spider(spider)
    
    def detach_spider(self):
        self.itemproc.detach_spider()
    
    def has_pending_response(self):
        return len(self.active_response)
    
    def enter_extracter(self, response, request, spider):
        try:
            self.active_response.append(response)
            
            spider_output = self.call_spider(response, request, spider)
            for item in spider_output:
                if isinstance(item, Request):
                    self.crawler.engine.schedule_later(item, spider)
                elif isinstance(item, BaseItem):
                    self.itemproc.process_item(item)
                elif item is None:
                    pass
                else:
                    logger.error(format='Spider must return request, BaseItem or None,'
                            ' got %(type)r in %(request)s',
                            spider=spider, request=request)
        finally:
            self.active_response.remove(response)
                
    
    def call_spider(self, response, request, spider):
        parse_response = request.callback or spider.parse
        parsed_resp = parse_response(response)
        for item in parsed_resp:
            yield item