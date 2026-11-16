#!/usr/bin/env python3
"""Kelsie-light hook for a trial without speech: one line on screen for the first 2.8 s.
Usage: hook.py NAME "тонкая часть" "ЖИРНОЕ СЛОВО" [outdir=/home/claude/out]
Thin part in Inter Thin, key word in Inter ExtraBold yellow (#FFD84D, Kelsie key colour), black outline.
Run it AFTER editwords.py (rechunk rewrites NAME.ass) and right before encode.sh. Re-running replaces the old hook.
Only facts that are certain: no hook is better than an invented one."""
import sys, os
name, thin, key = sys.argv[1:4]
out = sys.argv[4] if len(sys.argv) > 4 else '/home/claude/out'
p = os.path.join(out, name + '.ass')
s = open(p, encoding='utf-8').read()
s = '\n'.join(l for l in s.split('\n') if not l.startswith('Style: Hook') and ',Hook,' not in l)
style = 'Style: Hook,Inter Thin,88,&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,0,0,0,0,100,100,0,0,1,4,2,8,70,70,430,1'
lines = s.split('\n')
i = max(k for k, l in enumerate(lines) if l.startswith('Style: '))
lines.insert(i + 1, style)
s = '\n'.join(lines)
txt = thin.strip() + r'\N{\fnInter ExtraBold\c&H4DD8FF&}' + key.strip()
s = s.rstrip('\n') + '\nDialogue: 1,0:00:00.00,0:00:02.80,Hook,,0,0,0,,{\\fad(150,200)}' + txt + '\n'
open(p, 'w', encoding='utf-8').write(s)
print('hook added:', thin, '|', key)
