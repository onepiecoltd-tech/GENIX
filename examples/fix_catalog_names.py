""" Vá tên khoa học cho catalog: bản harvest đầu ghi tên rỗng do lỗi tách trường
names.dmp (trường name_class dính ký tự '|'). Chạy sau khi harvest xong:
    python3 examples/fix_catalog_names.py
"""
import json, os, sys, tarfile

ROOT = os.path.join(os.path.dirname(__file__), "..")
names = {}
with tarfile.open(os.path.join(ROOT, "data", "bulk", "taxdump.tar.gz")) as tf:
    with tf.extractfile("names.dmp") as f:
        for raw in f:
            parts = raw.decode("utf-8", "replace").split("\t|\t")
            if len(parts) >= 4 and parts[3].strip().strip("|").strip() == "scientific name":
                names[int(parts[0])] = parts[1].strip()
print(f"Đã nạp {len(names):,} tên khoa học")

cat_path = os.path.join(ROOT, "data", "catalog_all_species.json")
catalog = json.load(open(cat_path, encoding="utf-8"))
fixed = 0
for taxid, info in catalog.items():
    nm = names.get(int(taxid), "")
    if nm:
        info["scientific_name"] = nm
        fixed += 1
json.dump(catalog, open(cat_path, "w", encoding="utf-8"), ensure_ascii=False)
print(f"Đã vá tên cho {fixed:,}/{len(catalog):,} taxon trong catalog")
for t in ("9823", "9031", "4530"):
    if t in catalog:
        print(f"  taxid {t}: {catalog[t]}")
