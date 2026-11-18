"""
Harvester dữ liệu gen thật cho TOÀN BỘ loài động vật + thực vật có trong NCBI Gene.

Nguồn chính thống cho bulk (không nện API từng loài):
  NCBI FTP gene/DATA/GENE_INFO/{Plants, Invertebrates, Mammalia,
  Non-mammalian_vertebrates}/All_*.gene_info.gz  (~1,17 GB tổng)
  + NCBI Taxonomy taxdump.tar.gz (80 MB) để lấy tên khoa học theo tax_id.

Với mỗi loài (tax_id) streaming qua file 1 lần duy nhất:
  - đếm TỔNG số gene thật của loài (ghi vào catalog)
  - giữ tối đa 300 gene làm gene-block (ưu tiên protein-coding, thiếu thì bù loại khác)
  - ghi data/species_genes/<taxid>.json
Có checkpoint theo từng file nguồn (data/bulk/progress.json) — chạy lại sẽ bỏ qua
file đã xong. Chạy:  python3 -m genechain.bulk_harvest  (hoặc examples/harvest_all.py)
"""
from __future__ import annotations
import gzip, json, os, sys, tarfile, time
from collections import defaultdict

GENE_PER_SPECIES = 300
GROUP_FILES = [
    ("Plants", "All_Plants.gene_info.gz", "plant"),
    ("Invertebrates", "All_Invertebrates.gene_info.gz", "animal"),
    ("Mammalia", "All_Mammalia.gene_info.gz", "animal"),
    ("Non-mammalian_vertebrates", "All_Non-mammalian_vertebrates.gene_info.gz", "animal"),
]


def load_taxon_names(bulk_dir: str) -> dict:
    """tax_id -> scientific name, từ taxdump.tar.gz (names.dmp)."""
    names = {}
    with tarfile.open(os.path.join(bulk_dir, "taxdump.tar.gz")) as tf:
        with tf.extractfile("names.dmp") as f:
            for raw in f:
                parts = raw.decode("utf-8", "replace").split("\t|\t")
                if len(parts) >= 4 and parts[3].strip() == "scientific name":
                    names[int(parts[0])] = parts[1].strip()
    return names


def parse_group_file(path: str, kingdom: str, out_dir: str, stats: dict):
    """Streaming 1 file gene_info.gz: đếm + giữ 300 gene/loài, ghi file theo loài.

    File NCBI đã sắp xếp theo tax_id (đã kiểm chứng) nên chỉ cần giữ gene của
    taxon hiện tại trong RAM (<=600 dict) rồi xả xuống đĩa khi đổi taxon —
    an toàn bộ nhớ dù file có hàng chục triệu dòng.
    Cột gene_info: 0 tax_id, 1 GeneID, 2 Symbol, 6 chromosome, 7 map_location,
    8 description, 9 type_of_gene (đã đối chiếu với header thật).
    """
    os.makedirs(out_dir, exist_ok=True)
    n_taxa = 0

    def flush(taxid, total, pc, other):
        nonlocal n_taxa
        if taxid is None:
            return
        genes = (pc + other)[:GENE_PER_SPECIES]
        with open(os.path.join(out_dir, f"{taxid}.json"), "w", encoding="utf-8") as fo:
            json.dump(genes, fo, ensure_ascii=False)
        stats[taxid] = {"total_genes": total, "harvested_genes": len(genes), "kingdom": kingdom}
        n_taxa += 1

    cur, total, pc, other = None, 0, [], []
    with gzip.open(path, "rt", encoding="utf-8", errors="replace") as f:
        f.readline()  # header
        for line in f:
            c = line.rstrip("\n").split("\t")
            if len(c) < 10:
                continue
            taxid = int(c[0])
            if taxid != cur:
                flush(cur, total, pc, other)
                cur, total, pc, other = taxid, 0, [], []
            total += 1
            gene = {"code": f"NCBI:{c[1]}", "name": c[2], "trait": c[9],
                    "chromosome": c[6], "map_location": c[7], "description": c[8],
                    "origin_taxid": taxid, "source": "NCBI Gene bulk (gene_info)"}
            if gene["trait"] == "protein-coding":
                if len(pc) < GENE_PER_SPECIES:
                    pc.append(gene)
            elif len(other) < GENE_PER_SPECIES:
                other.append(gene)
    flush(cur, total, pc, other)
    return n_taxa


def run(root: str):
    bulk_dir = os.path.join(root, "data", "bulk")
    out_dir = os.path.join(root, "data", "species_genes")
    prog_path = os.path.join(bulk_dir, "progress.json")
    progress = json.load(open(prog_path)) if os.path.exists(prog_path) else {"done_files": []}
    catalog_path = os.path.join(root, "data", "catalog_all_species.json")
    catalog = json.load(open(catalog_path)) if os.path.exists(catalog_path) else {}

    print("[harvest] Nạp tên khoa học từ taxdump…", flush=True)
    names = load_taxon_names(bulk_dir)
    print(f"[harvest] {len(names):,} taxon có tên khoa học", flush=True)

    for _group, fname, kingdom in GROUP_FILES:
        if fname in progress["done_files"]:
            print(f"[harvest] Bỏ qua (đã xong): {fname}", flush=True)
            continue
        t0 = time.time()
        stats = {}
        n_species = parse_group_file(os.path.join(bulk_dir, fname), kingdom, out_dir, stats)
        for taxid, s in stats.items():
            s["scientific_name"] = names.get(taxid, "")
            catalog[str(taxid)] = s
        progress["done_files"].append(fname)
        json.dump(progress, open(prog_path, "w"))
        json.dump(catalog, open(catalog_path, "w", encoding="utf-8"), ensure_ascii=False)
        print(f"[harvest] Xong {fname}: {n_species:,} loài trong {time.time()-t0:.0f}s", flush=True)

    total_genes = sum(v["total_genes"] for v in catalog.values())
    print(f"[harvest] HOÀN TẤT: {len(catalog):,} loài, {total_genes:,} gene thật trong catalog", flush=True)
    return catalog


if __name__ == "__main__":
    run(sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "..", ".."))
