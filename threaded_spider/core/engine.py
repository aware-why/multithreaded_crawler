"""
This module implements the engine which controls
the Scheduler, Downloader and Spider.
"""
import time

from threaded_spider import logger
from threaded_spider.basic.threadpool import ThreadPool    
from threaded_spider.http import Request, Response
from threaded_spider.core.downloader import Downloader
from threaded_spider.core.scheduler import Scheduler

class Engine(object):
    
    def __init__(self, crawler):
        self.crawler = crawler
        self.settings = crawler.settings
        self.downloader = Downloader(crawler)
        self.scheduler = Scheduler()
        self.requests_to_be_scheduled = []
        self.thread_pool = ThreadPool(minthreads=self.settings.getint('THREAD_NUM', 7),
                                      maxthreads=self.settings.getint('THREAD_NUM', 7),
                                      name='engine_threadpool')
        self.spider = None
        self.running = False
        
    def start(self):
        """Start the execution engine"""
        
        assert not self.running, 'Engine already running.'
        
        self.start_time = time.time()
        self.running = True
        self.thread_pool.start()
        
    def stop(self, force=False):
        """Stop the execution engine gracefully"""
        
        assert self.running, 'Engine not running.'
        logger.info('@engine, stopping...')
        # Stop the threadpool and close spider.
        self.thread_pool.stop()
        self.thread_pool.dumpStats()
        self.running = False
        logger.info('@engine, stopped.')
        logger.info('@engine, unscheduled: %s' % len(self.requests_to_be_scheduled))
        logger.debug('@engine, unscheduled: %r' % self.requests_to_be_scheduled)
        logger.info('@engine, in scheduler: %s' % self.scheduler.mq.qsize())
        logger.debug('@engine, in scheduler: %r' % self.scheduler.mq.queue)
        logger.info('@engine, in downloader: %s' % self.downloader.has_pending_download())
    
    def attach_spider(self, spider, start_requests=()):
        """Attach a spider to the engine."""
        logger.info('@engine, Spider attached to engine.', spider=spider)
        self.spider = spider
        if callable(start_requests):
            start_requests = start_requests()
        self._start_requests = iter(start_requests)
        
        self.scheduler.attach_spider(spider)
        
    def process_next_request(self, spider):
        self._process_next_request(spider)    
          
    def _process_next_request(self, spider):
        """Grab a request object from scheduler and then download a 
        response object which is parsed by the spider.
        """
        request = self._process_next_request_from_scheduler(spider)
        
        if not request and self._start_requests:
            try:
                request = next(self._start_requests)
            except StopIteration:
                self._start_requests = None
            except Exception:
                logger.error(why='@engine, Fail to obtain request from start requests.',
                             spider=spider)
            else:
                logger.info('@engne, schedule a request from start_urls', spider=spider)
                self._schedule(request, spider)
        
        if self.spider_is_idle(spider):
            logger.info('@engine, Spider is idle.', spider=spider)
            self._spider_idle(spider)
                
    def _process_next_request_from_scheduler(self, spider):
        self._schedule2()
        request = self.scheduler.next_request()
        if not request:
            return
        
        def handle_download_output(succeed, result):
            self._handle_download_output(result, request, spider)
        
        # Error raised by tasks in the thread pool will be logged as 
        # `Unhandled Error` by default and not break down the main thread.    
        self.call_in_thread_with_callback(handle_download_output, self.download,
                                          request, spider)
        return request
    
    # Sub-threads use this to schedule later instead of 
    # operating on the scheduler queue directly.
    def schedule_later(self, request, spider):
        self.requests_to_be_scheduled.append((request, spider))
    
    # Main thread use two below to put request to the scheduler queue.
    def _schedule(self, request, spider):
        self.scheduler.enqueue_request(request)
    
    def _schedule2(self):
        while self.requests_to_be_scheduled:
            try:   
                item = self.requests_to_be_scheduled[0]
                self.requests_to_be_scheduled.remove(item)
            except IndexError:
                return
        
            request, spider = item
            self.scheduler.enqueue_request(request)    
        
    def spider_is_idle(self, spider):
        # Judge whether there is any request to be processed.
        has_unscheduled_request = len(self.requests_to_be_scheduled)
        has_pending_request = self.scheduler.has_pending_requests()
        has_pending_task = self.thread_pool.has_pending_task()
        has_pending_download = self.downloader.has_pending_download()
        return not any((has_unscheduled_request, has_pending_request, 
                        has_pending_download, has_pending_task))
    
    def _spider_idle(self, spider):
        self.crawler.stop()
    
    def call_in_thread(self, func, *args, **kws):
        self.thread_pool.callInThread(func, *args, **kws)
        
    def call_in_thread_with_callback(self, onResult, func, *args, **kws):
        self.thread_pool.callInThreadWithCallback(onResult, func, *args, **kws)
        
    def download(self, request, spider):
        if self.crawler.stopped:
                # Immediatelly exit once the crawler receive the stop signal
                logger.warn('Force to exit from downloader when crawler stop. '
                            'Request: %s' % request, spider=spider)
                return
            
        resp = self.downloader.fetch(request, spider)
        return resp
    
    def _handle_download_output(self, response, request, spider):
        assert isinstance(response, (Request, Response, type(None))), response
        if isinstance(response, Request):
            self.schedule_later(response, spider)
            return
        elif isinstance(response, type(None)):
            return
        
        self.call_spider(response, request, spider)
    
    def call_spider(self, response, request, spider):
        parse_response = request.callback or spider.parse
        parsed_resp = parse_response(response)
        for item in parsed_resp:
            if self.crawler.stopped:
                # Immediatelly exit once crawler receive stop signal
                logger.warn('Force to exit from spider`s parser when crawler stop. '
                            'Response: %s' % response, spider=spider)
                return
            
            if isinstance(item, Request):
                self.schedule_later(item, spider)
            else:
                logger.info('@engine, Spider Parsed: [item: %r]' % item, spider=spider)
        # TODO: Store the items after parsing.