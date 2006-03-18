#!/bin/sh

trap 'kill $bot' EXIT
trap 'exit 0' SIGTERM
while true; do
    /home/andreaja/usr/src/wd/odin/munin.py > /home/andreaja/usr/src/wd/odin/botlog 2>&1
    bot=$!
    wait $bot
    sleep 120
done
