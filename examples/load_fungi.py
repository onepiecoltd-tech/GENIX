"""Nạp bổ sung giới Nấm (All_Fungi.gene_info.gz) vào Block Registry v5.

Dùng lại đúng BlockRegistry.build_file (checkpoint/dọn gap như 4 file gốc),
gán kingdom='fungi', cập nhật catalog (tên khoa học từ taxdump names.dmp),
rồi tính Merkle root cho các loài mới (build_species_roots tự bỏ qua loài đã có).
"""
import gzip
import json
import os
import sqlite3
import sys
import tarfile
from collections import Counter

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from genechain.block_registry import BlockRegistry

ROOT = os.path.join(os.path.dirname(__file__), "..")
BULK = os.path.join(ROOT, "data", "bulk")
DB = os.path.join(ROOT, "data", "genechain_blocks.db")
FNAME = "All_Fungi.gene_info.gz"

# 1) Đếm gene theo taxid + tập taxid nấm từ file
counts = Counter()
with gzip.open(os.path.join(BULK, FNAME), "rt", encoding="utf-8", errors="replace") as f:
    header = f.readline()
    for line in f:
        counts[int(line.split("\t", 1)[0])] += 1
fungi_taxids = set(counts)
print(f"Fungi: {sum(counts.values()):,} gene | {len(fungi_taxids):,} taxid", flush=True)

# 2) Tên khoa học từ taxdump names.dmp (chỉ scientific name)
names = {}
with tarfile.open(os.path.join(BULK, "taxdump.tar.gz")) as tf:
    fh = tf.extractfile("names.dmp")
    for raw in fh:
        parts = raw.decode("utf-8", errors="replace").split("\t|\t")
        if len(parts) >= 4 and parts[3].strip().rstrip("|").strip() == "scientific name":
            tid = int(parts[0])
            if tid in fungi_taxids:
                names[tid] = parts[1].strip()
print(f"Tên khoa học tìm được: {len(names):,}/{len(fungi_taxids):,}", flush=True)

# 3) Kiểm tra chồng lấn với registry hiện tại (kỳ vọng 0)
conn = sqlite3.connect(DB)
existing = {r[0] for r in conn.execute("SELECT taxid FROM species")}
overlap = fungi_taxids & existing
print(f"Taxid nấm đã có trong registry: {len(overlap)}", flush=True)
assert not overlap, f"Chồng lấn taxid: {sorted(overlap)[:5]}"

# 4) Cập nhật catalog (backup trước)
cat_path = os.path.join(ROOT, "data", "catalog_all_species.json")
if not os.path.exists(cat_path + ".bak"):
    with open(cat_path, encoding="utf-8") as f, open(cat_path + ".bak", "w", encoding="utf-8") as g:
        g.write(f.read())
catalog = json.load(open(cat_path, encoding="utf-8"))
for tid in fungi_taxids:
    catalog[str(tid)] = {"total_genes": counts[tid], "harvested_genes": counts[tid],
                         "kingdom": "fungi", "scientific_name": names.get(tid, "")}
with open(cat_path, "w", encoding="utf-8") as f:
    json.dump(catalog, f, ensure_ascii=False)
print(f"Catalog: {len(catalog):,} loài (đã gồm nấm)", flush=True)

# kingdom meta cho build_species_roots
for tid in fungi_taxids:
    conn.execute("INSERT OR REPLACE INTO meta VALUES(?,?)", (f"kingdom:{tid}", "fungi"))
conn.commit()
conn.close()

# 5) Nạp file nấm bằng cơ chế checkpoint chuẩn
reg = BlockRegistry(DB)
reg.build_file(BULK, FNAME, "fungi")

# 6) Merkle root cho loài mới
reg.build_species_roots()

nb = reg.conn.execute("SELECT COUNT(*) FROM blocks").fetchone()[0]
no = reg.conn.execute("SELECT COUNT(*) FROM occurrences").fetchone()[0]
ns = reg.conn.execute("SELECT COUNT(*) FROM species").fetchone()[0]
nf = reg.conn.execute("SELECT COUNT(*) FROM species WHERE kingdom='fungi'").fetchone()[0]
print(f"HOÀN TẤT NẤM: registry hiện có {nb:,} block | {no:,} gene | {ns:,} loài (nấm: {nf:,})", flush=True)
print("Nấm men Saccharomyces cerevisiae (4932):", reg.species_info(4932), flush=True)
