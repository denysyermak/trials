#!/bin/bash
# slot.sh [NAME]: may a trial go out now? Prints "NOW" or "NEXT <time for send_later at=...>".
# Slots (America/New_York, Denys 11/25/2026, max 7 trials a day): 12:00 AM; 7:00, 9:00 AM; 1:00, 3:00, 5:00 PM; 10:00 PM. Main Reels 11 AM and 8 PM.
# A slot is usable from its start for 15 minutes, and only if no publication (any chat) in the last 50 min.
# RESERVATIONS (11/28/2026): pipeline/reserved.tsv lists slots already taken by a timer in some chat
# ("YYYY-MM-DD HH:MM<TAB>NAME<TAB>note"). NEXT never offers a slot reserved by another NAME.
# With NAME: NOW only if the slot is free or reserved by this NAME. Without NAME (old chats): old behaviour for NOW.
# After NEXT, reserve it at once: bash pipeline/reserve.sh "YYYY-MM-DD HH:MM" NAME "note", then send_later.
# `bash pipeline/slot.sh --list` shows today's and tomorrow's slots with their reservations.
cd "$(dirname "$0")/.." && git pull -q --rebase origin main 2>/dev/null
# A publication = a 'cleanup NAME' commit (done.sh runs right after PUBLISHED). Main-Reel uploads ('R1234', 'remove ... after upload') are scheduled posts and do not count.
LAST=$(git log --format='%ct %s' -60 | grep -E '^[0-9]+ cleanup ' | head -1 | cut -d' ' -f1)
python3 - "$LAST" "${1:-}" <<'EOF'
import sys, os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
tz = ZoneInfo("America/New_York")
now = datetime.now(tz)
last = datetime.fromtimestamp(int(sys.argv[1]), tz) if sys.argv[1] else now - timedelta(days=1)
me = sys.argv[2]
listing = me == "--list"
slots = [(0,0),(7,0),(9,0),(13,0),(15,0),(17,0),(22,0)]
earliest = last + timedelta(minutes=50)
res = {}
p = "pipeline/reserved.tsv"
if os.path.exists(p):
    for line in open(p, encoding="utf-8"):
        f = line.rstrip("\n").split("\t")
        if len(f) >= 2 and f[0][:1].isdigit():
            res[f[0]] = f[1:]
def key(s): return s.strftime("%Y-%m-%d %H:%M")
if listing:
    for d in range(2):
        day = (now + timedelta(days=d)).date()
        for h, m in slots:
            s = datetime(day.year, day.month, day.day, h, m, tzinfo=tz)
            r = res.get(key(s))
            state = "past" if s + timedelta(minutes=15) <= now else ("RESERVED " + " ".join(r) if r else "free")
            print(key(s), state)
    sys.exit()
for d in range(3):
    day = (now + timedelta(days=d)).date()
    for h, m in slots:
        s = datetime(day.year, day.month, day.day, h, m, tzinfo=tz)
        r = res.get(key(s))
        taken = r is not None and r[0] != me
        if s <= now < s + timedelta(minutes=15) and now >= earliest and not (me and taken):
            print("NOW"); sys.exit()
        if s > now and s >= earliest and not taken:
            print("NEXT " + s.strftime("%Y-%m-%dT%H:%M:00") + "[America/New_York]"); sys.exit()
EOF
