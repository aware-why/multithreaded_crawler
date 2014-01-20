"""
This module define the Item class which is base of Item instance object
in this project and the Filed class which is used to instantiate an item filed.
Item object yield by the the spider parser method or callback associated with 
a Request object should derive from the Item class.
"""

from UserDict import DictMixin
from pprint import pformat


class Field(dict):
    """Representation of an item field"""
    pass

class ItemMeta(type):
    """Apply some magic operations on the class which is being
    created"""
    
    def __new__(metacls, cls_name, bases, attrs):
        fields = {}
        extra_attrs = {}
        
        for k, v in attrs.iteritems():
            if isinstance(v, Field):
                fields[k] = v
            else:
                extra_attrs[k] = v
        
        cls = type.__new__(metacls, cls_name, bases, extra_attrs)
        # TODO: it's not necessary really?
        # cls.fields = cls.fields.copy()
        cls.fields.update(fields)
        return cls
    
class BaseItem(DictMixin, object):
    """
    All Item object used in this project should derive from this class.
    """
    
    __metaclass__ = ItemMeta
    fields = {}     # All keys declared are stored in it
    
    def __init__(self, iter_pairs_or_map_obj={}, **kws):
        self._values = {}
        if iter_pairs_or_map_obj or kws:
            for k, v in dict(iter_pairs_or_map_obj, **kws).iteritems():
                self[k] = v
                
    # Four User-defined operations on the value referenced by key.             
    # See DictMixin __doc__ string for more info.
    def __getitem__(self, key):
        # All keys manipulated are stored in _value attribute.
        return self._values[key]
    
    def __setitem__(self, key, value):
        if key in self.fields:
            self._values[key] = value
        else:
            raise KeyError('%s not supports this field: %s' % 
                           (self.__class__.__name__, key))
            
    def __delitem__(self, key):
        del self._values[key]
        
    def keys(self):
        return self._values.keys()
    
    def __getattr__(self, name):
        # When attribute not found in __dict__, should search by this method.
        if name in self.fields:
            raise AttributeError('Use item[%r] to get field value' %
                                 name)
        raise AttributeError(name)
    
    def __setattr__(self, name, value):
        if name == 'fields' or name =='__metaclass__':
            raise ValueError('Should not modify this attribute: %s' % name)
        
        if not name.startswith('_'):
            if name in self.fields:
                raise AttributeError('Use item[%r] = %r to set field value' %
                                     (name, value))
                  
        super(BaseItem, self).__setattr__(name, value)
            
    def __repr__(self):
        # Only print the _values attribute.
        return pformat(dict(self))
    
    def copy(self):
        # Construct another Item object having the same class attributes 
        # and the _value attribute as this Item, but not the other non-class.
        # attribtes.
        return self.__class__(self)
    
class Item(BaseItem):
    f1 = Field()
    f2 = Field()
    extra_class_attribute = '<class attribute of non-Field type> '
  
    
if __name__ == '__main__':
    item = Item()
    print 'Construct an Item object:', item
    print 'item.fields:', item.fields
    print 'extra non-field attribute:', item.extra_class_attribute
    print 'f1 in item:', 'f1' in item  # `f1` field is declared in Item
    print 'f1 in item.fields:', 'f1' in item.fields # `f1` field is not manipulated
    item['f1'] = 'Set f1'
    print 'After setting f1:', item['f1']
    print 'f1 in item:', 'f1' in item
    # item.f2 = 'Set f2'  will raise
    item._test = '_test'
    print 'item.fields:', item.fields
    print 'item._values:', item._values
    print 'item._test:', item._test
    
    item2 = item.copy()
    print 'Make a copy of this item:', item2
    print 'the non-field attribute of class-level in the copy:', item2.extra_class_attribute
    # print item2._test will raise