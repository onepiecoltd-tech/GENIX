#!/usr/bin/env node
/* Server nhieu nguoi choi — Son Hai Kinh Phieu Luu Ky.
   - HTTP: phuc vu file game tai / (game/son-hai-kinh-phieu-luu-ky.html)
   - WebSocket (cung cong): phong theo 8 map Son Hai Kinh, moi nguoi choi duoc
     random 1 loai that tu registry 31.189 loai, san NPC va san lan nhau,
     tien hoa theo cong thuc bo phan Son Hai Kinh (giong ban choi don).
   Chay: npm install && npm start   (cong mac dinh 8788, doi bang bien PORT)
*/
"use strict";
const http = require("http");
const fs = require("fs");
const path = require("path");
const { WebSocketServer } = require("ws");

const ROOT = path.join(__dirname, "..");
const PORT = process.env.PORT || 8788;
const WIN_MERGES = 40;

/* ===== Chong gian lan / lam dung (v6.1) ===== */
const MAX_PLAYERS = +process.env.MAX_PLAYERS || 300;
const MAX_CONN_PER_IP = +process.env.MAX_CONN_PER_IP || 4;
const TRUST_PROXY = process.env.TRUST_PROXY === "1";          // bat khi chay sau Cloudflare Tunnel/nginx
const ALLOWED_ORIGINS = (process.env.ALLOWED_ORIGINS || "").split(",").map(x => x.trim()).filter(Boolean);
const COOLDOWN = { hunt: 1500, travel: 2000, flee: 3000, chat: 1500 };   // ms
const PVP_IMMUNE_MS = 10000;      // nan nhan duoc mien san sau khi bi san / tai sinh
const PVP_PAIR_MS = 60000;        // cung 1 cap san - bi san: toi da 1 lan / phut
const PVP_GLOBAL_MS = 8000;       // moi nguoi: toi da 1 lan gop gen tu PvP / 8 giay
const REF_BONUS = 50, REF_JOIN_BONUS = 25, REF_MAX = 10;

function clean(s, max) {
  return Array.from(String(s == null ? "" : s))
    .filter(ch => ch >= " " && ch !== "\u007f" && !"<>&\"'`".includes(ch))
    .join("").replace(/\s+/g, " ").trim().slice(0, max);
}
const now = () => Date.now();
const ipCount = new Map();
function ipOf(req) {
  if (TRUST_PROXY) {
    const h = req.headers["cf-connecting-ip"] || (req.headers["x-forwarded-for"] || "").split(",")[0];
    if (h && h.trim()) return h.trim();
  }
  return req.socket.remoteAddress || "?";
}
function originOk(req) {
  const o = req.headers.origin;
  if (!o) return true;                                   // client khong phai trinh duyet (test, tool)
  if (ALLOWED_ORIGINS.length) return ALLOWED_ORIGINS.includes(o);
  try { return new URL(o).host === req.headers.host; } catch (e) { return false; }
}
const refCodes = new Map();                              // refCode -> player
const refIpSeen = new Set();                             // moi IP chi duoc tinh 1 luot gioi thieu
function newRefCode() {
  for (;;) {
    const c = Math.random().toString(36).slice(2, 8).toUpperCase();
    if (c.length === 6 && !refCodes.has(c)) return c;
  }
}

const pack = JSON.parse(fs.readFileSync(path.join(ROOT, "data/game_species_all.json"), "utf8"));
const shk = JSON.parse(fs.readFileSync(path.join(ROOT, "data/shk_data.json"), "utf8"));
const NAMES = JSON.parse(fs.readFileSync(path.join(ROOT, "data/server_names.json"), "utf8"));
const ROWS = pack.species;
const BYID = {}; ROWS.forEach(r => { BYID[r[0]] = r; });
const BYBUCKET = {}; ROWS.forEach(r => { (BYBUCKET[r[2]] = BYBUCKET[r[2]] || []).push(r); });
const MAPS = shk.maps;
const MAPBY = {}; MAPS.forEach(m => { MAPBY[m.id] = m; });

const powerOf = b => Math.round(30 * Math.pow(Math.max(b, 1) / 1000, 0.55));
function creatureOf(t) {
  const r = BYID[t]; if (!r) return null;
  const n = NAMES[t];
  return { taxid: t, disp: n ? n.vn : r[1], sci: r[1], bucket: r[2], genes: r[3],
           blocks: r[4], cls: r[5], ord: r[6], fam: r[7], snake: !!r[8], group: n ? n.g : null };
}

