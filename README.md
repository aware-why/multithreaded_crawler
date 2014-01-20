multithreaded_crawler
=====================

A condensed crawler framework of multithreaded model


dependency
=====================
At present, the framework depends on nothing except for modules in the python standard libraries.


Usage
=====================
cd threaded_spider
python run.py --help

You will see a demo output by `python run.py`, it crawls the sina.com.cn using five threads 
and has the crawling depth limited to be 2 by default.(It's tested in python2.7)
In threaded_spider directory, there are extra log files whose name like spider.*.log respectively 
generated using `python run.py --thread=*` command.
