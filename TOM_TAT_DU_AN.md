# TÓM TẮT DỰ ÁN — GeneChain

*Cập nhật: 17/11/2026, 22:44 (Asia/Saigon). Mọi con số trong file này đều đã
chạy thật và kiểm chứng trên đĩa, trừ mục "Đang thực hiện" ghi rõ trạng thái.*

## 1. Dự án là gì

GeneChain quản lý lai tạo mã gen bằng kiến trúc mượn từ Blockchain kết hợp
Merkle DAG: không lưu chuỗi ADN thô trên chuỗi, chỉ lưu **định danh bất biến
của từng gene** và **công thức tổ hợp** của chúng. Nhờ đó truy xuất ngược được
toàn bộ phả hệ/cấu phần của một giống và chia royalty tự động cho người tạo
giống gốc.

Giới hạn khoa học (nêu rõ từ đầu, không thay đổi):

- Hàm băm là một chiều — truy xuất ngược được là **phả hệ & cấu phần** qua các
  liên kết định danh, không "giải mã" được ADN từ hash.
- Ghép gene khác loài (heo × gà…) là **tổng hợp in-silico ở mức dữ liệu**
  (quản trị nguồn gốc / mô phỏng / game), không phải lai tự nhiên.
- Hai gene "trùng nhau" giữa hai loài = cùng **symbol chuẩn theo cơ quan danh
  pháp** (ortholog), không có nghĩa trình tự ADN giống hệt nhau.

## 2. Kiến trúc 3 lớp

| Lớp | Vai trò | Hiện trạng |
|---|---|---|
| 1. Lưu trữ gốc (off-chain) | Mỗi gene 1 CID content-addressed (`ipfs_sim.py`) | Mô phỏng IPFS chạy thật; chưa nối IPFS/Pinata thật |
| 2. Lai tạo & phả hệ (Merkle DAG) | DAG truy xuất tổ tiên, tỉ lệ đóng góp, Merkle root cam kết cấu phần (`dag.py`, `breeding.py`, `crossbreed.py`, `merkle.py`) | Chạy thật, có unit test |
| 3. Xác thực & bản quyền (on-chain) | `contracts/GeneBlock.sol` — ERC-721 tối giản tự chứa: `mintGenesis`, `breed`, `verifyProvenance`, `distributeRoyalty` | Có source hoàn chỉnh; **chưa biên dịch/deploy** (chưa cài solc, chưa lên testnet) |

## 3. Quá trình phát triển & kết quả đã kiểm chứng

### v1 — Prototype lúa (demo gốc)
- 3 giống lúa gốc → F1 = A×B → F2 = F1×C; đóng góp genesis của F2:
  **A 25% / B 25% / C 50%**.
- Royalty: bán 100.000, tỉ lệ 10% → pool 10.000, chia Viện Lúa ĐBSCL **7.500** /
  Trung Tâm Giống Miền Tây **2.500**.

### v2 — Đa loài mô phỏng (nay là LEGACY, chỉ phục vụ test logic)
- Mỗi loài = 1 block gồm 300 gene-block nhỏ mô phỏng (20 nhóm chức năng × 15).
- Heo × Gà → **154 heo / 146 gà**; (Heo-Gà) × Lúa → **72 / 77 / 151**.
- Merkle proof cho 1 gene trong block 300 gene: **9 bước**. 8/8 test đạt.

### v3 — Nối kênh dữ liệu gene THẬT
- **NCBI Gene (E-utilities)**: miễn phí, không cần key — đã gọi thật.
- **Ensembl REST**: đã kiểm chứng endpoint (ortholog liên loài).
- Loader `real_data.py` kéo 300 gene thật/loài (heo có LEP, IGF1, TGFB1; lúa có
  Xa21…); ghép heo × gà bằng gene thật: **150/150**, mọi block verified.
- Kênh đã loại: NCBI Datasets API trả sai dữ liệu khi truy vấn theo taxon —
  không dùng. Ensembl Genomes từng không kết nối được từ môi trường này.

### v4 — Harvest toàn bộ loài thực vật + động vật (xong)
- Đường bulk chính thống từ NCBI FTP: 4 file `gene_info` (~1,17 GB) + taxdump.
- **31.189 taxon**: thực vật 14.578; động vật 16.611 (Không xương sống 8.484,
  Có vú 1.699 — gồm cả người *Homo sapiens*, Thú khác 6.428).
- **52.339.023 gene thật** đã đếm; **2.853.513 gene-block** cắt sẵn
  (tối đa 300/loài) trong `data/species_genes/` (617 MB); 1.650 loài đủ 300.
- Catalog: `data/catalog_all_species.json` / `.csv`.

### v5 — Mô hình chốt (theo yêu cầu chủ dự án ngày 17/11/2026)
- **Không dữ liệu ảo** trong hệ thống thật; **1 gene thật = 1 block**;
  gene trùng giữa các loài là **cùng một block dùng chung**, không nhân bản.
