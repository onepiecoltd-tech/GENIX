# MASTER SPEC — GeneChain & Sơn Hải Kinh Phiêu Lưu Ký

*Đặc tả chuẩn (single source of truth) của toàn bộ dự án. Mọi thay đổi mô
hình phải sửa file này trước, rồi mới sửa code. Phiên bản spec: **6.0 —
19/11/2026**. Bản này thay thế v5.1 (17/11/2026), mở rộng từ lớp dữ liệu
GeneChain sang toàn bộ sản phẩm: on-chain, web demo, game, livestream,
multiplayer và trailer. Trạng thái thực tế ghi ở mục 13; số liệu trong spec
này đều là số đã kiểm chứng trên đĩa/on-chain, không phải số kỳ vọng.*

## 1. Mục đích & phạm vi

GeneChain là hệ thống quản lý lai tạo mã gen gồm 3 lớp: (1) lưu trữ gốc
off-chain theo định danh nội dung, (2) phả hệ & lai tạo dạng Merkle DAG,
(3) xác thực & chia royalty on-chain. Hệ thống quản lý **định danh và nguồn
gốc** của gene, không lưu trữ/phân phối chuỗi ADN thô trên chuỗi.

Trên nền dữ liệu thật đó, dự án có 3 sản phẩm hướng người dùng:

- **Web demo phả hệ GeneChain** — tra cứu 31.189 loài, phòng lai in-silico,
  kiểm chứng Merkle proof ngay trên trình duyệt, ma trận tương đồng.
- **Game "Sơn Hải Kinh Phiêu Lưu Ký"** — game sinh tồn/tiến hoá dùng 100%
  dữ liệu loài thật của registry, đối chiếu thần thoại Sơn Hải Kinh, có chế
  độ chơi đơn, chế độ LIVE theo bình luận và chế độ online nhiều người chơi.
- **Trailer game** — video giới thiệu 118 giây (có bản lồng tiếng).

Tài liệu liên quan: `TOM_TAT_DU_AN.md` (tóm tắt), `TOKENOMICS.md` (kinh tế
token), `GAME_DESIGN.md` (thiết kế game chi tiết), `LIVE_MODE.md` (cầu nối
bình luận), `MULTIPLAYER.md` (server nhiều người chơi + deploy).

## 2. Nguyên tắc bất biến (không được phá vỡ)

1. **Không dữ liệu ảo trong hệ thống thật.** Mọi gene phải có nguồn NCBI
   thật (GeneID truy ngược được). Đường mô phỏng `species_data.make_genes`
   là LEGACY, chỉ phục vụ unit test logic DAG, cấm dùng làm dữ liệu hệ
   thống. (Token "DINO" của bản game công viên khủng long sai ý tưởng ngày
   18/11 là mô phỏng và đã bị xoá cùng bản game đó.)
2. **1 gene chuẩn = 1 block.** Một gene chuẩn (định danh ở mục 4) tồn tại
   đúng một block trong toàn hệ thống.
3. **Gene trùng = block dùng chung.** Nếu hai loài có cùng gene chuẩn, cả
   hai cùng trỏ tới một block_id duy nhất — không tạo bản sao theo loài.
4. **Bất biến:** block đã tạo không sửa, không xoá; symbol/gene_type của
   block không đổi theo thời gian dù NCBI cập nhật (bản ghi loài tại thời
   điểm nạp được đóng băng trong occurrences).
5. **Trung thực khoa học:** (a) hash là một chiều — truy xuất là truy xuất
   phả hệ/cấu phần, không khôi phục ADN từ hash; (b) ghép khác loài là tổng
   hợp in-silico ở mức dữ liệu; (c) "gene trùng" = cùng symbol chuẩn theo cơ
   quan danh pháp (ortholog theo danh pháp), không khẳng định trình tự ADN
   giống hệt nhau; (d) loài trong registry là loài NCBI hiện sinh, không
   phải hoá thạch sống cùng thời — game trình bày chúng trong thế giới
   nguyên thuỷ giả tưởng và phải nói rõ điều này khi được hỏi.
6. **Không hứa hẹn giá trị tài chính.** GNCH có nguồn cung cố định và phí
   nền tảng thật; không chào bán công khai (ICO) — xem mục 10.4.

## 3. Định nghĩa

- **Gene record (bản ghi gene):** một dòng dữ liệu gene của một loài cụ thể
  trong NCBI Gene, định danh bởi cặp `(taxid, GeneID)` — khoá tự nhiên duy
  nhất, một loài không có hai bản ghi cùng GeneID.
- **Canonical gene (gene chuẩn):** cặp `(symbol chuẩn, loại gene)`, trong
  đó symbol chuẩn = `Symbol_from_nomenclature_authority` nếu có, ngược lại
  dùng `Symbol` của bản ghi; loại gene = trường `type_of_gene` của NCBI.
- **Block:** hiện thân duy nhất của một gene chuẩn trong hệ thống.
- **Occurrence:** một gene record trỏ tới block của nó, kèm dữ liệu riêng
  theo loài (nhiễm sắc thể, vị trí bản đồ).
- **SpeciesBlock:** cam kết của một loài = Merkle root trên tập block_id
  phân biệt của loài đó.
- **Hybrid block (block lai):** block tổng hợp in-silico từ gene của ≥2
  loài, mọi gene thành phần đều là block gốc, truy xuất được tỉ lệ từng
  loài.

