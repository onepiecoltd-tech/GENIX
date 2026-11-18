#!/usr/bin/env python3
"""Trailer ~2 phut cho Son Hai Kinh Phieu Luu Ky.
Dung tu: 6 clip AI da gen + anh game that (zones/forms/portraits),
nhac nen tong hop (trong taiko + dan tranh KS + drone), ffmpeg ghep.
"""
import os, subprocess, sys, glob
import numpy as np

ROOT = os.path.expanduser("~/workspace/genechain-merkle-dag")
TR = os.path.join(ROOT, "trailer")
SEG = os.path.join(TR, "segs")
os.makedirs(SEG, exist_ok=True)
FONT = "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf"
W, H, FPS = 1920, 1080, 30

# ---- doi ten clip cho gon ----
CLIPMAP = {"unglong": "ung", "chuclong": "chu", "cuuvi": "cuu",
           "world": "world", "cungky": "cung", "quykhu": "quy"}
for f in glob.glob(os.path.join(TR, "clips", "trailer-*.mp4.mp4")):
    base = os.path.basename(f)
    for k, v in CLIPMAP.items():
        if k in base:
            os.rename(f, os.path.join(TR, "clips", v + ".mp4"))
CLIPS = {v: os.path.join(TR, "clips", v + ".mp4") for v in CLIPMAP.values()}

ZONES = [
    ("linh-ho.webp", "QUY KHƯ · ĐÔNG HẢI"),
    ("rung-than-moc.webp", "THANH KHÂU SƠN"),
    ("hoa-diem-nguyen.webp", "CHƯƠNG NGA SƠN"),
    ("linh-dien.webp", "LINH SƠN"),
    ("van-hai-dao.webp", "CÔN LUÂN KHÂU"),
]
PORTRAITS = [9694, 13397, 32536, 9785, 52644, 61221, 9771, 9646,
             29073, 9612, 185886, 9593, 1496311, 9049, 6645, 28980]
STAGES = [(1, "NHĨ THỬ"), (2, "CỬU VĨ HỒ"), (3, "TẤT PHƯƠNG"), (4, "CÙNG KỲ"),
          (5, "TƯƠNG LIỄU"), (6, "ĐẾ GIANG"), (7, "CHÚC LONG"), (8, "ỨNG LONG")]

def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print("FAIL:", " ".join(cmd[:6]), "...\n", r.stderr[-1500:])
        sys.exit(1)

def dt(text, size, y, color="0xffd76a", border=3):
    return (f"drawtext=fontfile={FONT}:text='{text}':fontsize={size}:"
            f"fontcolor={color}:borderw={border}:bordercolor=black:"
            f"x=(w-text_w)/2:y={y}")

