/* Test chong gian lan / lam dung. Chay server voi TRUST_PROXY=1 (de gia lap nhieu IP), roi:
   TRUST_PROXY=1 PORT=8799 node server.js &  WS_URL=ws://127.0.0.1:8799 node test_security.js */
const WebSocket = require("ws");
const URL_ = process.env.WS_URL || "ws://127.0.0.1:8799";
const sleep = ms => new Promise(r => setTimeout(r, ms));
let fails = 0;
const check = (ok, label) => { console.log((ok ? "PASS " : "FAIL ") + label); if (!ok) fails++; };

function client(name, { ip, origin, ref } = {}) {
  return new Promise((resolve, reject) => {
    const headers = {}; if (ip) headers["x-forwarded-for"] = ip; if (origin) headers.origin = origin;
    const ws = new WebSocket(URL_, { headers });
    const c = { ws, events: [], results: [], states: [], welcome: null, closed: false, code: null };
    ws.on("open", () => ws.send(JSON.stringify({ type: "join", name, ref })));
    ws.on("message", raw => { const m = JSON.parse(raw);
      if (m.type === "welcome") { c.welcome = m; resolve(c); }
      if (m.type === "state") c.states.push(m);
      if (m.type === "event") c.events.push(m.text);
      if (m.type === "result") c.results.push(m); });
    ws.on("close", code => { c.closed = true; c.code = code; });
    ws.on("error", e => reject(e));
    setTimeout(() => reject(new Error("timeout " + name)), 6000);
  });
}
const last = c => c.states[c.states.length - 1];

(async () => {
  // 1. Origin la bi tu choi
  let rejected = false;
  try { await client("Evil", { ip: "1.1.1.1", origin: "https://evil.example" }); } catch (e) { rejected = /403/.test(e.message); }
  check(rejected, "origin la bi tu choi (403)");

  // 2. Ten chua HTML bi lam sach, nguoi khac khong thay ky tu nguy hiem
  const watcher = await client("Watcher", { ip: "2.2.2.1" });
  const bad = await client('<img src=x onerror=alert(1)>"\'`', { ip: "2.2.2.2" });
  await sleep(500);
  bad.ws.send(JSON.stringify({ type: "travel", map: watcher.welcome.map }));
  await sleep(1200);
  const names = (last(watcher).players || []).map(p => p.name).join("|");
  check(names.includes("Watcher") && !/[<>"'`]/.test(names), "ten HTML bi lam sach trong danh sach nguoi choi (" + names + ")");
  bad.ws.send(JSON.stringify({ type: "chat", text: "<script>alert(1)</script>" }));
  await sleep(500);
  check(!/[<>]/.test(watcher.events.join(" ")), "chat HTML bi lam sach");

  // 3. Spam hunt: chi 1 lan trong cooldown
  const A = await client("Spammer", { ip: "3.3.3.3" });
  A.ws.send(JSON.stringify({ type: "travel", map: "quy-khu" })); await sleep(300);
  const npcs = last(A).npcs;
  for (let i = 0; i < 30; i++) A.ws.send(JSON.stringify({ type: "hunt", target: npcs[i % npcs.length].id }));
  await sleep(800);
  check(last(A).you.merges <= 1, "spam 30 lenh hunt -> toi da 1 lan gop (merges=" + last(A).you.merges + ")");

  // 4. Spam travel: khong qua 1 lan chuyen map / 2s
  const maps = ["thanh-khau", "chuong-nga", "linh-son", "con-luan", "thien-son"];
  const B = await client("Traveler", { ip: "4.4.4.4" });
  const start = B.welcome.map;
  maps.forEach(m => B.ws.send(JSON.stringify({ type: "travel", map: m })));
  await sleep(700);
  check(last(B).map === maps[0] || last(B).map === start, "spam travel -> chi lenh dau co hieu luc (" + start + " -> " + last(B).map + ")");

  // 5. Payload qua lon -> ngat ket noi
  const C = await client("Big", { ip: "5.5.5.5" });
  C.ws.send("x".repeat(5000)); await sleep(500);
  check(C.closed, "payload > 2KB bi ngat ket noi");

  // 6. Flood tin nhan -> bi ngat
  const D = await client("Flood", { ip: "6.6.6.6" });
  for (let i = 0; i < 400; i++) D.ws.send(JSON.stringify({ type: "move", x: 50, y: 50 }));
  await sleep(600);
  check(D.closed, "flood 400 tin / 0.6s bi ngat ket noi");

  // 7. Gioi thieu: IP khac duoc +50 cho nguoi moi, cung IP khong duoc them
  const R = await client("Referrer", { ip: "7.7.7.1" });
  const code = R.welcome.you.refCode;
  check(/^[A-Z0-9]{6}$/.test(code), "co ma gioi thieu " + code);
  await client("Friend1", { ip: "7.7.7.2", ref: code });
  await client("Friend1b", { ip: "7.7.7.2", ref: code });   // cung IP -> khong tinh
  await client("Self", { ip: "7.7.7.1", ref: code });       // cung IP voi nguoi gioi thieu -> khong tinh
  await sleep(700);
  check(last(R).you.gx === 50 && last(R).you.refs === 1, "gioi thieu chi tinh 1 luot / IP, khong tu gioi thieu (gx=" + last(R).you.gx + ")");

  // 8. Double join bi bo qua
  const E = await client("Once", { ip: "8.8.8.8" });
  E.ws.send(JSON.stringify({ type: "join", name: "Again" })); await sleep(500);
  check(last(E).you.id === E.welcome.you.id, "join lan 2 bi bo qua");

  [watcher, bad, A, B, C, D, R, E].forEach(c => { try { c.ws.close(); } catch (e) {} });
  console.log(fails ? "SECURITY TEST FAIL (" + fails + ")" : "SECURITY TEST PASS");
  process.exit(fails ? 1 : 0);
})().catch(e => { console.error("ERR", e.message); process.exit(1); });
