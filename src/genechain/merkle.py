"""Merkle Tree trên danh sách CID gene của 1 SpeciesBlock.

Block loài = Merkle root của 300 gene-block nhỏ. Nhờ đó:
- Chỉ cần lưu 1 root (32 byte) on-chain để cam kết toàn bộ 300 gene.
- Kiểm chứng 1 gene có thuộc block hay không bằng Merkle proof O(log n),
  không cần tải cả 300 gene.
"""
from __future__ import annotations
import hashlib


def _h(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def leaf(cid: str) -> str:
    return _h(cid.encode("utf-8"))


def merkle_root(cids: list) -> str:
    if not cids:
        return _h(b"")
    level = [leaf(c) for c in sorted(cids)]
    while len(level) > 1:
        nxt = []
        for i in range(0, len(level), 2):
            a = level[i]
            b = level[i + 1] if i + 1 < len(level) else a  # số lẻ: nhân đôi node cuối
            nxt.append(_h((a + b).encode()))
        level = nxt
    return level[0]


def merkle_proof(cids: list, target_cid: str):
    """Trả về proof = [(sibling_hash, 'L'|'R'), ...] từ lá lên root, hoặc None nếu không có."""
    ordered = sorted(cids)
    if target_cid not in ordered:
        return None
    idx = ordered.index(target_cid)
    level = [leaf(c) for c in ordered]
    proof = []
    while len(level) > 1:
        if idx % 2 == 0:
            sib = level[idx + 1] if idx + 1 < len(level) else level[idx]
            proof.append((sib, "R"))
        else:
            proof.append((level[idx - 1], "L"))
        nxt = []
        for i in range(0, len(level), 2):
            a = level[i]
            b = level[i + 1] if i + 1 < len(level) else a
            nxt.append(_h((a + b).encode()))
        level, idx = nxt, idx // 2
    return proof


def verify_proof(cid: str, proof: list, root: str) -> bool:
    cur = leaf(cid)
    for sib, side in proof:
        cur = _h((sib + cur).encode()) if side == "L" else _h((cur + sib).encode())
    return cur == root
