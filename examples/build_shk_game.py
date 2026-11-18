#!/usr/bin/env python3
"""Build game Son Hai Kinh Phieu Luu Ky (ban dang nhap + random loai + san/tron).

Ghep vao game/shk_template.html:
  - GAME_DATA: 30 loai noi bat (gon), toan bo 31.189 loai dong/thuc vat that
    (data/game_species_all.json), du lieu Son Hai Kinh (data/shk_data.json)
  - ART: anh 30 loai + 5 vung + 4 di thu tien hoa + nen dang nhap (base64 WebP)
Dau ra: game/son-hai-kinh-phieu-luu-ky.html
"""
import base64
import io
import json
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
GAME = ROOT / "game"
GROUP_MAP = {"thu": "mammal", "chim": "bird", "ca": "fish", "bo_sat": "reptile",
             "luong_cu": "amphibian", "con_trung": "insect", "thuc_vat": "plant"}
ZONES = ["linh-ho", "rung-than-moc", "hoa-diem-nguyen", "linh-dien", "van-hai-dao"]


def data_uri(path: Path, max_w: int) -> str:
    im = Image.open(path).convert("RGB")
    if im.width > max_w:
        im = im.resize((max_w, round(im.height * max_w / im.width)), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "WEBP", quality=78)
    return "data:image/webp;base64," + base64.b64encode(buf.getvalue()).decode()


def main():
    gd = json.loads((ROOT / "data" / "game_data.json").read_text())
    featured = [{"t": sp["taxid"], "vn": sp["vn"], "n": sp["name"],
                 "g": GROUP_MAP.get(sp["group"], sp["group"]),
                 "ge": sp["genes"], "b": sp["blocks"]} for sp in gd["species"]]
    pack = json.loads((ROOT / "data" / "game_species_all.json").read_text())
    shk = json.loads((ROOT / "data" / "shk_data.json").read_text())
    game_data = {"featured": featured, "species": pack["species"], "shk": shk}

    art = {"species": {}, "zones": {}, "forms": {}}
    missing = []
    for sp in gd["species"]:
        p = GAME / "art_species" / f"{sp['taxid']}.webp"
        if not p.exists():
            missing.append(str(p)); continue
        art["species"][str(sp["taxid"])] = data_uri(p, 1000)
    for z in ZONES:
        p = GAME / "art_zones" / "final" / f"{z}.webp"
        if not p.exists():
            missing.append(str(p)); continue
        art["zones"][z] = data_uri(p, 1600)
    for n in range(1, 9):
        p = GAME / "art_forms" / f"stage{n}.webp"
        if not p.exists():
            missing.append(str(p)); continue
        art["forms"][str(n)] = data_uri(p, 1200)
    login = GAME / "art_zones" / "final" / "login.webp"
    if not login.exists():
        missing.append(str(login))
    else:
        art["login"] = data_uri(login, 1600)
    assert not missing, "Thieu anh: " + ", ".join(missing)

    tpl = (GAME / "shk_template.html").read_text(encoding="utf-8")
    html = tpl.replace("/*__DATA__*/ null",
                         json.dumps(game_data, ensure_ascii=False, separators=(",", ":")))
    html = html.replace("/*__ART__*/ null",
                        json.dumps(art, ensure_ascii=False, separators=(",", ":")))
    assert "/*__DATA__*/" not in html and "/*__ART__*/" not in html
    dest = GAME / "son-hai-kinh-phieu-luu-ky.html"
    dest.write_text(html, encoding="utf-8")
    print(f"Da ghi {dest} ({dest.stat().st_size/1e6:.2f} MB) — "
          f"{len(game_data['species'])} loai, {len(game_data['featured'])} loai noi bat, "
          f"{len(shk['maps'])} map SHK, {len(art['species'])} anh loai, {len(art['forms'])} anh di thu")


if __name__ == "__main__":
    main()
