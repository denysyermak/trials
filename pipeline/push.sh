#!/bin/bash
# push.sh NAME : copy out/NAME.mp4 to repo and push; print raw url
set -e
cd /home/claude/trials
git pull -q --rebase origin main
cp /home/claude/out/$1.mp4 .
git add $1.mp4 && git commit -qm "$1" && git push -q origin HEAD
echo "https://raw.githubusercontent.com/denysyermak/trials/main/$1.mp4"
