from .config import *
import collections

__all__ = ("Registry", "RegistryInstanceDict", "makeRegistry", "RegistryField",
           "registerConfig", "registerConfigurable")

class ConfigurableWrapper(object):
    """A wrapper for configurables
    
    Used for configurables that don't contain a ConfigClass attribute,
    or contain one that is being overridden.
    """
    def __init__(self, target, ConfigClass):
        self.ConfigClass = ConfigClass
        self._target = target

    def __call__(self, *args, **kwargs):
        return self._target(*args, **kwargs)
    

class Registry(collections.Mapping):
    """A base class for global registries, mapping names to configurables.

    There are no hard requirements on configurable, but they typically create an algorithm
    or are themselves the algorithm, and typical usage is as follows:
    - configurable is a callable whose call signature is (config, ...extra arguments...)
    - All configurables added to a particular registry will have the same call signature
    - All configurables in a registry will typically share something important in common.
      For example all configurables in psfMatchingRegistry return a psf matching
      class that has a psfMatch method with a particular call signature.

    A registry acts like a read-only dictionary with an additional register method to add items.
    The dict contains configurables and each configurable has an instance ConfigClass.

    Example:
    registry = Registry()
    class FooConfig(Config):
        val = Field(dtype=int, default=3, doc="parameter for Foo")
    class Foo(object):
        ConfigClass = FooConfig
        def __init__(self, config):
            self.config = config
        def addVal(self, num):
            return self.config.val + num
    registry.register("foo", Foo)
    names = registry.keys() # returns ("foo",)
    fooConfigurable = registry["foo"]
    fooConfig = fooItem.ConfigClass()
    foo = fooConfigurable(fooConfig)
    foo.addVal(5) # returns config.val + 5
    """

    def __init__(self, configBaseType=Config):
        """Construct a registry of name: configurables
        
        @param configBaseType: base class for config classes in registry
        """
        if not issubclass(configBaseType, Config):
            raise TypeError("configBaseType=%r must be a subclass of Config" % (configBaseType,))
        self._configBaseType = configBaseType
        self._dict = {}

    def register(self, name, target, ConfigClass=None):
        """Add a new item to the registry.
        
        @param target       A callable 'object that takes a Config instance as its first argument.
                            This may be a Python type, but is not required to be.
        @param ConfigClass  A subclass of pex_config Config used to configure the configurable;
                            if None then configurable.ConfigClass is used.
                          
        @note: If ConfigClass is provided then then 'target' is wrapped in a new object that forwards
               function calls to it.  Otherwise the original 'target' is stored.
        
        @raise AttributeError if ConfigClass is None and target does not have attribute ConfigClass
        """
        if name in self._dict:
            raise RuntimeError("An item with name %r already exists" % (name,))
        if ConfigClass is None:
            wrapper = target
        else:
            wrapper = ConfigurableWrapper(target, ConfigClass)
        if not issubclass(wrapper.ConfigClass, self._configBaseType):
            raise TypeError("ConfigClass=%r is not a subclass of %r" % (self._configBaseType,))
        self._dict[name] = wrapper
    
    def __getitem__(self, key):
        return self._dict[key]
    
    def __len__(self):
        return len(self._dict)
    
    def __iter__(self):
        return iter(self._dict)

    def __contains__(self, key):
        return key in self._dict

    def makeField(self, doc, default=None, optional=False, multi=False):
        return RegistryField(doc, self, default, optional, multi)

class RegistryAdaptor(object):
    """Private class that makes a Registry behave like the thing a ConfigChoiceField expects."""

    def __init__(self, registry):
        self.registry = registry

    def __getitem__(self, k):
        return self.registry[k].ConfigClass

class RegistryInstanceDict(ConfigInstanceDict):

    def __init__(self, fullname, typemap, multi, history=None):
        ConfigInstanceDict.__init__(self, fullname, typemap, multi, history)

    def _getTarget(self):
        if self._multi:
            raise AttributeError("Multi-selection field %s has no attribute 'target'" % self._fullname)
        return self.types.registry[self._selection]
    target = property(_getTarget)

    def _getTargets(self):
        if not self._multi:
            raise AttributeError("Single-selection field %s has no attribute 'targets'" % self._fullname)
        return [self.types.registry[c] for c in self._selection]
    targets = property(_getTarget)

    def apply(self, *args, **kwds):
        """Call the active target with the active config as the first argument.

        If this is a multi-selection field, return a list obtained by calling each active
        target with its corresponding active config as its first argument.

        Additional arguments will be passed on to the configurable or configurables.
        """
        if self.active is None:
            raise RuntimeError("No selection has been made for %s.  Options: %s" % \
                               (self._fullname, " ".join(self.types.registry.keys())))
        if self._multi:
            return [self.types.registry[c](self[c], *args, **kwds) for c in self._selection]
        else:
            return self.types.registry[self.name](self[self.name], *args, **kwds)

class RegistryField(ConfigChoiceField):

    def __init__(self, doc, registry, default=None, optional=False, multi=False,
                 instanceDictClass=RegistryInstanceDict):
        types = RegistryAdaptor(registry)
        ConfigChoiceField.__init__(self, doc, types, default, optional, multi, instanceDictClass)

def makeRegistry(doc, configBaseType=Config):
    """A convenience function to create a new registry.
    
    The returned value is an instance of a trivial subclass of Registry whose only purpose is to
    customize its doc string and set attrList.
    """
    cls = type("Registry", (Registry,), {"__doc__": doc})
    return cls(configBaseType=configBaseType)

def registerConfigurable(name, registry, ConfigClass=None):
    """A decorator that adds a class as a configurable in a Registry.

    If the 'ConfigClass' argument is None, the class's ConfigClass attribute will be used.
    """
    def decorate(cls):
        registry.register(name, target=cls, ConfigClass=ConfigClass)
        return cls
    return decorate

def registerConfig(name, registry, target):
    """A decorator that adds a class as a ConfigClass in a Registry, and associates it with the given
    configurable.
    """
    def decorate(cls):
        registry.register(name, target=target, ConfigClass=cls)
        return cls
    return decorate
