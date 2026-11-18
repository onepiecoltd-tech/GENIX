# MASTER SPEC — GeneChain

*Đặc tả chuẩn (single source of truth) của dự án GeneChain. Mọi thay đổi mô
hình phải sửa file này trước, rồi mới sửa code. Phiên bản spec: 5.1 —
17/11/2026. Trạng thái triển khai thực tế ghi ở mục 10.*

## 1. Mục đích & phạm vi

GeneChain là hệ thống quản lý lai tạo mã gen gồm 3 lớp: (1) lưu trữ gốc
off-chain theo định danh nội dung, (2) phả hệ & lai tạo dạng Merkle DAG,
(3) xác thực & chia royalty on-chain. Hệ thống quản lý **định danh và nguồn
gốc** của gene, không lưu trữ/phân phối chuỗi ADN thô trên chuỗi.

## 2. Nguyên tắc bất biến (không được phá vỡ)

1. **Không dữ liệu ảo trong hệ thống thật.** Mọi gene phải có nguồn NCBI thật
   (GeneID truy ngược được). Đường mô phỏng `species_data.make_genes` là
   LEGACY, chỉ phục vụ unit test logic DAG, cấm dùng làm dữ liệu hệ thống.
2. **1 gene chuẩn = 1 block.** Một gene chuẩn (định danh ở mục 4) tồn tại đúng
   một block trong toàn hệ thống.
3. **Gene trùng = block dùng chung.** Nếu hai loài có cùng gene chuẩn, cả hai
   cùng trỏ tới một block_id duy nhất — không tạo bản sao theo loài.
4. **Bất biến:** block đã tạo không sửa, không xoá; symbol/gene_type của block
   không đổi theo thời gian dù NCBI cập nhật (bản ghi loài tại thời điểm nạp
   được đóng băng trong occurrences).
5. **Trung thực khoa học:** (a) hash là một chiều — truy xuất là truy xuất
   phả hệ/cấu phần, không khôi phục ADN từ hash; (b) ghép khác loài là tổng
   hợp in-silico ở mức dữ liệu; (c) "gene trùng" = cùng symbol chuẩn theo cơ
   quan danh pháp (ortholog theo danh pháp), không khẳng định trình tự ADN
   giống hệt nhau.

## 3. Định nghĩa

- **Gene record (bản ghi gene):** một dòng dữ liệu gene của một loài cụ thể
  trong NCBI Gene, định danh bởi cặp `(taxid, GeneID)` — khoá tự nhiên duy
  nhất, một loài không có hai bản ghi cùng GeneID.
- **Canonical gene (gene chuẩn):** cặp `(symbol chuẩn, loại gene)`, trong đó
  symbol chuẩn = `Symbol_from_nomenclature_authority` nếu có, ngược lại dùng
  `Symbol` của bản ghi; loại gene = trường `type_of_gene` của NCBI.
- **Block:** hiện thân duy nhất của một gene chuẩn trong hệ thống.
- **Occurrence:** một gene record trỏ tới block của nó, kèm dữ liệu riêng
  theo loài (nhiễm sắc thể, vị trí bản đồ).
- **SpeciesBlock:** cam kết của một loài = Merkle root trên tập block_id
  phân biệt của loài đó.
- **Hybrid block (block lai):** block tổng hợp in-silico từ gene của ≥2 loài,
  mọi gene thành phần đều là block gốc, truy xuất được tỉ lệ từng loài.

## 4. Định danh block

```
block_id = "bafy" + SHA-256( UPPER(symbol_chuẩn) + "|" + loại_gene )[:52]
```

- Tiền tố `bafy` tương thích định dạng CID của lớp lưu trữ.
- Cùng công thức áp dụng cho mọi loài, mọi thời điểm — hai bản ghi cùng gene
  chuẩn ở bất kỳ loài nào cũng cho cùng block_id.
- Bản ghi thiếu symbol chuẩn (rỗng hoặc "-") **không được tạo block** và bị
  bỏ qua khi nạp; số lượng bỏ qua phải được báo cáo ở bước kiểm chứng cuối.

