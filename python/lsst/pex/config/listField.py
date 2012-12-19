# 
# LSST Data Management System
# Copyright 2008, 2009, 2010 LSST Corporation.
# 
# This product includes software developed by the
# LSST Project (http://www.lsst.org/).
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the LSST License Statement and 
# the GNU General Public License along with this program.  If not, 
# see <http://www.lsstcorp.org/LegalNotices/>.
#
from .config import Field, FieldValidationError, _typeStr, _autocast, Config
import traceback, copy
import collections

__all__ = ["ListField", 'ListOfListField']

class List(collections.MutableSequence):
    def __init__(self, config, field, value, at, label, setHistory=True):
        #print 'List constructor:'
        #print '  config:', config
        #print '  field:', field
        #print '  value:', value
        self._field = field
        self._config = config
        self._history = self._config._history.setdefault(self._field.name, [])
        self._list = []
        self.__doc__ = field.doc
        if value is not None:
            try:
                for i, x in enumerate(value):
                    self.insert(i, x, setHistory=False)
            except TypeError:
                msg = "Value %s is of incorrect type %s. Sequence type expected"%(value, _typeStr(value))
                raise FieldValidationError(self._field, self._config, msg)
        if setHistory:
            self._addHistory(at, label)

    def validateItem(self, i, x):

        if not isinstance(x, self._field.itemtype) and x is not None:
            msg="Item at position %d with value %s is of incorrect type %s. Expected %s"%\
                    (i, x, _typeStr(x), _typeStr(self._field.itemtype))
            raise FieldValidationError(self._field, self._config, msg)
                
        if self._field.itemCheck is not None and not self._field.itemCheck(x):
            msg="Item at position %d is not a valid value: %s"%(i, x)
            raise FieldValidationError(self._field, self._config, msg)

    def _transform(self, x, i, at, label, setHistory):
        return x

    def _getHistoryEntry(self):
        return list(self._list)

    def _addHistory(self, at, label):
        self.history.append((self._getHistoryEntry(), at, label))
    
    """
    Read-only history
    """
    history = property(lambda x: x._history)   

    def __contains__(self, x): return x in self._list

    def __len__(self): return len(self._list)

    def __setitem__(self, i, x, at=None, label="setitem", setHistory=True):
        if self._config._frozen:
            raise FieldValidationError(self._field, self._config, \
                    "Cannot modify a frozen Config")
        if isinstance(i, slice):
            k, stop, step = i.indices(len(self))
            xnew = []
            for j, xj in enumerate(x):
                xj=_autocast(xj, self._field.itemtype)
                xj = self._transform(xj, k+j, at, label, setHistory)
                self.validateItem(k, xj)
                xnew.append(xj)
                k += step
            x = xnew
        else:
            x = _autocast(x, self._field.itemtype)
            x = self._transform(x, i, at, label, setHistory)
            self.validateItem(i, x)
            
        self._list[i]=x
        if setHistory:
            if at is None:
                at = traceback.extract_stack()[:-1]
            self._addHistory(at, label)

        
    def __getitem__(self, i): return self._list[i]
    
    def __delitem__(self, i, at =None, label="delitem", setHistory=True):
        if self._config._frozen:
            raise FieldValidationError(self._field, self._config, \
                    "Cannot modify a frozen Config")
        del self._list[i]
        if setHistory:
            if at is None:
                at = traceback.extract_stack()[:-1]
            self._addHistory(at, label)

    def __iter__(self): return iter(self._list)

    def insert(self, i, x, at=None, label="insert", setHistory=True): 
        if at is None:
            at = traceback.extract_stack()[:-1]
        self.__setitem__(slice(i,i), [x], at=at, label=label, setHistory=setHistory)

    def __repr__(self): return repr(self._list)

    def __str__(self): return str(self._list)

    def __eq__(self, other):
        try:
            if len(self) != len(other):
                return False

            for i,j in zip(self, other):
                if i != j: return False
            return True
        except AttributeError:
            #other is not a sequence type
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __setattr__(self, attr, value, at=None, label="assignment"):
        if hasattr(getattr(self.__class__, attr, None), '__set__'):
            # This allows properties to work.
            object.__setattr__(self, attr, value)
        elif attr in self.__dict__ or attr in ["_field", "_config", "_history", "_list", "__doc__"]:
            # This allows specific private attributes to work.
            object.__setattr__(self, attr, value)
        else:
            # We throw everything else.
            msg = "%s has no attribute %s"%(_typeStr(self._field), attr)
            raise FieldValidationError(self._field, self._config, msg)

    def printHistory(self, prefix=''):
        print prefix, 'History of', type(self), self
        for x in self._history:
            (val, stack, comment) = x
            print prefix, '  ', comment, '=', val

        

