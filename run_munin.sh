#!/bin/sh

trap 'kill $bot' EXIT
trap 'exit 0' SIGTERM
while true; do
    /home/andreaja/usr/src/wd/odin/munin.py 2>&1 | tee /home/andreaja/usr/src/wd/odin/botlog
    bot=$!
    wait $bot
    sleep 120
done
