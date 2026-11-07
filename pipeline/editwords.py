#!/usr/bin/env python3
"""Per-video word fixes in OUT/NAME.json, then run process.py --rechunk.

  editwords.py NAME --show                  list words with indexes
  editwords.py NAME 'old=new' ...           replace first word equal to old
  editwords.py NAME 'old@-3=new'            replace word at index (neg ok), asserts it equals old
  editwords.py NAME 'old='                  delete word (empty replacement)
  editwords.py NAME '#30-36='               delete index range (inclusive)
Words are compared stripped, punctuation included ("риэлта." not "риэлта").
Rule: if a fragment is unclear even after re-transcription, delete it. Never invent words.
"""
import json, sys, subprocess, os
OUT = os.environ.get("OUT", "/home/claude/out")
name, specs = sys.argv[1], sys.argv[2:]
p = f"{OUT}/{name}.json"
d = json.load(open(p)); W = d["words"]; n = len(W)
if specs == ["--show"]:
    for i, w in enumerate(W): print(i, i - n, repr(w["w"]))
    sys.exit()
for s in specs:
    old, new = s.split("=", 1)
    val = (" " + new) if new else ""
    if old.startswith("#"):
        a, b = map(int, old[1:].split("-"))
        for i in range(a, b + 1): W[i]["w"] = ""
        continue
    if "@" in old:
        old, idx = old.split("@"); i = int(idx)
        assert W[i]["w"].strip() == old, (s, W[i]["w"])
    else:
        hits = [i for i, w in enumerate(W) if w["w"].strip() == old]
        if not hits: sys.exit(f"MISS {name}: {old}")
        i = hits[0]
    W[i]["w"] = val
json.dump(d, open(p, "w"), ensure_ascii=False, indent=1)
here = os.path.dirname(os.path.abspath(__file__))
subprocess.run(["python3", "-I", f"{here}/process.py", "--rechunk", name, OUT], check=True)