## 5. Mô hình dữ liệu — Block Registry (SQLite `data/genechain_blocks.db`)

| Bảng | Cột | Ràng buộc |
|---|---|---|
| `blocks` | block_id (PK), symbol, gene_type, full_name | 1 dòng / gene chuẩn |
| `occurrences` | taxid, gene_id, block_id, chromosome, map_location | Không khoá duy nhất khi nạp (tốc độ); tính duy nhất theo `(taxid, gene_id)` được bảo đảm bằng cơ chế nạp ở mục 7 + bước khử trùng lặp ở mục 8 |
| `species` | taxid (PK), kingdom, gene_records, distinct_blocks, merkle_root | 1 dòng / loài |
| `meta` | key (PK), value | checkpoint nạp, kingdom theo taxid, cờ trạng thái |

## 6. Nguồn dữ liệu & xuất xứ

- **Nguồn chuẩn duy nhất:** NCBI Gene — đường bulk FTP chính thống, 4 file
  `gene_info`: `All_Plants`, `All_Invertebrates`, `All_Mammalia`,
  `All_Non-mammalian_vertebrates`; tên khoa học từ NCBI Taxonomy (taxdump).
- E-utilities API chỉ dùng cho truy vấn nhỏ/kiểm chứng, không dùng harvest
  hàng loạt. NCBI Datasets API **bị cấm dùng** cho harvest theo taxon (đã
  kiểm chứng trả sai dữ liệu).
- Vũ trụ dữ liệu tại thời điểm chốt spec: 31.189 taxon (thực vật 14.578;
  động vật 16.611), 52.339.023 gene record được đếm. Số gene theo API
  `txid[Organism]` cao hơn vì cộng taxon con — không dùng làm chuẩn.
- Catalog chuẩn: `data/catalog_all_species.json` / `.csv`.

## 7. Đặc tả nạp dữ liệu (build pipeline)

1. Nạp streaming từng file theo thứ tự: Mammalia → Plants → Invertebrates →
   Non-mammalian vertebrates. File NCBI đã sắp theo tax_id tăng dần; pipeline
   dựa vào tính chất này.
2. **Checkpoint theo loài:** mốc tiến độ `progress:<file>` = taxid trọn cuối
   cùng đã commit. Dữ liệu và mốc tiến độ phải commit trong **cùng một giao
   dịch**. Checkpoint cập nhật: mỗi 200 loài trọn, và tại mọi lần ghi giữa
   chừng (flush) — khi flush, progress tiến tới loài trọn cuối cùng có mặt
   trong batch, loài đang nạp dở được ghi cờ `partial:<file>`.
3. **Khôi phục sau ngắt (bắt buộc đúng ngữ nghĩa này):** xoá occurrences của
   **mọi** taxon thuộc file có taxid > progress (một lần quét), xoá cờ
   partial, rồi nạp lại từ sau progress. Cấm chỉ xoá riêng loài dở — đó là
   lỗi đã gây trùng lặp ngày 17/11/2026 (xem mục 11).
4. Nạp xong một file: xoá progress/partial, đặt `done:<file>`.
5. Cache block_id theo `(symbol, loại gene)` trong phạm vi 1 file được phép
   (chỉ là tối ưu tốc độ, không đổi ngữ nghĩa).

## 8. Khử trùng lặp & pha Merkle root

1. Sau khi cả 4 file `done`, chạy **khử trùng lặp toàn cục một lần** (cờ
   `deduped:1`): xoá mọi occurrences trùng theo `(taxid, gene_id)`, giữ 1
   dòng; phải in ra số dòng trước/sau và số dòng đã loại bỏ.
2. Dựng index `occurrences(taxid, block_id)`.
3. Tính SpeciesBlock cho mọi loài có occurrence: `gene_records` = tổng
   occurrence, `distinct_blocks` = số block_id phân biệt, `merkle_root` trên
   danh sách block_id phân biệt đã sắp xếp. Pha này checkpoint mỗi 1.000 loài
   và bỏ qua loài đã có trong bảng `species` khi chạy lại.

