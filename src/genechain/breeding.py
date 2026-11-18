"""
Công thức lai tạo (Recombination)

Nguyên tắc từ bản tóm tắt: cấu phần gen gốc KHÔNG thay đổi bản chất, chỉ tái tổ hợp.
- Theo từng khóa tính trạng (trait): con thừa hưởng gene của cha HOẶC mẹ,
  chọn tất định (deterministic) theo seed = hash(hash_cha + hash_mẹ + tên con)
  -> cùng 1 cặp lai + cùng tên con luôn cho cùng kết quả, ai cũng kiểm chứng được.
  (Khi deploy game: thay seed bằng VRF ngẫu nhiên; nông nghiệp: thay bằng mô hình AI dự đoán.)
- Tính trạng chỉ có ở 1 bên: con vẫn thừa hưởng (gene lặn/trội đơn giản hoá).
"""
from __future__ import annotations
import hashlib


def _seeded_pick(seed_str: str, trait: str) -> int:
    h = hashlib.sha256(f"{seed_str}:{trait}".encode()).hexdigest()
    return int(h[:8], 16) % 2  # 0 = lấy từ parent A, 1 = lấy từ parent B


def breed_gene_cids(parent_a, parent_b, child_name: str, ipfs, gene_index: dict) -> list:
    """
    gene_index: cid -> GeneComponent dict (đọc từ IPFS)
    Trả về danh sách CID cấu thành đời con (không tạo gene mới, chỉ tái tổ hợp CID có sẵn).
    """
    seed = f"{parent_a.block_hash}:{parent_b.block_hash}:{child_name}"
    by_trait = {}  # trait -> {0: cid của A, 1: cid của B}
    for side, parent in enumerate((parent_a, parent_b)):
        for cid in parent.gene_cids:
            gene = gene_index[cid]
            by_trait.setdefault(gene["trait"], {})[side] = cid

    child_cids = []
    for trait, sides in sorted(by_trait.items()):
        if len(sides) == 1:
            child_cids.append(next(iter(sides.values())))
        else:
            child_cids.append(sides[_seeded_pick(seed, trait)])
    return sorted(child_cids)
