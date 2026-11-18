"""
Lớp 3 — Xác thực & bản quyền (On-chain simulation)

Mô phỏng đúng interface của Smart Contract GeneBlock.sol:
mintGenesis / breed / ownerOf / verifyProvenance / distributeRoyalty.
Khi deploy thật lên Polygon/Base, thay class này bằng web3.py gọi contract —
toàn bộ logic Lớp 1 & 2 (IPFS + DAG) giữ nguyên.
"""
from __future__ import annotations
from .models import SpeciesBlock
from .breeding import breed_gene_cids
from .royalty import royalty_split


class GeneChain:
    def __init__(self, ipfs, dag):
        self.ipfs, self.dag = ipfs, dag
        self.owners = {}       # token_id -> owner (mô phỏng ERC-721 ownerOf)
        self._next_id = 1
        self.events = []       # mô phỏng event log on-chain

    # --- Bước 1: Genesis ---
    def mint_genesis(self, name, creator, gene_dicts: list) -> SpeciesBlock:
        gene_cids = [self.ipfs.put(g) for g in gene_dicts]
        blk = SpeciesBlock(self._next_id, name, creator, sorted(gene_cids), [], 0).finalize()
        return self._register(blk, creator, "GenesisMinted")

    # --- Bước 2: Lai tạo ---
    def breed(self, parent_a_id, parent_b_id, child_name, breeder) -> SpeciesBlock:
        a, b = self.dag.get(parent_a_id), self.dag.get(parent_b_id)
        assert a.token_id != b.token_id, "Không thể tự lai cùng 1 block"
        gene_index = {cid: self.ipfs.get(cid) for cid in set(a.gene_cids + b.gene_cids)}
        child_cids = breed_gene_cids(a, b, child_name, self.ipfs, gene_index)
        blk = SpeciesBlock(self._next_id, child_name, breeder, child_cids,
                           [a.token_id, b.token_id], max(a.generation, b.generation) + 1).finalize()
        return self._register(blk, breeder, "Bred")

    def _register(self, blk, owner, event):
        self.dag.add(blk)
        self.owners[blk.token_id] = owner
        self._next_id += 1
        self.events.append({"event": event, "token_id": blk.token_id,
                            "name": blk.name, "block_hash": blk.block_hash})
        return blk

    # --- Bước 3: Hiển thị chi tiết cấu phần ---
    def describe(self, token_id) -> dict:
        blk = self.dag.get(token_id)
        genes = [self.ipfs.get(cid) for cid in blk.gene_cids]
        return {"token_id": blk.token_id, "name": blk.name, "creator": blk.creator,
                "owner": self.owners[token_id], "generation": blk.generation,
                "parents": blk.parents, "block_hash": blk.block_hash,
                "genes": sorted(genes, key=lambda g: g["trait"])}

    # --- Bước 4: Truy xuất ngược & chia royalty ---
    def trace_and_split(self, token_id, sale_amount, royalty_rate=0.10) -> dict:
        assert self.dag.verify(token_id), "Block hash không khớp — dữ liệu đã bị can thiệp"
        out = royalty_split(self.dag, token_id, sale_amount, royalty_rate)
        out["ancestors"] = self.dag.ancestors(token_id)
        out["verified"] = True
        return out
