#!/usr/bin/env python3
"""Mix ban trailer co voice + nhac (ducking) + tieng ngoai canh tong hop.
Dau vao: trailer/score.wav (nhac), trailer/vo/vo_XX.mp3 (loi thoai),
         trailer/silent.mp4 (hinh). Dau ra: TRAILER_VO.mp4.
"""
import os, subprocess, sys
import numpy as np
import wave as wavmod

TR = os.path.expanduser("~/workspace/genechain-merkle-dag/trailer")
SR = 44100
TOTAL = 118.0
N = int(TOTAL * SR)
rng = np.random.default_rng(7)

def load_wav(path):
    with wavmod.open(path, "rb") as wf:
        ch, sw, sr, nf = wf.getnchannels(), wf.getsampwidth(), wf.getframerate(), wf.getnframes()
        raw = wf.readframes(nf)
    a = np.frombuffer(raw, dtype=np.int16).astype(np.float64) / 32767.0
    a = a.reshape(-1, ch)
    if ch == 1:
        a = np.repeat(a, 2, axis=1)
    assert sr == SR, f"sample rate {sr}"
    return a

def decode_mp3(path):
    tmp = path + ".wav"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", path,
                    "-ar", str(SR), "-ac", "2", tmp], check=True)
    return load_wav(tmp)

score = load_wav(os.path.join(TR, "score.wav"))
if len(score) < N:
    score = np.pad(score, ((0, N - len(score)), (0, 0)))
score = score[:N]

# ---- Loi thoai: vi tri bat dau (giay) ----
PLACES = {1: 0.8, 2: 7.0, 3: 14.0, 4: 19.5, 5: 27.0, 6: 33.0, 7: 40.0,
          8: 51.3, 9: 58.3, 10: 64.8, 11: 70.5, 12: 77.7, 13: 87.2,
          14: 95.2, 15: 103.0, 16: 112.8}
vo_track = np.zeros((N, 2))
duck = np.ones(N)
for idx, t0 in PLACES.items():
    a = decode_mp3(os.path.join(TR, "vo", f"vo_{idx:02d}.mp3"))
    # vang nhe kieu phong lon (2 tieng phan xa)
    echo = a.copy()
    for dly, g in [(0.09, 0.28), (0.21, 0.14)]:
        d = int(dly * SR)
        echo[d:] += a[:-d] * g
    i = int(t0 * SR)
    j = min(N, i + len(echo))
    vo_track[i:j] += echo[:j - i] * 0.95
    # ducking: giam nhac trong luc doc (+0.35s duoi)
    d0 = max(0, int((t0 - 0.15) * SR))
    d1 = min(N, int((t0 + len(a) / SR + 0.35) * SR))
    ramp = int(0.25 * SR)
    duck[d0:d1] = np.minimum(duck[d0:d1], 0.52)
    if d0 > ramp:
        duck[d0 - ramp:d0] = np.minimum(duck[d0 - ramp:d0], np.linspace(1.0, 0.52, ramp))
    if d1 + ramp < N:
        duck[d1:d1 + ramp] = np.minimum(duck[d1:d1 + ramp], np.linspace(0.52, 1.0, ramp))
music = score * duck[:, None]

# ================= TIENG NGOAI CANH =================
amb = np.zeros((N, 2))

def put(t0, wave, gain=1.0, pan=0.0):
    i = int(t0 * SR)
    j = min(N, i + len(wave))
    if i >= N:
        return
    w = wave[:j - i] * gain
    lg = np.cos((pan + 1) * np.pi / 4)
    rg = np.sin((pan + 1) * np.pi / 4)
    amb[i:j, 0] += w * lg
    amb[i:j, 1] += w * rg

def lowpass(x, win):
    k = np.ones(win) / win
    return np.convolve(x, k, mode="same")

# Gio nen xuyen suot
for ch in range(2):
    nz = rng.standard_normal(N)
    w = lowpass(lowpass(nz, 60), 60)
    lfo = 0.65 + 0.35 * np.sin(2 * np.pi * 0.07 * np.arange(N) / SR + ch * 1.7)
    amb[:, ch] += w * lfo * 0.055

# Sam mo dau (0.15s)
t = np.arange(int(3.0 * SR)) / SR
thunder = np.sin(2 * np.pi * 50 * t) * np.exp(-t * 1.6) * 0.5 \
    + lowpass(rng.standard_normal(len(t)), 90) * np.exp(-t * 1.1) * 0.5
put(0.15, thunder, 0.8)

