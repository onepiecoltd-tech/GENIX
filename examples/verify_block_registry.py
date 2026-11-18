"""Kiểm chứng Block Registry sau khi build xong:
    PYTHONPATH=src python3 examples/verify_block_registry.py
In ra: tổng block, tổng gene thật, số loài có Merkle root, và đối chiếu
block dùng chung heo ∩ gà trong registry với số đo độc lập 13.399 (theo symbol).
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from genechain.block_registry import BlockRegistry

ROOT = os.path.join(os.path.dirname(__file__), "..")
reg = BlockRegistry(os.path.join(ROOT, "data", "genechain_blocks.db"))
c = reg.conn
print("done files:", [r[0] for r in c.execute("SELECT key FROM meta WHERE key LIKE 'done:%'")])
print(f"tong block gene chuan: {c.execute('SELECT COUNT(*) FROM blocks').fetchone()[0]:,}")
print(f"tong gene that (occurrences): {c.execute('SELECT COUNT(*) FROM occurrences').fetchone()[0]:,}")
print(f"loai co Merkle root: {c.execute('SELECT COUNT(*) FROM species').fetchone()[0]:,}")
for taxid, name in ((9823, "Heo"), (9031, "Gà"), (39947, "Lúa Japonica")):
    print(f"{name} (taxid {taxid}):", reg.species_info(taxid))
cnt, sample = reg.shared_blocks(9823, 9031)
print(f"Heo ∩ Gà trong registry (theo block_id = symbol + loai gene): {cnt:,}")
print("mau block chung:", sample)
print("Doi chieu: so do doc lap theo symbol chuan = 13,399 block")
