"""
GenomeRegistry — quản lý các SpeciesBlock đa loài (300 gene / block)
và ghép khác loài, trên cùng hạ tầng IPFS + Merkle DAG + on-chain sim.
"""
from __future__ import annotations
from .models import SpeciesBlock
from .species_data import SPECIES, make_genes, GENES_PER_SPECIES
from .crossbreed import synthesize_gene_cids, composition
from .merkle import merkle_proof, verify_proof, merkle_root


class GenomeRegistry:
    def __init__(self, ipfs, dag):
        self.ipfs, self.dag = ipfs, dag
        self.owners, self.events = {}, []
        self._next_id = 1

    def _gene_index(self, blocks) -> dict:
        cids = set()
        for b in blocks:
            cids.update(b.gene_cids)
        return {cid: self.ipfs.get(cid) for cid in cids}

    def _register(self, blk, owner, event):
        self.dag.add(blk)
        self.owners[blk.token_id] = owner
        self._next_id += 1
        self.events.append({"event": event, "token_id": blk.token_id, "name": blk.name,
                            "block_hash": blk.block_hash, "merkle_root": blk.merkle_root})
        return blk

    # --- Tạo block loài gốc từ danh sách gene dict bất kỳ (mô phỏng hoặc dữ liệu thật) ---
    def mint_from_gene_dicts(self, name, creator, gene_dicts: list) -> SpeciesBlock:
        gene_cids = [self.ipfs.put(g) for g in gene_dicts]
        blk = SpeciesBlock(self._next_id, name, creator, sorted(gene_cids), [], 0).finalize()
        return self._register(blk, creator, "SpeciesMinted")

    def mint_species(self, species_key: str) -> SpeciesBlock:
        """LEGACY (mô phỏng): hệ thống thật dùng dữ liệu NCBI qua real_data /
        bulk_harvest / block_registry — xem README v5."""
        import warnings
        warnings.warn("mint_species dùng dữ liệu MÔ PHỎNG (legacy). "
                      "Hệ thống thật: block_registry.BlockRegistry", DeprecationWarning)
        sp = SPECIES[species_key]
        gene_dicts = make_genes(species_key)
        assert len(gene_dicts) == GENES_PER_SPECIES
        return self.mint_from_gene_dicts(f"{sp['name']} ({sp['latin']})", sp["creator"], gene_dicts)

    # --- Ghép khác loài / lai thường: A + B -> block mới 300 gene ---
    def synthesize(self, parent_a_id, parent_b_id, child_name, creator,
                   target_size=GENES_PER_SPECIES) -> SpeciesBlock:
        a, b = self.dag.get(parent_a_id), self.dag.get(parent_b_id)
        assert a.token_id != b.token_id, "Hai block nguồn phải khác nhau"
        index = self._gene_index([a, b])
        child_cids = synthesize_gene_cids(a, b, child_name, index, target_size)
        blk = SpeciesBlock(self._next_id, child_name, creator, child_cids,
                           [a.token_id, b.token_id],
                           max(a.generation, b.generation) + 1).finalize()
        return self._register(blk, creator, "CrossBred")

    # --- Truy xuất ngược thành phần loài ---
    def composition_of(self, token_id) -> dict:
        blk = self.dag.get(token_id)
        return composition(blk.gene_cids, self._gene_index([blk]))

    # --- Kiểm chứng toàn vẹn 1 block ---
    def verify_block(self, token_id) -> bool:
        blk = self.dag.get(token_id)
        if blk.block_hash != blk.compute_hash():
            return False
        if blk.merkle_root != merkle_root(blk.gene_cids):
            return False
        return all(self.ipfs.has(cid) for cid in blk.gene_cids)  # ipfs.get() tự assert hash khi đọc

    # --- Merkle proof: chứng minh 1 gene thuộc block mà không cần lộ cả 300 gene ---
    def prove_gene(self, token_id, cid) -> dict:
        blk = self.dag.get(token_id)
        proof = merkle_proof(blk.gene_cids, cid)
        return {"cid": cid, "in_block": proof is not None, "proof": proof,
                "merkle_root": blk.merkle_root,
                "verified": proof is not None and verify_proof(cid, proof, blk.merkle_root)}
