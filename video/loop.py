# Seamless forward loop: the last D frames dissolve into the first D frames.
import sys, subprocess, numpy as np
ff, src, dst, L, D = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]), int(sys.argv[5])
W, H = 1280, 720
raw = subprocess.run([ff, "-loglevel", "error", "-i", src, "-frames:v", str(L), "-vf", "hqdn3d=3:3:6:6" + (("," + sys.argv[6]) if len(sys.argv) > 6 else ""),
                      "-f", "rawvideo", "-pix_fmt", "rgb48le", "-"], capture_output=True).stdout
fr = np.frombuffer(raw, np.uint16).reshape(-1, H, W, 3)
assert len(fr) == L, len(fr)
enc = subprocess.Popen([ff, "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb48le", "-s", f"{W}x{H}", "-r", "30000/1001", "-i", "-",
                        "-c:v", "libx264", "-preset", "slow", "-crf", "22", "-tune", "film", "-profile:v", "high", "-pix_fmt", "yuv420p",
                        "-movflags", "+faststart", dst], stdin=subprocess.PIPE)
for k in range(L - D):
    if k < D:
        # smoothstep weight: tail (frames L-D..L-1) fades out as head (frames 0..D-1) fades in
        t = (k + 0.5) / D; a = t * t * (3 - 2 * t)
        f = fr[L - D + k].astype(np.float32) * (1 - a) + fr[k].astype(np.float32) * a
        enc.stdin.write(np.clip(f + 0.5, 0, 65535).astype(np.uint16).tobytes())
    else:
        enc.stdin.write(fr[k].tobytes())
enc.stdin.close(); enc.wait()
