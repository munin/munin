#!/bin/bash

set -euo pipefail
source env/bin/activate
while python3 -u run_munin.py &>> munin.log; do
     # Restart if Munin returned exit code 0 (ie, after !raw quit)
    sleep 3
done
