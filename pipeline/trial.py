#!/usr/bin/env python3
"""Full-Kelsie trial Reel from raw iPhone clips (HDR tone map), live cover on frame 0.
Usage: python3 trial.py cfg.json [stage|pre|render|all]
cfg: name, srcs [[file, a, b]] (a/b None = whole), teaser [h0, h1] (stage s), rubric, place, key, sub,
     key_y, sub_y, pill_y, key_size, tag, realestate, cta {benefit, word}, fix {}, drop [[word, t]], keys [],
     npl (300)"""
import sys, os, json, subprocess, re
sys.path.insert(0, '/home/claude/work/lib')
import textstudio as ts, kstyle as ks, kchrome as kc
from PIL import Image, ImageDraw, ImageFont, ImageFilter

cfg = json.load(open(sys.argv[1]))
step = sys.argv[2] if len(sys.argv) > 2 else 'all'
NAME = cfg['name']
WD = '/home/claude/work/' + NAME
os.makedirs(WD, exist_ok=True); os.chdir(WD)
I = '/usr/share/fonts/opentype/inter/'
R = kc.RUBRIC[cfg['rubric']]
hexrgb = lambda c: tuple(int(c[i:i + 2], 16) for i in (1, 3, 5))
NPL = cfg.get('npl', 300)
TM = ('scale=1080:1920:flags=lanczos,zscale=t=linear:npl=%d,format=gbrpf32le,tonemap=tonemap=mobius:param=0.3:desat=0,'
      'zscale=p=bt709:t=bt709:m=bt709:r=tv:dither=error_diffusion,format=yuv420p,fps=30' % NPL)


def run(c):
    subprocess.run(c, check=True)


def dur(f):
    return float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', f]))


# ---------- 1. stage: tone map + concat ----------
def src_path(n):
    for p in ('/mnt/user-data/uploads/%s.mov' % n, '/home/claude/work/%s.mov' % n):
        if os.path.exists(p):
            return p
    import glob
    return glob.glob('/mnt/user-data/uploads/*%s.mov' % n)[0]


