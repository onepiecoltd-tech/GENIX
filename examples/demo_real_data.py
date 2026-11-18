"""
Demo v3 — Nạp dữ liệu gen THẬT từ NCBI vào GeneChain.
Mỗi loài: kéo 300 gene thật -> đóng băng vào IPFS -> tạo SpeciesBlock 300 gene.
Chạy:  PYTHONPATH=src python3 examples/demo_real_data.py
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from genechain.ipfs_sim import IPFSStore
from genechain.dag import PedigreeDAG
from genechain.genome_registry import GenomeRegistry
from genechain.real_data import load_real_genes, TAXID

ROOT = os.path.join(os.path.dirname(__file__), "..")
reg = GenomeRegistry(IPFSStore(os.path.join(ROOT, "data", "ipfs")), PedigreeDAG())
NAMES = {"heo": "Heo (Sus scrofa domesticus)", "ga": "Gà (Gallus gallus domesticus)",
         "lua": "Cây lúa (Oryza sativa)"}

print("=" * 70)
print("NẠP 300 GENE THẬT TỪ NCBI GENE CHO TỪNG LOÀI")
made = {}
for key in ("heo", "ga", "lua"):
    genes = load_real_genes(key, 300, cache_dir=os.path.join(ROOT, "data", "real"))
    blk = reg.mint_from_gene_dicts(NAMES[key] + " — dữ liệu thật NCBI", f"NCBI-import ({key})", genes)
    made[key] = blk
    print(f"  #{blk.token_id} {blk.name}: genes={len(blk.gene_cids)} "
          f"merkle_root={blk.merkle_root[:16]}… verified={reg.verify_block(blk.token_id)}")
    for g in genes[:3]:
        print(f"      vd: {g['code']} {g['name']} — {g['description']} "
              f"| NST {g['chromosome']} | {g['length_bp']} bp")

print("\nGHÉP THẬT: HEO × GÀ BẰNG GENE THẬT NCBI")
child = reg.synthesize(made["heo"].token_id, made["ga"].token_id,
                       "Block Lai Heo-Gà (gene thật NCBI)", creator="NCBI-import demo")
print(f"  #{child.token_id} genes={len(child.gene_cids)} | thành phần: {reg.composition_of(child.token_id)}")
print("=" * 70)
