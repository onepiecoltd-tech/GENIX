#!/usr/bin/env python3
"""Trích dữ liệu THẬT từ Block Registry cho game Trái Đất Nguyên Thủy — bản 30 loài.

Đầu ra: data/game_data.json gồm
- species: 30 loài (tên khoa học, tên Việt, nhóm, số gen, số block, Merkle root,
  10 gen protein-coding thật tiêu biểu, và BITSET của tập block mã hoá base64
  để game tự tính hợp block chính xác ngay trong trình duyệt)
- pair_roots: Merkle root THẬT của loài lai cho mọi cặp trong 30 loài
  (tái dùng demo_lab.json nếu có, tính mới bằng genechain.merkle nếu thiếu)
"""
import base64
import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from genechain.merkle import merkle_root  # noqa: E402

DB = ROOT / "data" / "genechain_blocks.db"
OUT = ROOT / "data" / "game_data.json"

# taxid, tên Việt, nhóm, cỡ (0..4), mô hình, màu chính
FEATURED = [
    (9823,  "Heo",                    "thu",       3, "quadruped", "#c98a8a"),
    (9031,  "Gà",                     "chim",      2, "bird",      "#d9a441"),
    (39947, "Lúa Japonica",           "thuc_vat",  1, "plant",     "#7fae4c"),
    (7955,  "Cá ngựa vằn",            "ca",        1, "fish",      "#7fb3d9"),
    (8030,  "Cá hồi Đại Tây Dương",   "ca",        3, "fish",      "#e08e6d"),
    (31033, "Cá nóc hổ",              "ca",        2, "fish",      "#b5c46d"),
    (28377, "Thằn lằn Anole",         "bo_sat",    1, "reptile",   "#6db56d"),
    (8478,  "Rùa vẽ",                 "bo_sat",    2, "reptile",   "#5d8a5d"),
    (8496,  "Cá sấu Mỹ",              "bo_sat",    4, "reptile",   "#4c704c"),
    (8839,  "Vịt nhà",                "chim",      2, "bird",      "#a8c686"),
    (8932,  "Bồ câu",                 "chim",      1, "bird",      "#9aa5b1"),
    (9233,  "Chim cánh cụt hoàng đế", "chim",      2, "bird",      "#5d7a9a"),
    (7227,  "Ruồi giấm",              "con_trung", 0, "insect",    "#b08968"),
    (7460,  "Ong mật",                "con_trung", 0, "insect",    "#e3c341"),
    (7091,  "Tằm",                    "con_trung", 0, "insect",    "#e8e3d3"),
    (9913,  "Bò nhà",                 "thu",       4, "quadruped", "#8a6d52"),
    (9796,  "Ngựa",                   "thu",       4, "quadruped", "#7a5236"),
    (9615,  "Chó nhà",                "thu",       2, "quadruped", "#b08968"),
    (9685,  "Mèo nhà",                "thu",       2, "quadruped", "#9a8b7a"),
    (10090, "Chuột nhắt",             "thu",       1, "quadruped", "#a8a8a8"),
    (9986,  "Thỏ",                    "thu",       2, "quadruped", "#cfc8bd"),
    (9940,  "Cừu",                    "thu",       3, "quadruped", "#e6e1d5"),
    (59729, "Chim sẻ vằn",            "chim",      1, "bird",      "#c46a8a"),
    (9103,  "Gà tây",                 "chim",      2, "bird",      "#6d5a4a"),
    (8090,  "Cá medaka",              "ca",        1, "fish",      "#d9c27a"),
    (69293, "Cá gai ba gai",          "ca",        1, "fish",      "#7a9a8d"),
    (8355,  "Ếch vuốt châu Phi",      "luong_cu",  1, "reptile",   "#5da85d"),
    (6239,  "Giun tròn C. elegans",   "con_trung", 0, "insect",    "#d9b8a6"),
    (4577,  "Ngô (bắp)",              "thuc_vat",  1, "plant",     "#6db56d"),
    (3702,  "Cải Arabidopsis",        "thuc_vat",  0, "plant",     "#8fce62"),
]
N = len(FEATURED)


