#################################################################################
# Software License Agreement (BSD License)
#
# Copyright (c) 2016, Bjarne Grossmann
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright
#   notice, this list of conditions and the following disclaimer.
# * Redistributions in binary form must reproduce the above copyright
#   notice, this list of conditions and the following disclaimer in the
#   documentation and/or other materials provided with the distribution.
# * Neither the name of the copyright holder nor the
#   names of its contributors may be used to endorse or promote products
#   derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#################################################################################


import importlib
import pkgutil
import sys
import inspect

import re

class PluginLoader(object):

    @classmethod
    def __import_plugins(self, package, base):
        results = []

        if isinstance(package, str):
            package = importlib.import_module(package)

        for loader, modname, is_pkg in pkgutil.walk_packages(path=package.__path__,
                                                             prefix=package.__name__+'.',
                                                             onerror=lambda x: None):
            if is_pkg: continue

            if modname not in sys.modules:
                importlib.import_module(modname)

            module = sys.modules[modname]

            pred = lambda member: inspect.isclass(member) and \
                                  member.__module__ == modname and \
                                  issubclass(member, base) and \
                                  not member.__subclasses__()

            classes = dict(inspect.getmembers(module, pred))
            results.extend(classes.values())

        results = [c for c in results if not c.__subclasses__()]

        return results

    @classmethod
    def signature(self, plugin):
        args = inspect.getargspec(plugin.__init__)
        names = args[0]
        defaults = args[-1] if args[-1] is not None else []
        req = names[1:len(names)-len(defaults)]
        opt = dict(zip(names[len(names)-len(defaults):], defaults))
        return (names[1:], req, opt)

    @classmethod
    def split(self, plugin):
        if inspect.isclass(plugin):
            name = plugin.__name__
        else:
            name = type(plugin).__name__
        return plugin.__module__.split(".") + [name]

    @classmethod
    def match(self, plugin, desc=None):
        clazz = self.split(plugin)[::-1]
        for a, b in zip(clazz, desc):
            if b and not re.match("^"+b+"$", a): return False
        return True

    @classmethod
    def instance(self, plugin, args_dict):
        names, req, opt = self.signature(plugin)
        print("Instantiating " + str(plugin) + " with arguments " + str(args_dict) + "  || REQUIRED: " + str(req) + " OPTIONAL: " + str(opt.keys()))
        p = None
        try:
            p = plugin(**args_dict)
        except Exception as e:
            print("  ERROR while instantiating: " + str(e))
        return p


    def __init__(self):
        self._plugins = None

    def __iter__(self):
        if self._plugins:
            return iter(self._plugins)
        else:
            return iter([])

    def _filter(self, desc):
        return [p for p in self._plugins if self.match(p, desc)]

    def _exclude(self, desc):
        return [p for p in self._plugins if not self.match(p, desc)]


    def load(self, folder, base_class):
        self._plugins = self.__import_plugins(folder, base_class)
        if self.size() == 0:
            raise Exception("No " + str(base_class) + " found!")
        else:
            print("Loaded " + str(self.size()) + " " + str(base_class) + " plugins:")
            self.list()
            print("------")

    def size(self):
        return len(self._plugins)

    def create(self, args_dict = {}):
        instances = []
        for p in self._plugins:
            names, req, opt = self.signature(p)
            args = opt.copy()
            args.update( { k:args_dict[k] for k in req if k in args_dict.keys()} )

            instance = self.instance(p, args)
            if instance is not None:
                instances.append(instance)

        return instances

    def getPluginByName(self, name):
        p = self._filter([name])
        if len(p) == 0: raise Exception("No plugin with name " + str(name) + " found!")
        elif len(p) > 1: print("WARNING: Multiple plugins with name " + str(name) + " found!\n" + str(p))
        return p[0]

    def list(self):
        for p in self._plugins:
            print(self.split(p))
        return [p.__name__ for p in self._plugins]

