"""
Logger based on logging and  basic.log module.
"""
from __future__ import with_statement
import logging, logging.handlers
import os, sys


from threaded_spider.basic import log
from threaded_spider.basic.util import unicode_to_str
from threaded_spider.basic.threadable import threadingmodule

# Logging levels
NOTSET = logging.DEBUG - 1
DEBUG = logging.DEBUG
INFO = logging.INFO
WARN = logging.WARN
ERROR = logging.ERROR
CRITICAL = logging.CRITICAL

level_ids = [DEBUG, INFO, WARN, ERROR, CRITICAL]
level_ids.reverse()

level_pairs = [(NOTSET, "NOISY"),
               (DEBUG, "DEBUG"),
               (INFO, "INFO"),
               (WARN, "WARN"),
               (ERROR, "ERROR"),
               (CRITICAL, "CRITICAL"),
               ]
level_pairs_reverse = [(v, k) for k, v in level_pairs]
level_pairs.extend(level_pairs_reverse) 
level_map = dict([(k, v) for k, v in level_pairs])


class FobjBasedOnLogging(object):
    def __init__(self, file_path, enable_console_output=True):
        self.logger = logging.getLogger()
        self.logger.setLevel(NOTSET)
        self.fh = None
        self.console = None
        
        if file_path is not None:
            self._add_file_handler(file_path)
        else:
            # If file_path is None, enable console output by default!
            enable_console_output = True
        if enable_console_output:
            self._add_console_handler()
            
    def _add_file_handler(self, file_path):
        # fh = logging.handlers.RotatingFileHandler(file_path, mode='a',
        #                                          maxBytes=10*1000*1000,
        #                                          backupCount=3,
        #                                          encoding=None)
        fh = logging.FileHandler(file_path, mode='w')
        fh.setLevel(NOTSET)
        self.logger.addHandler(fh)
        self.fh = fh
    
    def _add_console_handler(self):
        # Bind stderr to logging as handler
        console = logging.StreamHandler(sys.stderr)
        console.setLevel(NOTSET)
        self.logger.addHandler(console)
        self.console = console
        
    def write(self, msg):
        msg = msg.rstrip('\r \n')
        self.logger.log(NOTSET, msg)
    
    def flush(self):
        """Each log statement imediatelly flush buffer to disk file.
        It maybe result in low performance.
        """
        self.fh.flush()
        self.console.flush()
    
    def close(self):
        pass
    
    def fileno(self):
        return -1
    
    def read(self):
        raise IOError("Can't read from the log")
    
    readline = read
    readlines = read
    seek = read
    tell = read
    
class CrawlerLogObserver(log.FileLogObserver):

    def __init__(self, file_path, log_level=INFO, log_encoding='utf-8',
                 crawler=None, enable_console_output=True):
        self.level = log_level
        self.encoding = log_encoding
        if crawler:
            self.crawler = crawler
            self.emit = self._emit_with_crawler
        else:
            self.emit = self._emit
            
        f = FobjBasedOnLogging(file_path,
                               enable_console_output=enable_console_output)
        log.FileLogObserver.__init__(self, f)
        
    def _emit(self, eventDict):
        ev = _adapt_eventdict(eventDict, self.level, self.encoding)
        if ev is not None:
            log.FileLogObserver.emit(self, ev)
        return ev
    
    def _emit_with_crawler(self, eventDict):
        ev = self._emit(eventDict)
        if ev:
            level = ev['log_level']
            # TODO: self.crawler do something.

