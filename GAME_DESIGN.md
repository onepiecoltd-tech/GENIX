# GAME DESIGN — Trái Đất Nguyên Thủy GeneChain (v2, theo ý tưởng gốc của chủ dự án)

> v2 thay thế hoàn toàn v1 (bản "công viên khủng long" là hiểu lầm, đã bỏ).
> Nguyên tắc số 1 của v2: **mọi dữ liệu trong game là dữ liệu THẬT từ Block Registry của GeneChain** — loài thật, gen thật, số block thật, Merkle root thật, quan hệ chia sẻ gen thật. Phần hư cấu duy nhất là cách di chuyển/săn trong thế giới 3D.

## 1. Ý tưởng gốc (chủ dự án, 18/11/2026)

Dùng dữ liệu thật của các loài đã nạp vào GeneChain để dựng **Trái Đất thời nguyên thuỷ**. Mỗi loài có hình 3D trong thế giới, có **chú giải gen thật** của nó. Người chơi săn một loài để **gộp gen** của nó vào bộ gen của mình và **tiến hoá thành loài mới (loài lai)** — game **gợi ý nên săn loài nào** dựa trên dữ liệu gen thật.

## 2. Dữ liệu thật dùng trong game (trích từ registry, không bịa)

30 loài tiêu biểu đã kiểm chứng trong Block Registry (bản đầu 15 loài bị chủ dự án chê ít — đã mở rộng; phương pháp bitset dưới đây cho phép tăng tiếp lên hàng trăm loài mà số liệu vẫn chính xác):

- Thú: Heo, Bò, Ngựa, Chó, Mèo, Chuột nhắt, Thỏ, Cừu
- Chim: Gà, Vịt, Bồ câu, Chim cánh cụt hoàng đế, Chim sẻ vằn, Gà tây
- Cá: Cá ngựa vằn, Cá hồi, Cá nóc hổ, Cá medaka, Cá gai ba gai
- Bò sát & lưỡng cư: Thằn lằn Anole, Rùa vẽ, Cá sấu Mỹ, Ếch vuốt châu Phi
- Côn trùng & không xương sống: Ruồi giấm, Ong mật, Tằm, Giun tròn C. elegans
- Thực vật (nguồn gen thu thập): Lúa Japonica, Ngô, Cải Arabidopsis

Nấm sẽ thêm vào khi đợt nạp All_Fungi vào registry hoàn tất.

Mỗi loài trong game hiển thị: tên khoa học, số gen, số block phân biệt, Merkle root, và **danh sách gen thật tiêu biểu** (ký hiệu + tên đầy đủ, ví dụ LEP — leptin ở heo, GAPDH ở gà).

## 3. Cơ chế gộp gen — tiến hoá (toán học thật, tính trước từ registry)

- Bộ gen của người chơi = **hợp (union)** các block của những loài đã săn/gộp. Tập block của từng loài được nhúng vào game dưới dạng bitset (từ dữ liệu occurrences thật của registry); game tự tính số block hợp của BẤT KỲ tổ hợp nào ngay trong trình duyệt — chính xác tuyệt đối, không ước lượng, và mở rộng được tới hàng trăm loài.
- Khi nhắm một loài, game hiện số thật: **số block chung** với bộ gen hiện tại của bạn và **số block mới** loài đó bổ sung.
- **Gợi ý săn**: xếp hạng các loài chưa gộp theo số block mới bổ sung (từ cao xuống thấp) — săn đúng gợi ý là đường tiến hoá nhanh nhất.
- Lần gộp đầu tiên (2 loài) có **Merkle root của loài lai được tính thật** từ hợp block (cùng công thức registry) — "giấy chứng nhận" của loài mới, đối chiếu được với phòng lai in-silico trong web demo.
- Mỗi lần gộp thành công: loài của bạn tiến hoá — lớn hơn, mang tên lai (ví dụ Sus scrofa × Gallus gallus), và thừa hưởng tổng block mới.

## 4. Thế giới 3D — bối cảnh tiên hiệp (theo yêu cầu chủ dự án 18/11: "làm thật đẹp thế giới nguyên thuỷ, như 1 bộ phim tiên hiệp")

