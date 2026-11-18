#!/usr/bin/env python3
"""Lắp game Trái Đất Nguyên Thủy — BẢN ĐIỆN ẢNH AI.

Đọc game/cinematic_template.html + data/game_data.json + ảnh AI trong
game/art_species/<taxid>.webp và game/art_zones/final/<zone>.webp,
nén ảnh bằng Pillow, nhúng base64 vào template, ghi file game hoàn chỉnh.
"""
import base64
import io
import json
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
GAME = ROOT / "game"
ZONES = ["linh-ho", "rung-than-moc", "hoa-diem-nguyen", "linh-dien", "van-hai-dao"]


def data_uri(path: Path, max_w: int, quality: int = 78) -> str:
    im = Image.open(path).convert("RGB")
    if im.width > max_w:
        im = im.resize((max_w, round(im.height * max_w / im.width)), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "WEBP", quality=quality)
    return "data:image/webp;base64," + base64.b64encode(buf.getvalue()).decode()


def main():
    data = json.loads((ROOT / "data" / "game_data.json").read_text())
    art = {"species": {}, "zones": {}, "forms": {}}
    missing = []
    for sp in data["species"]:
        p = GAME / "art_species" / f"{sp['taxid']}.webp"
        if not p.exists():
            missing.append(str(p))
            continue
        art["species"][str(sp["taxid"])] = data_uri(p, 1000)
    for z in ZONES:
        p = GAME / "art_zones" / "final" / f"{z}.webp"
        if not p.exists():
            missing.append(str(p))
            continue
        art["zones"][z] = data_uri(p, 1600)
    for n in (1, 2, 3, 4):
        p = GAME / "art_forms" / f"form{n}.webp"
        if not p.exists():
            missing.append(str(p))
            continue
        art["forms"][str(n)] = data_uri(p, 1200)
    assert not missing, "Thieu anh: " + ", ".join(missing)

    tpl = (GAME / "cinematic_template.html").read_text(encoding="utf-8")
    assert tpl.count("/*__GAME_DATA__*/") == 1 and tpl.count("/*__ART__*/") == 1
    out = tpl.replace("/*__GAME_DATA__*/", json.dumps(data, ensure_ascii=False))
    out = out.replace("/*__ART__*/", json.dumps(art, ensure_ascii=False))
    dest = GAME / "son-hai-kinh-dien-anh.html"
    dest.write_text(out, encoding="utf-8")
    print(f"Da ghi {dest} ({dest.stat().st_size/1e6:.2f} MB) — "
          f"{len(art['species'])} anh loai, {len(art['zones'])} anh vung, {len(art['forms'])} anh tien hoa")


if __name__ == "__main__":
    main()