class ListField(Field):
    """
    Defines a field which is a container of values of type dtype

    If length is not None, then instances of this field must match this length 
    exactly.
    If minLength is not None, then instances of the field must be no shorter 
    then minLength
    If maxLength is not None, then instances of the field must be no longer 
    than maxLength
    
    Additionally users can provide two check functions:
    listCheck - used to validate the list as a whole, and
    itemCheck - used to validate each item individually    
    """
    def __init__(self, doc, dtype, default=None, optional=False,
            listCheck=None, itemCheck=None, 
            length=None, minLength=None, maxLength=None):
        if dtype not in Field.supportedTypes:
            raise ValueError("Unsupported dtype %s"%_typeStr(dtype))
        if length is not None:
            if length <= 0:
                raise ValueError("'length' (%d) must be positive"%length)
            minLength=None
            maxLength=None
        else:
            if maxLength is not None and maxLength <= 0:
                raise ValueError("'maxLength' (%d) must be positive"%maxLength)
            if minLength is not None and maxLength is not None \
                    and minLength > maxLength:
                raise ValueError("'maxLength' (%d) must be at least as large as 'minLength' (%d)"%(maxLength, minLength))
        
        if listCheck is not None and not hasattr(listCheck, "__call__"):
            raise ValueError("'listCheck' must be callable")
        if itemCheck is not None and not hasattr(itemCheck, "__call__"):
            raise ValueError("'itemCheck' must be callable")

        source = traceback.extract_stack(limit=2)[0]
        self._setup( doc=doc, dtype=List, default=default, check=None, optional=optional, source=source)
        self.listCheck = listCheck
        self.itemCheck = itemCheck
        self.itemtype = dtype
        self.length=length
        self.minLength=minLength
        self.maxLength=maxLength
   

    def validate(self, instance):
        """
        ListField validation ensures that non-optional fields are not None,
            and that non-None values comply with length requirements and
            that the list passes listCheck if supplied by the user.
        Individual Item checks are applied at set time and are not re-checked.
        """
        Field.validate(self, instance)
        value = self.__get__(instance)
        if value is not None:
            lenValue =len(value)
            if self.length is not None and not lenValue == self.length:
                msg = "Required list length=%d, got length=%d"%(self.length, lenValue)                
                raise FieldValidationError(self, instance, msg)
            elif self.minLength is not None and lenValue < self.minLength:
                msg = "Minimum allowed list length=%d, got length=%d"%(self.minLength, lenValue)
                raise FieldValidationError(self, instance, msg)
            elif self.maxLength is not None and lenValue > self.maxLength:
                msg = "Maximum allowed list length=%d, got length=%d"%(self.maxLength, lenValue)
                raise FieldValidationError(self, instance, msg)
            elif self.listCheck is not None and not self.listCheck(value):
                msg = "%s is not a valid value"%str(value)
                raise FieldValidationError(self, instance, msg)

    def _getListClass(self):
        return List
            
    def __set__(self, instance, value, at=None, label="assignment"):
        #print 'ListField.__set__:'
        #print '  inst', type(instance)
        #print '  value', value
        
        if instance._frozen:
            raise FieldValidationError(self, instance, "Cannot modify a frozen Config")

        if at is None:
            at = traceback.extract_stack()[:-1]

        if value is not None:
            ListClass = self._getListClass()
            print 'Creating object of type', ListClass
            value = ListClass(instance, self, value, at, label)
        else:
            history = instance._history.setdefault(self.name, [])
            history.append((value, at, label))

        print 'Actually setting value of', self.name, '=', value
        instance._storage[self.name] = value
        # if value is not None:
        #     print 'Adding history again'
        #     print 'instance is', type(instance)
        #     value._addHistory(at, label)
    
    def toDict(self, instance):        
        value = self.__get__(instance)        
        return list(value) if value is not None else None

            
