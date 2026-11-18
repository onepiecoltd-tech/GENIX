#!/usr/bin/env python3
"""Sinh loi thoai trailer bang TTS (giong nam tram, hung), tung cau mot file."""
import subprocess, os, sys

TR = os.path.expanduser("~/workspace/genechain-merkle-dag/trailer")
VO = os.path.join(TR, "vo")
os.makedirs(VO, exist_ok=True)
VOICE = "avocado_v2:magnus"  # Boomy Mountain: nam, tram, uy nghi

LINES = [
    "Ngàn năm trước, Sơn Hải Kinh đã ghi lại một thế giới của dị thú và thần sơn.",
    "Nay, thế giới ấy sống lại. Hoang dã. Khốc liệt. Không khoan nhượng.",
    "Tám vùng đất huyền thoại đang chờ kẻ dám bước vào.",
    "Từ biển Quy Khư sâu thẳm, đến Côn Luân mây phủ.",
    "Nơi đây, chỉ kẻ mạnh mới sống sót.",
    "Ba mươi mốt nghìn, một trăm tám mươi chín loài thật, từ dữ liệu gen của chính Trái Đất này.",
    "Mỗi người chơi, một loài duy nhất. Không ai giống ai.",
    "Sinh ra yếu ớt sao? Hãy đi săn, và gộp gen của con mồi.",
    "Thu thập từng bộ phận. Vảy cá. Sừng trâu. Thân rắn. Vuốt ưng.",
    "Để tiến hoá thành dị thú trong truyền thuyết.",
    "Tám cấp tiến hoá. Một đỉnh cao duy nhất.",
    "Nhưng nhớ lấy: kẻ săn mồi, cũng có thể trở thành con mồi.",
    "Chúc Long mở mắt, ngày hoá thành đêm.",
    "Khán giả không chỉ xem. Họ vào chơi cùng bạn, ngay trong buổi live.",
    "Một thế giới. Một loài. Một kẻ ngự trị.",
    "Sơn Hải Kinh, Phiêu Lưu Ký. Bạn sẽ là loài nào?",
]

for i, line in enumerate(LINES, 1):
    out = os.path.join(VO, f"vo_{i:02d}.mp3")
    if os.path.exists(out) and os.path.getsize(out) > 1000:
        print(f"vo_{i:02d} da co, bo qua")
        continue
    r = subprocess.run(["/opt/hatch/bin/tts", "speak", "--voice", VOICE,
                        "--language", "vi", "--speed", "95",
                        "--output", out, "--text-stdin"],
                       input=line, capture_output=True, text=True, timeout=180)
    if r.returncode != 0:
        print(f"vo_{i:02d} LOI:\n", r.stdout[-500:], r.stderr[-500:])
        sys.exit(1)
    print(f"vo_{i:02d} OK")

# Do thoi luong tung cau
for i in range(1, len(LINES) + 1):
    p = os.path.join(VO, f"vo_{i:02d}.mp3")
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                        "format=duration", "-of", "csv=p=0", p],
                       capture_output=True, text=True)
    print(f"vo_{i:02d}: {float(r.stdout.strip()):.2f}s | {LINES[i-1][:50]}")