def still_seg(img, dur, out, zoom_to=1.22, texts=(), dim=0.0, fill=False):
    frames = int(dur * FPS)
    if fill:
        vf = (f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,"
              f"crop={W}:{H},gblur=sigma=42,eq=brightness=-0.28[bg];"
              f"[0:v]scale={W}:{H}:force_original_aspect_ratio=decrease[fg];"
              f"[bg][fg]overlay=(W-w)/2:(H-h)/2,"
              f"scale=2560:1440,zoompan=z='1.05+{zoom_to-1.05:.3f}*on/{frames}':"
              f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s={W}x{H}:fps={FPS}")
    else:
        vf = (f"scale=2560:-2,zoompan=z='1.05+{zoom_to-1.05:.3f}*on/{frames}':"
              f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s={W}x{H}:fps={FPS}")
        if dim:
            vf += f",eq=brightness=-{dim}"
    for t in texts:
        vf += "," + t
    cmd = ["ffmpeg", "-y", "-loop", "1", "-i", img, "-filter_complex", vf,
           "-frames:v", str(frames), "-c:v", "libx264", "-preset", "veryfast",
           "-crf", "20", "-pix_fmt", "yuv420p", "-r", str(FPS), out]
    if not fill:
        cmd = ["ffmpeg", "-y", "-loop", "1", "-i", img, "-vf", vf,
               "-frames:v", str(frames), "-c:v", "libx264", "-preset", "veryfast",
               "-crf", "20", "-pix_fmt", "yuv420p", "-r", str(FPS), out]
    run(cmd)

def clip_seg(clip, dur, out, start=0.5, texts=()):
    vf = (f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
          f"fps={FPS},setsar=1")
    for t in texts:
        vf += "," + t
    run(["ffmpeg", "-y", "-ss", str(start), "-i", clip, "-vf", vf, "-t", str(dur),
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
         "-pix_fmt", "yuv420p", "-r", str(FPS), "-an", out])

segs = []
def add(path):
    segs.append(path)
    return path

G = os.path.join(ROOT, "game")
n = 0
def nxt():
    global n
    n += 1
    return os.path.join(SEG, f"seg_{n:02d}.mp4")

# 1. Title (5s)
p = nxt(); still_seg(os.path.join(G, "art_zones/final/login.webp"), 5.0, p, 1.16,
    texts=(dt("SƠN HẢI KINH", 118, 380), dt("PHIÊU LƯU KÝ", 118, 510),
           dt("SINH TỒN · GỘP GEN · TIẾN HOÁ", 44, 680, "0xffffff", 2))); add(p)
# 2. World clip (8s)
p = nxt(); clip_seg(CLIPS["world"], 8.0, p, 0.5); add(p)
# 3. Zones montage (5 x 2.6s)
for fn, name in ZONES:
    p = nxt(); still_seg(os.path.join(G, "art_zones/final", fn), 2.6, p, 1.2,
        texts=(dt(name, 52, 950),)); add(p)
# 4. Quy Khu clip (6s)
p = nxt(); clip_seg(CLIPS["quy"], 6.0, p, 1.0); add(p)
# 5. Species rapid fire (16 x 1.0s)
for t in PORTRAITS:
    p = nxt(); still_seg(os.path.join(G, "art_species2", f"{t}.webp"), 1.0, p,
                         1.14, fill=True); add(p)
# 6. Text card 31.189 (2.5s)
p = nxt(); still_seg(os.path.join(G, "art_species/9823.webp"), 2.5, p, 1.12, dim=0.42,
    texts=(dt("31.189 LOÀI THẬT", 96, 400),
           dt("Dữ liệu gen thật từ NCBI — mỗi người chơi MỘT loài", 42, 560, "0xffffff", 2))); add(p)
# 7. Cuu Vi clip (7s)
p = nxt(); clip_seg(CLIPS["cuu"], 7.0, p, 0.5); add(p)
# 8. Evolution ladder (8 x 2.4s)
for st, name in STAGES:
    p = nxt(); still_seg(os.path.join(G, "art_forms", f"stage{st}.webp"), 2.4, p,
        1.1 + st * 0.025, texts=(dt(f"CẤP {st} — {name}", 56, 950),)); add(p)
# 9. Cung Ky clip (7s)
p = nxt(); clip_seg(CLIPS["cung"], 7.0, p, 0.5); add(p)
# 10. Text card cong thuc (2.5s)
p = nxt(); still_seg(os.path.join(G, "art_forms/stage8.webp"), 2.5, p, 1.12, dim=0.42,
    texts=(dt("GỘP GEN — THU THẬP BỘ PHẬN", 72, 400),
           dt("Vảy cá · Sừng trâu · Thân rắn · Vuốt ưng · Cánh rồng", 42, 540, "0xffffff", 2))); add(p)
# 11. Chuc Long clip (8s)
p = nxt(); clip_seg(CLIPS["chu"], 8.0, p, 0.5); add(p)
# 12. Feature cards (3 x 2.6s)
FEATS = [
    ("art_species2/9694.webp", "SĂN HOẶC TRỐN", "Kẻ mạnh sống sót — kẻ yếu thành mồi"),
    ("art_forms/stage3.webp", "CHƠI ONLINE NHIỀU NGƯỜI", "Khán giả vào chơi qua link ghim ở bình luận"),
    ("art_forms/stage6.webp", "LIVE TƯƠNG TÁC", "Bình luận «SĂN / CHẠY» — số đông điều khiển trận đấu"),
]
for img, l1, l2 in FEATS:
    p = nxt(); still_seg(os.path.join(G, img), 2.6, p, 1.14, dim=0.38,
        texts=(dt(l1, 68, 420), dt(l2, 40, 545, "0xffffff", 2))); add(p)
# 13. Ung Long clip (10s)
p = nxt(); clip_seg(CLIPS["ung"], 10.0, p, 0.0); add(p)
# 14. End card (6s)
p = nxt(); still_seg(os.path.join(G, "art_forms/stage8.webp"), 6.0, p, 1.2,
    texts=(dt("SƠN HẢI KINH PHIÊU LƯU KÝ", 76, 400),
           dt("BẠN SẼ LÀ LOÀI NÀO?", 54, 540, "0xffffff", 2))); add(p)

# ---- tong thoi luong ----
def dur_of(f):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                        "format=duration", "-of", "csv=p=0", f],
                       capture_output=True, text=True)
    return float(r.stdout.strip())
TOTAL = sum(dur_of(s) for s in segs)
print(f"So doan: {len(segs)} | Tong: {TOTAL:.1f}s")

# ================= NHAC NEN (tong hop) =================
SR = 44100
BPM = 132.0
BEAT = 60.0 / BPM
N = int(TOTAL * SR)
music = np.zeros((N, 2), dtype=np.float64)
rng = np.random.default_rng(42)

def add_tone(buf, t0, wave, gain=1.0):
    i = int(t0 * SR)
    j = min(N, i + len(wave))
    if i < N:
        buf[i:j] += wave[:j - i] * gain

def taiko(t_hit, f0=110.0, dur=0.32, gain=0.9):
    t = np.arange(int(dur * SR)) / SR
    f = f0 * np.exp(-t * 9) + 38
    ph = np.cumsum(f) / SR * 2 * np.pi
    w = np.sin(ph) * np.exp(-t * 11) * gain
    nz = rng.standard_normal(len(t)) * np.exp(-t * 60) * 0.25 * gain
    add_tone(music[:, 0], t_hit, w + nz)
    add_tone(music[:, 1], t_hit, w + nz)

