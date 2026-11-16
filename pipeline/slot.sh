#!/bin/bash
# slot.sh: may a trial go out now? Prints "NOW" or "NEXT <time for send_later at=...>".
# Slots (America/New_York): 6:15, 7:30, 8:45 AM; 1:00, 2:15, 3:30, 4:45 PM; 9:00, 10:15, 11:30 PM.
# A slot is usable from its start for 15 minutes, and only if no publication (any chat) in the last 50 min.
cd "$(dirname "$0")/.." && git pull -q --rebase origin main 2>/dev/null
LAST=$(git log --format='%ct %s' -30 | grep -v ' cleanup' | head -1 | cut -d' ' -f1)
python3 - "$LAST" <<'EOF'
import sys
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
tz = ZoneInfo("America/New_York")
now = datetime.now(tz)
last = datetime.fromtimestamp(int(sys.argv[1]), tz) if sys.argv[1] else now - timedelta(days=1)
slots = [(6,15),(7,30),(8,45),(13,0),(14,15),(15,30),(16,45),(21,0),(22,15),(23,30)]
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
