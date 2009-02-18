#!/usr/bin/python


import sys, os, string
if hasattr(os, "getuid") and os.getuid() != 0:
    sys.path.insert(0, os.path.abspath(os.getcwd()))
### end of preamble


from munin.munin import run
run()
