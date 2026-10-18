import sys, subprocess, numpy as np
ff, src, motion, dst, nkeep = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], int(sys.argv[5])
W, H = 1280, 720
m = np.loadtxt(motion)[:nkeep]
d = m[:, 1:3]  # measured (dx, dy); content motion is -d

# Robust smoothing: median filter rejects mis-tracked frames, then a moving average
def smooth(v, med=5, avg=15):
    p = np.pad(v, med // 2, mode="edge")
    v = np.array([np.median(p[i:i + med]) for i in range(len(v))])
    p = np.pad(v, avg // 2, mode="reflect")
    return np.convolve(p, np.ones(avg) / avg, mode="valid")
sd = np.stack([smooth(d[:, 0]), smooth(d[:, 1])], 1)
sd -= sd[0]
np.savetxt(motion.replace(".txt", "_smooth.txt"), sd, fmt="%.3f")

# Valid region after shifting every frame: sample at (x - dx, y - dy)
x0 = int(np.ceil(max(sd[:, 0].max(), 0))) + 1; x1 = W + int(np.floor(min(sd[:, 0].min(), 0))) - 1
y0 = int(np.ceil(max(sd[:, 1].max(), 0))) + 1; y1 = H + int(np.floor(min(sd[:, 1].min(), 0))) - 1
# Largest 16:9 window inside it, centered
cw = min(x1 - x0, (y1 - y0) * 16 / 9); ch = cw * 9 / 16
cw, ch = int(cw) // 2 * 2, int(ch) // 2 * 2
cx = x0 + ((x1 - x0) - cw) // 2; cy = y0 + ((y1 - y0) - ch) // 2
print(f"crop {cw}x{ch} at {cx},{cy}  (valid x {x0}-{x1}, y {y0}-{y1})", file=sys.stderr)

dec = subprocess.Popen([ff, "-loglevel", "error", "-i", src, "-frames:v", str(nkeep), "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
enc = subprocess.Popen([ff, "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{cw}x{ch}", "-r", "30000/1001", "-i", "-",
                        "-vf", "scale=1280:720:flags=lanczos", "-c:v", "libx264", "-preset", "veryslow", "-crf", "12", "-pix_fmt", "yuv420p", dst], stdin=subprocess.PIPE)
yy, xx = np.mgrid[cy:cy + ch, cx:cx + cw].astype(np.float32)
for i in range(nkeep):
    f = np.frombuffer(dec.stdout.read(W * H * 3), np.uint8).reshape(H, W, 3).astype(np.float32)
    sx, sy = xx - sd[i, 0], yy - sd[i, 1]
    ix, iy = np.floor(sx).astype(int), np.floor(sy).astype(int)
    fx, fy = (sx - ix)[..., None], (sy - iy)[..., None]
    o = (f[iy, ix] * (1 - fx) * (1 - fy) + f[iy, ix + 1] * fx * (1 - fy)
         + f[iy + 1, ix] * (1 - fx) * fy + f[iy + 1, ix + 1] * fx * fy)
    enc.stdin.write(np.clip(o + 0.5, 0, 255).astype(np.uint8).tobytes())
enc.stdin.close(); enc.wait(); dec.wait()