Bối cảnh dựng bằng Three.js thuần (không asset ngoài): vòm trời shader chuyển sắc hoàng hôn, mặt trời + hào quang, mặt trăng và 700 sao; dãy núi xa tầng tầng trong sương; biển mây ~30 sprite trôi quanh đảo; 6 đảo bay lơ lửng với thác nước đổ xuống biển mây (texture cuộn), tinh thể phát sáng; cây thần cổ thụ khổng lồ treo quả linh quang; 3 cây linh đào hoa hồng phát sáng với hiệu ứng hoa rơi; tinh thể linh thạch nhấp nháy rải khắp đảo; cổng thiên môn đá cổ với vòng linh quang xoay; hoa sen trên hồ; dòng dung nham phát sáng; ~520 hạt linh khí vàng lơ lửng bay lên; ánh sáng điện ảnh ACES tone mapping (nắng vàng + fill ngọc lục).

Đảo nguyên thuỷ: núi lửa, hồ nước (cá bơi), rừng dương xỉ, bãi cỏ (lúa mọc thành khóm là nguồn gen thu thập thay vì săn). Mỗi loài động vật có mô hình 3D theo nhóm (thú 4 chân, chim có cánh vỗ, cá bơi trong hồ, bò sát thân dài, côn trùng bay/bò), thẻ tên khoa học lơ lửng phía trên. Loài lớn hơn săn bạn, loài nhỏ hơn chạy trốn — đúng quan hệ kích thước thật tương đối.

## 5. Kinh tế GNCH (giữ nguyên tokenomics đã duyệt)

Bản file chơi thử này chưa nối ví. Khi nối: phí tiến hoá (mỗi lần gộp gen) trả bằng GNCH và đốt 50% như GeneBlockV2; lai tạo loài trong game chính là `breed()` on-chain; thưởng lấy từ Quỹ hệ sinh thái. Cung cố định — càng chơi càng đốt. Giá vẫn phụ thuộc cầu thật, không cam kết.

## 6. Trung thực về giới hạn

- "Trái Đất nguyên thuỷ" là bối cảnh trình bày: các loài trong registry là loài có dữ liệu gen trên NCBI (phần lớn là loài hiện sinh), không phải hoá thạch. Game không tuyên bố chúng sống cùng thời.
- Săn/gộp gen trong game là mô phỏng ở tầng dữ liệu (in-silico) như toàn bộ dự án GeneChain: gộp được bộ block và truy vết được nguồn gốc, không tạo sinh vật thật ngoài đời.
- Hình 3D là mô hình khối tượng trưng theo nhóm loài, không phải mô hình giải phẫu chính xác.


## v3 — SƠN HẢI KINH PHIÊU LƯU KÝ (18/11/2026, theo yêu cầu của user)

User chốt 4 điểm: (1) bỏ chọn loài — game dạng đăng nhập, mỗi user được random 1 loài, có chọn SĂN hoặc TRỐN (khoẻ thì săn, yếu thì trốn sang map khác); (2) nạp toàn bộ dữ liệu động thực vật; (3) nạp toàn bộ dữ liệu quái vật/địa lý Sơn Hải Kinh, chia nhiều map; (4) khớp dữ liệu (2) để tiến hoá ra (3), loài thật được xếp vào map Sơn Hải Kinh có liên quan.

