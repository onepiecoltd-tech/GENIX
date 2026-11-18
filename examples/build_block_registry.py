"""Build Block Registry v5 (1 gene thật = 1 block):
    PYTHONPATH=src python3 examples/build_block_registry.py
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from genechain.block_registry import BlockRegistry
ROOT = os.path.join(os.path.dirname(__file__), "..")
reg = BlockRegistry(os.path.join(ROOT, "data", "genechain_blocks.db"))
reg.build_all(ROOT)
print("Heo ∩ Gà (block dùng chung):", reg.shared_blocks(9823, 9031))
print("Heo:", reg.species_info(9823))
print("Gà:", reg.species_info(9031))
