#!/bin/bash
# Prints "NAME<TAB>caption" of the first queue entry not yet in published.log; empty when the queue is done.
Q=${1:-/home/claude/out/queue.tsv}
LOG=$(dirname "$0")/published.log
while IFS=$'\t' read -r n c; do
  [ -z "$n" ] && continue
  grep -q "^$n " "$LOG" 2>/dev/null || { printf '%s\t%s\n' "$n" "$c"; exit 0; }
done < "$Q"