## 4. Định danh block

```
block_id = "bafy" + SHA-256( UPPER(symbol_chuẩn) + "|" + loại_gene )[:52]
```

- Tiền tố `bafy` tương thích định dạng CID của lớp lưu trữ.
- Cùng công thức áp dụng cho mọi loài, mọi thời điểm — hai bản ghi cùng
  gene chuẩn ở bất kỳ loài nào cũng cho cùng block_id.
- Bản ghi thiếu symbol chuẩn (rỗng hoặc "-") **không được tạo block** và bị
  bỏ qua khi nạp; số lượng bỏ qua phải được báo cáo ở bước kiểm chứng cuối.
- Merkle: lá = SHA-256 của chuỗi block_id; nút trong = SHA-256 của phép
  nối hai chuỗi hex con; nút lẻ nhân đôi; lá sắp xếp tăng dần theo
  block_id. Trình duyệt của web demo kiểm chứng proof bằng đúng công thức
  này (Web Crypto SHA-256).

## 5. Mô hình dữ liệu — Block Registry (SQLite `data/genechain_blocks.db`)

| Bảng | Cột | Ràng buộc |
|---|---|---|
| `blocks` | block_id (PK), symbol, gene_type, full_name | 1 dòng / gene chuẩn |
| `occurrences` | taxid, gene_id, block_id, chromosome, map_location | Không khoá duy nhất khi nạp (tốc độ); tính duy nhất theo `(taxid, gene_id)` được bảo đảm bằng cơ chế nạp ở mục 7 + bước khử trùng lặp ở mục 8 |
| `species` | taxid (PK), kingdom, gene_records, distinct_blocks, merkle_root | 1 dòng / loài |
| `meta` | key (PK), value | checkpoint nạp, kingdom theo taxid, cờ trạng thái |

Mọi thao tác SQLite nặng phải chạy với `SQLITE_TMPDIR` trỏ vào đĩa chính
(file tạm mặc định ở /tmp tmpfs 512MB từng gây lỗi SQLITE_FULL ngày
18/11/2026 dù đĩa còn 134GB trống).

## 6. Nguồn dữ liệu & xuất xứ

- **Nguồn chuẩn duy nhất:** NCBI Gene — đường bulk FTP chính thống, 4 file
  `gene_info`: `All_Plants`, `All_Invertebrates`, `All_Mammalia`,
  `All_Non-mammalian_vertebrates`; tên khoa học từ NCBI Taxonomy
  (taxdump). File mở rộng hậu spec: `All_Fungi.gene_info.gz` (mục 9).
- E-utilities API chỉ dùng cho truy vấn nhỏ/kiểm chứng, không dùng harvest
  hàng loạt. NCBI Datasets API **bị cấm dùng** cho harvest theo taxon (đã
  kiểm chứng trả sai dữ liệu). Ensembl Genomes REST không kết nối được từ
  môi trường build (chỉ loại cho harvest).
- Vũ trụ dữ liệu gốc: 31.189 taxon (thực vật 14.578; động vật 16.611 —
  gồm không xương sống 8.484, hữu nhũ 1.699, có xương sống khác 6.428),
  52.339.023 gene record được đếm. Số gene theo API `txid[Organism]` cao
  hơn vì cộng taxon con — không dùng làm chuẩn.
- Catalog chuẩn: `data/catalog_all_species.json` / `.csv` (đã mở rộng
  32.717 loài khi tính cả nấm — mục 9).

## 7. Đặc tả nạp dữ liệu (build pipeline)

1. Nạp streaming từng file theo thứ tự: Mammalia → Plants → Invertebrates
   → Non-mammalian vertebrates. File NCBI đã sắp theo tax_id tăng dần;
   pipeline dựa vào tính chất này.
2. **Checkpoint theo loài:** mốc tiến độ `progress:<file>` = taxid trọn
   cuối cùng đã commit. Dữ liệu và mốc tiến độ phải commit trong **cùng
   một giao dịch**. Checkpoint cập nhật: mỗi 200 loài trọn, và tại mọi lần
   ghi giữa chừng (flush) — khi flush, progress tiến tới loài trọn cuối
   cùng có mặt trong batch, loài đang nạp dở được ghi cờ `partial:<file>`.
3. **Khôi phục sau ngắt (bắt buộc đúng ngữ nghĩa này):** xoá occurrences
   của **mọi** taxon thuộc file có taxid > progress (một lần quét), xoá cờ
   partial, rồi nạp lại từ sau progress. Cấm chỉ xoá riêng loài dở — đó là
   lỗi đã gây trùng lặp ngày 17/11/2026 (mục 14).
4. Nạp xong một file: xoá progress/partial, đặt `done:<file>`.
5. Cache block_id theo `(symbol, loại gene)` trong phạm vi 1 file được
   phép (chỉ là tối ưu tốc độ, không đổi ngữ nghĩa).
6. Chạy lại loader luôn an toàn (idempotent theo checkpoint). Loader chạy
   nền bằng nohup, log ở `data/bulk/<file>.log` (nấm: `fungi.log`).

## 8. Khử trùng lặp & pha Merkle root

