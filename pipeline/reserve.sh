#!/bin/bash
# reserve.sh "YYYY-MM-DD HH:MM" NAME ["note"]: book a trial slot for NAME before setting send_later.
# Fails (exit 1) if another NAME already holds it: then run slot.sh NAME again and take the next slot.
# reserve.sh --free NAME : drop NAME's reservations (after publishing or when the video is cancelled).
set -e
cd "$(dirname "$0")/.."
git pull -q --rebase origin main
F=pipeline/reserved.tsv
touch $F
if [ "$1" = "--free" ]; then
  grep -v -P "^[^\t]+\t$2(\t|$)" $F > $F.tmp || true; mv $F.tmp $F
  git add $F; git commit -qm "free $2" || exit 0; git push -q origin HEAD; echo "freed $2"; exit 0
fi
HOLDER=$(awk -F'\t' -v k="$1" '$1==k{print $2}' $F)
if [ -n "$HOLDER" ] && [ "$HOLDER" != "$2" ]; then echo "TAKEN $1 by $HOLDER"; exit 1; fi
[ -z "$HOLDER" ] && printf '%s\t%s\t%s\n' "$1" "$2" "${3:-}" >> $F
git add $F; git commit -qm "reserve $1 $2" || true; git push -q origin HEAD
echo "RESERVED $1 $2"
