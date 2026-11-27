# Trial Reels pipeline

Goal: Denys drops a batch of videos into the chat; Claude subtitles them and publishes each to Instagram @denys.yermak.realtor as a **trial Reel** (graduationStrategy MANUAL), in fixed time slots (7 a day, one in each slot, see «Schedule»), without asking for confirmation. Nothing goes to Facebook or TikTok.

## Rules agreed with Denys
- Trial only, MANUAL. Account platformAccountId `28924267387235125` (vidIQ, Always Allow).
- FULL KELSIE ON EVERY TRIAL (Denys, 11/19/2026, replaces «subtitles only» and «Kelsie light»). Each trial is made as a finished main Reel, so a winner goes to the feed with one tap. Edit by skill `reels-editor` (mode «Готовое видео Дениса»): hook from the middle (a 2.5-4 s copy of the strongest moment placed at the start, the moment STAYS in the middle, section «Hook first»), Kelsie text (`reels-style-kelsie`), rubric colour, chrome key word, contact strip in the last 5 s on real estate Reels, music from denysyermak/music (`tools-music`). Videos without speech: no teaser needed if nothing stands out, but a hook line with a certain fact as before.
- LIVE COVER (Denys, 11/19/2026). Instagram and TikTok take the first frame as the cover (vidIQ cannot set a custom one), so frame 0 IS the cover, and it must be live, not a freeze: the teaser starts on a sharp frame where Denys looks into the camera, ideally smiling (pick it by the «Cover image» scoring in `reels-editor`; shift the teaser start by a few tenths of a second inside the chosen moment to land on such a frame). The cover text (place pill with FLORIDA, the big key word = the hook word, the price smaller under it on property Reels) is on screen from frame 0 for the whole teaser while the video plays. No still image, no stop-frame, no inserted 2-frame picture. If no sharp face frame exists in the chosen moment, pick another moment. Also export frame 0 as NAME_cover.png for the record. One property: never repeat a hook moment, key word or cover frame (`claude/hooks-by-house.md`).
- Caption (Denys, 11/19/2026, replaces the short 3-line trial caption): the full Instagram caption by `reels-scripts`: hook as the first line, text, price as one dated line on property Reels, keyword CTA only where `reels-scripts` allows it, the contact block «Контакты в описании», «Listed by» when it is another agent's listing, then 3-5 checked hashtags (sizes measured, rule in `reels-scripts`). Keep it in NAME.caption.txt (multi-line); queue.tsv keeps only NAME and the first line.
- A trial that takes off: Denys taps «Share with everyone» himself (the evening main slot, 8 PM ET, Tue/Thu/Sat, picked at the Monday review). Never republish it as a new post: a duplicate loses the views and comments the trial already has.
- If vidiq_instagram_publish_reel returns "inconclusive (Meta code 2)", do not republish and do not set the next timer: ask Denys whether it came out. If he says to continue from that video, publish it again with a new container.
- Schedule (Denys, 11/25/2026, replaces the 5 slots of 11/19): 7 trials a day, one per slot, only in these slots, America/New_York: 12:00 AM; 7:00, 9:00 AM; 1:00, 3:00, 5:00 PM; 10:00 PM. Main Reels go out at 11 AM and 8 PM and keep 2 hours each to themselves: no trial 11 AM-1 PM and 8-10 PM. History: 11/19/2026 cut 14-28 trials a day to 5 because views per day grew about 4x but follows per day stayed almost the same (4.6 vs 5.7) and 93% of trials got no comment; 11/25/2026 Denys moved to 7 slots.
- Slots are shared by ALL chats. Before every publish run `bash pipeline/slot.sh` (it pulls and reads git log): `NOW` = publish; `NEXT <time>` = do not publish, set `send_later(at=<time>)`. A slot is open for 15 min after its start and only if no trial was published (a 'cleanup NAME' commit) in the last 50 min.
- CONVEYOR mode, not batch: process video 1 and publish it at once, then keep processing the rest between publications. Do not trim videos (any length).
- Never invent words. If a fragment stays unclear after re-transcription, delete those words from the SUBTITLES only (video and audio stay untouched) and tell Denys which ones.
- After each publish: short message with link + caption. At the end: full list of links.
- Music (Denys, 11/16/2026): every trial gets a track from the private library denysyermak/music, a different one each time. With the full Kelsie edit use `tools-music` Часть 3 (17 LU under his voice); `bash pipeline/music.sh NAME silent|speech` still works for a file rendered here (`silent`: music is the main sound, `speech`: bed 20 LU under the voice).
- Time: about 15-25 min per trial now. Conveyor rule stays: never more than ~35 min of processing in one turn.
- Test (from 11/20/2026): full-Kelsie trials vs trials of 11/15-11/18/2026 (subtitles, hook line, music): views, skip rate, follows per 1,000 views. Report at the Monday review (content-market-research).
- Old tools kept for reference: hook.py and encode.sh (Kelsie light, 11/16-11/19/2026).

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

