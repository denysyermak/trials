# Trial Reels pipeline

Goal: Denys drops a batch of videos into the chat; Claude subtitles them and publishes each to Instagram @denys.yermak.realtor as a **trial Reel** (graduationStrategy MANUAL), in fixed time slots (max 10 a day, see «Schedule»), without asking for confirmation. Nothing goes to Facebook or TikTok.

## Rules agreed with Denys
- Trial only, MANUAL. Account platformAccountId `28924267387235125` (vidIQ, Always Allow).
- Caption (Denys, 11/09/2026, same as skill reels-scripts «Trial Reels»): first line = one short Russian phrase about what the video shows, then an empty line, then two fixed contact lines. No emoji, no hashtags. queue.tsv keeps only the first line; add the contact lines when publishing (step D):
  ```
  [О чём это видео, одной строкой]

  Нужна недвижимость в Америке? Пишите: WhatsApp, Telegram, SMS +1 (754) 286-8238
  Denys Yermak, REALTOR®, Berkshire Hathaway HomeServices Florida Network Realty
  ```
  On screen: subtitles only, no contact strip on trials.
- If vidiq_instagram_publish_reel returns "inconclusive (Meta code 2)", do not republish and do not set the next timer: ask Denys whether it came out. If he says to continue from that video, publish it again with a new container.
- Subtitles: simple white phrases, black outline, above Instagram's bottom UI.
- Schedule (Denys, 11/16/2026, replaces the 50-min interval): at most 10 trials a day, only in these slots, America/New_York: 6:15, 7:30, 8:45 AM; 1:00, 2:15, 3:30, 4:45 PM; 9:00, 10:15, 11:30 PM. Never 9 AM-1 PM and 5-9 PM: main Reels go out at 11 AM and 7 PM and get 2 hours each to themselves. Nothing 11:45 PM-6:15 AM.
- Slots are shared by ALL chats. Before every publish run `bash pipeline/slot.sh` (it pulls and reads git log): `NOW` = publish; `NEXT <time>` = do not publish, set `send_later(at=<time>)`. A slot is open for 15 min after its start and only if nobody published in the last 50 min.
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
2. Process video 1 fully (steps A-C below), write its caption, run `bash pipeline/slot.sh`. NOW: publish it (step D), tell Denys link + caption. NEXT: tell Denys when it goes out.
3. Process the next videos one by one, but stop ~10 min before the next slot (`slot.sh` shows it).
4. send_later(at = the next slot from `slot.sh`) with the timer message (step E). End the turn.

Each timer turn:
1. `bash pipeline/slot.sh`. NEXT: another chat took this slot, set send_later(at=NEXT time), end the turn. NOW: next video = `bash pipeline/next.sh`. If it is processed (NAME.mp4 exists and caption filled), publish it. If not, process it first (if the 15-min slot window passes, wait for the next slot), then publish.
2. Tell Denys link + caption.
3. Process further unprocessed videos until ~10 min before the next slot, then send_later(at = next slot from `slot.sh`), end the turn.
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
3. `vidiq_instagram_publish_reel(platformAccountId, videoUrl, caption = queue line + empty line + the 2 contact lines from Rules, trialParams={graduationStrategy: MANUAL})` -> containerId.
4. sleep ~50 s, call again with containerId only; repeat every ~20 s until PUBLISHED (takes 45-75 s).
5. `bash pipeline/done.sh NAME PERMALINK` (removes the mp4 from the repo, appends to published.log).
On any error: stop, do not retry automatically, tell Denys.

## E. Timer message
`send_later(at=<NEXT time from slot.sh>, initiation=human_schedule, message=...)`:
> Таймер: конвейер trial Reels по pipeline/README.md. Сначала `bash /home/claude/trials/pipeline/slot.sh`: NEXT = слот занят другим чатом, поставь send_later на это время и закончи. NOW = следующий ролик `bash /home/claude/trials/pipeline/next.sh`; если не обработан, обработай (A-C), опубликуй (D), коротко сообщи Денису ссылку и подпись. Потом обрабатывай остальные до ~10 минут перед следующим слотом и поставь send_later(at) на следующий слот из slot.sh. Не больше 10 trial в сутки, только в слоты. Видео не режь, неразборчивые слова убирай только из субтитров. Meta code 2: не публикуй повторно, спроси Дениса. Очередь пуста: дай список всех ссылок этой пачки из published.log.

## What did NOT work
- Hosting via claude.ai artifact: vidIQ gets no Content-Length.
- Google Drive from Claude's environment is blocked.
- Background processes stop after the reply: do everything in the foreground.
- VAD in whisper dropped chunks of speech.
- raw GitHub URLs cache ~5 min: a corrected video needs a new file name.
- Without PROMPT whisper sometimes returns text with no punctuation at all.

## Log
11/14-15/2026: 18 published at 50-min interval. 11/16/2026: switched to 10 fixed slots a day (slot.sh).
11/06-07/2026: 19 + 12 Reels published this way. published.log is local to the session (not committed).
