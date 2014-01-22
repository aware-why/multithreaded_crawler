"""This module define the base class for processing Item
objects yielded by spiders"""


class ItemProc(object):
    
    class SpiderInfo(object):
        def __init__(self, spider):
            self.spider = spider
    
    @classmethod
    def from_crawler(cls, crawler):
        try:
            proc = cls.from_settings(crawler.settings)
        except AttributeError:
            proc = cls()
        proc.crawler = crawler
        return proc
            
    def __init__(self, download_func=None):
        self.download_func = download_func
    
    def attach_spider(self, spider):
        self.spider_info = self.SpiderInfo(spider)
    
    def detach_spider(self):
        pass
    
    def process_item(self, item):
        """
        Do what you want to deal with the item,
        you could perserve it in the disk and others.
        """
        spider_info = self.spider_info
        self.pre_process(item, spider_info)
        self._process_item(item, spider_info)
        self.post_process(item, spider_info)
    
    def pre_process(self, item, spider_info):
        """You *may* override this method."""
        pass
        
    def _process_item(self, item, spider_info):
        """You *must* overidde this method to do your
        custom things."""
        pass
    
    def post_process(self, item, spider_info):
        """You *may* override this method."""
        pass
    
    