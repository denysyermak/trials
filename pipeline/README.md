# Trial Reels pipeline

Clone to /home/claude/trials. Setup: `pip install --break-system-packages faster-whisper` (model "medium" downloads on first run).

1. `python3 -I pipeline/process.py <video.mov> /home/claude/out`: Russian speech -> word timestamps -> phrase subtitles (.ass, Inter ExtraBold 74, white, black outline, above Instagram bottom UI). No VAD (VAD dropped speech). FIXES dict = word corrections.
2. `--rechunk NAME /home/claude/out` rebuilds subtitles from saved .json after editing FIXES.
3. `encode.sh in.mov subs.ass out.mp4`: 1080x1920 H.264 CRF 21, maxrate 8M, AAC, faststart (~30-40 MB / 30 s).
4. `push.sh NAME` -> raw.githubusercontent.com URL -> vidiq_video_upload(url) -> vidiq_instagram_publish_reel(trialParams MANUAL, account 28924267387235125) -> poll containerId until PUBLISHED.
5. `done.sh NAME PERMALINK` removes the file from the repo and logs it.
Raw URLs cache ~5 min: never reuse a file name for a changed video.
