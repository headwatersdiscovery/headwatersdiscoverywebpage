import sys, subprocess, numpy as np
ff, src = sys.argv[1], sys.argv[2]
W, H = 1280, 720
raw = subprocess.run([ff, "-loglevel", "error", "-i", src, "-f", "rawvideo", "-pix_fmt", "gray", "-"], capture_output=True).stdout
fr = np.frombuffer(raw, np.uint8).reshape(-1, H, W).astype(np.float32)
# Region: left/center ridgeline against the sky, away from the moon and its reflection
y0, y1, x0, x1 = 60, 360, 0, 760
ref = fr[0, y0:y1, x0:x1]
def shift(a, b, up=10):
    a = a - a.mean(); b = b - b.mean()
    win = np.outer(np.hanning(a.shape[0]), np.hanning(a.shape[1]))
    A = np.fft.fft2(a * win); B = np.fft.fft2(b * win)
    R = A * np.conj(B); R /= np.abs(R) + 1e-9
    c = np.fft.ifft2(R).real
    iy, ix = np.unravel_index(np.argmax(c), c.shape)
    # parabolic subpixel refinement
    def sub(cm, c0, cp): d = cm - 2*c0 + cp; return 0 if d == 0 else 0.5*(cm-cp)/d
    h, w = c.shape
    dy = iy + sub(c[(iy-1)%h, ix], c[iy, ix], c[(iy+1)%h, ix])
    dx = ix + sub(c[iy, (ix-1)%w], c[iy, ix], c[iy, (ix+1)%w])
    if dy > h/2: dy -= h
    if dx > w/2: dx -= w
    return dx, dy
out = []
for i in range(len(fr)):
    dx, dy = shift(ref, fr[i, y0:y1, x0:x1])
    out.append((i, dx, dy))
np.savetxt(sys.argv[3], out, fmt="%d %.3f %.3f")
