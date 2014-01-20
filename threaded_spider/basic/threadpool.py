"""
A pool of threads to which we dispatch tasks.
"""

from __future__ import with_statement

try:
    from Queue import Queue
except ImportError:
    from queue import Queue
import contextlib
import threading
import copy

from threaded_spider import logger
from threaded_spider.basic import context, failure


WorkerStop = object()

class ThreadPool(object):
    """
    This class (hopefully) generalizes the functionality of a pool of
    threads to which work can be dispatched.

    L{callInThread} and L{stop} should only be called from
    a single thread, unless you make a subclass where L{stop} and
    L{_startSomeWorkers} are synchronized, or else, maybe some workers
    can not be stopped.
    """
    min = 5
    max = 20
    joined = False
    started = False
    workers = 0
    name = None

    threadFactory = threading.Thread
    currentThread = staticmethod(threading.currentThread)

    def __init__(self, minthreads=5, maxthreads=20, name=None):
        """
        Create a new threadpool.

        @param minthreads: minimum number of threads in the pool
        @param maxthreads: maximum number of threads in the pool
        """
        assert minthreads >= 0, 'minimum is negative'
        assert minthreads <= maxthreads, 'minimum is greater than maximum'
        self.q = Queue(0)
        self.min = minthreads
        self.max = maxthreads
        self.name = name
        
        # Reference: http://effbot.org/pyfaq/what-kinds-of-global-value-mutation-are-thread-safe.htm.
        # Some operations on built-in data types are thread-safe because of GIL thread-switch mechanism. 
        # For instance, append\remove\extend method of list.
        self.waiters = []
        self.threads = []
        self.working = []
        self.active_tasks = []

    def start(self):
        """
        Start the threadpool.
        """
        if self.started:
            return
        
        self.joined = False
        self.started = True
        # Start some threads.
        self.adjustPoolsize()


    def startAWorker(self):
        self.workers += 1
        name = "ThreadPool-%s-%s" % (self.name or id(self), self.workers)
        newThread = self.threadFactory(target=self._worker, name=name)
        self.threads.append(newThread)
        newThread.start()


    def stopAWorker(self):
        self.q.put(WorkerStop)
        self.workers -= 1

    def _startSomeWorkers(self):
        neededSize = self.q.qsize() + len(self.working)
        # Create enough, but not too many
        while self.workers < min(self.max, neededSize):
            self.startAWorker()


    def callInThread(self, func, *args, **kw):
        """
        Call a callable object in a separate thread.

        @param func: callable object to be called in separate thread

        @param *args: positional arguments to be passed to C{func}

        @param **kw: keyword args to be passed to C{func}
        """
        self.callInThreadWithCallback(None, func, *args, **kw)


    def callInThreadWithCallback(self, onResult, func, *args, **kw):
        """
        Call a callable object in a separate thread and call C{onResult}
        with the return value.

        The callable is allowed to block, but the C{onResult} function
        must not block and should perform as little work as possible.

        @param onResult: a callable with the arguments C{(success, result)}.
            If the callable returns normally, C{onResult} is called with
            C{(True, result)} where C{result} is the return value of the
            callable. If the callable throws an exception, C{onResult} is
            called with C{(False, Exception)}.

            Optionally, C{onResult} may be C{None}, in which case it is not
            called at all.

        @param func: callable object to be called in separate thread

        @param *args: positional arguments to be passed to C{func}

        @param **kwargs: keyword arguments to be passed to C{func}
        """
        if self.joined:
            return
        
        self.active_tasks.append((func, args, kw))
        ctx = context.theContextTracker.currentContext().contexts[-1]
        o = (ctx, func, args, kw, onResult)
        self.q.put(o)

        if self.started:
            self._startSomeWorkers()


    @contextlib.contextmanager
    def _workerState(self, stateList, workerThread):
        """
        Manages adding and removing this worker from a list of workers
        in a particular state.

        @param stateList: the list managing workers in this state

        @param workerThread: the thread the worker is running in, used to
            represent the worker in stateList
        """
        stateList.append(workerThread)
        try:
            yield
        finally:
            stateList.remove(workerThread)


    def _worker(self):
        """
        Method used as target of the created threads: retrieve a task to run
        from the threadpool, run it, and proceed to the next task until
        threadpool is stopped.
        """
        ct = self.currentThread()
        with self._workerState(self.waiters, ct):
            o = self.q.get()
            
        while o is not WorkerStop:
            with self._workerState(self.working, ct):
                ctx, function, args, kwargs, onResult = o
                del o

                try:
                    result = context.call(ctx, function, *args, **kwargs)
                    success = True
                except Exception, e:
                    success = False
                    if onResult is None:
                        context.call(ctx, logger.error)
                        result = None
                    else:
                        result = e

                # callback after got result also invoked in this thread.
                if onResult is not None:
                    try:
                        context.call(ctx, onResult, success, result)
                    except:
                        context.call(ctx, logger.error)
                
            self.active_tasks.remove((function, args, kwargs))
            del function, args, kwargs
            del ctx, onResult, result
            
            with self._workerState(self.waiters, ct):
                o = self.q.get()

        self.threads.remove(ct)
        logger.debug('%s exit' % ct)

    def has_pending_task(self):
        return len(self.active_tasks) or len(self.working) or self.q.qsize()
        
    def stop(self):
        """
        Shutdown the threads in the threadpool.
        """
        if self.joined:
            return
        
        self.joined = True
        logger.info('@threadpool, stopping...')

        threads = copy.copy(self.threads)
        while self.workers:
            # Important, *must* give stop signal., otherwise sub-threads cannot join.
            self.q.put(WorkerStop)
            self.workers -= 1

        # and let's just make sure
        # FIXME: threads that have died before calling stop() are not joined.
        for thread in threads:
            logger.debug('@threadpool, waiting %s to join.' % thread)
            thread.join()
            logger.debug('@threadpool, waiting %s finish.' % thread)
        
        logger.info('@threadpool, stopped.')

    def adjustPoolsize(self, minthreads=None, maxthreads=None):
        if minthreads is None:
            minthreads = self.min
        if maxthreads is None:
            maxthreads = self.max

        assert minthreads >= 0, 'minimum is negative'
        assert minthreads <= maxthreads, 'minimum is greater than maximum'

        self.min = minthreads
        self.max = maxthreads
        if not self.started:
            return

        # Kill  some threads if we have too many.
        while self.workers > self.max:
            self.stopAWorker()
        # Start some threads if we have too few.
        while self.workers < self.min:
            self.startAWorker()
        # Start some threads if there is a need.
        self._startSomeWorkers()


    def dumpStats(self):
        logger.info('@threadpool, dump status:')
        logger.info('%s queue(number of tasks remain unfinished in pool): %s '   % (self.name, self.q.qsize()))
        logger.debug('%s queue(tasks remained in pool): %s '   % (self.name, self.q.queue))
        logger.info('%s waiters(threads waiting to grab a task): %s' % (self.name, self.waiters))
        logger.info('%s workers(threads being working on a task): %s' % (self.name, self.working))
        logger.info('%s total (thread objects still in the pool): %s'   % (self.name, self.threads))