1. Sau khi cả 4 file `done`, chạy **khử trùng lặp toàn cục một lần** (cờ
   `deduped:1`): xoá mọi occurrences trùng theo `(taxid, gene_id)`, giữ 1
   dòng; phải in ra số dòng trước/sau và số dòng đã loại bỏ. Kết quả thực
   tế 18/11/2026: 59.098.976 → **52.339.023** dòng (loại 6.759.953 trùng),
   khớp đúng tổng đếm độc lập từ file bulk.
2. Dựng index `occurrences(taxid, block_id)`.
3. Tính SpeciesBlock cho mọi loài có occurrence: `gene_records` = tổng
   occurrence, `distinct_blocks` = số block_id phân biệt, `merkle_root`
   trên danh sách block_id phân biệt đã sắp xếp. Pha này checkpoint mỗi
   1.000 loài và bỏ qua loài đã có trong bảng `species` khi chạy lại.

**Kết quả registry gốc (kiểm chứng 18/11/2026 bằng
`examples/verify_block_registry.py`):**

- **32.324.740 block chuẩn | 52.339.023 occurrence | Merkle root đủ
  31.189 loài.** Động vật: 16.611 loài / 40.918.630 gene; thực vật:
  14.578 loài / 11.420.393 gene.
- Heo *Sus scrofa* (9823): 54.048 gene → 39.244 block, root
  `d415dababc64b994db04aa604e67ce92879b3c0ac37439cf0e3c732341aa1fb3`.
- Gà *Gallus gallus* (9031): 32.204 → 28.245 block, root
  `8c5391674b2666f866275d3026042816da6b929fca59175030e5f6c1955975b7`.
- Lúa Japonica (39947): 39.421 → 38.798 block, root
  `648ebf5b902e38ff7634de8f709fae436a83cef1dd7a4c68f87fa3ca9d2ee868`.
- Heo ∩ gà theo registry = **13.377** block chung; đo độc lập theo symbol
  thuần = 13.399 (chỉ protein-coding: 13.213). Lệch 22 vì block_id tách
  theo (symbol + loại gene) — đã giải thích, không bỏ qua. Heo ∩ lúa = 73;
  gà ∩ lúa = 73; cả ba = 69.

## 9. Mở rộng nấm (fungi) — hậu spec, theo yêu cầu chủ dự án 18/11/2026

- Nguồn: `All_Fungi.gene_info.gz` từ NCBI FTP: **7.117.182 gene /
  1.528 taxon**, tên khoa học tìm được 1.528/1.528, giao nhau taxid với
  registry gốc = 0. Catalog mở rộng thành **32.717 loài** (kingdom
  `fungi`), bản sao lưu ở `catalog_all_species.json.bak`.
- Loader `examples/load_fungi.py` dùng lại nguyên cơ chế checkpoint của
  mục 7, sau đó tính Merkle root **chỉ cho loài mới**.
- Côn trùng **không** cần nạp riêng: đã có sẵn trong file Invertebrates
  (ví dụ ruồi giấm 7227: 25.079 gene; ong mật 7460: 12.731; tằm 7091:
  18.344).
- **Trạng thái tại 19/11/2026 00:40:** đang nạp — checkpoint taxid
  150.224 (cờ partial 152.316); occurrences toàn registry hiện
  54.091.387 (phần nấm đã vào 1.752.364), blocks 33.940.529; bảng
  `species` chưa có dòng nấm nào (pha root chưa chạy). Loader từng chết 3
  lần do runtime khởi động lại và 1 lần do lỗi "database is locked" ở
  bước đọc species; đã khởi động lại 19/11/2026, cơ chế dọn khoảng hở
  (981 taxon sau checkpoint) chạy đúng spec.
- **Khi nạp xong (checklist bắt buộc):** (1) kiểm chứng tổng mới:
  occurrences = 52.339.023 + số dòng nấm có symbol hợp lệ; species =
  32.717; lấy số liệu nấm men 4932 + 2 loài nấm mẫu + giao nhau nấm ∩ heo;
  (2) trích bucket `data/tmp_buckets/fungi.txt` từ file bulk; (3) nạp
  kingdom code 2 (nấm) vào `data/demo_data.json` + thêm mục Nấm vào web
  demo; (4) chạy lại `build_species_pack.py` + `build_shk_game.py` để nấm
  vào game (map Linh Sơn/Thiên Sơn/Bất Chu Sơn đã khai bucket fungi sẵn);
  (5) cập nhật spec này + MEMORY + TOM_TAT, đẩy GitHub.

## 10. Lớp on-chain (Ethereum Sepolia, chainId 11155111)

*Mạng thử nghiệm. Mọi địa chỉ dưới đây đều công khai tra cứu được trên
sepolia.etherscan.io. Khoá riêng chỉ nằm trong `deploy/*.json` (đã
.gitignore, nhãn TESTNET ONLY), không bao giờ in ra chat/log/git.*

### 10.1 GeneBlock v1 — `contracts/GeneBlock.sol`

- Địa chỉ: `0x6D2c50DE45719406faB09d00Dd79FB3b53b54AE0`.
- Token 1/2/3 = genesis heo/gà/lúa Japonica với Merkle root thật của
  registry (blockHash = SHA-256 của `GENECHAIN-V5:{taxid}:{root}`,
  geneCids gồm CID IPFS của loài + 3 block_id mẫu có proof); token 4 =
  lai heo×gà thế hệ 1, root lai `9f85aa43be79fba5b9ebe9951a457452aca91c4
  93da5a0668771472f62951c07`. Mọi root đã đọc ngược on-chain và khớp
  registry. v1 bất biến — không sửa, không thêm phí (muốn phí phải qua
  v2).