## 9. Truy vấn chuẩn

- `shared_blocks(taxid_a, taxid_b)`: INTERSECT trên tập block_id phân biệt
  của hai loài → số block dùng chung + mẫu symbol.
- `species_info(taxid)`: dòng SpeciesBlock của loài.
- `block_info(symbol)`: mọi block mang symbol đó (phân biệt theo loại gene).
- Số liệu tham chiếu độc lập (đo trực tiếp từ file bulk, ngoài registry):
  heo ∩ gà = **13.399** theo symbol (13.213 nếu chỉ protein-coding). Registry
  đếm theo block_id (symbol + loại gene) nên kết quả có thể lệch nhỏ; mọi
  lệch phải được giải thích trong báo cáo kiểm chứng, không im lặng bỏ qua.

## 10. Trạng thái tuân thủ (17/11/2026, 22:44)

| Hạng mục | Trạng thái |
|---|---|
| Lớp 1 IPFS mô phỏng + CID | ✅ Đạt |
| Lớp 2 DAG/phả hệ/royalty (demo v1) | ✅ Đạt — đóng góp F2: 25/25/50; royalty 100.000 → 7.500/2.500 |
| Harvest catalog 31.189 loài (v4) | ✅ Đạt |
| Registry: Mammalia | ✅ Xong — 9.261.337 gene; 4.787.384 block |
| Registry: Plants | ✅ Xong |
| Registry: Invertebrates | 🔄 Đang nạp — progress taxid 31.228 |
| Registry: Non-mammalian vertebrates | ⏳ Chưa nạp |
| Khử trùng lặp + Merkle root 31.189 loài | ⏳ Chờ nạp xong (code đã có, đã test) |
| Kiểm chứng cuối (`verify_block_registry.py`) | ⏳ Script sẵn sàng, chờ build xong |
| Contract `GeneBlock.sol` | ⚠️ Có source, **chưa biên dịch/chưa deploy** — không được tuyên bố đã on-chain |
| Web demo | ⚠️ Đang hiển thị mô hình v2 mô phỏng (LEGACY), chưa đúng spec v5 |

## 11. Nhật ký quyết định & sự cố

- **17/11/2026 — Chốt mô hình v5** theo yêu cầu chủ dự án: bỏ dữ liệu ảo,
  1 gene = 1 block, gene trùng là block dùng chung (thay cho mô hình v2
  "300 gene mô phỏng/loài").
- **17/11/2026 — Sự cố trùng lặp khi khôi phục:** cơ chế resume cũ chỉ xoá
  loài nạp dở; các loài trọn nằm sau checkpoint đã commit bị nạp lại, trùng
  đúng 2 lần (đo: taxid 7375 — 15.894 gene trùng; taxid 7461 — 13.147 gene
  trùng). Đã sửa theo mục 7.3 + mục 8.1 và kiểm thử lại đúng kịch bản lỗi.
- **Kênh dữ liệu bị loại:** NCBI Datasets API (trả sai taxon), Ensembl
  Genomes REST (không kết nối được từ môi trường build — chỉ loại cho mục
  đích harvest, không loại cho truy vấn ortholog sau này).

## 12. Tiêu chí nghiệm thu cuối của registry

1. Cả 4 file đều `done`; tổng occurrences sau khử trùng lặp ≤ 52.339.023 và
   phần chênh lệch được giải thích bằng số bản ghi thiếu symbol chuẩn.
2. Không còn cặp `(taxid, gene_id)` nào xuất hiện >1 lần trong occurrences.
3. `species` có đủ 31.189 loài có dữ liệu, mỗi loài 1 Merkle root.
4. `shared_blocks(9823, 9031)` chạy được và đối chiếu xong với 13.399.
5. Heo/gà/lúa có `species_info` đầy đủ (gene_records, distinct_blocks, root).