def _adapt_eventdict(eventDict, log_level=INFO, encoding='utf-8'):
    """Adapt the basic log eventDict to make it suitable for logging
    with a crawler log observer.
    
    @param log_level: the minimum level being logged.
    @param encoding: the text encoding.
    
    @ret None: Indicate the event should be ignored by a crawler log 
                observer.
    @ret dict: An event dict consisting of logging meta information.
    """
    
    ev = eventDict.copy()
    if ev['isError']:
        ev.setdefault('log_level', ERROR)
    
    # Optional, strip away the noise from outside crawler.
    # Ignore non-error message from outside crawler
    # if ev.get('system') != 'crawler' and not ev['isError']:
    #    return
    
    cur_level = ev.get('log_level', INFO)
    if cur_level < log_level:
        return
    
    spider = ev.get('spider')
    if spider:
        ev['system'] = spider.name
    
    cur_level_name = _get_log_level_name(cur_level)
    tid = threadingmodule.currentThread().getName()
    
    # Generally, message\format\isError are mutually exclusive.
    # `message` has priority over isError, `isError` over `format`.
    # See basic.log.textFromEventDict for more details.
    message = ev.get('message')
    if message:
        message = [unicode_to_str(x, encoding) for x in message]
        message[0] = '[%s] [%s] %s' % (cur_level_name, tid, message[0])  
        ev['message'] = message
    
    # The exception source description string
    why = ev.get('why')
    if why:
        why = unicode_to_str(why, encoding)
        why = '[%s] [%s] %s' % (cur_level_name, tid, why)
        ev['why'] = why
    
    fmt = ev.get('format')
    if fmt:
        fmt = unicode_to_str(fmt, encoding)
        fmt = '[%s] [%s] %s' % (cur_level_name, tid, fmt)
        ev['format'] = fmt
        
    return ev
      
def _get_log_level_id(level_name_or_id):
    if isinstance(level_name_or_id, int):
        if level_name_or_id < NOTSET:
            return level_ids[level_name_or_id - 1] 
        else:
            return level_name_or_id
    elif isinstance(level_name_or_id, basestring):
        return level_map.get(level_name_or_id, NOTSET)
    else:
        raise ValueError('Unknown log level: %r' % level_name_or_id)

def _get_log_level_name(level_name_or_id):
    if isinstance(level_name_or_id, basestring):
        if level_name_or_id in level_map:
            return level_name_or_id
        return 'UNKNOWN-LEVEL'
    elif isinstance(level_name_or_id, int):
        return level_map.get(level_name_or_id, 'UNKNOWN-LEVEL')
    else:
        raise ValueError('Unknown log name: %r' % level_name_or_id)
    
def start(log_file=None, log_level='INFO', enable_console_output=True,
          log_encoding='utf-8', redirect_stdout_to_logfile=False,
          crawler=None):
    """
    @param enable_console_output: log observer's messages write to stderr also.
        If enabled, the messages passed to debug/info/warn/error/critical methods 
        will *also* be wrote to console just like a duplicate.
    @param redirect_stdout_to_logfile:  redirect stderr to log observers.
        If enabled, messages passed to print/sys.stdout/sys.stderr will be
        delivered to log observers instead of the stdout or stderr.
    """
    
    log_level = _get_log_level_id(log_level)
    log_observer = CrawlerLogObserver(log_file, log_level=log_level,
                                      log_encoding=log_encoding,
                                      enable_console_output=enable_console_output,
                                      crawler=crawler) 
    log.startLoggingWithObserver(log_observer.emit, 
                                 setStdout=redirect_stdout_to_logfile) 
    return log_observer

def _log(message=None, **kw):
    kw.setdefault('system', 'crawler')
    if message is None:
        # Make sure `format` is in kw.
        log.msg(**kw)
    else:
        log.msg(message, **kw)

def debug(message=None, **kw):
    kw['log_level'] = DEBUG
    _log(message, **kw)

def info(message=None, **kw):
    kw['log_level'] = INFO
    _log(message, **kw)

def warn(message=None, **kw):
    kw['log_level'] = WARN
    _log(message, **kw)
    
def _log_err(_exc_value=None, _exc_desc=None, **kw):
    kw.setdefault('system', 'crawler')
    _exc_desc = _exc_desc or kw.pop('why', None)
    log.err(_exc_value, _exc_desc, **kw)

def error(_exc_value=None, _exc_desc=None, **kw):
    kw['log_level'] = ERROR
    _log_err(_exc_value, _exc_desc, **kw)

def critical(_exc_value=None, _exc_desc=None, **kw):
    kw['log_level'] = CRITICAL
    _log_err(_exc_value, _exc_desc, **kw)
                         