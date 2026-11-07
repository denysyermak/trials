#!/bin/bash
# done.sh NAME PERMALINK : remove from repo, log
set -e
cd /home/claude/trials
git rm -q $1.mp4 && git commit -qm "cleanup $1" && git push -q origin HEAD
echo "$1 published $2 $(TZ=America/New_York date +%H:%M)" >> /home/claude/trials/pipeline/published.log
echo logged
