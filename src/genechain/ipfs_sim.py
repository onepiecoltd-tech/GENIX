"""
Lớp 1 — Lưu trữ cấu phần gốc (Off-chain / IPFS simulation)

IPFS thật dùng CIDv1 (multihash SHA-256, base32). Ở prototype này ta mô phỏng
đúng nguyên lý content-addressing bằng stdlib:
  CID = "bafy" + sha256(canonical_json)[:52]
Cùng một nội dung -> cùng một CID, sửa 1 byte -> CID khác hoàn toàn.
Khi deploy thật, thay class này bằng ipfs-http-client / web3.storage,
interface put()/get() giữ nguyên.
"""
from __future__ import annotations
import hashlib, json, os


def canonical(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def cid_of(obj) -> str:
    return "bafy" + hashlib.sha256(canonical(obj)).hexdigest()[:52]


class IPFSStore:
    """Content-addressed store mô phỏng IPFS, lưu file <cid>.json trên đĩa."""

    def __init__(self, root: str):
        self.root = root
        os.makedirs(root, exist_ok=True)

    def put(self, obj: dict) -> str:
        cid = cid_of(obj)
        path = os.path.join(self.root, cid + ".json")
        if not os.path.exists(path):  # bất biến: nội dung đã có thì không ghi lại
            with open(path, "w", encoding="utf-8") as f:
                json.dump(obj, f, ensure_ascii=False, indent=2)
        return cid

    def get(self, cid: str) -> dict:
        with open(os.path.join(self.root, cid + ".json"), encoding="utf-8") as f:
            data = json.load(f)
        # Kiểm chứng toàn vẹn: hash của dữ liệu phải khớp CID
        assert cid_of(data) == cid, f"Integrity check failed for {cid}"
        return data

    def has(self, cid: str) -> bool:
        return os.path.exists(os.path.join(self.root, cid + ".json"))