### 10.2 Token GNCH — `contracts/GeneChainToken.sol` + `TOKENOMICS.md`

- Địa chỉ: `0x2Ed3244A67A6EBd3e1f000Ef651a129cbEf24BE6`. ERC-20, 18 số
  thập phân, **tổng cung cố định 1.000.000.000 GNCH**, không hàm mint sau
  phát hành, `burn()` chỉ đốt của chính người gọi.
- Phân bổ (đã chốt trong TOKENOMICS v1.1 và thực thi on-chain vào 7 ví
  kho): hệ sinh thái & thưởng lai tạo/dữ liệu 30% (ví
  `0x42e6517995420445D2Ee242cEaf58398E21BbDFC`), thanh khoản 15%, ngân
  khố & vận hành 15% (`0xB303F02af2682e06d54eE234f8F422e4902823e7`), cộng
  đồng & tăng trưởng 13%, đội ngũ 12% (khoá 6 tháng, trả dần 24 tháng),
  đối tác chiến lược 10%, dự phòng 5%.
- Tiện ích: phí đăng ký genesis, phí lai tạo, đơn vị chia royalty, staking
  mở tính năng registry, quản trị. Demo royalty GNCH đã chạy thật: 7.500 /
  2.500 GNCH cho hai viện giống mẫu (tỉ lệ 75/25 như ví dụ v1).

### 10.3 GeneBlock v2 — `contracts/GeneBlockV2.sol`

- Địa chỉ: `0x521c44eC1818Fea4142A3A8E13Cdb44abe61339C`. Logic ERC-721/
  phả hệ như v1, cộng phí bằng GNCH: genesis **100 GNCH**, lai **10
  GNCH**; mọi phí **đốt 50% / về ngân khố 50%** qua `transferFrom` +
  `burn()`; `distributeRoyalty` chia GNCH theo trọng số bps (tổng bắt
  buộc 10.000, phần lẻ về ngân khố).
- Kiểm thử vòng kín trên Sepolia đã đạt chính xác tuyệt đối: tổng đốt
  105 GNCH (cung 1.000.000.000 → 999.999.895), ngân khố +105, royalty
  10.000 GNCH tự chia 7.500/2.500.

### 10.4 Cổng lên mainnet (chưa mở)

Không ICO/chào bán công khai theo thiết kế (rủi ro pháp lý Việt Nam:
tiền mã hoá không phải phương tiện thanh toán hợp pháp; chào bán có thể
bị coi là huy động vốn/phát hành chứng khoán trái phép). Lên mainnet chỉ
khi: (1) kiểm toán hợp đồng (audit) xong, (2) có tư vấn pháp lý, (3) chủ
dự án quyết định rõ ràng. Chuỗi gợi ý: Base L2.

### 10.5 IPFS

- Node kubo cục bộ trong dự án; nội dung: catalog + danh sách block đầy
  đủ của 12 loài nổi bật, CIDv1 ghi ở `data/ipfs_cids.json`. CID thư mục
  gốc: `bafybeibl5zkyuiztmuotur2zs3ulhbk3uzxxiie65ttrj7w4taimqxbdqq`;
  catalog: `bafybeibijpxhayobw7tdhhgr2tf3xolic6iymhafoz5z2gbslcii4ypjnu`.
- **Giới hạn đã kiểm chứng:** node trong sandbox kết nối 0 peer (mạng
  libp2p bị chặn/NAT) — CID là thật và đã pin cục bộ nhưng **chưa truy
  cập được công khai**. Muốn công khai cần tài khoản dịch vụ pinning
  (web3.storage/Pinata/Filebase) của chủ dự án hoặc chủ dự án tự chạy
  node. Không được tuyên bố "đã lên IPFS công khai" trước khi có bằng
  chứng truy xuất qua gateway.

## 11. Web demo phả hệ

- Artifact tĩnh "Web Demo Cây Phả Hệ GeneChain", dữ liệu nhúng từ
  registry thật: `data/demo_data.json` (toàn bộ 31.189 loài dạng mảng
  gọn [taxid, tên, kingdom 0=động vật/1=thực vật, gene, block, root] —
  tổng gene nhúng cộng lại đúng 52.339.023) và `data/demo_lab.json`.
- Tính năng chuẩn: (1) tra cứu toàn bộ loài; (2) **phòng lai in-silico**:
  chọn 2 trong 12 loài nổi bật → union/chỉ-A/chỉ-B/dùng chung + Merkle
  root của phép hợp, đủ 66 cặp (ví dụ heo×gà: chung 13.377, hợp 54.112,
  root `9f85aa43…`); (3) **kiểm chứng Merkle proof trên trình duyệt** với
  3 gene mẫu/loài cho heo, gà, lúa (proof đã kiểm chứng phía Python
  trước); (4) **ma trận tương đồng 12×12** = số block dùng chung (không
  phải cây phân loại chính thức — chú thích bắt buộc); (5) mục trưng bày
  cá, bò sát, chim và bộ ba heo/gà/lúa.
- Kingdom code: nấm sẽ là 2 khi mục 9 hoàn tất; giao diện phải xử lý cả
  3 giá trị.

## 12. Game — Sơn Hải Kinh Phiêu Lưu Ký