Đã triển khai:
- **Đăng nhập cục bộ**: nhập tên → hồ sơ lưu trên máy (localStorage), lần đầu được random 1 loài trong toàn bộ 31.189 loài động + thực vật thật của registry (gói `data/game_species_all.json`: taxid, tên khoa học, bucket phân loại từ file bulk NCBI, số gen, số block). Tiến trình (số loài đã gộp, sinh lực, map) lưu theo từng người chơi. Đây là hồ sơ trên thiết bị, KHÔNG phải tài khoản online — bản file tĩnh không có máy chủ.
- **Săn / Trốn**: mỗi chạm trán hiện thẻ so sánh sức (🟢 yếu hơn / 🟡 ngang sức / 🔴 mạnh hơn — nên trốn). "Lực" suy ra đơn điệu từ số block thật của loài: power = 30·(blocks/1000)^0,55; gộp gen cộng 30% lực của con mồi. Săn kẻ mạnh hơn → bị thương; trốn → nhảy sang map ngẫu nhiên khác (25% bị cắn -8 HP nếu kẻ rình mạnh hơn); vào map mới có 30% bị mai phục bởi kẻ mạnh hơn. Thắng khi gộp đủ 40 loài (Chúc Long hiện thế); chết khi HP = 0, hồi sinh giữ nguyên loài.
- **8 map Sơn Hải Kinh** (`data/shk_data.json`): Quy Khư·Đông Hải, Thanh Khâu Sơn, Chương Nga Sơn, Linh Sơn, Côn Luân Khâu, Thiên Sơn, Chương Vĩ Sơn, Bất Chu Sơn — mỗi map có địa danh/hán tự/quyển trích, dị thú trấn giữ, và quần thể loài thật: 30 loài nổi bật (có ảnh AI) được xếp đích danh vào map liên quan (gà → Chương Nga Sơn của Tất Phương; chó → Thanh Khâu, huyết mạch Cửu Vĩ Hồ…), loài thường trong CSDL xuất hiện theo bucket (có vú / có xương sống / không xương sống / thực vật).
- **Tiến hoá ra dị thú Sơn Hải Kinh**: thang 4 cấp như bản trước (Cửu Vĩ Hồ 2–8, Cùng Kỳ 9–16, Đế Giang 17–24, Chúc Long 25+) kèm trích mô tả gốc; thêm "huyết mạch" theo nhóm loài (cá → Mạch Văn Diêu Ngư, chim → Mạch Loan Điểu, bò sát → Mạch Chúc Long, thực vật → Mạch Phù Tang…).
- File: `game/son-hai-kinh-phieu-luu-ky.html` (7,35 MB; template `game/shk_template.html`, builder `examples/build_shk_game.py`, trích gói `examples/build_species_pack.py`). Bản điện ảnh cũ (chọn loài, bitset hợp nhất chính xác) từng giữ ở `game/son-hai-kinh-dien-anh.html` — hai bản dùng hai mô hình khác nhau: bản cũ tính hợp block chính xác cho 30 loài; bản Phiêu Lưu Ký dùng mô hình lực suy từ số block thật để chơi được với toàn bộ 31.189 loài. (18/11/2026: theo yêu cầu của user, đã xoá các bản game cũ — Trái Đất Nguyên Thuỷ 3D, bản điện ảnh Trái Đất Nguyên Thuỷ, bản điện ảnh Sơn Hải Kinh cùng các bản sao trong your_files và 240 file ảnh raw trung gian; chỉ giữ bản Phiêu Lưu Ký hiện hành + template/builder/art nguồn, nên bản điện ảnh vẫn dựng lại được từ `game/cinematic_template.html` + `examples/build_cinematic_game.py` khi cần. Các file đã xoá nằm trong thùng rác khôi phục được tới 18/12/2026.)
- Nấm: registry nấm vẫn đang nạp nền (checkpoint taxid 37769, đã khởi động lại loader 18/11) nên chưa vào gói game; khi nạp xong chỉ cần chạy lại build_species_pack + build_shk_game là có thêm bucket fungi.

- Mở rộng thang tiến hoá (18/11/2026, user yêu cầu thêm dị thú đẳng cấp cao/đặc biệt): từ 4 cấp lên **8 cấp** — 1 Nhĩ Thử (gộp 2–4), 2 Cửu Vĩ Hồ (5–8), 3 Tất Phương (9–12), 4 Cùng Kỳ (13–16), 5 Tương Liễu (17–20), 6 Đế Giang (21–24), 7 Chúc Long (25–29), 8 Ứng Long (30+) — Ứng Long là hình dạng tối thượng mới ở màn thắng (gộp đủ 40 loài). Ảnh 4 cấp mới vẽ thêm (Nhĩ Thử, Tất Phương, Tương Liễu, Ứng Long) lưu ở `game/art_forms/stage1-8.webp`; 4 ảnh cũ form1-4 giữ nguyên cho bản điện ảnh. `data/shk_data.json` đã gán stage 1–8 tương ứng.

