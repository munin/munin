#!/bin/bash

set -euo pipefail
source env/bin/activate
python3 -u run_munin.py &>> munin.log