*File chuẩn duy nhất hiện hành: `game/son-hai-kinh-phieu-luu-ky.html`
(build từ `game/shk_template.html` bằng `examples/build_shk_game.py`).
Mọi bản game cũ (3D Trái Đất Nguyên Thuỷ, bản điện ảnh, bản Sơn Hải Kinh
điện ảnh) đã xoá ngày 18/11/2026 theo yêu cầu chủ dự án; bản điện ảnh vẫn
dựng lại được từ `game/cinematic_template.html` +
`examples/build_cinematic_game.py` khi cần. Khác biệt mô hình phải nói
rõ: bản điện ảnh tính hợp block chính xác bằng bitset cho 30 loài; bản
Phiêu Lưu Ký dùng mô hình lực suy từ số block thật để chơi được với toàn
bộ 31.189 loài.*

### 12.1 Gói dữ liệu game

- `data/game_species_all.json` (pack v3): mọi loài động + thực vật, mỗi
  dòng `[taxid, tên khoa học, bucket, số gene, số block, lớp, bộ, họ, cờ
  rắn]`. Bucket: mammal 1.699 / invertebrate 8.484 / vertebrate 6.428 /
  plant 14.578 (trích từ cột taxid của 4 file bulk NCBI). Phân loại
  lớp/bộ/họ + cờ Serpentes (taxid 8570) trích từ taxdump vào
  `data/species_taxonomy.json`; lớp của 30.983/31.189 loài ở
  `data/species_class.json` (206 loài không xác định được lớp).
- Nguồn sự thật của pack là registry (qua `data/demo_data.json` + file
  bucket + taxonomy), không đọc trực tiếp SQLite khi loader đang chạy
  (tránh khoá DB).

### 12.2 Chơi đơn (đăng nhập cục bộ)

- Nhập tên → hồ sơ lưu localStorage trên thiết bị (`shkpl_profiles`,
  tiến trình `shkpl_prog_<tên>`). Đây **không phải tài khoản online**.
- Lần đầu: hệ thống **random đúng 1 loài** trong toàn bộ 31.189 loài cho
  người chơi; người chơi quay lại được tiếp tục tiến trình.
- Sức mạnh suy ra đơn điệu từ số block thật:
  `power = round(30 × (blocks/1000)^0,55)`. Gộp gen một loài cộng 30%
  lực của con mồi (làm tròn) và +10 sinh lực (tối đa 100).
- Săn loài mạnh hơn: mất `10 + 18 × (1 − tỉ lệ lực)` sinh lực. Trốn =
  nhảy sang map ngẫu nhiên khác (bị cắn −8 HP với xác suất 25% nếu kẻ
  rình mạnh hơn). Vào map mới: 30% bị mai phục bởi loài mạnh hơn chưa
  gộp. Chết (HP 0): hồi sinh cùng loài, tiến trình đặt lại. **Thắng:
  gộp đủ 40 loài.**
- Hiển thị trên map: tối đa **12 thẻ ở 12 vị trí riêng** (7 loài nổi bật
  luân phiên + 5 loài thường lấy mẫu theo bucket của map), và **không
  hai thẻ đang hiển thị nào dùng chung một hình** (loài chưa có chân
  dung riêng dùng ảnh đại diện theo lớp sinh học thật của nó). HUD tối
  đa 468px, tên loài dài cắt "…" một dòng để không che tên map. Giao
  diện game **không hiển thị** số gen/block/Merkle/GNCH (chủ dự án đã
  yêu cầu bỏ toàn bộ chú giải kỹ thuật); dữ liệu thật vẫn chạy ở tầng
  cơ chế.

### 12.3 Tám map Sơn Hải Kinh (`data/shk_data.json`)

| Map | Tên | Hán tự | Bucket quần thể |
|---|---|---|---|
| quy-khu | Quy Khư · Đông Hải | 歸墟 | vertebrate, invertebrate |
| thanh-khau | Thanh Khâu Sơn | 青丘之山 | mammal, invertebrate |
| chuong-nga | Chương Nga Sơn | 章莪之山 | mammal, vertebrate |
| linh-son | Linh Sơn | 靈山 | plant, fungi |
| con-luan | Côn Luân Khâu | 崑崙之丘 | vertebrate, invertebrate, mammal |
| thien-son | Thiên Sơn | 天山 | cả bốn bucket |
| chuong-vi | Chương Vĩ Sơn | 章尾山 | vertebrate |
| bat-chu | Bất Chu Sơn | 不周山 | cả bốn bucket (nguy hiểm nhất) |

Loài nổi bật được xếp đích danh vào map có liên quan trong Sơn Hải Kinh
(ví dụ gà → Chương Nga Sơn của Tất Phương; chó → Thanh Khâu, huyết mạch
Cửu Vĩ Hồ); loài thường xuất hiện theo bucket. Huyết mạch theo nhóm:
cá → Văn Diêu Ngư, chim → Loan Điểu, bò sát → Chúc Long, thực vật →
Phù Tang, họ chó → Cửu Vĩ Hồ...

### 12.4 Hình ảnh

- Mọi loài đều có hình: ảnh đại diện theo **lớp sinh học thật** (20 ảnh
  ở `game/art_classes/`) khi chưa có chân dung riêng. Ánh xạ dự phòng
  cho các lớp hiếm khai trong template (bảng CLS_FB).
