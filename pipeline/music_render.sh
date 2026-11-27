#!/bin/bash
# music.sh NAME "moods" : mix library track into render.mp4 -> /home/claude/out/NAME.mp4, log used.tsv
N=$1; MOODS=$2; MUS=/home/claude/music; git -C $MUS pull -q --rebase origin main
TRK=$(python3 - "$MUS" "$MOODS" <<'PY'
import json, random, sys
m, moods = sys.argv[1], sys.argv[2].split()
lib = json.load(open(m + '/library.json'))
used = [l.rstrip('\n').split('\t')[-1] for l in open(m + '/used.tsv', encoding='utf-8') if l.strip()][-30:]
print(random.choice([x['file'] for x in lib if not x.get('skip') and x['file'] not in used and x.get('duration', 0) >= 20 and x['mood'] in moods]))
PY
)
python3 $MUS/tools/mix.py /home/claude/work/$N/render.mp4 $MUS/$TRK /home/claude/out/$N.mp4 ${GAP:-17}
printf '%s\t%s\t%s\n' "$(TZ=America/New_York date +%m/%d/%Y)" "trial $N" "$TRK" >> $MUS/used.tsv
(cd $MUS && git add used.tsv && git commit -qm "music trial $N" && git -c push.negotiate=true push -q origin main)
echo TRACK $TRK
