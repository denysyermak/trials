import sys, subprocess, numpy as np, cv2
src, t0, t1 = sys.argv[1], float(sys.argv[2]), float(sys.argv[3]); out = sys.argv[4]
H = '/home/claude/work/cvdata/data/haarcascades/'
face = cv2.CascadeClassifier(H + 'haarcascade_frontalface_default.xml')
eye = cv2.CascadeClassifier(H + 'haarcascade_eye.xml')
smile = cv2.CascadeClassifier(H + 'haarcascade_smile.xml')
FPS = 10
raw = subprocess.run(['ffmpeg', '-v', 'error', '-ss', str(t0), '-t', str(t1 - t0), '-i', src, '-vf', 'fps=%d,scale=540:960' % FPS,
                      '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-'], capture_output=True).stdout
n = len(raw) // (540 * 960 * 3); res = []
for i in range(n):
    im = np.frombuffer(raw, np.uint8, 540 * 960 * 3, i * 540 * 960 * 3).reshape(960, 540, 3)
    g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
    lap = np.abs(cv2.Laplacian(cv2.resize(g, (540, 960)), cv2.CV_32F))
    bl = lap[:960 // 16 * 16, :540 // 16 * 16].reshape(60, 16, 33, 16).mean((1, 3))
    gs = (bl > 6).mean()
    fs = face.detectMultiScale(g, 1.15, 6, minSize=(90, 90))
    if len(fs) == 0:
        res.append((gs * 0.3, t0 + i / FPS, 0, 0, None)); continue
    x, y, w, h = max(fs, key=lambda f: f[2] * f[3]); fg = g[y:y + h, x:x + w]
    es = eye.detectMultiScale(fg[:h // 2], 1.1, 6, minSize=(w // 8, w // 8))
    sm = smile.detectMultiScale(fg[h // 2:], 1.6, 22, minSize=(w // 4, h // 8))
    sh = cv2.Laplacian(fg, cv2.CV_64F).var()
    res.append((gs * (1 + 0.5 * (len(es) >= 2) + 0.5 * (len(sm) > 0)) * min(1, sh / 80), t0 + i / FPS, len(es), len(sm), (x*2, y*2, w*2, h*2)))
res.sort(key=lambda r: -r[0])
top = res[:12]
for r in top: print('%.2f s=%.3f eyes=%d smile=%d face=%s' % (r[1], r[0], r[2], r[3], r[4]))
tiles = []
for r in top:
    i = int(round((r[1] - t0) * FPS)); im = np.frombuffer(raw, np.uint8, 540 * 960 * 3, i * 540 * 960 * 3).reshape(960, 540, 3).copy()
    im = cv2.resize(im, (180, 320)); cv2.putText(im, '%.1f' % r[1], (4, 22), 0, 0.7, (0, 255, 255), 2); tiles.append(im)
while len(tiles) < 12: tiles.append(np.zeros((320, 180, 3), np.uint8))
cv2.imwrite(out, np.vstack([np.hstack(tiles[k:k + 6]) for k in (0, 6)]))