- Chân dung riêng: mục tiêu **300 loài** (ảnh 720px WebP ≈ 60KB/ảnh;
  game ≈ 26MB khi đủ 300; phương án 500 đã bị loại vì quá nặng). Tiến
  độ hiện tại: **78/300** (30 loài gốc ở `game/art_species/` + 48 loài
  nổi tiếng ở `game/art_species2/`), ưu tiên loài nổi tiếng/hay gặp.
  Phong cách khoá cứng: ảnh điện ảnh tiên hiệp, ánh sáng giờ vàng, hạt
  linh quang — đồng nhất mọi đợt vẽ.
- 5 ảnh nền vùng đất + 1 ảnh nền đăng nhập ở `game/art_zones/final/`.

### 12.5 Công thức tiến hoá (đối chiếu Sơn Hải Kinh)

Tiến hoá không tính thuần theo số lần gộp: mỗi cấp yêu cầu **số lần gộp
tối thiểu + đủ bộ phận**, bộ phận khớp theo phân loại NCBI thật của các
loài đã gộp (ghi log kèm map lúc gộp). Cấp đạt được = cấp cao nhất liên
tục từ cấp 1 mà mọi điều kiện đều thoả.

| Cấp | Dị thú | Gộp ≥ | Bộ phận bắt buộc |
|---|---|---|---|
| 1 | Nhĩ Thử 鼠 | 2 | 1 loài bộ Rodentia (thân chuột) + 1 loài bộ Lagomorpha (đầu thỏ) |
| 2 | Cửu Vĩ Hồ 九尾狐 | 5 | 2 loài họ Canidae |
| 3 | Tất Phương 畢方 | 9 | 1 loài lớp Aves + săn 1 loài ngay tại Chương Nga Sơn (lửa Chương Nga) |
| 4 | Cùng Kỳ 窮奇 | 13 | 1 loài họ Felidae + 1 loài lớp Aves |
| 5 | Tương Liễu 相柳 | 17 | 3 loài rắn (Serpentes) |
| 6 | Đế Giang 帝江 | 21 | 2 loài lớp Aves + 1 loài lớp Insecta |
| 7 | Chúc Long 燭龍 | 25 | 1 loài rắn + 1 loài bộ Primates |
| 8 | Ứng Long 應龍 | 30 | 1 cá (Actinopteri/Chondrichthyes — vảy cá) + 1 họ Bovidae (sừng trâu) + 1 rắn + 1 chim săn mồi (Accipitriformes/Falconiformes/Strigiformes — vuốt ưng) + 1 lớp Aves (cánh rồng) |

Ảnh 8 cấp ở `game/art_forms/stage1-8.webp`, vẽ theo mô tả gốc trong
Sơn Hải Kinh (Đế Giang: thân túi vàng, đỏ như lửa đan sa, sáu chân bốn
cánh, không mặt — đã kiểm chứng bằng mắt). Panel tiến hoá hiện checklist
bộ phận + nút tìm loài cho bộ phận thiếu; gợi ý săn gắn huy hiệu cho
loài cho bộ phận đang thiếu. Thắng vẫn tính ở 40 lần gộp (Ứng Long là
hình dạng tối thượng ở màn thắng).

### 12.6 Chế độ LIVE (bình luận điều khiển)

- Nút 🔴 LIVE: vòng bình chọn **10 giây**, mỗi tài khoản 1 phiếu/vòng;
  từ khoá đội Săn (`săn/san`) đấu đội Chạy (`chạy/chay/trốn/tron`); hết
  giờ AI thực thi lệnh đông hơn (săn = săn mục tiêu yếu nhất chưa gộp;
  chạy = trốn map khác); hoà/không phiếu = AI đứng yên. Thanh tỉ số +
  đếm ngược hiển thị trên cùng cho stream.
- Nguồn bình luận: (a) mô phỏng tích hợp để test; (b) dán thủ công;
  (c) cầu nối `live_bridge.py` chạy **trên máy của streamer** (cổng
  127.0.0.1:8787): YouTube qua API chính thức (YT_API_KEY +
  YT_LIVE_CHAT_ID), TikTok qua thư viện TikTokLive (**không chính
  thức**), Facebook qua Graph API. Token chỉ ở máy streamer. Bản HTML
  tĩnh không tự đọc được chat của các nền tảng — không tuyên bố khác.
  Chi tiết: `LIVE_MODE.md`. Cầu nối đã smoke-test đạt.

### 12.7 Nhiều người chơi (online) — `server/server.js`

- Node.js + WebSocket (`ws`), **một cổng 8788** phục vụ cả file game
  (HTTP `/`, `/game`; `/health` kiểm tra sống) lẫn realtime. Route phải
  bỏ qua query string (link `?join=1` từng bị 404 — đã sửa).
- Phòng = 8 map Sơn Hải Kinh. Mỗi map có **8 NPC** sinh từ bucket của
  map, hồi sinh sau 4 giây khi bị ăn. Vào chơi: server **random 1 loài
  thật trong 31.189 loài**, đặt vào map quê hương (ưu tiên map có loài
  nổi bật trùng taxid, sau đó theo bucket).
- Giao thức: client gửi `join/move/hunt/flee/travel/chat`; server trả
  `welcome/state (mỗi 300ms)/result/event/evo/win/respawn`. Server là
  nơi tính toàn bộ: lực (cùng công thức 12.2), gộp gen (+30% lực con
  mồi, +10 HP), công thức tiến hoá (cùng bảng 12.5, tính trên log gộp
  kèm map), thắng ở 40 lần gộp.
