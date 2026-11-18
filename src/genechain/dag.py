"""
Lớp 2 — Merkle DAG / Cây phả hệ

Khác blockchain tuyến tính (1-1), mỗi SpeciesBlock trỏ tới 0 (genesis) hoặc 2 parents,
tạo thành đồ thị có hướng không chu trình (DAG). Từ 1 block đời con, ta truy xuất
ngược được toàn bộ tổ tiên và tỉ lệ đóng góp gen của từng tổ tiên.
"""
from __future__ import annotations
from collections import defaultdict


class PedigreeDAG:
    def __init__(self):
        self.blocks = {}  # token_id -> SpeciesBlock

    def add(self, block):
        assert block.token_id not in self.blocks, "token_id đã tồn tại"
        for p in block.parents:
            assert p in self.blocks, f"Parent {p} chưa tồn tại — DAG không cho phép trỏ tới block chưa có"
        self.blocks[block.token_id] = block
        return block

    def get(self, token_id):
        return self.blocks[token_id]

    def ancestors(self, token_id):
        """Trả về {ancestor_id: depth_gần_nhất} — truy xuất ngược toàn bộ phả hệ."""
        result, stack = {}, [(token_id, 0)]
        while stack:
            cur, depth = stack.pop()
            for p in self.blocks[cur].parents:
                if p not in result or result[p] > depth + 1:
                    result[p] = depth + 1
                stack.append((p, depth + 1))
        return result

    def genesis_contributions(self, token_id):
        """
        Tỉ lệ gen đóng góp của từng Genesis Block vào token_id.
        Mỗi lần lai, con nhận 50% từ mỗi parent -> đệ quy nhân 0.5 qua từng thế hệ.
        Tổng luôn = 1.0 (kiểm chứng trong test).
        """
        contrib = defaultdict(float)

        def walk(tid, weight):
            blk = self.blocks[tid]
            if not blk.parents:
                contrib[tid] += weight
            else:
                for p in blk.parents:
                    walk(p, weight / len(blk.parents))

        walk(token_id, 1.0)
        return dict(sorted(contrib.items()))

    def verify(self, token_id) -> bool:
        """Xác thực tính toàn vẹn Merkle: hash lưu trong block phải khớp hash tính lại."""
        blk = self.blocks[token_id]
        return blk.block_hash == blk.compute_hash()
