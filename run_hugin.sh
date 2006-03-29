#!/bin/sh

botexe="/home/idimmu/Projects/odin/hugin.py"
botname="/home/idimmu/Projects/odin/pid.hugin"
botdir="/home/idimmu/Projects/odin"

cd $botdir
if test -r $botname; then
  # there is a pid file -- is it current?
  botpid=`cat $botname`
  if `kill -CHLD $botpid >/dev/null 2>&1`; then
    # it's still going
    # back out quietly
    exit 0
  fi
  echo "Hugin Crontab notice:"
  echo ""
  echo "Stale $botname file (erasing it)"
  rm -f $botname
fi
echo ""
echo "No Hugin running. Reloading it..."
echo ""
#mv -f $botdir/log $botdir/oldlog
$botexe #> $botdir/log 2>&1 &

