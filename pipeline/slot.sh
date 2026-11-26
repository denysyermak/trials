#!/bin/bash
# slot.sh: may a trial go out now? Prints "NOW" or "NEXT <time for send_later at=...>".
# Slots (America/New_York, Denys 11/25/2026, max 7 trials a day): 12:00 AM; 7:00, 9:00 AM; 1:00, 3:00, 5:00 PM; 10:00 PM. Main Reels 11 AM and 8 PM.
# A slot is usable from its start for 15 minutes, and only if no publication (any chat) in the last 50 min.
cd "$(dirname "$0")/.." && git pull -q --rebase origin main 2>/dev/null
# A publication = a 'cleanup NAME' commit (done.sh runs right after PUBLISHED). Main-Reel uploads ('R1234', 'remove ... after upload') are scheduled posts and do not count.
LAST=$(git log --format='%ct %s' -60 | grep -E '^[0-9]+ cleanup ' | head -1 | cut -d' ' -f1)
python3 - "$LAST" <<'EOF'
import sys
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
tz = ZoneInfo("America/New_York")
now = datetime.now(tz)
last = datetime.fromtimestamp(int(sys.argv[1]), tz) if sys.argv[1] else now - timedelta(days=1)
slots = [(0,0),(7,0),(9,0),(13,0),(15,0),(17,0),(22,0)]
earliest = last + timedelta(minutes=50)
for d in range(3):
    day = (now + timedelta(days=d)).date()
    for h, m in slots:
        s = datetime(day.year, day.month, day.day, h, m, tzinfo=tz)
        if s <= now < s + timedelta(minutes=15) and now >= earliest:
            print("NOW"); sys.exit()
        if s > now and s >= earliest:
            print("NEXT " + s.strftime("%Y-%m-%dT%H:%M:00") + "[America/New_York]"); sys.exit()
EOF
