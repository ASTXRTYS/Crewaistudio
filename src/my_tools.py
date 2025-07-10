import os, sys
APP_DIR = os.path.join(os.path.dirname(__file__), 'app')
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

from importlib import import_module

_mod = import_module('app.my_tools')
for _name in getattr(_mod, '__all__', dir(_mod)):
    globals()[_name] = getattr(_mod, _name)

del _mod, _name 