def main():
    con = sqlite3.connect(DB)
    catalog = json.loads((ROOT / "data" / "catalog_all_species.json").read_text())

    species = []
    block_lists = []
    for idx, (taxid, vn, group, size, model, color) in enumerate(FEATURED):
        row = con.execute(
            "SELECT gene_records, distinct_blocks, merkle_root FROM species WHERE taxid=?",
            (taxid,)).fetchone()
        assert row, f"thieu species {taxid}"
        genes, blocks, root = row
        syms = con.execute(
            """SELECT b.symbol, b.full_name FROM blocks b
               JOIN occurrences o ON o.block_id = b.block_id
               WHERE o.taxid=? AND b.gene_type='protein-coding'
               GROUP BY b.block_id ORDER BY b.symbol""", (taxid,)).fetchall()
        step = max(1, len(syms) // 10)
        samples = [{"symbol": s, "name": (f or "")} for s, f in syms[::step][:10]]
        ids = [r[0] for r in con.execute(
            "SELECT DISTINCT block_id FROM occurrences WHERE taxid=?", (taxid,))]
        block_lists.append(set(ids))
        species.append({
            "idx": idx, "taxid": taxid,
            "name": catalog[str(taxid)]["scientific_name"],
            "vn": vn, "group": group, "size": size, "model": model, "color": color,
            "genes": genes, "blocks": blocks, "root": root,
            "sample_genes": samples,
        })
        print(f"[{idx}] {species[-1]['name']}: {genes} gen, {blocks} block", flush=True)

    # --- Bitset tập block của từng loài trên vũ trụ chung ---
    universe = {}
    for ids in block_lists:
        for b in ids:
            if b not in universe:
                universe[b] = len(universe)
    U = len(universe)
    nbytes = (U + 7) // 8
    print(f"Vu tru block cua {N} loai: {U} ({nbytes} byte/loai)", flush=True)
    for sp, ids in zip(species, block_lists):
        v = 0
        for b in ids:
            v |= 1 << universe[b]
        assert v.bit_count() == sp["blocks"]
        sp["bits"] = base64.b64encode(v.to_bytes(nbytes, "little")).decode()

    # --- Merkle root loài lai cho mọi cặp ---
    lab = json.loads((ROOT / "data" / "demo_lab.json").read_text())
    by_taxid = {sp["taxid"]: sp["idx"] for sp in species}
    known = {}
    for key, pair in lab.get("pairs", {}).items():
        a, b = (int(x) for x in key.split("x"))
        if a in by_taxid and b in by_taxid:
            i, j = sorted((by_taxid[a], by_taxid[b]))
            known[f"{i}-{j}"] = pair["root"]
    pair_roots = {}
    total = N * (N - 1) // 2
    done = 0
    for i in range(N):
        for j in range(i + 1, N):
            k = f"{i}-{j}"
            pair_roots[k] = known.get(k) or merkle_root(sorted(block_lists[i] | block_lists[j]))
            done += 1
            if done % 40 == 0:
                print(f"pair_roots {done}/{total}", flush=True)
    print(f"pair_roots: {len(pair_roots)} cap (tai dung {len(known)})", flush=True)
    assert pair_roots["0-1"] == "9f85aa43be79fba5b9ebe9951a457452aca91c493da5a0668771472f62951c07"
    print("Kiem chung heo×ga: KHOP root 9f85aa43...", flush=True)

    out = {
        "meta": {"species_count": N, "universe_blocks": U, "bit_bytes": nbytes,
                 "note": "So lieu that tu GeneChain Block Registry (NCBI), tinh 18/11/2026"},
        "species": species,
        "pair_roots": pair_roots,
    }
    OUT.write_text(json.dumps(out, ensure_ascii=False))
    print(f"Da ghi {OUT} ({OUT.stat().st_size/1e6:.2f} MB)")


if __name__ == "__main__":
    main()
