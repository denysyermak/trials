# Trial Reels pipeline

Goal: Denys drops a batch of videos into the chat; Claude subtitles them and publishes each to Instagram @denys.yermak.realtor as a **trial Reel** (graduationStrategy MANUAL), in fixed time slots (max 5 a day, see «Schedule»), without asking for confirmation. Nothing goes to Facebook or TikTok.

## Rules agreed with Denys
- Trial only, MANUAL. Account platformAccountId `28924267387235125` (vidIQ, Always Allow).
- Caption (Denys, 11/09/2026; contact question changed 11/19/2026; same as skill reels-scripts «Trial Reels»): first line = one short Russian phrase about what the video shows, then an empty line, then two fixed contact lines. No emoji, no hashtags. queue.tsv keeps only the first line; add the contact lines when publishing (step D):
  ```
  [О чём это видео, одной строкой]

  Нужен дом в Jacksonville или St. Johns? Пишите: WhatsApp, Telegram, SMS +1 (754) 286-8238
  Denys Yermak, REALTOR®, Berkshire Hathaway HomeServices Florida Network Realty
  ```
  On screen: subtitles only, no contact strip on trials.
- If vidiq_instagram_publish_reel returns "inconclusive (Meta code 2)", do not republish and do not set the next timer: ask Denys whether it came out. If he says to continue from that video, publish it again with a new container.
- Subtitles: simple white phrases, black outline, above Instagram's bottom UI.
- Schedule (Denys, 11/19/2026, replaces the 10 slots of 11/16): at most 5 trials a day, only in these slots, America/New_York: 8:45 AM; 1:00, 3:30 PM; 9:00, 10:15 PM. Why fewer: 11/06-11/16/2026 at 14-28 trials a day views per day grew about 4x, but follows per day stayed almost the same (4.6 vs 5.7) and 93% of trials got no comment. Never 9 AM-1 PM and 5-9 PM: main Reels go out at 11 AM and 7 PM and get 2 hours each to themselves. Nothing 10:30 PM-8:45 AM.
- Slots are shared by ALL chats. Before every publish run `bash pipeline/slot.sh` (it pulls and reads git log): `NOW` = publish; `NEXT <time>` = do not publish, set `send_later(at=<time>)`. A slot is open for 15 min after its start and only if no trial was published (a 'cleanup NAME' commit) in the last 50 min.
- CONVEYOR mode, not batch: process video 1 and publish it at once, then keep processing the rest between publications. Do not trim videos (any length).
- Never invent words. If a fragment stays unclear after re-transcription, delete those words from the SUBTITLES only (video and audio stay untouched) and tell Denys which ones.
- After each publish: short message with link + caption. At the end: full list of links.
- Music (Denys, 11/16/2026): every trial gets a track from the private library denysyermak/music, a different one each time: `bash pipeline/music.sh NAME silent|speech` after encode. `silent` = no speech kept in subtitles: music is the main sound, original sound stays very quiet under it. `speech` = someone talks: quiet bed 20 LU under the voice. Video stream copied, length unchanged.
- Kelsie light (Denys, 11/16/2026): subtitles stay as they are (white phrases, black outline). Videos WITHOUT speech also get one hook line for the first 2.8 s: `python3 pipeline/hook.py NAME "тонкая часть" "КЛЮЧЕВОЕ"` (Inter Thin + yellow Inter ExtraBold key word). Hook = a concrete fact a stranger understands in 1 s (a number, a place, a contrast), only facts that are certain (place seen in frames or known from Denys). Not sure -> no hook. Videos with speech get no hook. Run hook.py AFTER editwords.py (rechunk rewrites the .ass) and right before encode.sh.
- Full Kelsie (cover, rubric colour, chrome word) only for trial winners that Denys moves to a main slot (11 AM or 7 PM), not in this pipeline.
- Test (from 11/16/2026): after the first 10 silent trials with hook + music, compare their views and skip rate with the 11/15 batch (silent trials without hook and music: about 270 views on average, skip rate 66-85%; trials with speech 345-1,720) and tell Denys. If no clear gain, ask him whether to keep it.

