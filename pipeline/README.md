# Trial Reels pipeline

Goal: Denys drops a batch of videos into the chat; Claude subtitles them and publishes each to Instagram @denys.yermak.realtor as a **trial Reel** (graduationStrategy MANUAL), one every 50 minutes, without asking for confirmation. Nothing goes to Facebook or TikTok.

## Rules agreed with Denys
- Trial only, MANUAL. Account platformAccountId `28924267387235125` (vidIQ, Always Allow).
- Caption: one short Russian phrase about what the video shows. No emoji, no hashtags.
- Subtitles: simple white phrases, black outline, above Instagram's bottom UI.
- Interval 50 min. Instagram allows ~30 trial Reels per 24 h (Denys's count); 50 min = ~29/day, safely under. Never go below 50 min. (At 15 min Reels sat at zero views.)
- CONVEYOR mode, not batch: process video 1 and publish it at once, then keep processing the rest between publications. Do not trim videos (any length).
- Never invent words. If a fragment stays unclear after re-transcription, delete those words from the SUBTITLES only (video and audio stay untouched) and tell Denys which ones.
- After each publish: short message with link + caption. At the end: full list of links.

## Setup (new chat)
1. add_repo denysyermak/trials (push), `git clone --depth 1 https://github.com/denysyermak/trials /home/claude/trials`, register_repo_root.
2. `pip install -q --break-system-packages faster-whisper`, then preload: `python3 -c "from faster_whisper import WhisperModel; WhisperModel('medium',device='cpu',compute_type='int8')"` (run from /tmp).
3. `git config user.name Claude; git config user.email noreply@anthropic.com`; `git push --dry-run` to check access. `mkdir -p /home/claude/out`.
4. Load vidIQ tools: `select:mcp__vidIQ__vidiq_video_upload,mcp__vidIQ__vidiq_instagram_publish_reel`.

## Conveyor (the order of work)
A send_later timer does NOT interrupt a running turn: it waits until the turn ends. So never process for more than ~35 min in one turn.

First turn (videos just arrived):
1. Put all names into queue.tsv in file-number order with an empty caption for now.
2. Process video 1 fully (steps A-C below), write its caption, publish it (step D), tell Denys link + caption.
3. Process the next videos one by one until ~35 min have passed since that publish.
4. send_later(delay_minutes = 50 minus minutes already spent after the publish, at least 1) with the timer message (step E). End the turn.

Each timer turn:
1. Next video = `bash pipeline/next.sh`. If it is processed (NAME.mp4 exists and caption filled), publish it. If not, process it first, then publish.
2. Tell Denys link + caption.
3. Process further unprocessed videos for up to ~35 min, then send_later for the remaining time to 50 min, end the turn.
4. Queue empty: give the full list of links of this batch from published.log, no new timer.

## A. Transcribe (foreground only, background processes die after a reply)
Use the prompt, it restores punctuation and spells local names right:
```
export PROMPT="Привет, друзья! Это Флорида, St. Johns County, Джексонвилл. Недвижимость, риэлтор, аквапарк, townhouse."
timeout 280 python3 -I pipeline/process.py /mnt/user-data/uploads/NAME.mov /home/claude/out
```
Add brand/place names seen in frames to PROMPT (e.g. "V Pizza"). A 20-60 s video takes ~1-2 min.

## B. Check the transcript
Read the full text + subtitle chunks. Typical errors: риэлтор, Джексонвилл, недвижимость, English place names, kids' speech.
- Look at frames (ffmpeg -ss T -frames:v 1) to identify signs, restaurants, communities.
- Unclear fragment: cut it to a wav (`ffmpeg -ss S -t D -i in.mov -vn -ac 1 -ar 16000 x.wav`), re-transcribe with beam 1/5, with and without prompt. Load wav as numpy (int16/32768), not by path. Still unclear -> delete from subtitles.
- Fix with `python3 pipeline/editwords.py NAME 'old=new' 'old@-2=new' '#30-36='` (`--show` lists indexes). It reruns --rechunk.
- Recurring errors go into FIXES in process.py (commit them).

## C. Encode + spot check + caption
`timeout 120 bash pipeline/encode.sh /mnt/user-data/uploads/NAME.mov /home/claude/out/NAME.ass /home/claude/out/NAME.tmp.mp4 && mv /home/claude/out/NAME.tmp.mp4 /home/claude/out/NAME.mp4`. Look at 3-4 frames in one hstack jpg: subtitles readable, above bottom UI, video not stretched. Write the caption into queue.tsv (`NAME<TAB>caption`).

## D. Publish one
1. `bash pipeline/push.sh NAME` -> prints raw.githubusercontent.com URL.
2. `vidiq_video_upload(url=RAW, title=NAME)` -> videoUrl.
3. `vidiq_instagram_publish_reel(platformAccountId, videoUrl, caption, trialParams={graduationStrategy: MANUAL})` -> containerId.
4. sleep ~50 s, call again with containerId only; repeat every ~20 s until PUBLISHED (takes 45-75 s).
5. `bash pipeline/done.sh NAME PERMALINK` (removes the mp4 from the repo, appends to published.log).
On any error: stop, do not retry automatically, tell Denys.

## E. Timer message
`send_later(delay_minutes=..., initiation=human_schedule, message=...)`:
> Таймер: конвейер trial Reels по pipeline/README.md. Следующий ролик: `bash /home/claude/trials/pipeline/next.sh`. Если он ещё не обработан, обработай (A-C), затем опубликуй (D), коротко сообщи Денису ссылку и подпись. Потом обрабатывай следующие ролики не дольше ~35 минут и поставь новый send_later так, чтобы следующая публикация вышла через 50 минут после этой (не раньше: лимит Instagram ~30 trial в сутки). Видео не режь, неразборчивые слова убирай только из субтитров. Если очередь пуста, дай итоговый список всех ссылок этой пачки из published.log.

## What did NOT work
- Hosting via claude.ai artifact: vidIQ gets no Content-Length.
- Google Drive from Claude's environment is blocked.
- Background processes stop after the reply: do everything in the foreground.
- VAD in whisper dropped chunks of speech.
- raw GitHub URLs cache ~5 min: a corrected video needs a new file name.
- Without PROMPT whisper sometimes returns text with no punctuation at all.

## Log
11/06-07/2026: 19 + 12 Reels published this way. published.log is local to the session (not committed).
