# Chế độ LIVE — khán giả điều khiển game bằng bình luận

Trong game **Sơn Hải Kinh Phiêu Lưu Ký**, bấm nút **🔴 LIVE** ở thanh trên:

- Mỗi vòng bình chọn kéo dài **10 giây**. Khán giả gõ **«Săn»** hoặc **«Chạy»**
  (không dấu cũng được: `san`, `chay`, `tron`).
- Mỗi tài khoản tính **1 phiếu** trong một vòng. Hết giờ, lệnh nào nhiều hơn
  được **AI thực thi ngay**: Săn → AI săn con mồi yếu nhất trên map;
  Chạy → AI trốn sang map ngẫu nhiên khác. Hòa hoặc không có phiếu → AI chờ vòng sau.
- Thanh LIVE đỏ trên cùng màn hình hiện đếm ngược + tỉ số phiếu theo thời gian thực,
  thiết kế để khán giả xem stream nhìn rõ.

## 3 cách đưa bình luận vào game

### 1. Mô phỏng (test thử, không cần tài khoản)
Tick **🎭 Mô phỏng bình luận** trong panel LIVE — game tự sinh bình luận giả
để bạn kiểm tra giao diện và nhịp vòng.

### 2. Dán thủ công
Copy bình luận từ bất kỳ đâu, dán vào ô trong panel LIVE (mỗi dòng một bình luận,
có dạng `Tên: nội dung` thì càng tốt) rồi bấm **Nạp bình luận đã dán**.

### 3. Cầu nối chat thật (TikTok / YouTube / Facebook)
Game là một file HTML tĩnh nên không thể tự đọc chat của các nền tảng
(họ yêu cầu API key/token và quyền truy cập). Chạy chương trình cầu nối
`live_bridge.py` **trên máy của bạn** — nó kết nối bằng chính tài khoản/API
của bạn và đưa bình luận vào game qua địa chỉ cục bộ `http://127.0.0.1:8787`.

```bash
cd genechain-merkle-dag
python3 live_bridge.py
```

Trong game: tick **🌉 Cầu nối chat thật**, giữ nguyên địa chỉ
`http://127.0.0.1:8787`, bấm **🔴 LIVE**.

Thiết lập theo nền tảng (đặt biến môi trường trước khi chạy cầu nối):

- **YouTube (API chính thức):** tạo API key ở Google Cloud (YouTube Data API v3),
  lấy `liveChatId` của buổi stream, rồi:
  `YT_API_KEY=... YT_LIVE_CHAT_ID=... python3 live_bridge.py`
- **TikTok:** `pip install TikTokLive` (thư viện **không chính thức**, có thể
  hỏng khi TikTok đổi giao thức), rồi:
  `TIKTOK_USER=@tenkenh python3 live_bridge.py`
- **Facebook:** cần Page Access Token của fanpage và ID của video live, rồi:
  `FB_PAGE_TOKEN=... FB_LIVE_VIDEO_ID=... python3 live_bridge.py`
  (một số quyền có thể cần app được Facebook duyệt.)
- **Mọi nền tảng khác / dự phòng:** gõ hoặc dán bình luận trực tiếp vào cửa sổ
  của cầu nối — mỗi dòng được tính là một bình luận.

Lưu ý: cầu nối chỉ chạy trên máy của bạn và chỉ bạn mới truy cập được
(127.0.0.1). Token/API key nằm ở máy bạn, không đi vào file game.
