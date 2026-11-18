# GeneChain — Blockchain & Merkle DAG cho Quản Lý Lai Tạo Mã Gen

Prototype **chạy được thật** triển khai đúng ý tưởng trong file tóm tắt
`tom-tat-blockchain-va-lai-tao-gen.md`: mượn kiến trúc liên kết của Blockchain,
kết hợp Merkle DAG để quản lý lai tạo — không lưu gen thô trên chuỗi, chỉ lưu
công thức tổ hợp các mã định danh gen bất biến, cho phép **truy xuất ngược**
toàn bộ phả hệ và **chia royalty tự động** cho người tạo giống gốc.

> Lưu ý trung thực về giới hạn (như chính bản tóm tắt đã nêu): hàm băm là một
> chiều — không ai "giải mã ngược" được từ hash ra ADN gốc. Cái truy xuất
> ngược được ở đây là **phả hệ & cấu phần** (qua các liên kết CID trong DAG),
> không phải dữ liệu gen gốc từ hash.

## Kiến trúc 3 lớp

| Lớp | Trong prototype này | Khi deploy thật |
|---|---|---|
| **1. Lưu trữ gốc (Off-chain)** | `src/genechain/ipfs_sim.py` — content-addressed store, CID = `bafy+sha256(canonical JSON)`, kiểm chứng toàn vẹn khi đọc | IPFS + IPLD (ipfs-http-client / web3.storage / Pinata) |
| **2. Lai tạo & Phả hệ (Merkle DAG)** | `dag.py` (truy xuất tổ tiên, tỉ lệ đóng góp gen), `breeding.py` (tái tổ hợp tất định theo trait), `models.py` (Merkle root cho mỗi block) | IPLD DAG + AI dự đoán tính trạng (nông nghiệp) hoặc VRF (game) |
| **3. Xác thực & Bản quyền (On-chain)** | `chain.py` — mô phỏng interface contract; `contracts/GeneBlock.sol` — Solidity thật | Polygon / Base (cộng đồng, game) hoặc Hyperledger Fabric (viện nghiên cứu, cấp phép) |

## Quy trình 4 bước — đã chạy trong demo

1. **Genesis Blocks:** 3 giống lúa thuần chủng gốc (dữ liệu mẫu ở `data/genesis.json`:
   chịu hạn/kháng đạo ôn/năng suất, chịu mặn/thơm/chín sớm, chịu ngập/đạm cao),
   mỗi gene lưu IPFS được 1 CID bất biến.
2. **Lai tạo:** `Delta Gold F1 = A × B`, `Mekong Prime F2 = F1 × C`.
   Gen con là tái tổ hợp CID của cha mẹ theo từng trait — không sinh gene lạ,
   kết quả tất định nên ai cũng kiểm chứng lại được.
3. **Hiển thị cấu phần:** đọc ngược CID -> chi tiết từng gene của F2 (8 tính trạng).
4. **Truy xuất ngược & royalty:** F2 có đóng góp genesis A 25% / B 25% / C 50%.
   Bán thương mại 100.000 với royalty 10% -> pool 10.000 chia tự động:
   Viện Lúa ĐBSCL (tạo A + C) nhận 7.500, Trung Tâm Giống Miền Tây (tạo B) nhận 2.500.

## Chạy thử (không cần cài gì thêm — chỉ dùng Python stdlib)

```bash
PYTHONPATH=src python3 examples/demo.py          # demo end-to-end 4 bước
PYTHONPATH=src python3 -m unittest discover -s tests -v   # 4 test: CID bất biến,
                                                  # lai tạo tất định, đóng góp gen = 100%,
                                                  # royalty đúng, phát hiện giả mạo hash
```

## Smart Contract

`contracts/GeneBlock.sol` (Solidity ^0.8.20, tự chứa ERC-721 tối giản để đọc độc lập):
`mintGenesis()` · `breed(parentA, parentB, ...)` · `getSpecies()` ·
`verifyProvenance()` · `distributeRoyalty(genesisIds, weightsBps)` — contract
kiểm chứng tổng trọng số = 10.000 bps trước khi chi tiền cho các creator tổ tiên.

Deploy production nên: dùng OpenZeppelin ERC-721 + **ERC-6551** (Token Bound
Account cho mỗi giống), deploy lên **Polygon Amoy / Base Sepolia** testnet trước.

## Cấu trúc thư mục