class ListOfListField(ListField):

    def __init__(self, doc, dtype, **kwargs):

        oldtypes = Field.supportedTypes
        newtypes = oldtypes + (List,)
        Field.supportedTypes = newtypes

        self._subkwargs = kwargs.pop('subkwargs', {})

        super(ListOfListField, self).__init__(doc, List, **kwargs)

        Field.supportedTypes = oldtypes

        self._subfields = {}
        self._subtype = dtype
        
        #self._subfield = ListField('subfield of ListOfListField', dtype,
        #        **kwargs)
        #self._subfield.name = 'sublist'

        self._subconfig = Config()
        
    def getSubfield(self, i):
        try:
            return self._subfields[i]
        except:
            pass
        sf = ListField('subfield[%i] of ' + self.name, self._subtype,
                       **self._subkwargs)
        sf.name = '%s[%i]' % (self.name, i)
        self._subfields[i] = sf
        return sf

    def getSubconfig(self, i):
        return self._subconfig
    
    def _getListClass(self):
        return ListOfList
        
    #def __set__(self, instance, value, at=None, label="assignment"):
    #    print 'LoLField.__set__'
    #     print '  inst', type(instance)
    #     print '  value', value
    #    return super(ListOfListField, self).__set__(instance, value,
    #                                                at=at, label=label)

class SubList(List):
    def __init__(self, mylist, i, *args, **kwargs):
        self.__dict__['_mylist'] = mylist
        self.__dict__['_mylisti'] = i
        #self._mylist = mylist
        super(SubList, self).__init__(*args, **kwargs)

    def _addHistory(self, at, label, selfOnly=False):
        print 'SubList: adding to my history'
        super(SubList, self)._addHistory(at, label)
        if not selfOnly:
            print 'SubList: adding to parent history'
            self._mylist._addHistory(at, label + '[%i]'%self._mylisti)

class ListOfList(List):
    def __init__(self, *args, **kwargs):
        print 'ListOfList constructor; delegating'
        super(ListOfList, self).__init__(*args, **kwargs)
        
    def __set__(self, instance, value, at=None, label="assignment"):
        print 'ListOfList.__set__'
        super(ListOfList, self).__set__(instance, value, at=at, label=label)

    def _transform(self, x, i, at, label, setHistory):
        # convert iterables (except strings) to List objects
        if not isinstance(x, basestring):
            try:
                it = iter(x)
                #field = self._field._subfield

                # If my element at that position isn't already a list...
                #if i < len(self._list) and isinstance(self._list[i], List):
                #   return x

                field = self._field.getSubfield(i)
                config = self._field.getSubconfig(i)

                print 'Creating new List object for', field.name #, '[%i]' % i

                print 'resetting history'
                config._history[field.name] = []
                print 'setHistory:', setHistory
                
                #lst = SubList(self, i, config, field, None, at, label, setHistory)
                #lst[:] = x

                lst = SubList(self, i, config, field, x, at, label, setHistory)

                lst._addHistory(at, label, selfOnly=True)
                
                #lst = List(config, field, x, at, label, setHistory)
                #print 'LoLField: transformed to', type(lst), lst
                return lst

            except TypeError:
                # not iterable, fine
                pass
        return x
    
    def _getHistoryEntry(self):
        return list([x._getHistoryEntry() for x in self._list])
