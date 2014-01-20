"""
Crawler to use a spider to crawl web pages.
"""
import time
import signal
import traceback

from threaded_spider import logger
from threaded_spider.core.engine import Engine

class Crawler(object):
    
    def __init__(self, settings):
        self.settings = settings
        self._start_requests = lambda: ()
        self._spider = None
        
    def attach_spider(self, spider, requests=None):
        assert self._spider is None, 'Spider already attached.'
        self._spider = spider
        self._spider.attach_crawler(self)
        
        if requests is None:
            self._start_requests = spider.start_requests
        else:
            self._start_requests = lambda: requests
      
    def prepare_engine(self):
        assert self._spider is not None, 'Please attach a spider first.'
        self.engine = Engine(self)
        self.engine.attach_spider(self._spider, start_requests=self._start_requests)
              
    def crawl(self):
        # Start the engine and install the shutdown signal handler.
        self.stopped = False
        self.delayed_calls = []
        self._handle_shutdown()
        logger.info('***************************************')
        logger.info('Crawler started.')
        logger.info('***************************************')
        
        self.engine.start()
        try:
            while not self.stopped:
                self.engine.process_next_request(self._spider)
                time.sleep(0.01)
                
                while self.delayed_calls:
                    try:
                        item = self.delayed_calls[0]
                        self.delayed_calls.remove(item)
                    except IndexError:
                        break
                    func, args, kws = item
                    logger.info('delayed call: %s %s %s' %(func, args, kws))
                    func(*args, **kws)
        except Exception, e:
            logger.error(why='Error when engine processes next request.')
            self.stop(force=True)
        except KeyboardInterrupt:
            logger.warn('Receive interrupt, crawler exits. Stack as follows:\n'
                        '%s' % ''.join(traceback.format_stack()))
            self.stop(force=True)
        finally:
            pass
        
    def _handle_shutdown(self):
        # Make sure access objects *having no race conditions* in the signal handler.
        # Otherwise, the main thread will go into dead lock when ctrl+c is pressed.
        # The bulit-in data type itself, such as list, is already thread-safe and 
        # not cause dead lock by means of append\remove\slice.
        def on_shutdown(signum, frame):
            if self.stopped:
                return
            self.call_later(self.stop, True)
            
        signal.signal(signal.SIGINT, on_shutdown)
    
    def call_later(self, func, *args, **kws):
        self.delayed_calls.append((func, args, kws))
      
    def stop(self, force=False):
        # Stop the engine.
        if self.stopped:
            return
        
        self.stopped = True
        logger.info('Crawler Stopping...')
        self.engine.stop(force=force)
        logger.info('Crawler stopped.')