- Full hình ảnh (18/11/2026): user yêu cầu mọi loài đều có hình. Đã trích lớp sinh học thật từ NCBI taxdump cho 30.983/31.189 loài (`data/species_class.json`, pack v2 có thêm trường class) và vẽ 20 ảnh đại diện theo lớp (`game/art_classes/`) — mọi loài đều hiện thẻ hình đúng lớp của mình, hết thẻ chữ trơ. Mục tiêu chốt với user: **300 loài có chân dung riêng** (ảnh 720px WebP ~60KB/ảnh, game ~26MB khi đủ 300; 500 thì ~38MB quá nặng). Tiến độ: 78/300 (30 gốc + đợt 0: 24 loài nổi tiếng + đợt 1: 24 loài). Các đợt sau tiếp tục bổ sung dần tới 300, ưu tiên loài nổi tiếng và hay gặp trên map.

- Logic tiến hoá theo công thức Sơn Hải Kinh (18/11/2026, user yêu cầu): tiến hoá không còn tính thuần theo số lần gộp — mỗi cấp dị thú có "công thức bộ phận" đối chiếu mô tả gốc, khớp theo phân loại NCBI thật (lớp/bộ/họ + cờ rắn Serpentes, trích từ taxdump vào `data/species_taxonomy.json`, pack v3): Nhĩ Thử = Rodentia + Lagomorpha; Cửu Vĩ Hồ = 2 Canidae; Tất Phương = Aves + săn tại Chương Nga; Cùng Kỳ = Felidae + Aves; Tương Liễu = 3 loài rắn; Đế Giang = 2 Aves + Insecta; Chúc Long = rắn + Primates; Ứng Long = cá + Bovidae + rắn + chim săn mồi + Aves (đúng ví dụ của user: vảy cá, sừng trâu, thân rắn). Panel tiến hoá hiện checklist bộ phận + nút 🎯 Tìm loài cho bộ phận thiếu; gợi ý săn gắn huy hiệu 🧩 cho loài cho bộ phận đang thiếu. Tiến trình cũ được migrate (absorbed → log).
- Chế độ LIVE (18/11/2026): nút 🔴 LIVE — vòng bình chọn 10 giây, khán giả gõ Săn/Chạy (mỗi tài khoản 1 phiếu/vòng), hết giờ AI thực thi lệnh đông hơn (săn con yếu nhất / trốn map khác); thanh tỉ số + đếm ngược trên cùng cho stream. Nguồn bình luận: mô phỏng test, dán thủ công, hoặc cầu nối `live_bridge.py` (chạy trên máy streamer: YouTube API chính thức, TikTok qua TikTokLive không chính thức, Facebook Graph API, hoặc gõ trực tiếp) phục vụ tại 127.0.0.1:8787 — hướng dẫn ở LIVE_MODE.md. Đã smoke-test cầu nối OK.
- Sửa trùng hình + HUD gọn (18/11/2026, theo ảnh playtest của user): mỗi map tối đa 12 thẻ ở 12 vị trí riêng (7 loài nổi bật luân phiên + 5 loài thường), khi chọn loài lên map thì loại trừ trùng ảnh — không hai thẻ nào đang hiển thị dùng cùng một hình; gợi ý săn cũng khử trùng theo ảnh. HUD thu gọn còn tối đa 468px, tên loài dài tự cắt "…" một dòng để không che tên map.
- Nhiều người chơi online (18/11/2026): server `server/server.js` (Node + WebSocket, cổng 8788 phục vụ cả game lẫn realtime) — phòng theo 8 map, mỗi người vào được random 1 loài thật từ 31.189 loài, 8 NPC/map hồi sinh liên tục, săn NPC + săn lẫn nhau (PvP: kẻ thua −35 HP, chết thì tái sinh loài mới nhưng giữ số lần gộp), tiến hoá theo công thức bộ phận do server tính, thắng ở 40 lần gộp, sự kiện cả phòng (ai săn ai, ai tiến hoá) được phát cho mọi người. Client có nút 🌐 Online ở màn đăng nhập + HUD (thẻ người chơi viền vàng, bấm nền map để di chuyển, panel tiến hoá lấy từ server). Đã test tự động 2 client (vào phòng → đổi map → săn NPC → trốn): PASS; server phục vụ đúng bản game mới. Deploy: `server/Dockerfile` + hướng dẫn `MULTIPLAYER.md` — máy nhà + Cloudflare Tunnel miễn phí hợp nhất cho livestream theo phiên; Fly.io/Railway/VPS cho 24/7; sandbox của Muse không host được server công khai. Giới hạn: trạng thái lưu trong RAM (restart = chơi lại), chưa có tài khoản/mật khẩu.