```
contracts/GeneBlock.sol        Smart contract on-chain (Lớp 3)
src/genechain/
  ipfs_sim.py                  Lớp 1: IPFS content-addressing simulation
  models.py                    GeneComponent + SpeciesBlock + Merkle root
  dag.py                       Lớp 2: Pedigree DAG, ancestors, contributions
  breeding.py                  Lớp 2: công thức tái tổ hợp theo trait
  royalty.py                   Chia royalty theo đóng góp genesis
  chain.py                     Lớp 3: registry mô phỏng interface contract
data/genesis.json              Gene mẫu + 3 giống gốc (lúa ĐBSCL)
data/ipfs/                     File gene được tạo khi chạy demo (theo CID)
examples/demo.py               Demo 4 bước
tests/test_genechain.py        4 unit test
```

## Lộ trình tiếp theo (chọn 1)

- **A. Web demo:** giao diện trực quan cây phả hệ DAG, kéo-thả lai tạo, xem royalty.
- **B. Deploy testnet:** Hardhat + OpenZeppelin + ERC-6551, deploy Polygon Amoy, nối ví.
- **C. IPFS thật:** thay `ipfs_sim` bằng IPFS node/Pinata, gene thật dạng JSON chuẩn.
- **D. Bản game:** giống loài = NFT game, lai tạo bằng VRF ngẫu nhiên, marketplace.
- **E. Bản nông nghiệp/doanh nghiệp:** Hyperledger Fabric, phân quyền viện/trại giống.

## v2 — Đa loài: mỗi loài là 1 block gồm 300 gene-block nhỏ (theo ý tưởng mở rộng)

- **Heo, Gà, Cây lúa — mỗi loài 1 SpeciesBlock gồm đúng 300 gene-block nhỏ bất biến**
  (`src/genechain/species_data.py`): 20 nhóm chức năng phổ quát × 15 biến thể.
  Mỗi gene có CID riêng trên IPFS, trường `origin` ghi loài gốc và không bao giờ đổi.
  300 gene của 1 block được cam kết bằng **1 Merkle root duy nhất** (`merkle.py`);
  chứng minh 1 gene thuộc block chỉ cần proof 9 bước (log2 300), không cần lộ cả 300 gene.
- **Ghép khác loài** (`crossbreed.py`, `genome_registry.py`): ghép theo từng nhóm
  chức năng phổ quát, block con vẫn đủ 300 gene, mọi gene đều là CID gốc của cha/mẹ
  (không sửa, không sinh gene lạ) nên truy xuất ngược được % thành phần từng loài.

Kết quả đã chạy (`examples/demo_cross_species.py`, 8/8 test pass):
- Heo × Gà -> Block Lai HG-01: **heo 154 gene (51,3%) / gà 146 gene (48,7%)**
- (Heo-Gà) × Lúa -> Block Lai HGL-02: **heo 72 (24,0%) / gà 77 (25,7%) / lúa 151 (50,3%)**
- Merkle proof cho gene PIG-113 trong block lai 3 loài: 9 bước, verified.

> Ghi chú khoa học: ghép heo × gà ở đây là **tổng hợp in-silico ở mức dữ liệu**
> (mô hình quản trị nguồn gốc gene / simulation / game), không phải lai tự nhiên —
> heo và gà không thể lai tự nhiên. Khi có dữ liệu giải trình tự thật, thay
> `make_genes()` bằng loader đọc dữ liệu gene thật, toàn bộ hệ thống giữ nguyên.

```bash
PYTHONPATH=src python3 examples/demo_cross_species.py
```

## v3 — Kênh dữ liệu gen THẬT làm input (đã kiểm chứng trực tiếp)

| Kênh | Nội dung | Truy cập |
|---|---|---|
| **NCBI Gene / E-utilities** ✅ đã nối | GeneID bất biến, symbol, mô tả, NST, vị trí, độ dài bp — heo 89.841 gene, gà 58.600, lúa 102.125 | API miễn phí, không cần key (3 req/s; đăng ký key miễn phí -> 10 req/s) |
| **Ensembl REST** ✅ đã kiểm chứng endpoint | Genome, gene, biến thể, **ortholog liên loài** (chìa khoá để ghép theo gene tương đồng thật) — `rest.ensembl.org`, cây/non-vertebrate ở `rest.ensemblgenomes.org` | API miễn phí, không cần key |
| NCBI Datasets API | Tải cả bộ genome (FASTA/GFF/GenBank) theo accession/taxid | Miễn phí |
| UniProt REST | Protein, chức năng, GO terms | Miễn phí |
| RAP-DB / IRGSP, Gramene | Chuyên sâu cho lúa | Miễn phí |
| Animal QTLdb, Chicken QTLdb | QTL tính trạng heo/gà (năng suất, kháng bệnh...) | Miễn phí |
| KEGG / Gene Ontology | Pathway & nhóm chức năng — dùng làm 'trait phổ quát' chuẩn thay cho nhóm tự định nghĩa | Miễn phí (KEGG API có giới hạn) |
| Dữ liệu riêng của trại/viện | File giải trình tự FASTA / GFF3 / VCF / CSV từ máy sequencing | Người dùng tự cung cấp — loader nạp cùng 1 đường |

