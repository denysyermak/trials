# Trial Reels pipeline

Goal: Denys drops a batch of videos into the chat; Claude subtitles them and publishes each to Instagram @denys.yermak.realtor as a **trial Reel** (graduationStrategy MANUAL), one every 30 minutes, without asking for confirmation. Nothing goes to Facebook or TikTok.

## Rules agreed with Denys
- Trial only, MANUAL. Account platformAccountId `28924267387235125` (vidIQ, Always Allow).
- Caption: one short Russian phrase about what the video shows. No emoji, no hashtags.
- Subtitles: simple white phrases, black outline, above Instagram's bottom UI.
- Interval 30 min (at 15 min Reels sat at zero views while the next one went out).
- Process the WHOLE batch first, then publish. Do not trim videos longer than 30 s.
- Never invent words. If a fragment stays unclear after re-transcription, delete it from the subtitles and tell Denys which ones.
- After each publish: short message with link + caption. At the end: full list of links.

## Setup (new chat)
1. add_repo denysyermak/trials (push), `git clone --depth 1 https://github.com/denysyermak/trials /home/claude/trials`, register_repo_root.
2. `pip install -q --break-system-packages faster-whisper`, then preload: `python3 -c "from faster_whisper import WhisperModel; WhisperModel('medium',device='cpu',compute_type='int8')"` (run from /tmp).
3. `git config user.name Claude; git config user.email noreply@anthropic.com`; `git push --dry-run` to check access. `mkdir -p /home/claude/out`.
4. Load vidIQ tools: `select:mcp__vidIQ__vidiq_video_upload,mcp__vidIQ__vidiq_instagram_publish_reel`.

## Step 1: transcribe the batch (foreground only, background processes die after a reply)
Use the prompt from the start, it restores punctuation and spells local names right:
```
export PROMPT="Привет, друзья! Это Флорида, St. Johns County, Джексонвилл. Недвижимость, риэлтор, аквапарк, townhouse."
for f in A B C; do timeout 280 python3 -I pipeline/process.py /mnt/user-data/uploads/$f.mov /home/claude/out; done
```
Keep each Bash call under 10 min (several videos per call, re-run skips nothing, so list only the ones left). Add brand/place names seen in frames to PROMPT (e.g. "V Pizza").

## Step 2: check every transcript
Print full text + subtitle chunks for each video and read them all. Typical errors: риэлтор, Джексонвилл, недвижимость, English place names, kids' speech.
- Look at frames (ffmpeg -ss T -frames:v 1) to identify signs, restaurants, communities.
- Unclear fragment: cut it to a wav (`ffmpeg -ss S -t D -i in.mov -vn -ac 1 -ar 16000 x.wav`), re-transcribe with beam 1/5, with and without prompt. Load wav as numpy (int16/32768), not by path. Still unclear -> delete.
- Fix with `python3 pipeline/editwords.py NAME 'old=new' 'old@-2=new' '#30-36='` (`--show` lists indexes). It reruns --rechunk.
- Recurring errors go into FIXES in process.py (commit them).

## Step 3: encode + spot check
`timeout 120 bash pipeline/encode.sh /mnt/user-data/uploads/NAME.mov /home/claude/out/NAME.ass /home/claude/out/NAME.mp4` (encode to a .tmp.mp4 and mv, so a killed run never leaves a broken file). Grab 3-4 frames into one hstack jpg and look: subtitles readable, above bottom UI, video not stretched.

## Step 4: queue
Write `/home/claude/out/queue.tsv`: `NAME<TAB>caption`, one line per video, in the order to publish (usually file number order). `pipeline/next.sh` prints the next unpublished line.

## Step 5: publish one
1. `bash pipeline/push.sh NAME` -> prints raw.githubusercontent.com URL.
2. `vidiq_video_upload(url=RAW, title=NAME)` -> videoUrl.
3. `vidiq_instagram_publish_reel(platformAccountId, videoUrl, caption, trialParams={graduationStrategy: MANUAL})` -> containerId.
4. sleep ~50 s, call again with containerId only; repeat every ~20 s until PUBLISHED (takes 45-75 s).
5. `bash pipeline/done.sh NAME PERMALINK` (removes the mp4 from the repo, appends to published.log).
On any error: stop, do not retry automatically, tell Denys.

## Step 6: timer
Publish the first video right away (or when 30 min passed since the last one), then after each publish:
`send_later(delay_minutes=30, initiation=human_schedule, message=...)` with this message:
> Таймер: опубликуй следующий trial Reel. Возьми строку из `bash /home/claude/trials/pipeline/next.sh`. Цепочка: push.sh NAME -> vidiq_video_upload(raw url) -> vidiq_instagram_publish_reel (account 28924267387235125, caption из queue.tsv, trialParams MANUAL) -> ждать PUBLISHED -> done.sh NAME PERMALINK. Затем коротко сообщи Денису ссылку и подпись и поставь следующий таймер send_later на 30 минут, если в очереди ещё есть ролики. Если очередь пуста, дай итоговый список всех ссылок этой пачки из published.log.

## What did NOT work
- Hosting via claude.ai artifact: vidIQ gets no Content-Length.
- Google Drive from Claude's environment is blocked.
- Background processes stop after the reply: do everything in the foreground.
- VAD in whisper dropped chunks of speech.
- raw GitHub URLs cache ~5 min: a corrected video needs a new file name.
- Without PROMPT whisper sometimes returns text with no punctuation at all.

## Log
11/06-07/2026: 19 + 12 Reels published this way. published.log is local to the session (not committed).
