"""
Compatibility module to provide backwards compatibility for useful Python
features.

@var unicode: The type of Unicode strings, C{unicode} on Python 2 and C{str}
    on Python 3.

@var NativeStringIO: An in-memory file-like object that operates on the native
    string type (bytes in Python 2, unicode in Python 3).

"""

import sys, string

if sys.version_info < (3, 0):
    _PY3 = False
else:
    _PY3 = True

if _PY3:
    from io import StringIO as NativeStringIO
else:
    from io import BytesIO as NativeStringIO

if _PY3:
    unicode = str
else:
    unicode = unicode