/* ===== Cong thuc tien hoa (khop ban choi don) ===== */
const RAPTORS = ["Accipitriformes", "Falconiformes", "Strigiformes"];
const RECIPES = {
  1: { merges: 2, parts: [
    { label: "Thân chuột", need: 1, hint: "một loài gặm nhấm (bộ Rodentia)", test: c => c.ord === "Rodentia" },
    { label: "Đầu thỏ", need: 1, hint: "một loài thỏ (bộ Lagomorpha)", test: c => c.ord === "Lagomorpha" } ] },
  2: { merges: 5, parts: [
    { label: "Huyết mạch cáo", need: 2, hint: "2 loài họ Chó (Canidae)", test: c => c.fam === "Canidae" } ] },
  3: { merges: 9, parts: [
    { label: "Thân chim", need: 1, hint: "một loài chim (lớp Aves)", test: c => c.cls === "Aves" },
    { label: "Lửa Chương Nga", need: 1, hint: "săn 1 loài ngay tại Chương Nga Sơn", mapPart: "chuong-nga", test: () => false } ] },
  4: { merges: 13, parts: [
    { label: "Thân hổ", need: 1, hint: "một loài họ Mèo (Felidae)", test: c => c.fam === "Felidae" },
    { label: "Cánh chim", need: 1, hint: "một loài chim (lớp Aves)", test: c => c.cls === "Aves" } ] },
  5: { merges: 17, parts: [
    { label: "Chín đầu rắn", need: 3, hint: "3 loài rắn khác nhau", test: c => !!c.snake } ] },
  6: { merges: 21, parts: [
    { label: "Bốn cánh", need: 2, hint: "2 loài chim", test: c => c.cls === "Aves" },
    { label: "Sáu chân", need: 1, hint: "một loài côn trùng (lớp Insecta)", test: c => c.cls === "Insecta" } ] },
  7: { merges: 25, parts: [
    { label: "Thân rắn", need: 1, hint: "một loài rắn", test: c => !!c.snake },
    { label: "Mặt người", need: 1, hint: "một loài linh trưởng (bộ Primates)", test: c => c.ord === "Primates" } ] },
  8: { merges: 30, parts: [
    { label: "Vảy cá", need: 1, hint: "một loài cá", test: c => c.cls === "Actinopteri" || c.cls === "Chondrichthyes" },
    { label: "Sừng trâu", need: 1, hint: "một loài họ Trâu bò (Bovidae)", test: c => c.fam === "Bovidae" },
    { label: "Thân rắn", need: 1, hint: "một loài rắn", test: c => !!c.snake },
    { label: "Vuốt ưng", need: 1, hint: "một loài chim săn mồi", test: c => RAPTORS.includes(c.ord) },
    { label: "Cánh rồng", need: 1, hint: "một loài chim (lớp Aves)", test: c => c.cls === "Aves" } ] }
};
function partCount(p, pl) {
  if (p.mapPart) return pl.log.filter(e => e.map === p.mapPart).length;
  return pl.log.map(e => creatureOf(e.t)).filter(Boolean).filter(p.test).length;
}
function stageOf(pl) {
  let s = 0;
  while (s < 8) {
    const R = RECIPES[s + 1];
    if (pl.merges < R.merges || !R.parts.every(p => partCount(p, pl) >= p.need)) break;
    s++;
  }
  return s;
}
function partsProgress(pl) {
  const s = stageOf(pl);
  if (s >= 8) return { stage: s, next: null, parts: [] };
  const R = RECIPES[s + 1];
  const beast = shk.beasts.find(b => b.stage === s + 1);
  return { stage: s, next: beast ? beast.name : "", mergesNeed: R.merges,
           parts: R.parts.map(p => { const n = partCount(p, pl);
             return { label: p.label, hint: p.hint, n: Math.min(n, p.need), need: p.need, ok: n >= p.need }; }) };
}

/* ===== Phong theo map + NPC ===== */
const rooms = {};
MAPS.forEach(m => { rooms[m.id] = { map: m, players: new Map(), npcs: new Map(), seq: 1 }; });
function spawnNpc(room) {
  const pool = [];
  room.map.buckets.forEach(b => { if (BYBUCKET[b]) pool.push(...BYBUCKET[b]); });
  if (!pool.length) return;
  const r = pool[Math.floor(Math.random() * pool.length)];
  const id = "n" + room.seq++;
  room.npcs.set(id, { id, taxid: r[0], x: 6 + Math.random() * 86, y: 16 + Math.random() * 64 });
}
MAPS.forEach(m => { for (let i = 0; i < 8; i++) spawnNpc(rooms[m.id]); });

