import time

"""On windows, time.sleep will raise IOError(4, Interrupted function call) 
when ctrl+c pressed, suppress this unnecessary prompt.
"""
old_time_sleep = time.sleep
def new_time_sleep(secs):
    try:
        old_time_sleep(secs)
    except IOError, e:
        if e.errno == 4:
            pass
time.sleep = new_time_sleep

"""Provides compatibility with python3"""
from threaded_spider.basic.compat import unicode