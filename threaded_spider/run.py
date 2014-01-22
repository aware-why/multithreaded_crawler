# -*- coding:utf-8 -*-
"""Run a spider in multiple threads which crawls from specific start url with specified depth"""

from __future__ import with_statement

import optparse
import sys
import os
import re
import time

# Temporarily declare the search path for the package.
CUR_DIR = os.path.dirname(os.path.abspath(__file__))
pkg_path = os.path.join(CUR_DIR, '..')
sys.path.insert(0, pkg_path)

from threaded_spider import logger
from threaded_spider.crawler import Crawler
from threaded_spider.keyword_spider import KeyWordSpider
from threaded_spider.settings import Settings
from threaded_spider.basic.failure import startDebugMode
# startDebugMode()

def main():
    parser = optparse.OptionParser(usage='%prog [options]', version='1.0')
    parser.add_option('-u', dest='start_url', default='http://www.sina.com.cn',
                      help='The start URL to crawl from, set to %default by default.')
    parser.add_option('-d', dest='max_depth', default=2,
                      type='int',
                      help='Maximum depth when crawling, set to %default by default.')
    parser.add_option('--thread', dest='thread_num', default=5,
                      type='int',
                      help='Thread count in threadpool, set to %default by default.')
    parser.add_option('--dbfile', dest='db_fp', default='sqlite.db',
                      help='Sqlite database file path, set to %default by default.')
    parser.add_option('--key', dest='key_words', default=[],
                      action='append',
                      help='The key words to be searched in the web pages.')
    parser.add_option('-l', dest='log_level', default=4,
                      type='choice', choices=['1', '2', '3', '4', '5'],
                      help='Log level, the larger the numerical value the more verbose the log info.')
    parser.add_option('--test', dest='test_mode', default=False,
                      action='store_true',
                      help='Run in test mode to do unit tests')

    opts, args = parser.parse_args()
    print opts, args
    
    log_file = os.path.join(CUR_DIR, 'spider.log')
    logger.start(log_file, log_level=opts.log_level,
                 redirect_stdout_to_logfile=True,
                 enable_console_output=True)
    start = time.time()
    print '@main, start.哈哈  when %s'  % start
    
    
    if not os.path.isabs(opts.db_fp):
        opts.db_fp = os.path.join(CUR_DIR, opts.db_fp)
    from threaded_spider.keyword_itemproc import DB_SCHEMA
    
    _s = Settings(values={'MAX_DEPTH': opts.max_depth, 'LOG_LEVEL': opts.log_level,
                          'THREAD_NUM': opts.thread_num,
                          'ITEM_PROCESSOR': 'threaded_spider.keyword_itemproc.DBStore',
                          'DB_FP': opts.db_fp, 'DB_SCHEMA': DB_SCHEMA,}
                  )
    spider = KeyWordSpider('spider.sina', start_urls=[opts.start_url])
    crawler = Crawler(_s) 
    print '@main, crawler settings: %s' % crawler.settings   
    crawler.attach_spider(spider)
    crawler.prepare_engine()
    crawler.crawl()
    
    end = time.time()
    print '@main, stopped when %s and %s seconds elapsed.' % (end, end - start)


from threaded_spider.basic.threadpool import ThreadPool    
import threading
from threaded_spider.basic.util import make_utf8
_count_lock = threading.RLock()
down_count = 0
def test_download(start_url):
    from threaded_spider.core.downloader import Downloader
    from threaded_spider.http import Request
    downloader = Downloader()
    req = Request(start_url)
    resp = downloader.fetch(req)
    html = make_utf8(resp.body)
    print html[:206]
    print ord(html[0]), ord('<')
   
    def filter_href(base_url, href):
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
        
    import BeautifulSoup
    soup = BeautifulSoup.BeautifulSoup(html)
    hrefs = set() 
    for item in soup.fetch('a'):  
        href = item.get('href', None)
        href = filter_href(start_url, href)
        if href:
            hrefs.add(href)
    print 'There are <%s> different links.' % len(hrefs)
    #return

    thread_pool = ThreadPool(minthreads=7,
                             maxthreads=7,
                             name='thread_pool_name')
    thread_pool.start()
    
    def after_download(succeed, result):
        global down_count
        
        with _count_lock:
            down_count += 1
            print 'This is <%s> url.' % down_count
            
    def download_url_page(url):
        logger.info(format='DOWN_URL_START %(url)s', url=url)
        try:
            req = Request(url)
            resp = downloader.fetch(req)
            body = make_utf8(resp.body)[:25]
        except:
            logger.error(why='DOWN_URL_FAIL %s' % url)
        else:
            logger.info(format='DOWN_URL_FINISH %(url)s [body=%(body)r]', url=url, body=body) 
    for link in hrefs:
        thread_pool.callInThreadWithCallback(after_download, download_url_page, link)

    thread_pool.stop()
    thread_pool.dumpStats()
    logger.info('download url total: <%s>' % down_count)

def test_threadpool():
    thread_pool = ThreadPool(minthreads=2,
                             maxthreads=2,
                             name='thread_pool_name')
    thread_pool.start()
    
    def onResult(succeed, result):
        print succeed, result
    def task_func(i):
        if i < 2:
            return 1
        else:
            print 'tid:<%s>, task ing...i:<%d>' % (ThreadPool.currentThread().getName(), i)
            return task_func(i-1) + task_func(i-2)
    thread_pool.callInThreadWithCallback(onResult, task_func, 5)
    thread_pool.callInThreadWithCallback(onResult, task_func, 6)
    thread_pool.stop()
    
def test_log():
    logger.start('test.log',
                 redirect_stdout_to_logfile=True,
                 enable_console_output=True)
    
    print 'stdout1'
    print >> sys.stdout, 'stdout2' 
    print >> sys.stderr, 'stderr' 
    logger.debug('logging debug...')
    logger.info('logging info中文啊.')
    logger.warn('logging warn...')
    
    try:
        pass
        logger.error()
    except:
        logger.error(why='No exception captured in basic.failure.Failure.')
         
    try:
        print 'pause...' >> sys.stderr
    except:
        logger.error(why='`print` statement syntax error.')
        
    logger.critical('Log done.', why='这不是错误，只是日志结束。')


if __name__ == '__main__':
    main()
