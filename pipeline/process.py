#!/usr/bin/env python3
"""Transcribe a video, burn simple phrase subtitles, encode 1080x1920 H.264 for Instagram.
Usage: process.py <input.mov> <outdir>
Writes <outdir>/<name>.mp4, <name>.json (segments + words), <name>.ass
"""
import sys, os, json, subprocess, re

MODEL = os.environ.get("WMODEL", "medium")
FIXES = {"8.45": "8:45", "в бой дом": "в бой, дом", "флориде": "Флориде", "америке": "Америке", "все принтер": "Все, принтер", "Сен-Джонс": "St. Johns", "Каунти": "County", "8.15": "8:15", "обращается": "обращаться", "Доллар три": "Dollar Tree", "доллар три": "Dollar Tree", "недурого": "по дороге", "павликсом": "Publix", "Велком": "Welcome", "Фолл Брей": "Fall Break", "Сен-Джонс Каунти": "St. Johns County", "Julenton": "Julington", "Джулентон": "Julington", "8.09": "8:09", "Джексон-Вилле": "Джексонвилле", "аквапарт": "аквапарк", "КРИСМОС": "Christmas", "Крисмос": "Christmas", "помештаем": "помечтаем"}

def ts(t):
    h = int(t // 3600); m = int(t % 3600 // 60); s = t % 60
    return f"{h}:{m:02d}:{s:05.2f}"

def chunks_from_words(words, max_words=4, max_chars=22, max_gap=0.6):
    out, cur = [], []
    merged = []
    for w in words:
        txt = w["w"].strip()
        if not txt:
            continue
        if merged and re.match(r"^[.\-:,%]", txt) and not w["w"].startswith(" "):
            merged[-1] = {"s": merged[-1]["s"], "e": w["e"], "w": merged[-1]["w"] + txt}
        else:
            merged.append(dict(w))
    for w in merged:
        for a, b in FIXES.items():
            w["w"] = w["w"].replace(a, b)
        if cur:
            gap = w["s"] - cur[-1]["e"]
            joined = " ".join(x["w"].strip() for x in cur + [w])
            ends_sentence = re.search(r"[.!?…]$", cur[-1]["w"].strip()) or (len(cur) >= 2 and cur[-1]["w"].strip().endswith(","))
            if len(cur) >= max_words or len(joined) > max_chars or gap > max_gap or ends_sentence:
                out.append(cur); cur = []
        cur.append(w)
    if cur:
        out.append(cur)
    res = []
    for i, c in enumerate(out):
        text = " ".join(x["w"].strip() for x in c)
        for a, b in FIXES.items():
            text = text.replace(a, b)
        text = re.sub(r"[.,…]+$", "", text)  # no trailing punctuation on captions
        s = c[0]["s"]; e = c[-1]["e"]
        if i + 1 < len(out):
            e = min(max(e, s + 0.4), out[i + 1][0]["s"])
        res.append((s, e, text))
    return res

def write_ass(chunks, path):
    head = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Sub,Inter ExtraBold,74,&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,0,0,0,0,100,100,0,0,1,5,2,2,80,80,600,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(head)
        for s, e, t in chunks:
            f.write(f"Dialogue: 0,{ts(s)},{ts(e)},Sub,,0,0,0,,{t}\n")

def rechunk(name, outdir):
    d = json.load(open(os.path.join(outdir, name + ".json"), encoding="utf-8"))
    chunks = chunks_from_words(d["words"])
    write_ass(chunks, os.path.join(outdir, name + ".ass"))
    d["chunks"] = chunks
    json.dump(d, open(os.path.join(outdir, name + ".json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return chunks

def main():
    if sys.argv[1] == "--rechunk":
        for c in rechunk(sys.argv[2], sys.argv[3]): print(c[2])
        return
    src, outdir = sys.argv[1], sys.argv[2]
    os.makedirs(outdir, exist_ok=True)
    name = os.path.splitext(os.path.basename(src))[0]
    wav = os.path.join(outdir, name + ".wav")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", src, "-vn", "-ac", "1", "-ar", "16000", wav], check=True)
    from faster_whisper import WhisperModel
    m = WhisperModel(MODEL, device="cpu", compute_type="int8", cpu_threads=2)
    import wave, numpy as np
    with wave.open(wav, "rb") as wf:
        audio = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16).astype(np.float32) / 32768.0
    segs, info = m.transcribe(audio, language="ru", word_timestamps=True, vad_filter=False, beam_size=5, initial_prompt=os.environ.get("PROMPT") or None)
    segments, words = [], []
    for s in segs:
        segments.append({"s": s.start, "e": s.end, "t": s.text.strip()})
        for w in s.words or []:
            words.append({"s": w.start, "e": w.end, "w": w.word})
    os.remove(wav)
    chunks = chunks_from_words(words)
    ass = os.path.join(outdir, name + ".ass")
    write_ass(chunks, ass)
    with open(os.path.join(outdir, name + ".json"), "w", encoding="utf-8") as f:
        json.dump({"segments": segments, "words": words, "chunks": chunks}, f, ensure_ascii=False, indent=1)
    print(f"{name}: transcribed {len(chunks)} chunks", flush=True)

if __name__ == "__main__":
    main()
