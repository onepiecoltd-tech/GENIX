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
               hp: 100, bonus: 0, merges: 0, kills: 0, absorbed: [], log: [], won: false, ws };
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
           kills: pl.kills, power: effPower(pl), absorbed: pl.absorbed,
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
  const after = stageOf(pl);
  if (after > before) {
    send(pl, { type: "evo", stage: after });
    roomEvent(room, "🧬 " + pl.name + " vừa tiến hoá lên cấp " + after + "!", pl.id);
  }
  if (pl.merges >= WIN_MERGES && !pl.won) {
    pl.won = true;
    send(pl, { type: "win" });
    roomEvent(room, "👑 " + pl.name + " đã đạt Ứng Long và hoàn thành hành trình " + WIN_MERGES + " lần gộp!", pl.id);
  }
}
function respawn(pl) {
  pl.taxid = ROWS[Math.floor(Math.random() * ROWS.length)][0];
  pl.hp = 100;
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
const server = http.createServer((req, res) => {
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
const wss = new WebSocketServer({ server });
wss.on("connection", ws => {
  let pl = null;
  ws.on("message", raw => {
    let m; try { m = JSON.parse(raw); } catch (e) { return; }
    if (m.type === "join") {
      pl = newPlayer(ws, m.name);
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
      roomEvent(rooms[pl.map], "💬 " + pl.name + ": " + String(m.text || "").slice(0, 120), pl.id);
    }
  });
  ws.on("close", () => {
    if (pl) {
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
server.listen(PORT, () => console.log("Server Son Hai Kinh dang chay: http://127.0.0.1:" + PORT + " (game + WebSocket)"));
