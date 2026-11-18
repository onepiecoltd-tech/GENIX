#!/usr/bin/env python3
"""Trich goi du lieu toan bo loai dong/thuc vat cho game Son Hai Kinh.

Nguon: catalog_all_species.json (ten, tong gen, kingdom) + bang species trong
registry SQLite (distinct_blocks that) + bucket phan loai tu file bulk NCBI
(Mammalia / Invertebrates / Non-mammalian vertebrates / Plants).
Chi lay cac loai da co trong registry (dong vat + thuc vat, 31.189 loai).
Nam (fungi) chua nap xong registry nen chua vao goi nay.

Dau ra: data/game_species_all.json
  {"count": N, "species": [[taxid, ten_khoa_hoc, bucket, genes, blocks], ...]}
"""
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BUCKETS = ["mammal", "invertebrate", "vertebrate", "plant", "fungi"]


def main():
    # Nguon so lieu: demo_data.json (da trich tu registry, gom ca 31.189 loai
    # dong/thuc vat kem distinct_blocks that) — tranh doc DB dang bi khoa
    # boi tien trinh nap nam chay nen.
    demo = json.loads((ROOT / "data" / "demo_data.json").read_text())
    tax_path = ROOT / "data" / "species_taxonomy.json"
    taxonomy = json.loads(tax_path.read_text()) if tax_path.exists() else {}
    bucket_of = {}
    bdir = ROOT / "data" / "tmp_buckets"
    for b in BUCKETS:
        p = bdir / f"{b}.txt"
        if p.exists():
            for line in p.read_text().split():
                bucket_of[int(line)] = b
    out = []
    for row in demo["species"]:
        taxid, name, _kingdom, genes, blocks = row[0], row[1], row[2], row[3], row[4]
        tx = taxonomy.get(str(taxid)) or [None, None, None, 0]
        out.append([taxid, name, bucket_of.get(taxid, "?"), genes, blocks,
                    tx[0], tx[1], tx[2], tx[3]])
    out.sort(key=lambda r: r[0])
    dest = ROOT / "data" / "game_species_all.json"
    dest.write_text(json.dumps({"count": len(out), "species": out},
                               ensure_ascii=False, separators=(",", ":")))
    pig = next(r for r in out if r[0] == 9823)
    print(f"Da ghi {dest} ({dest.stat().st_size/1e6:.2f} MB) — {len(out)} loai")
    print("Heo:", pig)
    assert pig[2] == "mammal" and pig[4] == 39244, pig
    from collections import Counter
    print("Theo bucket:", dict(Counter(r[2] for r in out)))


if __name__ == "__main__":
    main()
