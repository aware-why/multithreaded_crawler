"""
Provide some very basic threading primitives, such as
synchronization.
"""

import threading
from functools import wraps


threadingmodule = threading
XLock = threadingmodule.RLock
_synchLockCreator = XLock()

def _synchPre(self):
    # Make sure the class instance create the lock only once.
    # And the lock is for a series of specific bounded methods of a class instance
    # which will all access a shared object.
    if '_threadable_lock' not in self.__dict__:
        _synchLockCreator.acquire()
        if '_threadable_lock' not in self.__dict__:
            self.__dict__['_threadable_lock'] = XLock()
        _synchLockCreator.release()
    self._threadable_lock.acquire()
    
def _synchPost(self):
    self._threadable_lock.release()
    
def _sync(klass, function):
    @wraps(function)
    def sync(self, *args, **kwargs):
        _synchPre(self)
        try:
            return function(self, *args, **kwargs)
        finally:
            _synchPost(self)
    return sync

def synchronize(*klasses):
    """
    Make all methods listed in each class' synchronized attribute synchronized.

    The synchronized attribute should be a list of strings, consisting of the
    names of methods that must be synchronized. If we are running in threaded
    mode these methods will be wrapped with a lock.
    """
    if threadingmodule is not None:
        for klass in klasses:
            for methodName in klass.synchronized:
                sync = _sync(klass, klass.__dict__[methodName])
                # Set a function object as a class-atribute
                # so that class.attr return a unbounded method
                setattr(klass, methodName, sync)

