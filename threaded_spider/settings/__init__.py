"""Settings for the crawler."""

from . import _default as default_settings


class Settings(object):
    
    def __init__(self, values=None):
        self.values = values.copy() if values else {}
        self.global_defaults = default_settings
        
    def __getitem__(self, opt_name):
        if opt_name in self.values:
            return self.values[opt_name]
        return getattr(self.global_defaults, opt_name, None)
    
    def get(self, name, default=None):
        return self[name] if self[name] is not None else default
    
    def getbool(self, name, default=False):
        """
        True is 1, False is 0
        """
        return bool(int(self.get(name, default=default)))
    
    def getint(self, name, default=0):
        return int(self.get(name, default=default))
    
    def getfloat(self, name, default=0.0):
        return float(self.get(name, default=default))
    
    def __str__(self):
        d = {}
        for k, v in self.values.items():
            d[k] = v
        for k in dir(self.global_defaults):
            if not k.startswith('__'):
                d.setdefault(k, getattr(self.global_defaults, k))
        
        return '%r' % d
    