if step in ('stage', 'all') and not os.path.exists('stage.mov'):
    lst = open('list.txt', 'w')
    for i, (n, a, b) in enumerate(cfg['srcs']):
        f = src_path(n)
        tr = ffprobe = subprocess.check_output(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries',
                                                'stream=color_transfer', '-of', 'csv=p=0', f]).decode().strip()
        vf = TM if 'b67' in tr or 'smpte2084' in tr else 'scale=1080:1920:flags=lanczos,format=yuv420p,fps=30'
        cmd = ['ffmpeg', '-v', 'error', '-y']
        if a is not None:
            cmd += ['-ss', '%.3f' % a]
        cmd += ['-i', f]
        if b is not None:
            cmd += ['-t', '%.3f' % (b - (a or 0))]
        cmd += ['-vf', vf, '-af', 'volume=3dB,alimiter=limit=0.89:level=disabled,aresample=48000', '-ac', '2',
                '-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '14', '-c:a', 'pcm_s16le', 'p%d.mov' % i]
        run(cmd)
        lst.write("file 'p%d.mov'\n" % i)
    lst.close()
    run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', 'list.txt', '-c', 'copy', 'stage.mov'])
    print('STAGE', dur('stage.mov'))

# ---------- words on the stage timeline ----------
words, off = [], 0.0
for i, (n, a, b) in enumerate(cfg['srcs']):
    raw = json.load(open('/home/claude/out/%s.json' % n))['words']
    a0 = a or 0.0
    for w in raw:
        if i in cfg.get('nosub', []):
            break
        t = w['w']
        if w['s'] < a0 - 0.05 or (b is not None and w['s'] > b):
            continue
        if words and not t.startswith(' ') and re.match(r'^[,.\-:%!?]', t) and words[-1].get('src') == i:
            words[-1]['w'] += t.strip(); words[-1]['e'] = w['e'] - a0 + off
            continue
        words.append(dict(w=t.strip(), s=w['s'] - a0 + off, e=w['e'] - a0 + off, src=i))
    off += dur('p%d.mov' % i) if os.path.exists('p%d.mov' % i) else 0
for w in words:
    for x, y in cfg.get('fix', {}).items():
        w['w'] = w['w'].replace(x, y)
words = [w for w in words if w['w'] and not any(w['w'] == d and abs(w['s'] - t) < 0.4 for d, t in cfg.get('drop', []))]

if step == 'stage':
    sys.exit()
# ---------- 2. teaser copied to the start ----------
H0, H1 = cfg['teaser']; X = 0.3
HL = H1 - H0; OFF = HL - X
if step in ('pre', 'all', 'render') and not os.path.exists('pre.mov'):
    fc = ('[0:v]setpts=PTS-STARTPTS,fps=30,format=yuv420p,settb=AVTB[hv];[1:v]setpts=PTS-STARTPTS,fps=30,format=yuv420p,settb=AVTB[mv];'
          '[hv][mv]xfade=transition=fade:duration=%g:offset=%g[v];[0:a]asetpts=PTS-STARTPTS[ha];[1:a]asetpts=PTS-STARTPTS[ma];'
          '[ha][ma]acrossfade=d=%g[a]' % (X, OFF, X))
    run(['ffmpeg', '-v', 'error', '-y', '-ss', '%.3f' % H0, '-t', '%.3f' % HL, '-i', 'stage.mov', '-i', 'stage.mov',
         '-filter_complex', fc, '-map', '[v]', '-map', '[a]', '-c:v', 'libx264', '-crf', '14', '-preset', 'fast', '-c:a', 'pcm_s16le', 'pre.mov'])
if step == 'pre':
    sys.exit()
D = dur('pre.mov')
hook_end = OFF + X / 2
fw = [dict(w=w['w'], s=w['s'] + OFF, e=w['e'] + OFF) for w in words]
json.dump(dict(words=fw, D=D, hook_end=hook_end, OFF=OFF), open('timeline.json', 'w'), ensure_ascii=False, indent=0)

# ---------- 3. ASS: phrases, tag ----------
RE = cfg.get('realestate', False)
CTA = cfg.get('cta')
cta0 = D - 3.0
a = ts.ASS()
skip = [(0, OFF - 0.05)] + ([(cta0, D + 1)] if CTA else []) + [tuple(x) for x in cfg.get('cap_skip', [])]
ks.phrases(a, fw, skip=skip, keys=cfg.get('keys', []), key_color=R[1],
           y_at=(lambda t: 1250 if t >= D - 5.0 else 1460) if RE else None)


def _sec(x):
    h, m, z = x.split(':'); return int(h) * 3600 + int(m) * 60 + float(z)


if RE:
    T5, new = D - 5.0, []
    for ev in a.events:
        p = ev.split(',', 9)
        if _sec(p[1]) < T5 < _sec(p[2]) and ('pos(540,1460)' in ev or 'pos(540,1467)' in ev):
            p1 = list(p); p1[2] = ts.tc(T5); new.append(','.join(p1))
            p2 = list(p); p2[1] = ts.tc(T5)
            p2[9] = p2[9].replace('pos(540,1460)', 'pos(540,1250)').replace('pos(540,1467)', 'pos(540,1257)')
            new.append(','.join(p2))
        else:
            new.append(ev)
    a.events = new
if cfg.get('tag'):
    ts.tag(a, hook_end, D, cfg['tag'])
a.save('caps.ass')
ov = ks.caption_overlaps('caps.ass')
bad = [l[:60] for l in open('caps.ass', encoding='utf-8') if RE and l.startswith('Dialogue:') and 'pos(540,1460)' in l
       and _sec(l.split(',', 9)[2]) > D - 5.0 + 0.005]
print('overlaps', ov, 'strip', bad)
assert not ov and not bad

# ---------- 4. stickers ----------
stickers = []
os.makedirs('st', exist_ok=True)


def seq(name, frames_fn, t0, t1):
    d = 'st/' + name; os.makedirs(d, exist_ok=True)
    n = int(round((t1 - t0) * 30)); prev = None; size = None
    for i in range(n):
        im = frames_fn(i / 30.0, t1 - t0)
        fn = '%s/%04d.png' % (d, i)
        if os.path.lexists(fn):
            os.remove(fn)
        if im is None and prev:
            os.link(prev, fn); continue
        im.save(fn, compress_level=1); prev = fn; size = size or im.size
    return d + '/%04d.png', size


def fade_out(im, t, T, fo=0.25):
    al = max(0.0, min(1.0, (T - t) / fo))
    if al < 1:
        im = im.copy(); im.putalpha(im.getchannel('A').point(lambda v: int(v * al)))
    return im


def pill_img(text, size=44, fill=R[1], outline=R[0], ink='#FFFFFF'):
    f = ImageFont.truetype(I + 'InterDisplay-Bold.otf', size)
    tw = f.getlength(text); w, hh = int(tw + 84), int(size * 1.65)
    im = Image.new('RGBA', (w + 60, hh + 60), (0, 0, 0, 0))
    sh = Image.new('RGBA', im.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle((30, 36, 30 + w, 36 + hh), hh // 2, fill=(0, 0, 0, 120))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(10)))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((30, 30, 30 + w, 30 + hh), hh // 2, fill=hexrgb(R[2]) + (170,), outline=hexrgb(outline) + (255,), width=5)
    d.text((30 + w / 2, 30 + hh / 2), text, font=f, fill=ink, anchor='mm')
    return im


def line_img(text, size=64, face='InterDisplay-Bold.otf'):
    f = ImageFont.truetype(I + face, size)
    while f.getlength(text) > 860 and size > 30:
        size -= 2; f = ImageFont.truetype(I + face, size)
    w = int(f.getlength(text)) + 80; h = int(size * 1.6) + 40
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    sh = Image.new('RGBA', im.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).text((w / 2, h / 2 + 5), text, font=f, fill=(0, 0, 0, 190), anchor='mm')
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(8)))
    ImageDraw.Draw(im).text((w / 2, h / 2), text, font=f, fill='white', anchor='mm', stroke_width=2, stroke_fill=(20, 20, 20, 160))
    return im


T = hook_end
P = pill_img(cfg['place'])
pat, sz = seq('pill', lambda t, T_: fade_out(P, t, T_), 0, T)
stickers.append(dict(pattern=pat, t0=0.0, x=540, y=cfg.get('pill_y', 330)))
KS = cfg.get('key_size', 190)
ch_cache = {}


def chrome_frame(t, T_):
    p = min(1.0, t / 1.4)
    k = round(p, 2)
    if k not in ch_cache:
        ch_cache[k] = kc.chrome(cfg['key'], cfg['rubric'], 'metal', face='geo-cy', size=KS, shine=-0.2 + 1.4 * p)
    return fade_out(ch_cache[k], t, T_)


pat, sz = seq('key', chrome_frame, 0, T)
stickers.append(dict(pattern=pat, t0=0.0, x=540, y=cfg.get('key_y', 520)))
if cfg.get('sub'):
    S_ = line_img(cfg['sub'], cfg.get('sub_size', 60))
    pat, sz = seq('sub', lambda t, T_: fade_out(S_, t, T_), 0, T)
    stickers.append(dict(pattern=pat, t0=0.0, x=540, y=cfg.get('sub_y', 680)))


def cta_block(benefit, keyword):
    fs_b = 54
    while ImageFont.truetype(I + 'InterDisplay-Bold.otf', fs_b).getlength(benefit) > 820 and fs_b > 36:
        fs_b -= 2
    fb = ImageFont.truetype(I + 'InterDisplay-Bold.otf', fs_b); fm = ImageFont.truetype(I + 'InterDisplay-Bold.otf', 66)
    pill = pill_img('«%s»' % keyword, 88, fill=R[1], outline=R[0])
    W_, H_ = 900, 140 + pill.height
    im = Image.new('RGBA', (W_, H_), (0, 0, 0, 0))
    for txt, f, y in ((benefit, fb, 30), ('Напишите в комментариях', fm, 100)):
        sh = Image.new('RGBA', im.size, (0, 0, 0, 0)); ImageDraw.Draw(sh).text((W_ / 2, y + 4), txt, font=f, fill=(0, 0, 0, 190), anchor='mm')
        im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(6)))
        ImageDraw.Draw(im).text((W_ / 2, y), txt, font=f, fill='white', anchor='mm')
    im.alpha_composite(pill, ((W_ - pill.width) // 2, 130))
    return im


if CTA:
    C = cta_block(CTA['benefit'], CTA['word'])
    stickers.append(ks.animate(ks.layered(C), cta0, D + 0.5, x=540, y=cfg.get('cta_y', 1080), enter='pop', exit='cut', name='cta', out_dir='st'))


def contact_strip(d='contact', dur_=5.0):
    sb = lambda s: ImageFont.truetype(I + 'InterDisplay-SemiBold.otf', s)
    aa, p = 'WhatsApp / Telegram / SMS  ', '+1 (754) 286-8238'
    fs, fn = sb(27), sb(36)
    m = ImageDraw.Draw(Image.new('L', (1, 1)))
    x = 540 - (m.textlength(aa, font=fs) + m.textlength(p, font=fn)) / 2
    items = [((x, 1385), aa, fs, 'ls'), ((x + m.textlength(aa, font=fs), 1385), p, fn, 'ls'),
             ((540, 1424), 'Denys Yermak, REALTOR®', sb(23), 'mm'),
             ((540, 1455), 'Berkshire Hathaway HomeServices Florida Network Realty', ImageFont.truetype(I + 'InterDisplay-Medium.otf', 20), 'mm')]
    sh = Image.new('RGBA', (1080, 1920), (0, 0, 0, 0)); dr = ImageDraw.Draw(sh)
    for (px, py), t, f, an in items:
        dr.text((px, py + 4), t, font=f, fill=(0, 0, 0, 140), anchor=an)
    im = sh.filter(ImageFilter.GaussianBlur(7)); dr = ImageDraw.Draw(im)
    for xy, t, f, an in items:
        dr.text(xy, t, font=f, fill='#FFFFFF', anchor=an)
    os.makedirs(d, exist_ok=True); im.save(d + '/contact.png')
    for i in range(int(round(dur_ * 30))):
        dst = '%s/strip_%04d.png' % (d, i)
        if not os.path.lexists(dst): os.symlink('contact.png', dst)
    return d + '/strip_%04d.png'


if RE:
    stickers.append(dict(pattern=contact_strip(dur_=min(5.0, D)), t0=max(0.0, D - 5.0), x=540, y=960))

# ---------- 5. render ----------
ts.EXPORT = ['-c:v', 'libx264', '-preset', 'fast', '-crf', '17', '-maxrate', '12M', '-bufsize', '24M', '-profile:v', 'high', '-pix_fmt', 'yuv420p',
             '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-color_range', 'tv',
             '-tag:v', 'avc1', '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-ac', '2', '-movflags', '+faststart']
ts.burn('pre.mov', 'caps.ass', 'render.mp4', stickers=stickers)
run(['ffmpeg', '-v', 'error', '-y', '-i', 'render.mp4', '-frames:v', '1', '/home/claude/out/%s_cover.png' % NAME])
print('DONE', D, hook_end)