## Setup (new chat)
1. add_repo denysyermak/trials (push), `git clone --depth 1 https://github.com/denysyermak/trials /home/claude/trials`, register_repo_root.
2. `pip install -q --break-system-packages faster-whisper`, then preload: `python3 -c "from faster_whisper import WhisperModel; WhisperModel('medium',device='cpu',compute_type='int8')"` (run from /tmp).
3. `git config user.name Claude; git config user.email noreply@anthropic.com`; `git push --dry-run` to check access. `mkdir -p /home/claude/out`.
4. Load vidIQ tools: `select:mcp__vidIQ__vidiq_video_upload,mcp__vidIQ__vidiq_instagram_publish_reel`.
5. Music library: add_repo denysyermak/music (push), `git clone --depth 1 https://github.com/denysyermak/music /home/claude/music`, then `git -C /home/claude/music config user.name Claude; git -C /home/claude/music config user.email noreply@anthropic.com` (music.sh logs every used track to used.tsv and pushes it).

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

## C. Hook, encode, music, spot check, caption
1. Video without speech and a certain fact: `python3 pipeline/hook.py NAME "тонкая часть" "КЛЮЧЕВОЕ"`.
2. `timeout 120 bash pipeline/encode.sh /mnt/user-data/uploads/NAME.mov /home/claude/out/NAME.ass /home/claude/out/NAME.tmp.mp4 && mv /home/claude/out/NAME.tmp.mp4 /home/claude/out/NAME.mp4`.
3. `bash pipeline/music.sh NAME silent` (no speech) or `bash pipeline/music.sh NAME speech`.
4. Look at 3-4 frames in one hstack jpg: hook and subtitles readable, above bottom UI, video not stretched. Write the caption into queue.tsv (`NAME<TAB>caption`).

## D. Publish one
1. `bash pipeline/push.sh NAME` -> prints raw.githubusercontent.com URL.
2. `vidiq_video_upload(url=RAW, title=NAME)` -> videoUrl.
3. `vidiq_instagram_publish_reel(platformAccountId, videoUrl, caption = queue line + empty line + the 2 contact lines from Rules, trialParams={graduationStrategy: MANUAL})` -> containerId.
4. sleep ~50 s, call again with containerId only; repeat every ~20 s until PUBLISHED (takes 45-75 s).
5. `bash pipeline/done.sh NAME PERMALINK` (removes the mp4 from the repo, appends to published.log).
On any error: stop, do not retry automatically, tell Denys.

## E. Timer message
`send_later(at=<NEXT time from slot.sh>, initiation=human_schedule, message=...)`:
> Таймер: конвейер trial Reels по pipeline/README.md. Сначала `bash /home/claude/trials/pipeline/slot.sh`: NEXT = слот занят другим чатом, поставь send_later на это время и закончи. NOW = следующий ролик `bash /home/claude/trials/pipeline/next.sh`; если не обработан, обработай (A-C), опубликуй (D), коротко сообщи Денису ссылку и подпись. Потом обрабатывай остальные до ~10 минут перед следующим слотом и поставь send_later(at) на следующий слот из slot.sh. Не больше 5 trial в сутки, только в слоты. Видео не режь, неразборчивые слова убирай только из субтитров. Meta code 2: не публикуй повторно, спроси Дениса. Очередь пуста: дай список всех ссылок этой пачки из published.log.

## What did NOT work
- Hosting via claude.ai artifact: vidIQ gets no Content-Length.
- Google Drive from Claude's environment is blocked.
- Background processes stop after the reply: do everything in the foreground.
- VAD in whisper dropped chunks of speech.
- raw GitHub URLs cache ~5 min: a corrected video needs a new file name.
- Without PROMPT whisper sometimes returns text with no punctuation at all.

## Log
11/19/2026: 5 slots a day instead of 10 (slot.sh); contact line now «Нужен дом в Jacksonville или St. Johns?» instead of «Нужна недвижимость в Америке?».
11/14-15/2026: 18 published at 50-min interval. 11/16/2026: switched to 10 fixed slots a day (slot.sh); music for every trial (music.sh) and a hook line on videos without speech (hook.py).
11/06-07/2026: 19 + 12 Reels published this way. published.log is local to the session (not committed).