# Song bien Quy Khu (24-35s)
seg = int(11 * SR)
tt = np.arange(seg) / SR
ocean = lowpass(lowpass(rng.standard_normal(seg), 45), 45)
swell = (0.55 + 0.45 * np.sin(2 * np.pi * tt / 6.5)) ** 2
edge = np.minimum(1, tt / 1.5) * np.minimum(1, (11 - tt) / 1.5)
put(24.0, ocean * swell * edge, 0.5)

# Chim rung thua (trong doan zones 14-24s)
for ct in [15.2, 18.7, 21.3, 55.5]:
    ct_t = np.arange(int(0.14 * SR)) / SR
    chirp = np.sin(2 * np.pi * (4300 - 1400 * ct_t / 0.14) * ct_t) \
        * np.sin(np.pi * ct_t / 0.14) ** 2
    put(ct, chirp, 0.035, pan=rng.uniform(-0.6, 0.6))

# Whoosh chuyen canh
def whoosh(t0, dur=0.8):
    m = int(dur * SR)
    nz = rng.standard_normal(m)
    spec = np.fft.rfft(nz)
    freqs = np.fft.rfftfreq(m, 1 / SR)
    out = np.zeros(m)
    step = SR // 20
    for s in range(0, m, step):
        e = min(m, s + step)
        c = 300 + 2700 * (s / m)
        mask = np.exp(-0.5 * ((freqs - c) / 500) ** 2)
        chunk = np.fft.irfft(np.fft.rfft(nz[s:e]) * mask[:len(np.fft.rfft(nz[s:e]))], e - s)
        out[s:e] = chunk
    env = np.sin(np.pi * np.arange(m) / m) ** 2
    put(t0, out * env, 0.30)
whoosh(31.8)
whoosh(57.3)
whoosh(102.2, 1.1)

# Lua Chuc Long (84-97s): ram thap + tieng no liti
seg = int(13 * SR)
tt = np.arange(seg) / SR
fire = lowpass(rng.standard_normal(seg), 120) * np.minimum(1, tt / 1.2) \
    * np.minimum(1, (13 - tt) / 1.2)
put(84.0, fire, 0.20)
for _ in range(110):
    pt = 84.3 + rng.uniform(0, 12.2)
    plen = int(rng.uniform(0.002, 0.008) * SR)
    pop = rng.standard_normal(plen) * np.exp(-np.arange(plen) / (plen * 0.3))
    put(pt, pop, rng.uniform(0.05, 0.22), pan=rng.uniform(-0.8, 0.8))

# Tieng gam cua di thu
def roar(t0, f0=80.0, dur=1.6, gain=0.55):
    t = np.arange(int(dur * SR)) / SR
    f = f0 * (1 + 0.35 * np.exp(-t * 2.2)) * (1 + 0.03 * np.sin(2 * np.pi * 27 * t))
    ph = np.cumsum(f) / SR * 2 * np.pi
    w = np.tanh(2.2 * (np.sin(ph) + 0.5 * np.sin(2 * ph) + 0.25 * np.sin(3 * ph)))
    growl = 0.75 + 0.25 * np.sin(2 * np.pi * 23 * t)
    env = np.minimum(1, t / 0.18) * np.exp(-np.maximum(0, t - dur * 0.55) * 2.4)
    breath = lowpass(rng.standard_normal(len(t)), 30) * 0.4
    put(t0, (w * growl + breath) * env, gain)
roar(77.0, 84, 1.5, 0.5)     # Cung Ky
roar(86.9, 64, 1.9, 0.6)     # Chuc Long
roar(102.9, 74, 2.2, 0.7)    # Ung Long

mix = music + vo_track + amb
mix = np.tanh(mix * 1.1)
mix = mix / max(1e-6, np.max(np.abs(mix))) * 0.89
pcm = (mix * 32767).astype(np.int16)
out_wav = os.path.join(TR, "final_mix.wav")
with wavmod.open(out_wav, "wb") as wf:
    wf.setnchannels(2)
    wf.setsampwidth(2)
    wf.setframerate(SR)
    wf.writeframes(pcm.tobytes())
print("Mix xong")

OUT = os.path.join(TR, "SON_HAI_KINH_PHIEU_LUU_KY_TRAILER_VO.mp4")
r = subprocess.run(["ffmpeg", "-y", "-v", "error", "-i",
                    os.path.join(TR, "silent.mp4"), "-i", out_wav,
                    "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                    "-af", "loudnorm=I=-14:TP=-1.5:LRA=11,"
                           "afade=t=in:st=0:d=0.4,afade=t=out:st=115.5:d=2.5",
                    "-c:a", "aac", "-b:a", "192k", "-shortest", OUT])
if r.returncode != 0:
    sys.exit(1)
print("TRAILER VO:", OUT, f"{os.path.getsize(OUT)/1e6:.1f} MB")