- PvP: săn trúng người chơi khác → người săn gộp được gen của loài nạn
  nhân, nạn nhân −35 HP; chết → tái sinh thành loài random mới nhưng
  **giữ nguyên số lần gộp và log tiến hoá**. Săn hụt kẻ mạnh hơn: mất
  HP theo cùng công thức chơi đơn. Sự kiện phòng (ai vào, ai săn ai, ai
  tiến hoá, ai thắng) phát cho mọi người trong map.
- **Thiết kế theo phiên live — KHÔNG lưu người chơi** (chủ dự án chốt
  18/11/2026): trạng thái chỉ ở RAM server; tắt server là xoá sạch;
  không tài khoản, không mật khẩu, không cơ sở dữ liệu người chơi.
  Không được tự ý thêm lưu trữ bền vững.
- Link mời khán giả: panel Online trong game có ô link + nút Copy,
  dạng `<địa chỉ server>/?join=1` — khán giả mở link là vào thẳng panel
  online, địa chỉ server tự nhận diện theo link (tham số `?srv=` ghi đè
  khi cần). Quy trình buổi live chuẩn: bật server → mở Cloudflare
  Tunnel → streamer vào chơi → ghim link mời vào bình luận.
- Kiểm thử chuẩn: `server/test_client.js` — 2 client giả lập (vào
  phòng → về cùng map → săn NPC → trốn), kết quả yêu cầu: **TEST
  PASS**. Đã đạt 18/11/2026 và đạt lại sau mọi sửa đổi route/client.
- Deploy: `server/Dockerfile` (build từ thư mục gốc dự án). Khuyến
  nghị: máy chủ dự án + Cloudflare Tunnel (miễn phí, theo phiên live)
  hoặc Fly.io/Railway/VPS (24/7). **Sandbox của Muse không host được
  server công khai** (không có đường vào từ internet) — không tuyên bố
  server đang chạy công khai khi chưa có bằng chứng.

## 13. Trailer game

- File: `trailer/SON_HAI_KINH_PHIEU_LUU_KY_TRAILER.mp4` — **118 giây,
  1920×1080, 30fps**, dựng bằng `trailer/build_trailer.py`: 6 clip AI
  chuyển động từ ảnh game (Ứng Long, Chúc Long, Cửu Vĩ Hồ, Cùng Kỳ,
  thế giới, Quy Khư) + montage ảnh thật của game (tựa đề, 5 vùng đất,
  16 loài chạy nhanh 1 giây/loài, thang tiến hoá 8 cấp, 3 thẻ tính
  năng: Săn/Trốn — Online — LIVE) + thẻ số liệu "31.189 loài thật".
- Nhạc: bản phối gốc tổng hợp bằng mã (trống taiko 132 BPM + đàn tranh
  ngũ cung Karplus-Strong + drone + chiêng), không dùng nhạc có bản
  quyền. Master **−14 LUFS / TP −1,5**.
- Bản lồng tiếng: `..._TRAILER_VO.mp4` — 16 câu voiceover tiếng Việt
  (`trailer/make_vo.py`, giọng nam trầm uy nghi, tốc độ 95) đặt khớp
  từng đoạn hình (`trailer/mix_trailer.py`); nhạc tự hạ **−5,7dB**
  (ducking) khi có lời; tiếng ngoại cảnh tổng hợp: gió nền xuyên suốt,
  sấm mở đầu, sóng Quy Khư (24–35s), lửa Chúc Long (84–97s), tiếng gầm
  cho Cùng Kỳ/Chúc Long/Ứng Long, whoosh chuyển cảnh. Chất lượng phát
  âm tiếng Việt của TTS có giới hạn — khi giao bản lồng tiếng phải nói
  rõ điều này.
- File MP4 (85MB/bản) **không đẩy GitHub** (giới hạn kênh đẩy); chỉ
  script + file voice mẫu được đẩy. Bản giao nằm ở `trailer/` và
  `~/workspace/your_files/`.

## 14. GitHub & quy ước làm việc

- Repo công khai: **onepiecoltd-tech/GENIX**. Đẩy qua GitHub Git Data
  API bằng công cụ hỗ trợ của connector custom.github (token PAT quyền
  Contents read/write chỉ trên GENIX, lưu trong Secure Vault; SSH từ
  sandbox bị chặn ở tầng mạng). Mỗi lần đẩy phải kiểm chứng
  `tree_khop: true` (cây thư mục từ xa ≡ cây cục bộ) mới được báo xong.
- **Quy tắc thường trực (chủ dự án, 18/11/2026): làm xong mục nào tự
  đẩy lên GitHub mục đó, không chờ nhắc.** Không chạy hai lượt đẩy đồng
  thời và không sửa file trong lúc đang đẩy (sự cố 18/11/2026: hai lượt
  đẩy chồng nhau gây lỗi 422 non-fast-forward + một bản chụp giữa
  chừng; đã xử lý bằng một lượt đẩy sạch và kiểm chứng lại).
- `.gitignore` bắt buộc loại trừ: khoá ví (`deploy/testnet-wallet.json`,
  `deploy/token_vaults.json`), DB registry + WAL, `data/bulk/`,
  `data/species_genes/`, thư mục IPFS + công cụ, `node_modules`, file
  zip, và media lớn của trailer (`trailer/clips/`, `trailer/segs/`,
  `trailer/*.mp4`, `trailer/*.wav`, `trailer/vo/*.wav`).