def shaker(t_hit, gain=0.05):
    t = np.arange(int(0.05 * SR)) / SR
    w = rng.standard_normal(len(t)) * np.exp(-t * 90) * gain
    add_tone(music[:, 0], t_hit, w)
    add_tone(music[:, 1], t_hit, w)

def drone(f=73.42, t0=0.0, dur=TOTAL, gain=0.16):
    t = np.arange(int(dur * SR)) / SR
    env = np.minimum(1.0, t / 6.0) * np.minimum(1.0, (dur - t) / 5.0 + 0.2)
    w = (np.sin(2 * np.pi * f * t) + 0.6 * np.sin(2 * np.pi * f * 2 * t)
         + 0.35 * np.sin(2 * np.pi * f * 3.01 * t)
         + 0.5 * np.sin(2 * np.pi * f * 1.5 * t)) * env * gain
    add_tone(music[:, 0], t0, w)
    add_tone(music[:, 1], t0, w * 0.92)

def pluck(freq, t0, gain=0.5, dur=1.4):
    nn = int(SR / freq)
    buf = rng.uniform(-1, 1, nn)
    out = np.zeros(int(dur * SR))
    cur = buf.copy()
    idx = 0
    for i in range(len(out)):
        out[i] = cur[idx]
        cur[idx] = 0.996 * 0.5 * (cur[idx] + cur[(idx + 1) % nn])
        idx = (idx + 1) % nn
    out *= np.exp(-np.arange(len(out)) / SR * 1.1) * gain
    add_tone(music[:, 0], t0, out)
    add_tone(music[:, 1], t0, out * 0.9)

def gong(t0, gain=0.8):
    dur = 4.5
    t = np.arange(int(dur * SR)) / SR
    w = np.zeros_like(t)
    for f, a in [(98, 1.0), (147.3, 0.6), (196.5, 0.45), (261.2, 0.3), (329.7, 0.18)]:
        w += a * np.sin(2 * np.pi * f * t) * np.exp(-t * 1.4)
    w *= gain
    add_tone(music[:, 0], t0, w)
    add_tone(music[:, 1], t0, w)

drone()
drone(110.0, gain=0.07)
total_beats = int(TOTAL / BEAT)
# Trong: intro thưa -> groove chinh -> leo thang cuoi
for b in range(total_beats):
    t = b * BEAT
    bar = b // 4
    if b % 4 == 0:
        taiko(t, 120, 0.4, 0.95)
    if b % 4 == 2:
        taiko(t, 95, 0.3, 0.7)
    if b >= 8 and b % 2 == 1:
        taiko(t, 150, 0.16, 0.4)
    if b >= 16:
        shaker(t, 0.045)
        shaker(t + BEAT / 2, 0.03)
    if b >= total_beats - 32 and b % 4 == 3:
        taiko(t, 170, 0.2, 0.55)
# Dan tranh: ngu cung D F G A C — cau chay o cac doan build
PENTA = [293.66, 349.23, 392.0, 440.0, 523.25, 587.33, 698.46, 783.99]
phrase_times = list(np.arange(6 * BEAT, 40 * BEAT, BEAT / 2)) + \
               list(np.arange(64 * BEAT, TOTAL - 14, BEAT / 2))
for i, t in enumerate(phrase_times):
    if t >= TOTAL - 8:
        break
    note = PENTA[(i * 2 + (i // 8) * 3) % len(PENTA)]
    pluck(note, float(t), 0.34)
# Gong mo dau + cao trao cuoi
gong(0.05, 0.5)
gong(max(0.0, TOTAL - 6.2), 0.85)
taiko(TOTAL - 0.6, 90, 0.5, 1.0)

music = np.tanh(music * 1.15)
music = music / max(1e-6, np.max(np.abs(music))) * 0.89
pcm = (music * 32767).astype(np.int16)
import wave as wavmod
with wavmod.open(os.path.join(TR, "score.wav"), "wb") as wf:
    wf.setnchannels(2)
    wf.setsampwidth(2)
    wf.setframerate(SR)
    wf.writeframes(pcm.tobytes())
print("Score xong:", TOTAL, "s")

# ================= GHEP =================
listf = os.path.join(SEG, "list.txt")
with open(listf, "w") as f:
    for s in segs:
        f.write(f"file '{s}'\n")
silent = os.path.join(TR, "silent.mp4")
run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", listf,
     "-c", "copy", silent])
OUT = os.path.join(TR, "SON_HAI_KINH_PHIEU_LUU_KY_TRAILER.mp4")
run(["ffmpeg", "-y", "-i", silent, "-i", os.path.join(TR, "score.wav"),
     "-map", "0:v", "-map", "1:a", "-c:v", "copy",
     "-af", "loudnorm=I=-14:TP=-1.5:LRA=11,afade=t=in:st=0:d=0.4,"
            f"afade=t=out:st={TOTAL-2.5:.1f}:d=2.5",
     "-c:a", "aac", "-b:a", "192k", "-shortest", OUT])
print("TRAILER:", OUT, f"{os.path.getsize(OUT)/1e6:.1f} MB")