function homeMapOf(taxid) {
  const m = MAPS.find(mm => mm.featured.includes(taxid));
  if (m) return m.id;
  const bucket = BYID[taxid][2];
  const ms = MAPS.filter(mm => mm.buckets.includes(bucket));
  return (ms[0] || MAPS[0]).id;
}
const effPower = pl => powerOf(creatureOf(pl.taxid).blocks) + pl.bonus;

let pidSeq = 1;
function newPlayer(ws, name) {
  const taxid = ROWS[Math.floor(Math.random() * ROWS.length)][0];
  const pl = { id: "p" + pidSeq++, name: String(name || "Khách").slice(0, 24), taxid,
               map: homeMapOf(taxid), x: 30 + Math.random() * 40, y: 45 + Math.random() * 25,
               hp: 100, bonus: 0, merges: 0, kills: 0, absorbed: [], log: [], won: false, ws,
               gx: 0, refs: 0, refCode: newRefCode(), immuneUntil: 0, lastPvp: 0, hitBy: new Map(), cd: {} };
  refCodes.set(pl.refCode, pl);
  rooms[pl.map].players.set(pl.id, pl);
  return pl;
}
function moveRoom(pl, destId) {
  rooms[pl.map].players.delete(pl.id);
  pl.map = destId;
  pl.x = 30 + Math.random() * 40; pl.y = 45 + Math.random() * 25;
  rooms[destId].players.set(pl.id, pl);
}
function publicPlayer(pl) {
  const c = creatureOf(pl.taxid);
  return { id: pl.id, name: pl.name, taxid: pl.taxid, disp: c.disp, sci: c.sci,
           x: Math.round(pl.x), y: Math.round(pl.y), hp: pl.hp,
           power: effPower(pl), stage: stageOf(pl), merges: pl.merges };
}
function publicNpc(n) {
  const c = creatureOf(n.taxid);
  return { id: n.id, taxid: n.taxid, disp: c.disp, sci: c.sci,
           x: Math.round(n.x), y: Math.round(n.y), power: powerOf(c.blocks) };
}
function youPayload(pl) {
  const c = creatureOf(pl.taxid);
  return { id: pl.id, taxid: pl.taxid, disp: c.disp, sci: c.sci, hp: pl.hp, merges: pl.merges,
           kills: pl.kills, power: effPower(pl), absorbed: pl.absorbed, gx: pl.gx, refCode: pl.refCode, refs: pl.refs,
           progress: partsProgress(pl), won: pl.won };
}
function send(pl, obj) { try { pl.ws.send(JSON.stringify(obj)); } catch (e) { /* da ngat */ } }
function roomEvent(room, text, exceptId) {
  room.players.forEach(p => { if (p.id !== exceptId) send(p, { type: "event", text }); });
}

