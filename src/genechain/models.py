"""Mô hình dữ liệu: GeneComponent (nguyên tử bất biến) & SpeciesBlock (block giống loài)."""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
import hashlib, json


def _hash(obj) -> str:
    raw = json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


@dataclass
class GeneComponent:
    code: str          # vd "DRT-09"
    name: str          # vd "Chịu hạn"
    trait: str         # khóa tính trạng: drought / salinity / yield ...
    score: int         # 0-100, mức biểu hiện
    description: str = ""

    def to_dict(self):
        return asdict(self)


@dataclass
class SpeciesBlock:
    token_id: int
    name: str
    creator: str                    # địa chỉ / tên người tạo (sẽ là ví on-chain khi deploy)
    gene_cids: list                 # danh sách CID của GeneComponent cấu thành
    parents: list = field(default_factory=list)   # [token_id cha, token_id mẹ] — rỗng nếu genesis
    generation: int = 0
    block_hash: str = ""            # hash(parents + gene_cids + name) — định danh block
    merkle_root: str = ""           # Merkle root của riêng danh sách gene_cids (cam kết 300 gene)

    def compute_hash(self) -> str:
        return _hash({
            "token_id": self.token_id, "name": self.name, "creator": self.creator,
            "gene_cids": sorted(self.gene_cids), "parents": self.parents,
            "generation": self.generation,
        })

    def finalize(self):
        from .merkle import merkle_root
        self.block_hash = self.compute_hash()
        self.merkle_root = merkle_root(self.gene_cids)
        return self

    def to_dict(self):
        return asdict(self)
