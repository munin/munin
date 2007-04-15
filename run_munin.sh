#!/bin/sh

trap 'kill $bot' EXIT
#trap 'exit 0' SIGTERM
while true; do
    /home/munin/odin/munin.py 2>&1 | tee /home/munin/odin/botlog
    bot=$!
    wait $bot
    sleep 120
done