Loader thật: `src/genechain/real_data.py` + `examples/demo_real_data.py`.
Đã chạy thật: kéo 300 gene NCBI cho mỗi loài vào block riêng (heo có LEP, IGF1,
TGFB1...; lúa có Xa21 kháng bệnh, gene chịu mặn...) — mọi block verified,
ghép heo × gà bằng gene thật cho block lai 300 gene, thành phần đúng 150/150.
Gene thật kéo về được cache ở `data/real/` và đóng băng bằng CID nên bất biến
trong hệ thống dù NCBI cập nhật sau này.

Lưu ý: dữ liệu genome đầy đủ rất lớn (heo ~2,5 Gb) — hệ thống không lưu chuỗi
ADN thô on-chain; chỉ lưu metadata + định danh gene làm gene-block, chuỗi thô
nằm ở IPFS/off-chain theo đúng kiến trúc 3 lớp.

## v4 — Harvest TOÀN BỘ loài động vật + thực vật từ NCBI (đã chạy xong)

Đường bulk chính thống (không nện API): tải 4 file `gene_info` từ NCBI FTP
(Plants / Invertebrates / Mammalia / Non-mammalian vertebrates, tổng ~1,17 GB)
+ taxdump lấy tên khoa học, rồi streaming-parse bằng `src/genechain/bulk_harvest.py`.

Kết quả (kiểm chứng trên đĩa):
- **31.189 taxon**: thực vật 14.578, động vật 16.611 (gồm cả người — Homo sapiens
  nằm trong Mammalia của NCBI), 31.186/31.189 có tên khoa học
- **52.339.023 gene thật** được đếm trong catalog; **2.853.513 gene-block** đã cắt
  (tối đa 300/loài, ưu tiên protein-coding) lưu ở `data/species_genes/<taxid>.json` (617 MB)
- 1.650 loài có đủ trọn 300 gene; heo Sus scrofa 54.048 gene, gà Gallus gallus 32.204,
  lúa Japonica (taxid 39947) 39.421 — đều đã dựng block + ghép thử, verified
- Catalog: `data/catalog_all_species.json` / `.csv` (tax_id, tên khoa học, tổng gene, số gene-block)
- Lưu ý: số gene theo API txid[Organism] cao hơn số trong file bulk vì API cộng cả
  các taxon con (giống/chủng); file bulk tính theo đúng từng tax_id.

## v5 — Mô hình chốt của chủ dự án: 1 gene thật = 1 block, block trùng = block dùng chung

- **Không dữ liệu ảo**: đường mô phỏng (species_data.make_genes) đã đánh dấu LEGACY,
  chỉ còn phục vụ unit-test logic DAG. Mọi gene trong hệ thống thật đều từ NCBI.
- **1 mã gen = 1 block** (`block_registry.py`): block_id = SHA-256(symbol chuẩn theo
  cơ quan danh pháp + loại gene), lưu trong SQLite `data/genechain_blocks.db`
  (bảng blocks), mỗi bản ghi gene thật của từng loài (bảng occurrences, 52,3 triệu)
  trỏ tới đúng 1 block; SpeciesBlock = Merkle root trên tập block của loài.
- **Gene trùng nhau = block dùng chung** (đo thật từ dữ liệu bulk đầy đủ,
  `data/shared_genes_report.json`):
  heo (54.048 gene) ∩ gà (32.204 gene) = **13.399 block chung** (riêng protein-coding: 13.213);
  heo ∩ lúa = 73, gà ∩ lúa = 73, cả 3 loài = 69 (chủ yếu gene bào quan/ribosome bảo tồn cao —
  symbol thực vật kém chuẩn hoá hơn động vật nên phép so theo symbol đếm thiếu ortholog thực vật).
- "Trùng nhau" = cùng symbol chuẩn (ortholog theo danh pháp), không phải trùng trình tự
  ADN — trình tự/vị trí riêng từng loài nằm ở occurrences (GeneID, NST, vị trí).
