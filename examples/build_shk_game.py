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

# Loai co chan dung rieng doi 2 (game/art_species2/<taxid>.webp): (taxid, ten VN, nhom)
PORTRAITS = [
    (9694, "Hổ Bengal", "mammal"), (9689, "Sư tử châu Phi", "mammal"),
    (9691, "Báo hoa mai", "mammal"), (13125, "Linh miêu Á-Âu", "mammal"),
    (9785, "Voi châu Phi", "mammal"), (9894, "Hươu cao cổ", "mammal"),
    (9833, "Hà mã", "mammal"), (9807, "Tê giác trắng", "mammal"),
    (9627, "Cáo đỏ", "mammal"), (9612, "Sói xám", "mammal"),
    (9646, "Gấu trúc lớn", "mammal"), (9649, "Gấu trúc đỏ", "mammal"),
    (29073, "Gấu Bắc cực", "mammal"), (9593, "Khỉ đột", "mammal"),
    (38626, "Gấu túi koala", "mammal"), (9317, "Kangaroo xám", "mammal"),
    (13397, "Cá mập trắng", "fish"), (9771, "Cá voi xanh", "mammal"),
    (6645, "Bạch tuộc", "invertebrate"), (89248, "Ngựa vằn", "mammal"),
    (13037, "Bướm chúa", "insect"), (52644, "Đại bàng đầu trắng", "bird"),
    (30461, "Cú đại bàng", "bird"), (56313, "Cú lợn", "bird"),
    # Dot 1 (huong toi 300 chan dung)
    (32536, "Báo gêpa", "mammal"), (9690, "Báo đốm Mỹ", "mammal"),
    (29064, "Báo tuyết", "mammal"), (9644, "Gấu nâu", "mammal"),
    (9783, "Voi châu Á", "mammal"), (9901, "Bò rừng Mỹ", "mammal"),
    (9870, "Tuần lộc", "mammal"), (9852, "Nai sừng tấm", "mammal"),
    (8801, "Đà điểu", "bird"), (9049, "Chim công", "bird"),
    (176014, "Vẹt đuôi dài đỏ", "bird"), (185886, "Cá sư tử", "fish"),
    (80972, "Cá hề", "fish"), (195334, "Cá mập đầu búa", "fish"),
    (61221, "Rồng Komodo", "reptile"), (1496311, "Trăn gấm", "reptile"),
    (91907, "Tắc kè hoa", "reptile"), (111132, "Ếch phi tiêu vàng", "amphibian"),
    (63978, "Bướm khế", "insect"), (177283, "Cua dừa", "invertebrate"),
    (109280, "Cá ngựa", "fish"), (28980, "Hồng sam khổng lồ", "plant"),
    (4362, "Cây bẫy kẹp", "plant"), (4232, "Hướng dương", "plant"),
]
# Anh dai dien theo lop sinh hoc NCBI (game/art_classes/<Class>.webp)
CLASSES = ["Magnoliopsida", "Insecta", "Actinopteri", "Mammalia", "Aves",
           "Malacostraca", "Gastropoda", "Amphibia", "Lepidosauria", "Arachnida",
           "Anthozoa", "Bivalvia", "Chondrichthyes", "Polypodiopsida", "Pinopsida",
           "Polychaeta", "Cephalopoda", "Bryopsida", "Echinoidea", "Demospongiae"]


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
    by_taxid = {r[0]: r for r in pack["species"]}
    for t, vn, g in PORTRAITS:
        r = by_taxid.get(t)
        if r:
            game_data["featured"].append({"t": t, "vn": vn, "n": r[1], "g": g,
                                          "ge": r[3], "b": r[4]})

    art = {"species": {}, "zones": {}, "forms": {}, "portraits": {}, "classes": {}}
    missing = []
    for sp in gd["species"]:
        p = GAME / "art_species" / f"{sp['taxid']}.webp"
        if not p.exists():
            missing.append(str(p)); continue
        art["species"][str(sp["taxid"])] = data_uri(p, 1000)
    for t, _vn, _g in PORTRAITS:
        p = GAME / "art_species2" / f"{t}.webp"
        if not p.exists():
            missing.append(str(p)); continue
        art["portraits"][str(t)] = data_uri(p, 720)
    for cn in CLASSES:
        p = GAME / "art_classes" / f"{cn}.webp"
        if not p.exists():
            missing.append(str(p)); continue
        art["classes"][cn] = data_uri(p, 720)
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
