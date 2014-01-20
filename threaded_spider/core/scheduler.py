"""
A scheduler is used to store the Request objects which 
will be taken out to be processed by the downloader 
and spider.
"""

import Queue

from threaded_spider import logger

class Scheduler(object):
    
    def __init__(self):
        self.mq = Queue.Queue()
       
    def attach_spider(self, spider):
        self.spider = spider
        logger.info('@scheduler, Spider attached to scheduler.', spider=spider)
        
    def __len__(self):
        return self.mq.qsize()
    
    def enqueue_request(self, request):
        self.mq.put(request)
        
    def next_request(self):
        try:
            request = self.mq.get_nowait()
        except Queue.Empty, e:
            logger.debug('@scheduler, The scheduler queue is empty.', spider=self.spider)
        except Exception, e:
            logger.error(why='@scheduler, Fail to retrive data from the scheduler queue.', 
                         spider=self.spider)
        else:
            return request
        return None
    
    def has_pending_requests(self):
        return len(self)