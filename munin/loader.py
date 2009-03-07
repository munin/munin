"""
A class for loading and reloading modules, and keeping track
of them in a dictionary.
"""

import sys
import os

import traceback

class Loader(object):
    """Loader class for modules."""

    def __init__(self, logfile=sys.stdout, loaded=None):
        """Takes a logfile parameter that defaults to
        sys.stderr, and loaded which has to be a dictionary
        if provided. Raises TypeError if loaded is provided,
        and is anything else than None or a dictionary.."""

        self.log = logfile
        if loaded is None:
            self.loaded = {}
        else:
            if not isinstance(loaded, dict):
                raise TypeError("__init__ in %s excepts dictionary but was given %s." % (
                    self.__class__, loaded.__class__))
            self.loaded = loaded

    def __getitem__(self, key):
        """Overloads operator [] for Loader. It will
        perform a lookup directly in the module dictionary,
        which means it may raise KeyError.

        Loader does not support assignment into module
        dictionary."""

        return self.loaded[key]

    def docstr(self, module):
        """Return the docstring of module if present in loader,
        otherwise raises KeyError."""

        try:
            return self.loaded[module].__doc__
        except KeyError:
            return "No such module has been loaded."

    def get_module(self, name):
        """If name has already been imported, return
        the module object, otherwise try to import it,
        then return it.

        If it fails, it returns a str instance that could
        be counted as an error message, otherwise
        it returns a module object, so a test for failure
        requires something like this:

        module = importer.get_module(name)
        if isinstance(module, str):
            # Handle error
        else:
            # Things turned out alright.
        """

        if name in self.loaded:
            return self.loaded[name]

        self.imp(name)

        try:
            return self.loaded[name]
        except KeyError:
            print self.loaded.keys()
            return "Module %s not present and could not be loaded."%(name,)

    def add_module(self, name, module):
        """Add a module named name to the loaded modules."""

        self.loaded[name] = module

    def imp(self, name):
        """Tries to import name as a module. It can look
        into a package for import as well.

        Catches exceptions present in modules."""

        failure = True

        try:
            self.loaded[name] = __import__(name,fromlist=name.split('.')[-1])
            failure = False
        except SyntaxError, e:
            result = "You have a SyntaxError in the module you're trying to load: %s" % (e,)
        except ImportError, e:
            result = "Could not load module %s: %s" % (name, e)
        except Exception, e:
            result = "Exception: %s when loading module." % (e,)

        if failure:
            print result
            traceback.print_exc(None, sys.stderr)
            return False
        return True

    def reload(self, name):
        """Tries to reload the module named name. It is an
        error to try to reload a module not already imported.
        This will result in a KeyError. This method
        may raise any exceptions that can result from importing
        a module. External references to the currently imported module
        will have to be manually updated."""

        failure = True

        try:
            newmod = reload(self.loaded[name])
            self.loaded[name] = newmod
            failure = False
        except KeyError:
            result = "Module %s not present. Import it first." % (name,)
        except ImportError, e:
            result = "Failed to import module %s: %s" % (name, e)
        except Exception, e:
            result = "Exception: %s" % (e,)

        if failure:
            traceback.print_exc(None, sys.stderr)
            return result
        return "Module %s successfully reloaded." % (name,)

    def refresh(self):
        for name in self.loaded:
            self.reload(name)

    def populate(self,basedir):
        os.path.walk(basedir,self.add_directory,None)

    def add_directory(self,arg,directory,files):
        base_module = '.'.join(directory.split(os.sep))
        module_files = [x for x in files if x[-3:].lower() == '.py' and len(x) > 3 and x != "__init__.py"]
        for m in module_files:
            module = base_module + "." + m[:-3]
            if not self.imp(module):
                raise

    def get_submodules(self,name):
        name_len=len(name)
        result=[]
        for k in self.loaded.keys():
            if k[:name_len] == name:
                result.append(self.loaded[k])
        return result