function absorb(pl, taxid, room) {
  const before = stageOf(pl);
  pl.absorbed.push(taxid);
  pl.log.push({ t: taxid, map: room.map.id });
  pl.merges++; pl.kills++;
  pl.bonus += Math.round(powerOf(BYID[taxid][4]) * 0.3);
  pl.hp = Math.min(100, pl.hp + 10);
  pl.gx += 10;
  const after = stageOf(pl);
  if (after > before) {
    pl.gx += 100 * (after - before);
    send(pl, { type: "evo", stage: after });
    roomEvent(room, "🧬 " + pl.name + " vừa tiến hoá lên cấp " + after + "!", pl.id);
  }
  if (pl.merges >= WIN_MERGES && !pl.won) {
    pl.won = true; pl.gx += 300;
    send(pl, { type: "win" });
    roomEvent(room, "👑 " + pl.name + " đã đạt Ứng Long và hoàn thành hành trình " + WIN_MERGES + " lần gộp!", pl.id);
  }
}
function respawn(pl) {
  pl.taxid = ROWS[Math.floor(Math.random() * ROWS.length)][0];
  pl.hp = 100; pl.immuneUntil = now() + PVP_IMMUNE_MS;
  moveRoom(pl, homeMapOf(pl.taxid));
  send(pl, { type: "respawn", text: "Bạn tái sinh thành " + creatureOf(pl.taxid).disp + " (tiến trình gộp gen được giữ nguyên)" });
}
function doHunt(pl, targetId) {
  const room = rooms[pl.map];
  const mp = effPower(pl);
  if (room.npcs.has(targetId)) {
    const n = room.npcs.get(targetId);
    const c = creatureOf(n.taxid), tp = powerOf(c.blocks);
    if (mp >= tp) {
      room.npcs.delete(targetId);
      absorb(pl, n.taxid, room);
      send(pl, { type: "result", ok: true, text: "🧬 Đã gộp gen của " + c.disp + "!" });
      setTimeout(() => spawnNpc(room), 4000);
    } else {
      const dmg = 10 + Math.round(18 * (1 - mp / tp));
      pl.hp -= dmg;
      send(pl, { type: "result", ok: false, text: "💥 Săn hụt " + c.disp + " — bị thương -" + dmg + " sinh lực" });
      if (pl.hp <= 0) respawn(pl);
    }
    return;
  }
  const victim = room.players.get(targetId);
  if (victim && victim.id !== pl.id) {
    const t = now();
    if (t < victim.immuneUntil) { send(pl, { type: "result", ok: false, text: "🛡 " + victim.name + " đang được bảo hộ vài giây" }); return; }
    if (t - pl.lastPvp < PVP_GLOBAL_MS) { send(pl, { type: "result", ok: false, text: "⏳ Bạn vừa săn người chơi — chờ chút" }); return; }
    if (t - (pl.hitBy.get(victim.id) || 0) < PVP_PAIR_MS) { send(pl, { type: "result", ok: false, text: "⏳ Vừa săn " + victim.name + " xong — đổi mục tiêu khác" }); return; }
    pl.lastPvp = t; pl.hitBy.set(victim.id, t);
    if (pl.hitBy.size > 200) pl.hitBy.clear();
    victim.immuneUntil = t + PVP_IMMUNE_MS;
    const tp = effPower(victim);
    if (mp >= tp) {
      absorb(pl, victim.taxid, room);
      victim.hp -= 35;
      send(pl, { type: "result", ok: true, text: "⚔️ Đã hạ " + victim.name + " và gộp gen " + creatureOf(victim.taxid).disp + "!" });
      send(victim, { type: "result", ok: false, text: "💥 " + pl.name + " vừa săn bạn và lấy mất gen " + creatureOf(pl.taxid).disp + " (-35 sinh lực)" });
      roomEvent(room, "⚔️ " + pl.name + " vừa săn " + victim.name + "!", pl.id);
      if (victim.hp <= 0) respawn(victim);
    } else {
      const dmg = 10 + Math.round(18 * (1 - mp / tp));
      pl.hp -= dmg;
      send(pl, { type: "result", ok: false, text: "💥 Săn hụt " + victim.name + " (mạnh hơn bạn) — bị thương -" + dmg + " sinh lực" });
      if (pl.hp <= 0) respawn(pl);
    }
  }
}

