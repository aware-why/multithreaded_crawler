"""
Miscellaneous tools.
"""
import errno

def retry_when_interrupt(f, *a, **kw):
    """
    Call C{f} with the given arguments, handling C{EINTR} by retrying.
    
    @param f: A function to call.
    @param *a: Positional arguments to pass to C{f}.
    @param **kw: Keyword arguments to pass to C{f}.

    @return: Whatever C{f} returns.
    
    @raise: Whatever C{f} raises, except for C{IOError} or C{OSError} with
        C{errno} set to C{EINTR}.
    """
    while True:
        try:
            return f(*a, **kw)
        except (IOError, OSError) as e:
            if e.args[0] == errno.EINTR:
                continue
            raise
        
def make_unicode(value, prefer_encodings=None):
    if prefer_encodings is None:
        prefer_encodings = ['utf8', 'gbk', 'gbk?']
    
    if isinstance(value, unicode) or value is None:
        return value
    
    if not isinstance(value, str):
        return value

    for enc in prefer_encodings:
        try:
            if enc.endswith('!'):
                return value.decode(enc[:-1], 'ignore')
            elif enc.endswith('?'):
                return value.decode(enc[:-1], 'replace')
            elif enc.endswith('&'):
                return value.decode(enc[:-1], 'xmlcharrefreplace')
            elif enc.endswith('\\'):
                return value.decode(enc[:-1], 'backslashreplace')
            else:
                return value.decode(enc)
        except UnicodeError:
            pass
    else:
        raise

def _make_unicode_elem(obj, **options):
    if isinstance(obj, list):
        obj = [_make_unicode_elem(elem, **options) for elem in obj]
    elif isinstance(obj, dict):
        obj = dict((make_unicode(k, **options), _make_unicode_elem(v, **options)) for k,v in obj.items())
    elif isinstance(obj, str):
        obj = make_unicode(obj, **options)
    return obj

def make_unicode_obj(obj, **options):
    return _make_unicode_elem(obj, **options)

def make_utf8(value, prefer_encodings=None):
    uv = make_unicode(value, prefer_encodings)
    if uv is None:
        return None
    
    if not isinstance(uv, unicode):
        return uv
        
    return uv.encode('utf8', 'xmlcharrefreplace')

def _make_utf8_elem(obj, **options):
    if isinstance(obj, list):
        obj = [_make_utf8_elem(elem, **options) for elem in obj]
    elif isinstance(obj, dict):
        obj = dict((make_utf8(k, **options), _make_utf8_elem(v, **options)) for k,v in obj.items())
    elif isinstance(obj, unicode):
        obj = make_utf8(obj, **options)

    return obj

def make_utf8_obj(obj, prefer_encodings=None):
    return _make_utf8_elem(obj, prefer_encodings=prefer_encodings)

def str_to_unicode(text, encoding=None, errors='strict'):
    """Return the unicode representation of text in the given encoding. Unlike
    .encode(encoding) this function can be applied directly to a unicode
    object without the risk of double-decoding problems (which can happen if
    you don't use the default 'ascii' encoding)
    """
    if text is None:
        return None
    
    if encoding is None:
        encoding = 'utf-8'
    if isinstance(text, str):
        return text.decode(encoding, errors)
    elif isinstance(text, unicode):
        return text
    else:
        raise TypeError('str_to_unicode must receive a str or unicode object, got %s' % type(text).__name__)

def unicode_to_str(text, encoding=None, errors='strict'):
    """Return the str representation of text in the given encoding. Unlike
    .encode(encoding) this function can be applied directly to a str
    object without the risk of double-decoding problems (which can happen if
    you don't use the default 'ascii' encoding)
    """
    if text is None:
        return None
    
    if encoding is None:
        encoding = 'utf-8'
    if isinstance(text, unicode):
        return text.encode(encoding, errors)
    elif isinstance(text, str):
        return text
    else:
        raise TypeError('unicode_to_str must receive a unicode or str object, got %s' % type(text).__name__)

def load_object(path):
    """
    Load an object given its absolute object path, and return it.
    
    Object can be a class, function, variable or instance.
    path ie: 'threaded_spider.core.engine.Engine'
    """
    
    try:
        dot = path.rindex('.')
    except ValueError, e:
        raise ValueError('Not a full object path: %s', path)
    
    mod_name, obj_name = path[:dot], path[dot+1:]
    try:
        mod = __import__(mod_name)
        names = mod_name.split('.')
        for xname in names:
            mod = getattr(mod, xname)
    except ImportError, e:
        raise ImportError('Error loading object <%s>: %s' % (path, e))
    
    try:
        obj = getattr(mod, obj_name)
    except AttributeError, e:
        raise NameError('Module <%s> doesnt define any object named <%s>' 
                        % (mod.__name__, obj_name))
    
    return obj