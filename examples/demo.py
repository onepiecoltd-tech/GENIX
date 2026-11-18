"""
Demo end-to-end 4 bước theo bản tóm tắt:
 1. Genesis Blocks -> 2. Lai tạo F1, F2 -> 3. Xem cấu phần -> 4. Truy xuất ngược + chia royalty
Chạy:  PYTHONPATH=src python3 examples/demo.py
"""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from genechain.ipfs_sim import IPFSStore
from genechain.dag import PedigreeDAG
from genechain.chain import GeneChain

ROOT = os.path.join(os.path.dirname(__file__), "..")
ipfs = IPFSStore(os.path.join(ROOT, "data", "ipfs"))
chain = GeneChain(ipfs, PedigreeDAG())

with open(os.path.join(ROOT, "data", "genesis.json"), encoding="utf-8") as f:
    seed = json.load(f)
genes = seed["genes"]

print("=" * 68)
print("BƯỚC 1 — GENESIS BLOCKS (giống thuần chủng gốc)")
for sp in seed["genesis_species"]:
    blk = chain.mint_genesis(sp["name"], sp["creator"], [genes[g] for g in sp["genes"]])
    print(f"  #{blk.token_id} {blk.name} | creator={blk.creator} | hash={blk.block_hash[:16]}…")

print("\nBƯỚC 2 — LAI TẠO (Recombination: A+B -> C, gen gốc chỉ tái tổ hợp)")
f1 = chain.breed(1, 2, "Delta Gold F1", breeder="NongTrai-Xanh (Dave)")
print(f"  #{f1.token_id} {f1.name} | parents=[1,2] | gen={f1.generation} | hash={f1.block_hash[:16]}…")
f2 = chain.breed(f1.token_id, 3, "Mekong Prime F2", breeder="NongTrai-Xanh (Dave)")
print(f"  #{f2.token_id} {f2.name} | parents=[{f1.token_id},3] | gen={f2.generation} | hash={f2.block_hash[:16]}…")

print("\nBƯỚC 3 — CẤU PHẦN CHI TIẾT CỦA F2 (đọc ngược từ IPFS qua CID)")
d = chain.describe(f2.token_id)
for g in d["genes"]:
    print(f"  - [{g['trait']:<10}] {g['code']} {g['name']}: {g['score']}/100 — {g['description']}")

print("\nBƯỚC 4 — TRUY XUẤT NGƯỢC & CHIA ROYALTY (bán thương mại 100,000)")
r = chain.trace_and_split(f2.token_id, sale_amount=100_000)
print(f"  Verified Merkle hash: {r['verified']} | Tổ tiên: {r['ancestors']}")
print(f"  Đóng góp gen từ genesis: {r['contributions']}")
print(f"  Royalty pool (10%): {r['royalty_pool']:,.0f} | Người bán giữ: {r['seller_keeps']:,.0f}")
for creator, amt in r["payouts"].items():
    print(f"    -> {creator}: {amt:,.0f}")
print("=" * 68)
