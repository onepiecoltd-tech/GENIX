"""
Demo v2 — Đa loài & ghép khác loài theo ý tưởng:
 Heo = 1 block gồm 300 gene-block nhỏ bất biến. Gà, cây lúa cũng vậy.
 Ghép gene heo × gà -> block mới. Ghép tiếp block lai × cây -> block mới nữa.
Chạy:  PYTHONPATH=src python3 examples/demo_cross_species.py
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from genechain.ipfs_sim import IPFSStore
from genechain.dag import PedigreeDAG
from genechain.genome_registry import GenomeRegistry

ROOT = os.path.join(os.path.dirname(__file__), "..")
reg = GenomeRegistry(IPFSStore(os.path.join(ROOT, "data", "ipfs")), PedigreeDAG())

print("=" * 70)
print("BƯỚC 1 — MỖI LOÀI LÀ 1 BLOCK GỒM 300 GENE-BLOCK NHỎ BẤT BIẾN")
blocks = {}
for key in ("heo", "ga", "lua"):
    blk = reg.mint_species(key)
    blocks[key] = blk
    print(f"  #{blk.token_id} {blk.name:<42} genes={len(blk.gene_cids)} "
          f"merkle_root={blk.merkle_root[:16]}… verified={reg.verify_block(blk.token_id)}")

print("\nBƯỚC 2 — GHÉP GEN HEO × GÀ -> BLOCK MỚI (chimera in-silico)")
chimera = reg.synthesize(blocks["heo"].token_id, blocks["ga"].token_id,
                         "Block Lai Heo-Gà (HG-01)", creator="PhongTongHopGen (Eve)")
print(f"  #{chimera.token_id} {chimera.name} | parents={[blocks['heo'].token_id, blocks['ga'].token_id]} "
      f"| genes={len(chimera.gene_cids)} | merkle_root={chimera.merkle_root[:16]}…")
print(f"  Thành phần truy xuất ngược: {reg.composition_of(chimera.token_id)}")

print("\nBƯỚC 3 — GHÉP TIẾP (HEO-GÀ) × CÂY LÚA -> BLOCK MỚI THẾ HỆ 2")
tri = reg.synthesize(chimera.token_id, blocks["lua"].token_id,
                     "Block Lai Heo-Gà-Lúa (HGL-02)", creator="PhongTongHopGen (Eve)")
print(f"  #{tri.token_id} {tri.name} | generation={tri.generation} | genes={len(tri.gene_cids)}")
print(f"  Thành phần truy xuất ngược: {reg.composition_of(tri.token_id)}")
print(f"  Toàn bộ tổ tiên của block lai 3 loài: {reg.dag.ancestors(tri.token_id)}")

print("\nBƯỚC 4 — MERKLE PROOF: CHỨNG MINH 1 GENE HEO NẰM TRONG BLOCK LAI 3 LOÀI")
target = next(cid for cid in tri.gene_cids
              if reg.ipfs.get(cid)["origin"] == "heo")
gene = reg.ipfs.get(target)
proof = reg.prove_gene(tri.token_id, target)
print(f"  Gene {gene['code']} ({gene['name']}) | CID={target[:20]}…")
print(f"  Proof gồm {len(proof['proof'])} bước (log2(300) ≈ 9) | verified={proof['verified']}")
print("=" * 70)