## C. Full Kelsie edit, live cover, music, spot check, caption
1. Load skill `reels-editor` (it opens `reels-style-kelsie`, `tools-music`). Pick the hook moment from the transcript and a contact sheet; its first frame must be a sharp face frame (see «LIVE COVER»).
2. Render by `reels-editor`: teaser copy at the start with the cover text from frame 0, Kelsie captions, contact strip on real estate Reels, music baked in. Output /home/claude/out/NAME.mp4 (1080x1920 H.264).
3. Check: frame 0 at grid size 437x584 (a good cover by itself), 3-4 more frames in one hstack jpg (text readable, above bottom UI, not stretched), the moment still plays in the middle.
4. Caption into NAME.caption.txt, first line into queue.tsv (`NAME<TAB>first line`).

## D. Publish one
1. `bash pipeline/push.sh NAME` -> prints raw.githubusercontent.com URL.
2. `vidiq_video_upload(url=RAW, title=NAME)` -> videoUrl.
3. `vidiq_instagram_publish_reel(platformAccountId, videoUrl, caption = full text of NAME.caption.txt, trialParams={graduationStrategy: MANUAL})` -> containerId.
4. sleep ~50 s, call again with containerId only; repeat every ~20 s until PUBLISHED (takes 45-75 s).
5. `bash pipeline/done.sh NAME PERMALINK` (removes the mp4 from the repo, appends to published.log).
On any error: stop, do not retry automatically, tell Denys.

## E. Timer message
`send_later(at=<NEXT time from slot.sh>, initiation=human_schedule, message=...)`:
> Таймер: конвейер trial Reels по pipeline/README.md. Сначала `bash /home/claude/trials/pipeline/slot.sh`: NEXT = слот занят другим чатом, поставь send_later на это время и закончи. NOW = следующий ролик `bash /home/claude/trials/pipeline/next.sh`; если не обработан, обработай (A-C, полный Келси, живая обложка на первом кадре, полное описание), опубликуй (D), коротко сообщи Денису ссылку и подпись. Потом обрабатывай остальные до ~10 минут перед следующим слотом и поставь send_later(at) на следующий слот из slot.sh. 7 trial в сутки, по одному в слот. Видео не режь, неразборчивые слова убирай только из субтитров. Meta code 2: не публикуй повторно, спроси Дениса. Очередь пуста: дай список всех ссылок этой пачки из published.log.

## What did NOT work
- Hosting via claude.ai artifact: vidIQ gets no Content-Length.
- Google Drive from Claude's environment is blocked.
- Background processes stop after the reply: do everything in the foreground.
- VAD in whisper dropped chunks of speech.
- raw GitHub URLs cache ~5 min: a corrected video needs a new file name.
- Without PROMPT whisper sometimes returns text with no punctuation at all.

## Log
11/27/2026: pipeline/trial.py (raw iPhone HDR clips to a full-Kelsie trial: tone map, teaser copy, live cover on frame 0, phrase captions, contact strip, CTA; usage in its header), faces.py (sharp face frames for the teaser start; needs OpenCV haarcascades cloned to /home/claude/work/cvdata), music.sh (library track into render.mp4).
11/25/2026: 7 trial slots a day instead of 5: 12:00 AM; 7:00, 9:00 AM; 1:00, 3:00, 5:00 PM; 10:00 PM (slot.sh).
11/19/2026 (night): 5 trials a day, one per slot; full Kelsie on every trial (hook from the middle, live cover on frame 0, full caption with 3-5 hashtags); winners go to the feed by «Share with everyone», never reposted.
11/19/2026 (later): evening main Reel 7 PM -> 8 PM; trial slot 9:00 PM -> 5:30 PM (slot.sh).
11/19/2026: 5 slots a day instead of 10 (slot.sh); contact line now «Нужен дом в Jacksonville или St. Johns?» instead of «Нужна недвижимость в Америке?».
11/14-15/2026: 18 published at 50-min interval. 11/16/2026: switched to 10 fixed slots a day (slot.sh); music for every trial (music.sh) and a hook line on videos without speech (hook.py).
11/06-07/2026: 19 + 12 Reels published this way. published.log is local to the session (not committed).