- Đo thật từ dữ liệu đầy đủ (`data/shared_genes_report.json`):
  - Heo: 54.048 gene → 39.232 symbol chuẩn phân biệt
  - Gà: 32.204 gene → 28.237 symbol chuẩn phân biệt
  - Lúa Japonica: 39.421 gene → 38.794 symbol chuẩn phân biệt
  - **Heo ∩ Gà = 13.399 block chung** (chỉ protein-coding: 13.213)
  - Heo ∩ Lúa = 73; Gà ∩ Lúa = 73; cả ba loài = 69 (gene bào quan/ribosome
    bảo tồn cao; symbol thực vật kém chuẩn hoá nên so theo symbol đếm thiếu
    ortholog thực vật — đã ghi nhận là giới hạn của phương pháp)

## 4. Đang thực hiện — Block Registry v5

Registry SQLite `data/genechain_blocks.db` chứa toàn bộ 52,3 triệu bản ghi
gene thật, mỗi bản ghi trỏ tới đúng 1 block; mỗi loài có 1 Merkle root trên
tập block của mình. Trạng thái lúc 22:44 ngày 17/11/2026:

| File dữ liệu | Trạng thái |
|---|---|
| Mammalia (Có vú) | ✅ Xong — 9.261.337 gene đã nạp; riêng nhóm này sinh 4.787.384 block |
| Plants (Thực vật) | ✅ Xong 100% |
| Invertebrates (Không xương sống) | 🔄 Đang nạp — checkpoint taxid 31.228/… |
| Non-mammalian vertebrates (Thú khác) | ⏳ Chưa bắt đầu |

Sau khi nạp xong 4 file: **khử trùng lặp toàn cục** → dựng index → tính
**Merkle root cho 31.189 loài** → chạy `examples/verify_block_registry.py`
đối chiếu tổng block/gene và heo ∩ gà trong registry với số đo độc lập 13.399.

Sự cố đã xử lý minh bạch: cơ chế khôi phục sau ngắt từng có lỗi nạp trùng
(bảng gene không có khoá duy nhất; loài đã nạp trọn nằm sau checkpoint bị nạp
lại) — đo được trùng đúng 2 lần ở các loài trong vùng hở (ví dụ taxid 7375:
15.894 gene × 2). Đã sửa: xoá sạch vùng sau checkpoint khi chạy lại,
checkpoint tiến theo từng loài trọn, cộng bước khử trùng lặp toàn cục trước
pha Merkle root; đã kiểm thử lại đúng kịch bản lỗi (không trùng, không mất).

## 5. Tài sản dự án

- Mã nguồn: `src/genechain/` (14 module), hợp đồng `contracts/GeneBlock.sol`
- Dữ liệu: catalog 31.189 loài, 2,85 triệu gene-block cắt sẵn, báo cáo block
  dùng chung, registry SQLite đang xây (5,6 GB tại thời điểm viết)
- Web demo trực quan cây phả hệ (slug `web-demo-cay-pha-he-genechain`) —
  **lưu ý: web demo hiện hiển thị mô hình v2 mô phỏng**, chưa dựng lại bằng
  dữ liệu thật v5
- Tài liệu: `README.md` (chi tiết theo từng phiên bản), `MASTER_SPEC.md`
  (đặc tả chuẩn), file tóm tắt này

## 6. Chưa làm / quyết định còn mở

- Biên dịch + deploy contract lên testnet (Polygon Amoy / Base Sepolia),
  cân nhắc OpenZeppelin + ERC-6551 khi production
- Nối IPFS thật thay lớp mô phỏng
- Dựng lại web demo bằng dữ liệu thật của registry v5
- Đối chiếu ortholog thực vật bằng Ensembl Plants để bổ sung phần block chung
  liên giới mà phép so symbol đang đếm thiếu

## 7. Cập nhật 2026-11-18 — Block Registry v5 HOÀN TẤT

- Nạp xong 4/4 file NCBI; khử trùng lặp toàn cục: 59.098.976 -> 52.339.023
  dòng (bỏ 6.759.953 dòng trùng do nạp lại sau gián đoạn), khớp chính xác
  tổng số gene đếm độc lập từ file nguồn — không mất gene nào.
- Tổng kết registry: **32.324.740 block gene chuẩn** (1 gene chuẩn = 1 block),
  **52.339.023 gene thật** (occurrences), **31.189 loài** đều có Merkle root.
- Heo (9823): 54.048 gene -> 39.244 block, root
  d415dababc64b994db04aa604e67ce92879b3c0ac37439cf0e3c732341aa1fb3
- Gà (9031): 32.204 gene -> 28.245 block, root
  8c5391674b2666f866275d3026042816da6b929fca59175030e5f6c1955975b7
- Lúa Japonica (39947): 39.421 gene -> 38.798 block, root
  648ebf5b902e38ff7634de8f709fae436a83cef87fa3ca9d2ee868
- Heo ∩ Gà trong registry (block_id = symbol + loại gene): **13.377** block
  dùng chung. Đối chiếu phép đo độc lập theo symbol thuần: 13.399. Chênh 22
  là do registry tách block theo (symbol + loại gene): vài symbol trùng tên
  nhưng khác loại gene giữa hai loài nên không tính là cùng một block.
- Sự cố cuối: CREATE INDEX tràn thư mục tạm /tmp 512MB của SQLite (ổ thật
  còn 134GB); đã sửa bằng SQLITE_TMPDIR trỏ sang ổ chính.