- Môi trường build: giới hạn 1,5 CPU dùng chung + 6GB RAM; /tmp là
  tmpfs 512MB (xem mục 5). Thế hệ ảnh/video theo đợt nhỏ có checkpoint
  (skill quota_aware_media_production).

## 15. Trạng thái tuân thủ (19/11/2026)

| Hạng mục | Trạng thái |
|---|---|
| Registry 4 file gốc + dedupe + Merkle 31.189 loài | ✅ Đạt, đã kiểm chứng (mục 8) |
| Nấm (fungi) | 🔄 Đang nạp, checkpoint taxid 150.224; checklist hoàn tất ở mục 9 |
| Web demo (tra cứu + phòng lai + proof + ma trận) | ✅ Đạt trên dữ liệu thật |
| GeneBlock v1 + 4 token Sepolia | ✅ Đạt, root đọc ngược khớp |
| GNCH + phân bổ 7 kho + demo royalty | ✅ Đạt on-chain |
| GeneBlock v2 + kiểm thử vòng kín phí/royalty | ✅ Đạt (đốt đúng 105 GNCH) |
| IPFS CID + pin cục bộ | ✅ Đạt; ⏳ công khai chờ dịch vụ pinning của chủ dự án |
| Game chơi đơn (31.189 loài, 8 map, công thức tiến hoá) | ✅ Đạt |
| Hình ảnh game | ✅ Mọi loài có hình; chân dung riêng 78/300 (đang bổ sung theo đợt) |
| Chế độ LIVE + cầu nối bình luận | ✅ Đạt, đã smoke-test |
| Nhiều người chơi + link mời `?join=1` | ✅ Đạt, test 2 client PASS |
| Trailer 118s + bản lồng tiếng | ✅ Đạt |
| Mainnet | ⏸ Chưa mở — chờ audit + pháp lý (mục 10.4) |

## 16. Nhật ký quyết định & sự cố

- **17/11/2026 — Chốt mô hình v5** theo yêu cầu chủ dự án: bỏ dữ liệu
  ảo, 1 gene = 1 block, gene trùng là block dùng chung (thay mô hình v2
  "300 gene mô phỏng/loài").
- **17/11/2026 — Sự cố trùng lặp khi khôi phục:** cơ chế resume cũ chỉ
  xoá loài nạp dở; các loài trọn nằm sau checkpoint đã commit bị nạp
  lại, trùng đúng 2 lần. Đã sửa theo mục 7.3 + 8.1 và kiểm thử lại đúng
  kịch bản lỗi.
- **18/11/2026 — Sửa khái niệm game:** chủ dự án bác bản "công viên
  khủng long" (đã xoá hẳn artifact đó); game phải dùng dữ liệu loài
  thật của GeneChain trong thế giới nguyên thuỷ/Sơn Hải Kinh.
- **18/11/2026 — Các chốt thiết kế game theo playtest:** bỏ toàn bộ chú
  giải gen/block khỏi giao diện; tiến hoá theo công thức bộ phận Sơn
  Hải Kinh; chơi online **theo phiên live, không lưu user**; mỗi lần
  làm xong tự đẩy GitHub.
- **18/11/2026 — Sự cố đẩy GitHub:** hai lượt đẩy chồng nhau → 422
  non-fast-forward; xử lý bằng một lượt đẩy sạch, kiểm chứng tree khớp.
- **18–19/11/2026 — Loader nấm chết nhiều lần** (runtime khởi động lại;
  1 lần lỗi khoá DB): luôn khôi phục đúng bằng checkpoint + dọn khoảng
  hở, không nạp lại từ đầu, không mất dữ liệu đã commit.

## 17. Tiêu chí nghiệm thu

Registry (đã đạt cho 4 file gốc; áp dụng tương tự khi nấm xong):

1. Cả 4 file đều `done`; tổng occurrences sau khử trùng lặp ≤
   52.339.023 và phần chênh lệch được giải thích bằng số bản ghi thiếu
   symbol chuẩn.
2. Không còn cặp `(taxid, gene_id)` nào xuất hiện >1 lần trong
   occurrences.
3. `species` có đủ 31.189 loài có dữ liệu, mỗi loài 1 Merkle root.
4. `shared_blocks(9823, 9031)` chạy được và đối chiếu xong với 13.399.
5. Heo/gà/lúa có `species_info` đầy đủ (gene_records, distinct_blocks,
   root).

On-chain & sản phẩm:

6. Mọi địa chỉ hợp đồng/token ở mục 10 tra cứu được trên Sepolia
   Etherscan; root của token 1–4 đọc ngược khớp registry.
7. Web demo: tổng gene nhúng = 52.339.023; 66 cặp lai tính được; proof
   mẫu kiểm chứng đạt trên trình duyệt.
8. Game: build từ template không lỗi JS; test_client của server đạt
   TEST PASS; link `?join=1` trả HTTP 200 và mở đúng panel online.
9. Trailer: đúng 118 giây ±2, 1920×1080/30fps, âm thanh −14 LUFS ±1.
10. GitHub: sau mỗi đợt việc, cây thư mục GENIX khớp cây cục bộ
    (`tree_khop: true`) và không chứa bất kỳ khoá riêng/DB/media lớn
    nào bị cấm ở mục 14.
