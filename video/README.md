# Background video: how `assets/headwaters-bg.mp4` is made

The homepage background is a moonrise over Evolution Valley, built from one
source clip in four steps. Running the commands below reproduces
`assets/headwaters-bg.mp4` **byte for byte** (verified 2026-10-18).

```
52220035608_9e5b280dae_vm.mp4   original Flickr download, 12.5 s, 1280x720, 11.6 Mbps, with audio
        │  1. track.py      measure camera shake on the ridgeline
        │  2. stabilize.py  remove the shake, trim to 12.0 s, crop and rescale to 1280x720
        ▼
stab.mp4                        stabilized master, 12.0 s, ~15 MB, near-lossless (CRF 12)
        │  3. loop.py       noise reduction + mild grade + 1.5 s crossfade loop
        ▼
assets/headwaters-bg.mp4        10.5 s seamless loop, ~920 KB, no audio
        │  4. ffmpeg        first frame
        ▼
assets/headwaters-poster.jpg    still shown while the video loads
```

The source clip is not committed (it is in `.gitignore`). Keep a copy of it,
and ideally of `stab.mp4`, somewhere backed up.

## Setup

Requires Python 3 with `numpy` and `imageio-ffmpeg` (which bundles an ffmpeg
binary that includes libx264). Built with Python 3.14.6, numpy 2.5.4,
imageio-ffmpeg 0.6.0 and ffmpeg 7.1. Other versions should give visually
identical output, but not necessarily identical bytes.

```bash
python3 -m venv venv
venv/bin/pip install numpy imageio-ffmpeg
FF=$(venv/bin/python -c "import imageio_ffmpeg; print(imageio_ffmpeg.get_ffmpeg_exe())")
SRC=52220035608_9e5b280dae_vm.mp4
```

Run the steps from the repo root.

## 1. Track camera shake (`track.py`)

```bash
venv/bin/python video/track.py $FF $SRC motion.txt
```

This compares every frame with frame 0 by phase correlation, with sub-pixel
refinement, and writes one `frame dx dy` line per frame (375 frames). It looks
only at the left and center ridgeline against the sky (`y 60–360, x 0–760`),
because the moon and its reflection change brightness and would confuse the
measurement.

## 2. Stabilize and trim (`stabilize.py`)

```bash
venv/bin/python video/stabilize.py $FF $SRC motion.txt stab.mp4 360
```

- **Trim:** `360` keeps the first 360 frames (12.0 s) and drops the last 0.5 s,
  where the camera wobbles at the end.
- **Smoothing:** the measured shake goes through a median filter (5 frames, to
  ignore mis-tracked frames) and then a moving average (15 frames). Each frame
  is shifted by the smoothed amount with bilinear sampling. An earlier attempt
  used 9 and 31 frames and was rejected in favor of these values.
- **Crop:** it prints `crop 1238x696 at 22,19`. That is the largest centered
  16:9 window that stays inside the frame after every shift, scaled back up to
  1280x720 with Lanczos.
- **Output:** x264 `veryslow`, CRF 12 (near lossless), so later steps start
  from a clean master.

## 3. Grade and loop (`loop.py`)

```bash
GRADE="curves=all='0/0 0.06/0.11 0.2/0.31 0.6/0.68 1/1',colorbalance=bs=0.06:bm=0.04:rs=-0.02:rm=-0.02"
venv/bin/python video/loop.py $FF stab.mp4 assets/headwaters-bg.mp4 360 45 "$GRADE"
```

- **Noise reduction:** `hqdn3d=3:3:6:6` is always applied (it is built into the
  script).
- **Grade (optional 6th argument):** an ffmpeg filter applied after noise
  reduction, at 16 bits per channel.
  - `curves` lifts the shadows and midtones a little, bringing out the sky
    gradient, the far ridgeline and the lake reflection.
  - `colorbalance` adds a slight blue to the shadows and midtones, so the lifted
    tones read as moonlight rather than grey.
  - Leave the argument out to get the original, ungraded dark version (the
    site's first version, from commit `7e84c13`).
- **Loop:** `360 45` means use 360 frames and crossfade the last 45 frames
  (1.5 s) into the first 45, with a smoothstep curve. The result is 315 frames
  (10.5 s) that loop seamlessly, always playing forward. A ping-pong loop was
  rejected because playing backward reverses the left-to-right glint on the
  water.
- **Output:** x264 `slow`, CRF 22, `-tune film`, high profile, `+faststart`,
  no audio.

## 4. Poster frame

```bash
$FF -y -i assets/headwaters-bg.mp4 -frames:v 1 -q:v 4 assets/headwaters-poster.jpg
```

## Choices made along the way (2026-10-18)

- **Grade strength:** a stronger lift
  (`curves=all='0/0 0.07/0.16 0.2/0.38 0.6/0.75 1/1'` with the same
  `colorbalance`) made the video easier to see, but it competed with the page
  text. The mild grade above was chosen; keep any future grading subtle.
- **Grade from the master, not from the web file:** the grade goes on
  `stab.mp4` before the loop step, so the final file is compressed only once.
- **No saturation boost:** the footage has almost no color, and boosting
  saturation turned it green. `colorbalance` is the way to tint it.
- **No AI sharpening or upscaling:** the scene is mostly silhouettes, and the
  dark areas hold sensor noise rather than detail. Sharpening would mostly
  enhance noise and compression artifacts, and give the moon's glow a hard
  edge.
- **File size:** the graded loop is about 920 KB, against 530 KB ungraded,
  because the brighter shadows have more to compress. A two-pass 400 kbps
  encode (`-b:v 400k`) gets it down to about 545 KB with little visible
  difference, if size ever matters.