/* ===== HTTP + WebSocket ===== */
const gameFile = path.join(ROOT, "game/son-hai-kinh-phieu-luu-ky.html");
const SEC_HEADERS = {
  "X-Content-Type-Options": "nosniff", "Referrer-Policy": "no-referrer", "X-Frame-Options": "DENY",
  "Content-Security-Policy": "default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; img-src data: blob:; " +
    "media-src data: blob:; font-src data:; connect-src 'self' ws: wss: http://127.0.0.1:8787 http://localhost:8787; " +
    "base-uri 'none'; form-action 'none'; frame-ancestors 'none'"
};
const server = http.createServer((req, res) => {
  Object.entries(SEC_HEADERS).forEach(([k, v]) => res.setHeader(k, v));
  const urlPath = req.url.split("?")[0];
  if (urlPath === "/health") { res.writeHead(200, { "Content-Type": "application/json" }); res.end('{"ok":true}'); return; }
  if (urlPath === "/" || urlPath.startsWith("/game")) {
    fs.readFile(gameFile, (err, buf) => {
      if (err) { res.writeHead(500); res.end("Chua build game"); return; }
      res.writeHead(200, { "Content-Type": "text/html; charset=utf-8" });
      res.end(buf);
    });
    return;
  }
  res.writeHead(404); res.end("Not found");
});
process.on("uncaughtException", e => console.error("uncaught:", e && e.message));
const wss = new WebSocketServer({
  server, maxPayload: 2048,
  verifyClient: (info, done) => {
    if (!originOk(info.req)) return done(false, 403, "Forbidden origin");
    const ip = ipOf(info.req);
    if ((ipCount.get(ip) || 0) >= MAX_CONN_PER_IP) return done(false, 429, "Too many connections");
    done(true);
  }
});
wss.on("connection", (ws, req) => {
  let pl = null;
  const ip = ipOf(req);
  ipCount.set(ip, (ipCount.get(ip) || 0) + 1);
  ws.on("error", () => {});                       // frame loi / qua lon: dong ket noi, khong sap server
  let tokens = 20, lastRefill = now(), strikes = 0, strikeT = now();
  const strike = () => {
    const t = now(); if (t - strikeT > 10000) { strikes = 0; strikeT = t; }
    if (++strikes > 40) { try { ws.close(1008, "rate limit"); } catch (e) {} }
  };
  ws.on("message", raw => {
    const t = now();
    tokens = Math.min(20, tokens + (t - lastRefill) / 100); lastRefill = t;   // 10 tin/giay, burst 20
    if (tokens < 1) { strike(); return; }
    tokens -= 1;
    let m; try { m = JSON.parse(raw); } catch (e) { return; }
    if (!m || typeof m !== "object") return;
    if (m.type !== "join" && m.type !== "move" && COOLDOWN[m.type]) {
      if (pl) {
        if (t - (pl.cd[m.type] || 0) < COOLDOWN[m.type]) { strike(); return; }
        pl.cd[m.type] = t;
      }
    }
    if (m.type === "join") {
      if (pl) return;                                              // chi duoc join 1 lan / ket noi
      if (wss.clients.size > MAX_PLAYERS) { send({ ws }, { type: "result", ok: false, text: "Phòng đã đầy" }); ws.close(); return; }
      pl = newPlayer(ws, clean(m.name, 24) || "Khách"); pl.ip = ip;
      const ref = refCodes.get(clean(m.ref, 8).toUpperCase());
      if (ref && ref !== pl && ref.ip !== ip && ref.refs < REF_MAX && !refIpSeen.has(ip)) {
        refIpSeen.add(ip); ref.refs++; ref.gx += REF_BONUS; pl.gx += REF_JOIN_BONUS;
        send(ref, { type: "event", text: "🎁 " + pl.name + " vào chơi qua mã của bạn: +" + REF_BONUS + " điểm GENIX" });
      }
      send(pl, { type: "welcome", you: youPayload(pl), map: pl.map,
                 maps: MAPS.map(x => ({ id: x.id, name: x.name, backdrop: x.backdrop })) });
      roomEvent(rooms[pl.map], "👋 " + pl.name + " (" + creatureOf(pl.taxid).disp + ") vừa vào " + MAPBY[pl.map].name, pl.id);
      return;
    }
    if (!pl) return;
    if (m.type === "move") {
      pl.x = Math.max(2, Math.min(96, +m.x || 50));
      pl.y = Math.max(10, Math.min(88, +m.y || 50));
    } else if (m.type === "hunt") {
      doHunt(pl, String(m.target || ""));
    } else if (m.type === "flee") {
      const others = MAPS.filter(x => x.id !== pl.map);
      const dest = others[Math.floor(Math.random() * others.length)];
      moveRoom(pl, dest.id);
      send(pl, { type: "result", ok: true, text: "🏃 Bạn đã trốn sang " + dest.name });
    } else if (m.type === "travel") {
      if (MAPBY[m.map] && m.map !== pl.map) {
        moveRoom(pl, m.map);
        send(pl, { type: "result", ok: true, text: "🗺 Đã tới " + MAPBY[m.map].name });
      }
    } else if (m.type === "chat") {
      const txt = clean(m.text, 120); if (txt) roomEvent(rooms[pl.map], "💬 " + pl.name + ": " + txt, pl.id);
    }
  });
  ws.on("close", () => {
    ipCount.set(ip, Math.max(0, (ipCount.get(ip) || 1) - 1));
    if (pl) {
      refCodes.delete(pl.refCode);
      rooms[pl.map].players.delete(pl.id);
      roomEvent(rooms[pl.map], "👋 " + pl.name + " đã rời phòng", pl.id);
    }
  });
});
setInterval(() => {
  Object.values(rooms).forEach(room => {
    if (!room.players.size) return;
    const players = [...room.players.values()].map(publicPlayer);
    const npcs = [...room.npcs.values()].map(publicNpc);
    room.players.forEach(pl => send(pl, { type: "state", map: room.map.id, you: youPayload(pl), players, npcs }));
  });
}, 300);
setInterval(() => {
  const all = [];
  Object.values(rooms).forEach(r => r.players.forEach(p => all.push(p)));
  if (!all.length) return;
  const top = all.sort((a, b) => b.merges - a.merges || b.kills - a.kills).slice(0, 10)
    .map(p => ({ name: p.name, merges: p.merges, stage: stageOf(p), disp: creatureOf(p.taxid).disp }));
  all.forEach(p => send(p, { type: "board", top, online: all.length }));
}, 3000);
server.listen(PORT, () => console.log("Server Son Hai Kinh dang chay: http://127.0.0.1:" + PORT + " (game + WebSocket)"));
