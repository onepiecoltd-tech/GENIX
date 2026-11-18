# TOKENOMICS — GeneChain Token (bản thiết kế v1.1, ĐÃ DUYỆT 18/11/2026)

> Trạng thái: ĐÃ ĐƯỢC CHỦ DỰ ÁN DUYỆT ngày 18/11/2026 — ký hiệu GNCH, tổng cung 1 tỷ, phí lai tạo 10 GNCH + đốt 50% giữ nguyên như thiết kế; riêng tỷ lệ phân bổ do Muse thiết kế lại theo hướng tối ưu thương mại (mục 3).
> Nguyên tắc xuyên suốt (kế thừa MASTER_SPEC): không hứa hẹn lợi nhuận, không bán coin huy động vốn từ công chúng ở giai đoạn này; coin tồn tại để vận hành nền tảng GeneChain, không phải để đầu cơ.

## 1. Thông tin cơ bản

| Hạng mục | Đề xuất | Ghi chú |
|---|---|---|
| Tên | GeneChain Token | |
| Ký hiệu | **GNCH** | Ký hiệu "GENE" đã có dự án khác dùng (Genopets trên Solana) — tránh trùng để khỏi nhầm lẫn và tranh chấp thương hiệu |
| Chuẩn | ERC-20 | Tương thích ví/sàn hệ Ethereum |
| Decimals | 18 | Chuẩn ERC-20 |
| Tổng cung | **1.000.000.000 GNCH (1 tỷ), cố định** | Không mint thêm sau khi phát hành; chỉ giảm qua cơ chế đốt phí |
| Mạng phát hành đầu tiên | Sepolia testnet (demo) | Mainnet chỉ sau khi qua cổng quyết định ở mục 7 |
| Mạng mainnet đề xuất | Base (Ethereum L2) | Phí gas rẻ hơn Ethereum L1 nhiều lần, vẫn thuộc hệ Ethereum; contract GeneBlock hiện tại port sang không đổi logic |

## 2. Coin dùng để làm gì (tiện ích thật trong GeneChain)

1. **Phí lai tạo on-chain**: mỗi lần `breed()` tạo block lai mới, người lai trả phí bằng GNCH (mức khởi điểm đề xuất: 10 GNCH/lần, DAO/quản trị chỉnh được).
2. **Tiền tệ chia royalty**: `distributeRoyalty()` trong GeneBlock.sol trả bằng GNCH thay vì ETH — người tạo giống gốc nhận GNCH theo đúng trọng số đóng góp gen (bps) đã có trong contract.
3. **Phí đăng ký block genesis mới**: viện/trung tâm giống muốn ghi một loài/giống mới lên chuỗi trả phí GNCH.
4. **Staking mở tính năng registry nâng cao**: stake GNCH để dùng tra cứu Merkle proof hàng loạt, API dữ liệu 32,7 nghìn loài, và quyền "curator" (kiểm duyệt dữ liệu loài mới nạp vào registry).
5. **Quản trị**: nắm GNCH = quyền biểu quyết các tham số: mức phí, nguồn dữ liệu mới (thêm giới sinh vật), tỷ lệ đốt.

Mọi tiện ích trên đều gắn với hành động có thật trên nền tảng — đây là điều kiện để coin có nhu cầu sử dụng thật thay vì chỉ có người mua bán qua lại.

## 3. Phân bổ tổng cung (1 tỷ GNCH = 100%) — bản tối ưu thương mại

Logic thương mại: quỹ lớn nhất vẫn là hệ sinh thái (động cơ tạo nhu cầu dùng coin thật); thanh khoản nâng lên 15% để thị trường đủ sâu nếu niêm yết; tách riêng quỹ tăng trưởng/marketing 13% làm "ngân sách bán hàng"; đối tác chiến lược 10% để kéo viện/trung tâm giống lên nền tảng; đội ngũ hạ còn 12% (nằm trong biên 10–15% mà nhà đầu tư coi là lành mạnh) nhưng khóa cứng.

| Quỹ | Tỷ lệ | Số lượng | Khóa / vesting |
|---|---|---|---|
| Hệ sinh thái & thưởng lai tạo/dữ liệu | 30% | 300.000.000 | Mở dần theo hoạt động thật trên nền tảng, không xả một lần |
| Thanh khoản | 15% | 150.000.000 | Khóa trong pool tối thiểu 12 tháng nếu lên mainnet |
| Kho bạc & vận hành/kinh doanh (treasury) | 15% | 150.000.000 | Ví đa chữ ký (multisig), chi theo ngân sách công khai |
| Cộng đồng & tăng trưởng (marketing, airdrop theo đóng góp) | 13% | 130.000.000 | Chi theo chiến dịch, công bố định kỳ |
| Đội ngũ & sáng lập | 12% | 120.000.000 | Cliff 6 tháng, vesting tuyến tính 24 tháng |
| Đối tác chiến lược (viện nghiên cứu, trung tâm giống, nền tảng) | 10% | 100.000.000 | Vesting 12 tháng, phân bổ gắn với hợp tác thật |
| Dự phòng | 5% | 50.000.000 | Multisig, chỉ dùng khi có quyết định quản trị |

## 4. Dòng chảy giá trị & cơ chế đốt

