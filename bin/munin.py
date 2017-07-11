#!/usr/bin/python -u


import sys
import os
import string
if hasattr(os, "getuid") and os.getuid() != 0:
    sys.path.insert(0, os.path.abspath(os.getcwd()))

from munin.munin import run
run()
