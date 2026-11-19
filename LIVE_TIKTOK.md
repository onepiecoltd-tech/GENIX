# Live TikTok + AI "Thiên Đạo" (v6.2)

## Chạy nhanh (Windows)
1. Cài Node.js 20+ và Python 3 (và `cloudflared` nếu muốn khán giả vào chơi cùng).
2. Chạy `start_live.bat` lần đầu → tạo `live.env` → điền `TIKTOK_USER=@kênh` và `ANTHROPIC_API_KEY=...` → chạy lại.
3. Trong game: bấm **🔴 LIVE** → tick **🌉 Cầu nối chat thật**. Dòng "AI Thiên Đạo: Claude (…) ✓" nghĩa là AI đã nối.
4. Đưa cửa sổ game lên TikTok bằng LIVE Studio / OBS (khung dọc 9:16). Khóa API chỉ nằm trên máy bạn (`live.env` đã .gitignore).
Test không cần TikTok: `SIMULATE=1 python3 live_bridge.py` (tự sinh bình luận/quà/tim/follow giả).

## Luồng dữ liệu
TikTok → `live_bridge.py` (chuẩn hoá sự kiện) → game đọc `/poll` → game gửi ảnh chụp trạng thái `/state`
→ mỗi 10s bridge hỏi Claude → hành động đã lọc → game thực thi + hiện lời bình (và đọc thành tiếng nếu bật).

## Khán giả tương tác
| Sự kiện | Tác động |
|---|---|
| Bình luận `săn` / `chạy` | Bỏ phiếu mỗi 10s (như cũ) |
| `map thiên sơn` / `đi linh sơn` | Bỏ phiếu đổi map — thắng nếu ≥2 người và hơn số phiếu săn/chạy |
| `loài hổ` | Gợi ý con mồi cho lần săn kế (chỉ nhận loài có trên map và hạ được) |
| Bình luận khác | Hiện ở bảng tin; AI đọc và có thể trả lời |
| Thả tim | Nạp thanh Linh khí; đầy → +30 sinh lực |
| Follow | Một sinh linh mang tên người đó xuất hiện trên map (săn được) |
| Share | +5 sinh lực + bảng tin |
| Quà < 10 xu / 10–99 / ≥100 | +15 sinh lực / lực +20% trong 60s / Hộ pháp (boss vừa sức) xuất hiện |
| Vào phòng | Bảng tin (AI có thể chào) |

## AI Thiên Đạo — an toàn
- Chỉ trả lời bằng công cụ `thien_dao_act` với **hành động trong danh sách cố định**: `say` (≤2 câu, ≤140 ký tự), `command` (hunt/flee/travel tới 1 trong 8 map), `world_event` (rain_linh_khi / blessing / storm / boss, cooldown 180s).
- Bình luận khán giả được gói trong thẻ `<khan_gia>` và luôn coi là **dữ liệu không tin cậy**; đầu ra AI được bridge lọc lại (bỏ trường lạ, cắt độ dài, che link, che từ cấm — thêm từ qua `BAD_WORDS`).
- `command` của AI chỉ có tác dụng khi khán giả **không** ra lệnh rõ ràng trong vòng đó (AI lái lúc vắng phiếu); khán giả luôn có quyền quyết.
- Hạn mức: tối đa `AI_MAX_CALLS_PER_HOUR` lần gọi/giờ; live vắng thì 1 lượt/45s. Lỗi mạng/AI → tự chuyển sang luật có sẵn (cảm ơn quà/follow bằng mẫu câu).
- Không có `ANTHROPIC_API_KEY` → chạy luật có sẵn, mọi tương tác game vẫn hoạt động.

## Hai nguồn AI: API key (chính) và usage Claude Pro (phụ, có nút bật/tắt)
| Nút ⚡ "Dùng usage Claude Pro" | Thứ tự dùng |
|---|---|
| **Tắt** (mặc định) | API key → luật có sẵn |
| **Bật** | `claude` (usage gói Pro) → hết usage/lỗi tự chuyển **API key** → luật có sẵn |

- Nút nằm cạnh ô chọn cầu nối trong game (hoặc đặt `AI_USE_USAGE=1` trong `live.env`). Dòng trạng thái cho biết đang dùng nguồn nào, ví dụ `Claude Pro usage (haiku) ✓` hoặc `hết usage Claude Pro → đã chuyển sang API key`.
- Cần cài Claude Code và đăng nhập sẵn (chạy `claude` một lần trong terminal). Bridge gọi `claude -p` với **toàn bộ công cụ tắt**, không nạp MCP, không lưu phiên, chạy trong thư mục tạm rỗng; tin nhắn gửi qua stdin. `ANTHROPIC_API_KEY` bị **gỡ khỏi môi trường tiến trình con** (nếu để lại, Claude Code sẽ tính tiền API thay vì usage).
- Hết usage: bridge đọc thời điểm reset nếu `claude` báo, không thì thử lại sau 15 phút; bấm tắt/bật nút để thử lại ngay (ví dụ sau khi đăng nhập lại). Khi nút bật mà CLI đang chờ nhịp (`CLI_MIN_GAP`, mặc định 20s) bridge **chờ**, không đốt API key.
- Chậm hơn API (mỗi lượt khởi động một tiến trình), và live dài có thể chạm hạn mức 5 giờ của gói. Đầu ra vẫn qua cùng bộ lọc danh sách cố định như API.
- Dùng chương trình tự động gọi `claude` bằng đăng nhập gói Pro: bạn nên tự đọc lại điều khoản gói của Anthropic cho phù hợp mục đích dùng.

## Giới hạn (nói thẳng)
- Backend usage (`claude -p`) mới chỉ test với `claude` giả, **chưa chạy với Claude Code đã đăng nhập thật**: cần thử một lượt trước khi live (mở terminal, gõ `claude -p "xin chào"` xem có trả lời không).
- Thư viện **TikTokLive không chính thức**: có thể hỏng khi TikTok đổi giao thức, và dùng nó là rủi ro với điều khoản TikTok. Luôn có cách dự phòng: dán bình luận / gõ `/gift Rose 5`, `/follow tên`, `/like 20` vào cửa sổ bridge.
- Hiệu ứng quà/tim/follow/sự kiện thế giới chạy ở **chế độ chơi đơn của streamer** (LIVE). Chế độ online nhiều người chỉ nhận lời bình/lệnh, vì trạng thái ở đó do server quyết định.
- Quà tặng chỉ gắn với hiệu ứng vui trong game; không hứa lợi thế thắng-thua hay giá trị quy đổi.
- `start_live.bat` chưa được chạy thử trên Windows thật (môi trường build là Linux) — nếu lỗi ở bước tunnel, chạy `cloudflared tunnel --url http://127.0.0.1:8788` thủ công.
- Tham số quà (xu/ngưỡng) lấy từ `diamond_count` của TikTok; ngưỡng 10/100 chỉnh ở `giftEffect()` trong `game/shk_template.html`.
