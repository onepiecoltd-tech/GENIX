# SƠN HẢI KINH PHIÊU LƯU KÝ — CHẾ ĐỘ NHIỀU NGƯỜI CHƠI (ONLINE)

Server ở `server/server.js` (Node.js + WebSocket). Một cổng duy nhất phục vụ cả
file game lẫn kết nối realtime: người chơi mở trang game là vào thẳng thế giới
chung, không cần cài thêm gì.

## Cách chơi online hoạt động

- Mỗi khán giả mở link game → bấm **🌐 Chơi online nhiều người** → nhập tên →
  server **random cho họ đúng 1 loài thật** trong registry 31.189 loài
  (đúng luật bản chơi đơn), đặt vào map quê hương của loài đó.
- Phòng chơi = 8 map Sơn Hải Kinh. Trong mỗi map có **8 sinh linh hoang dã
  (NPC)** sinh ra liên tục từ dữ liệu thật của map đó + tất cả người chơi
  đang ở map.
- Bấm vào một thẻ để **Săn** (NPC hoặc người chơi khác — server tính lực từ
  số block gen thật, kẻ thua mất sinh lực, chết thì tái sinh thành loài mới
  nhưng giữ nguyên số lần gộp), bấm nền map để **di chuyển**, bấm nút map để
  **sang map khác**, hoặc **Trốn** để nhảy sang map ngẫu nhiên.
- Tiến hoá theo đúng công thức bộ phận Sơn Hải Kinh như bản chơi đơn
  (server tính bằng phân loại học thật: họ Chó, họ Mèo, rắn, Bovidae...),
  thắng khi gộp đủ 40 loài. Mọi sự kiện (ai săn ai, ai tiến hoá) được thông
  báo cho cả phòng.
- Kết hợp với chế độ LIVE: streamer vừa livestream TikTok/YouTube/Facebook,
  khán giả vừa mở link vào chơi cùng, bình luận vẫn điều khiển nhân vật của
  streamer như cũ.

## Chạy thử trên máy của bạn (miễn phí, hợp nhất khi livestream)

Yêu cầu: Node.js 20+.

```
cd server
npm install
npm start          # http://127.0.0.1:8788
```

Mở http://127.0.0.1:8788 trên trình duyệt để chơi thử. Kiểm tra tự động:
`node test_client.js` (2 người chơi giả lập: vào phòng, đổi map, săn, trốn).

Để khán giả vào được từ internet khi bạn livestream, dùng **Cloudflare
Tunnel** (miễn phí, không cần mở cổng modem):

```
cloudflared tunnel --url http://127.0.0.1:8788
```

Lệnh này cho ra một link `https://....trycloudflare.com` — dán link đó lên
livestream, khán giả mở là chơi. Tắt máy/tắt tunnel thì phòng đóng (phù hợp
kiểu chơi theo phiên live).

## Deploy 24/7 (phòng mở cả khi bạn tắt máy)

Có sẵn `server/Dockerfile` (build từ thư mục gốc dự án):

```
docker build -f server/Dockerfile -t shk-server .
docker run -d -p 8788:8788 shk-server
```

Nơi deploy gợi ý:

| Nơi | Giá tham khảo | Ghi chú |
|---|---|---|
| Máy của bạn + Cloudflare Tunnel | 0đ | Hợp nhất cho livestream theo phiên |
| Fly.io | ~2–5 USD/tháng | Có sẵn Dockerfile, `fly launch` là xong, ngủ khi không ai chơi |
| Railway | ~5 USD/tháng | Dễ nhất: nối repo GitHub GENIX, chọn Dockerfile |
| VPS (Hetzner/DigitalOcean) | ~4–6 USD/tháng | Toàn quyền kiểm soát, chạy Docker như trên |
| Oracle Cloud Always Free | 0đ | Miễn phí 24/7 nhưng đăng ký khó (cần thẻ quốc tế) |
| Render bản free | 0đ | Server ngủ sau 15 phút không dùng — không hợp chơi live |

Lưu ý: sandbox của Muse **không** host được server công khai (không có
đường vào từ internet), nên server phải chạy trên máy của bạn hoặc một trong
các nền tảng trên.

## Giới hạn hiện tại (nói thẳng)

- **Chơi theo phiên live, không lưu người chơi** (chủ dự án chốt
  18/11/2026): trạng thái chỉ nằm trong RAM của server — tắt server hoặc hết
  phiên live là xoá sạch, phiên sau mọi người được random loài mới từ đầu.
  Không tài khoản, không mật khẩu, không cơ sở dữ liệu người chơi; khán giả
  chỉ cần nhập tên hiển thị.
- Một tiến trình server phục vụ tốt vài trăm người chơi đồng thời; đông hơn
  nữa cần tách phòng/load balancer (chưa làm).
- Dữ liệu loài là dữ liệu thật của GeneChain (31.189 loài động–thực vật);
  nấm sẽ tự có mặt khi registry nấm nạp xong và đóng gói lại dữ liệu game.
