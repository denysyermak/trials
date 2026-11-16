#!/bin/bash
# music.sh NAME silent|speech : bake a library track into /home/claude/out/NAME.mp4 (video stream copied, length unchanged).
#   silent = no speech in the video: music is the main sound, the original sound stays very quiet under it.
#   speech = he/someone talks: quiet music bed far under the voice (mix.py, 20 LU below the voice).
# Track: random calm mood (lounge, chillhop, chillhouse, lofi, bossa, sunset, tropical, acoustic), skip=false,
# not among the last 30 rows of used.tsv. Logs the track to /home/claude/music/used.tsv, commits and pushes it.
set -e
NAME=$1; MODE=$2; OUT=/home/claude/out; MUS=/home/claude/music
git -C $MUS pull -q --rebase origin main 2>/dev/null || true
TRK=$(python3 - "$MUS" <<'EOF'
import json, random, sys
m = sys.argv[1]
lib = json.load(open(m + '/library.json'))
used = [l.rstrip('\n').split('\t')[-1] for l in open(m + '/used.tsv', encoding='utf-8') if l.strip()][-30:]
ok = [x['file'] for x in lib if not x.get('skip') and x['file'] not in used and x.get('duration', 0) >= 20
      and x['mood'] in ('lounge', 'chillhop', 'chillhouse', 'lofi', 'bossa', 'sunset', 'tropical', 'acoustic')]
print(random.choice(ok))
EOF
)
if [ "$MODE" = speech ]; then
  python3 $MUS/tools/mix.py $OUT/$NAME.mp4 $MUS/$TRK $OUT/$NAME.m.mp4 20 >/dev/null
else
  D=$(ffprobe -v error -show_entries format=duration -of csv=p=0 $OUT/$NAME.mp4)
  FO=$(python3 -c "print(max(0, $D - 1.5))")
  ffmpeg -v error -y -i $OUT/$NAME.mp4 -stream_loop -1 -i $MUS/$TRK -filter_complex \
   "[1:a]loudnorm=I=-16:TP=-1.5:LRA=11,afade=t=in:d=0.5,afade=t=out:st=$FO:d=1.5[m];[0:a]volume=-16dB[o];[o][m]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.95:level=disabled[a]" \
   -map 0:v -map '[a]' -c:v copy -c:a aac -b:a 192k -ar 48000 -ac 2 -movflags +faststart -t $D $OUT/$NAME.m.mp4
fi
mv $OUT/$NAME.m.mp4 $OUT/$NAME.mp4
printf '%s\t%s\t%s\n' "$(TZ=America/New_York date +%m/%d/%Y)" "trial $NAME" "$TRK" >> $MUS/used.tsv
(cd $MUS && git add used.tsv && git commit -qm "trial $NAME: $TRK" && git -c push.negotiate=true push -q origin main) || echo "WARN: used.tsv not pushed"
echo "$NAME <- $TRK ($MODE)"
