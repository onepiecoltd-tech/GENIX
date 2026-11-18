"""
Ghép gen KHÁC LOÀI (cross-species synthesis) — in-silico, ở mức dữ liệu.

Ý tưởng của chủ dự án: heo là 1 block gồm 300 gene-block nhỏ, gà cũng vậy.
Ghép ADN heo × gà -> chọn lọc gene từ cả hai theo từng nhóm chức năng phổ quát
-> tạo thành 1 block mới (chimera block) vẫn gồm 300 gene, trong đó mỗi gene
vẫn là CID bất biến gốc của heo hoặc gà (không gene nào bị sửa hay sinh mới),
nên truy xuất ngược được chính xác block mới có bao nhiêu % gene heo, % gene gà.

Lưu ý khoa học: đây là mô hình dữ liệu / mô phỏng tổng hợp gen, KHÔNG phải
lai tự nhiên (heo và gà không lai tự nhiên được). Giá trị của nó nằm ở quản trị
nguồn gốc gene, game/simulation, và nghiên cứu in-silico.
"""
from __future__ import annotations
import hashlib
from collections import defaultdict


def _rank(seed: str, cid: str) -> str:
    return hashlib.sha256(f"{seed}:{cid}".encode()).hexdigest()


def synthesize_gene_cids(block_a, block_b, child_name: str, gene_index: dict,
                         target_size: int = 300) -> list:
    """
    gene_index: cid -> gene dict (có 'trait' và 'origin')
    Theo từng trait: chia đều số gene cần lấy cho 2 parents (lẻ thì bên được
    chọn tất định theo seed lấy phần hơn), chọn gene cụ thể bằng xếp hạng hash
    tất định -> ai chạy lại cũng ra đúng block con đó.
    """
    seed = f"{block_a.block_hash}:{block_b.block_hash}:{child_name}"
    by_trait = defaultdict(lambda: {0: [], 1: []})
    for side, blk in enumerate((block_a, block_b)):
        for cid in blk.gene_cids:
            by_trait[gene_index[cid]["trait"]][side].append(cid)

    traits = sorted(by_trait)
    per_trait = target_size // len(traits)
    child, used = [], set()
    for trait in traits:
        sides = by_trait[trait]
        extra_to = int(_rank(seed, trait)[:2], 16) % 2  # trait lẻ: seed quyết định bên lấy +1
        need = {0: per_trait // 2 + (1 if per_trait % 2 and extra_to == 0 else 0),
                1: per_trait // 2 + (1 if per_trait % 2 and extra_to == 1 else 0)}
        if per_trait % 2 == 0:
            need = {0: per_trait // 2, 1: per_trait // 2}
        for side in (0, 1):
            ranked = sorted(sides[side], key=lambda c: _rank(f"{seed}:{trait}", c))
            for cid in ranked[:need[side]]:
                child.append(cid)
                used.add(cid)
    # Dữ liệu thật thường lệch nhóm (vd 90% là protein-coding): nếu 1 nhóm không đủ
    # gene để chia đều, bù bằng gene chưa dùng của cả 2 parents (vẫn toàn gene gốc,
    # vẫn tất định) để block con luôn đủ target_size.
    if len(child) < target_size:
        rest = [cid for blk in (block_a, block_b) for cid in blk.gene_cids if cid not in used]
        rest.sort(key=lambda c: _rank(f"{seed}:fill", c))
        child.extend(rest[:target_size - len(child)])
    return sorted(child[:target_size])


def composition(gene_cids: list, gene_index: dict) -> dict:
    """Tỉ lệ gene theo loài gốc (origin) — truy xuất ngược thành phần của 1 block."""
    counts = defaultdict(int)
    for cid in gene_cids:
        g = gene_index[cid]
        counts[g.get("origin") or g.get("origin_taxid")] += 1
    total = len(gene_cids)
    return {k: {"genes": v, "pct": round(v * 100 / total, 1)}
            for k, v in sorted(counts.items())}
