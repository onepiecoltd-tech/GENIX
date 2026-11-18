"""
⚠️ LEGACY / MÔ PHỎNG — KHÔNG dùng cho hệ thống thật.
Chủ dự án đã chốt (2026-11-17): không lấy dữ liệu ảo, 1 gene thật = 1 block.
Đường dữ liệu thật: real_data.py (NCBI API), bulk_harvest.py (NCBI bulk),
block_registry.py (1 gene = 1 block, block trùng = block dùng chung).
Module này chỉ còn phục vụ unit-test logic DAG cũ.

Dữ liệu loài đa hệ: mỗi loài = 1 SpeciesBlock gồm đúng 300 gene-block nhỏ bất biến.

300 gene được sinh tất định (deterministic) từ mã loài: chạy lại bao nhiêu lần
cũng ra đúng 300 gene đó, đúng CID đó — đây là 'bộ gene tham chiếu' của loài
trong mô hình. Khi có dữ liệu giải trình tự thật, thay hàm make_genes() bằng
loader đọc file gene thật (JSON/FASTA đã chuẩn hoá), interface giữ nguyên.

20 nhóm chức năng phổ quát (universal traits) dùng chung cho mọi loài là
chìa khoá để ghép khác loài: gene heo và gene gà cùng nhóm 'immunity'
ghép được với nhau ở mức dữ liệu, vì chúng nói về cùng 1 chức năng.
"""
from __future__ import annotations
import hashlib

GENES_PER_SPECIES = 300

UNIVERSAL_TRAITS = [
    ("growth", "Sinh trưởng"), ("muscle", "Cơ"), ("fat", "Mỡ / tích luỹ"),
    ("immunity", "Miễn dịch"), ("metabolism", "Trao đổi chất"),
    ("thermoregulation", "Điều hoà thân nhiệt"), ("reproduction", "Sinh sản"),
    ("digestion", "Tiêu hoá"), ("bone", "Xương / cấu trúc"),
    ("coat", "Da - lông - vỏ"), ("sensory", "Giác quan"),
    ("behavior", "Tập tính"), ("longevity", "Tuổi thọ"),
    ("stress", "Chịu stress"), ("disease_resistance", "Kháng bệnh"),
    ("nutrient_use", "Sử dụng dinh dưỡng"), ("oxygen", "Hô hấp / oxy"),
    ("cell_repair", "Sửa chữa tế bào"), ("hormone", "Nội tiết"),
    ("development", "Phát triển phôi / cơ thể"),
]

SPECIES = {
    "heo": {"prefix": "PIG", "name": "Heo", "latin": "Sus scrofa domesticus",
            "creator": "VienChanNuoi (Heo)"},
    "ga": {"prefix": "CHK", "name": "Gà", "latin": "Gallus gallus domesticus",
           "creator": "VienChanNuoi (Ga)"},
    "lua": {"prefix": "RCE", "name": "Cây lúa", "latin": "Oryza sativa",
            "creator": "VienLua-DBSCL (Lua)"},
}


def _score(seed: str) -> int:
    return 50 + int(hashlib.sha256(seed.encode()).hexdigest()[:6], 16) % 51  # 50..100, tất định


def make_genes(species_key: str, count: int = GENES_PER_SPECIES) -> list:
    """Sinh `count` gene-block nhỏ cho 1 loài. Mỗi gene là 1 dict -> 1 CID bất biến trên IPFS."""
    sp = SPECIES[species_key]
    genes = []
    per_trait = count // len(UNIVERSAL_TRAITS)  # 300 / 20 = 15 gene mỗi nhóm chức năng
    n = 0
    for trait_key, trait_label in UNIVERSAL_TRAITS:
        for variant in range(1, per_trait + 1):
            n += 1
            code = f"{sp['prefix']}-{n:03d}"
            genes.append({
                "code": code,
                "name": f"{sp['name']} · {trait_label} · biến thể {variant}",
                "trait": trait_key,
                "score": _score(code),
                "origin": species_key,  # loài gốc sinh ra gene này — không bao giờ đổi
                "description": f"Gene-block bất biến #{n} của {sp['name']} ({sp['latin']}), "
                               f"nhóm chức năng {trait_label}.",
            })
    return genes
