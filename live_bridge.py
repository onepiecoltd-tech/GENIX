#!/usr/bin/env python3
"""Cau noi chat LIVE cho game Son Hai Kinh Phieu Luu Ky.

Game (file HTML) khong the tu doc binh luan TikTok/YouTube/Facebook vi cac nen
tang nay yeu cau API key / token / duyet ung dung. Chuong trinh nay chay tren
MAY CUA NGUOI STREAM, ket noi toi cac phong chat bang tai khoa/API cua chinh
ho, roi phuc vu binh luan qua HTTP cuc bo de game doc:

    GET http://127.0.0.1:8787/votes?since=<ms>
    -> {"votes": [{"user": "...", "text": "...", "ts": 1234567890}], "now": ...}

Cach chay:
    python3 live_bridge.py

Nguon binh luan (bat cai nao dung cai do, doc LIVE_MODE.md de biet chi tiet):
  - Ban phim: go truc tiep vao cua so nay, moi dong la mot binh luan
    (dinh dang "Ten: noi dung" hoac chi noi dung).
  - YouTube (API chinh thuc): dat bien moi truong YT_API_KEY va YT_LIVE_CHAT_ID.
  - TikTok (thu vien khong chinh thuc TikTokLive): dat TIKTOK_USER=@kenh.
  - Facebook (Graph API): dat FB_PAGE_TOKEN va FB_LIVE_VIDEO_ID.

Chi dung thu vien chuan cua Python cho HTTP server; cac ket noi nen tang dung
urllib, rieng TikTok can cai them: pip install TikTokLive
"""
import json
import os
import sys
import threading
import time
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HOST, PORT = "127.0.0.1", 8787
_lock = threading.Lock()
_votes = []  # [{user, text, ts}] ts = milliseconds


def add_vote(user, text):
    text = (text or "").strip()
    if not text:
        return
    with _lock:
        _votes.append({"user": str(user)[:40], "text": text[:200],
                       "ts": int(time.time() * 1000)})
        del _votes[:-2000]
    print(f"  [vote] {user}: {text}")


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/votes":
            try:
                since = float(urllib.parse.parse_qs(parsed.query).get("since", [0])[0])
            except ValueError:
                since = 0
            with _lock:
                out = [v for v in _votes if v["ts"] > since]
            body = json.dumps({"votes": out, "now": int(time.time() * 1000)}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif parsed.path == "/health":
            body = b'{"ok": true}'
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, *args):
        pass


def _get_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "shk-live-bridge/1.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


def youtube_thread():
    key = os.environ.get("YT_API_KEY")
    chat_id = os.environ.get("YT_LIVE_CHAT_ID")
    if not key or not chat_id:
        return
    print("[YouTube] Dang nghe chat cua live chat id:", chat_id)
    token = None
    while True:
        try:
            q = {"liveChatId": chat_id, "part": "snippet,authorDetails", "key": key}
            if token:
                q["pageToken"] = token
            url = "https://www.googleapis.com/youtube/v3/liveChat/messages?" + urllib.parse.urlencode(q)
            data = _get_json(url)
            for item in data.get("items", []):
                sn = item.get("snippet", {})
                if sn.get("type") == "textMessageEvent":
                    add_vote(item.get("authorDetails", {}).get("displayName", "YouTube"),
                             sn.get("textMessageDetails", {}).get("messageText", ""))
            token = data.get("nextPageToken")
            wait = max(2.0, data.get("pollingIntervalMillis", 5000) / 1000.0)
        except Exception as e:  # noqa: BLE001 - cau noi khong duoc chet vi loi mang
            print("[YouTube] Loi:", e)
            wait = 10.0
        time.sleep(wait)


def facebook_thread():
    token = os.environ.get("FB_PAGE_TOKEN")
    video = os.environ.get("FB_LIVE_VIDEO_ID")
    if not token or not video:
        return
    print("[Facebook] Dang nghe binh luan cua live video id:", video)
    seen = set()
    while True:
        try:
            url = ("https://graph.facebook.com/v19.0/" + urllib.parse.quote(video)
                   + "/comments?fields=from{name},message,created_time&limit=50&order=reverse_chronological"
                   + "&access_token=" + urllib.parse.quote(token))
            data = _get_json(url)
            for c in reversed(data.get("data", [])):
                if c.get("id") in seen:
                    continue
                seen.add(c.get("id"))
                add_vote((c.get("from") or {}).get("name", "Facebook"), c.get("message", ""))
        except Exception as e:  # noqa: BLE001
            print("[Facebook] Loi:", e)
        time.sleep(5)


def tiktok_thread():
    user = os.environ.get("TIKTOK_USER")
    if not user:
        return
    try:
        from TikTokLive import TikTokLiveClient  # type: ignore
        from TikTokLive.events import CommentEvent  # type: ignore
    except Exception:
        print("[TikTok] Chua cai thu vien TikTokLive. Cai bang: pip install TikTokLive")
        return
    print("[TikTok] Dang nghe phong live cua:", user)
    client = TikTokLiveClient(unique_id=user)

    @client.on(CommentEvent)
    async def _on_comment(event):
        add_vote(event.user.nickname or event.user.unique_id, event.comment)

    try:
        client.run()
    except Exception as e:  # noqa: BLE001
        print("[TikTok] Loi:", e)


def stdin_thread():
    print("[Ban phim] Go binh luan vao day (moi dong mot binh luan), Ctrl+C de thoat.")
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        if ":" in line and len(line.split(":", 1)[0]) <= 30:
            u, t = line.split(":", 1)
            add_vote(u.strip(), t.strip())
        else:
            add_vote("console", line)


def main():
    for fn in (youtube_thread, facebook_thread, tiktok_thread):
        threading.Thread(target=fn, daemon=True).start()
    threading.Thread(target=stdin_thread, daemon=True).start()
    srv = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"Cau noi LIVE dang chay tai http://{HOST}:{PORT} — mo game, bat LIVE va tick 'Cau noi chat that'.")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nDa dung cau noi.")


if __name__ == "__main__":
    main()
