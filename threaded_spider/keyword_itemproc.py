"""Store the item info yielded by the KeyWordSpider into sqlite database"""
from __future__ import with_statement
import os
import sqlite3
import Queue
from threading import Thread

from threaded_spider import logger
from threaded_spider.core.itemproc import  ItemProc
from threaded_spider.basic.util import make_unicode

DB_SCHEMA = """
begin transaction;

create table keyword_page (
id    integer primary key autoincrement not null,
url    text not null,
body    blob default '',
keyword    text,
depth    integer,
parent_url    text,
root_url    text
);

create unique index ui_url on keyword_page(url);
replace into keyword_page (url, body, depth) values ('http://test', 'page body', 1);
replace into keyword_page (url, body, depth) values ('http://test', 'page body', 1);

commit;
"""

class DBStore(ItemProc):
    """Use sqlite as storage."""
    
    def attach_spider(self, spider):
        super(DBStore, self).attach_spider(spider)
        self.db = ThreadedSqlite(self.crawler.settings.get('DB_SCHEMA'),
                                 self.crawler.settings.get('DB_FP'))
        
    def detach_spider(self):
        super(DBStore, self).detach_spider()
        self.db.close()
        
    def _process_item(self, item, spider_info): 
        print 'Got url: %r, depth: %r' % (item['self_url'], item['depth'])
        sql = 'replace into keyword_page (url, body, depth) values (:url, :body, :depth)'
        arg = {'url': item['self_url'], 'body': buffer(item['html_content']),
               'depth': item['depth']}
        self.db.execute(sql, arg)
        
class ThreadedSqlite(Thread):
    """
    It's thread-safe, easy to use in multithread 
    and simulates to execute SQL statements in sqlite3 asynchronously.
    """
    
    def __init__(self, sql_schema, db_file):
        super(ThreadedSqlite, self).__init__()
        
        self._create_db(sql_schema, db_file)
        assert os.path.exists(db_file), '@keyword_itemproc, %s not exists' % db_file
        self.db_file = db_file
        self.conn = None
        
        self.req_queue = Queue.Queue()
        
        self.setName('sqlite_thread')
        self.start()
        self.running = True
    
    def _create_db(self, sql_schema, db_file):
        if os.path.exists(db_file):
            logger.warn('@keyword_itemproc, Assume that schema established for sqlite database %s '
                        % db_file)
        else:
            if os.path.exists(sql_schema):
                with open(sql_schema) as f:
                    sql_schema = f.read()
            with sqlite3.connect(db_file) as conn:
                conn.executescript(sql_schema)
            logger.info('@keyword_itemproc, Database file created: %s, using schema: %r' 
                        % (db_file, sql_schema))
    
    def run(self):
        try:
            with sqlite3.connect(self.db_file) as conn:
                self.conn = conn
                conn.text_factory = str     # Recognize text type in sqlite as str in python
                conn.row_factory = sqlite3.Row
                
                cursor = conn.cursor()
                while True:
                    sql, arg, res = self.req_queue.get()
                    if sql == '--close--':
                        break
                    cursor.execute(sql, arg)
                    if res:
                        for rec in cursor.fetchall():
                            res.put(rec)
                        res.put('--end--')
        except Exception, e:
            logger.error(why=str(e))
        finally:
            logger.info('@keyword_itemproc, sqlite close connection.')
            self.running = False
            if self.conn:
                self.conn.close()
            
    def execute(self, sql, arg=None, res=None):
        if not self.running:
            return
        
        self.req_queue.put((sql, arg or tuple(), res))
        
    def select(self, sql, arg=None):
        res = Queue.Queue()
        self.execute(sql, arg, res)
        while True:
            rec = res.get()
            if rec == '--end--': 
                break
            yield rec
    
    def close(self):
        self.execute('--close--')
        self.join()
        
        