- Phí lai tạo + phí đăng ký genesis: **50% đốt vĩnh viễn, 50% về treasury**. Càng nhiều hoạt động lai tạo thật, cung càng giảm — áp lực giảm phát gắn với mức sử dụng, không gắn với chiêu trò.
- Ví dụ chạy thử bằng số của demo v1: một block lai bán giá tương đương 100.000 đơn vị, royalty 10% = 10.000 GNCH; theo trọng số đóng góp gen, Viện Lúa ĐBSCL (tạo A + C, 75%) nhận 7.500 GNCH, Trung Tâm Giống Miền Tây (tạo B, 25%) nhận 2.500 GNCH — đúng cơ chế `distributeRoyalty` đã có, chỉ đổi đơn vị trả sang GNCH.
- Không có lãi suất hứa hẹn, không có "staking APY cố định". Thưởng staking (nếu có) lấy từ phí nền tảng thật, công bố nguồn.

## 5. Những điều thiết kế này CỐ TÌNH không làm

- Không ICO/IDO/bán công khai ở giai đoạn này (rủi ro pháp lý tại Việt Nam: tiền ảo không phải phương tiện thanh toán hợp pháp; phát hành bán huy động vốn từ công chúng có thể bị xem là trái phép).
- Không cam kết giá, không cam kết mua lại, không marketing kiểu "đầu tư sinh lời".
- Không mint ẩn: tổng cung cố định ghi cứng trong contract, ai cũng kiểm chứng được trên Etherscan.

## 6. Bảo vệ kỹ thuật

- Contract ERC-20 viết tối giản, không hàm mint sau deploy, không quyền admin rút tiền của người dùng.
- Ví treasury/đội ngũ dùng multisig (tối thiểu 2/3 chữ ký).
- Trước mainnet bắt buộc: kiểm toán (audit) contract bởi bên thứ ba + rà soát pháp lý. Hai việc này cần ngân sách thật và quyết định riêng của chủ dự án.

## 7. Lộ trình qua cổng quyết định

| Giai đoạn | Nội dung | Điều kiện qua cổng |
|---|---|---|
| 0 — Demo testnet | Tạo GNCH trên Sepolia theo đúng thông số trên; nối phí `breed()` và `distributeRoyalty()` trả bằng GNCH; phát thử qua faucet nội bộ | Chủ dự án duyệt tài liệu này |
| 1 — Vận hành thử | Mời viện/trung tâm giống dùng thử trên testnet, đo số lần lai tạo/chia royalty thật | Có người dùng thử thật và phản hồi |
| 2 — Quyết định mainnet | Chọn mạng (đề xuất Base), audit, tư vấn pháp lý, khóa thanh khoản | Chủ dự án quyết định riêng, có tư vấn luật |
| 3 — Mainnet | Deploy bản đã audit, phân bổ theo mục 3 | Chỉ sau giai đoạn 2 |

## 8. Đã chốt khi duyệt (18/11/2026)

1. Ký hiệu GNCH — **đồng ý**.
2. Tổng cung 1 tỷ cố định — **đồng ý**.
3. Tỷ lệ phân bổ — chủ dự án giao Muse thiết kế tối ưu thương mại: bản ở mục 3 (30/15/15/13/12/10/5).
4. Phí lai tạo khởi điểm 10 GNCH/lần và đốt 50% phí — **đồng ý**.

Bước thực thi: tạo GNCH trên Sepolia testnet đúng thông số trên, phân bổ on-chain vào 7 ví quỹ riêng. Lưu ý kỹ thuật: contract GeneBlock hiện tại (0x6D2c50DE45719406faB09d00Dd79FB3b53b54AE0) là bất biến, không sửa được để trừ phí GNCH trong `breed()` — muốn phí/royalty GNCH chạy tự động trong contract cần GeneBlock v2 (quyết định riêng, không tự ý thay contract đang chạy).

## 9. Kết quả thực thi trên Sepolia testnet (18/11/2026, đã kiểm chứng on-chain)

- Token GNCH: **0x2Ed3244A67A6EBd3e1f000Ef651a129cbEf24BE6** — tổng cung đúng 1.000.000.000, ví deployer còn 0 (đã phân bổ hết).
- Phân bổ thực tế: Hệ sinh thái 299.990.000 (300M trừ 10.000 demo royalty) · Thanh khoản 150.000.000 · Treasury 150.000.000 · Tăng trưởng 130.000.000 · Đội ngũ 120.000.000 · Đối tác 100.000.000 · Dự phòng 50.000.000.
- Demo royalty bằng GNCH đã chạy thật: Viện Lúa ĐBSCL nhận 7.500 GNCH, Trung Tâm Giống Miền Tây nhận 2.500 GNCH (đúng tỷ lệ 75/25 của ví dụ mục 4).
- Chi tiết giao dịch: `deploy/token_result.json`; khóa các ví quỹ demo: `deploy/token_vaults.json` (chỉ testnet).
- GeneBlock v2 (nối phí + royalty GNCH, chủ dự án duyệt 18/11/2026): **0x521c44eC1818Fea4142A3A8E13Cdb44abe61339C**. Kiểm tra khép kín trên Sepolia đạt chính xác: phí genesis 100 GNCH × 2 + phí lai 10 GNCH → đốt 105 GNCH (tổng cung 1.000.000.000 → 999.999.895), treasury nhận 105 GNCH; royalty 10.000 GNCH tự chia 7.500/2.500 cho hai ví viện tạo giống. Chi tiết: `deploy/v2_result.json`. Contract v1 và 4 token của nó giữ nguyên.
