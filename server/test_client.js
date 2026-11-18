/* Test tu dong: 2 client vao phong, di chuyen map, san NPC, tron.
   Chay server truoc (npm start), roi: node test_client.js */
const WebSocket = require("ws");
const URL = process.env.WS_URL || "ws://127.0.0.1:8788";
let failures = 0;
function client(name) {
  return new Promise((resolve, reject) => {
    const ws = new WebSocket(URL);
    const c = { ws, name, welcome: null, states: [], results: [] };
    ws.on("open", () => ws.send(JSON.stringify({ type: "join", name })));
    ws.on("message", raw => {
      const m = JSON.parse(raw);
      if (m.type === "welcome") { c.welcome = m; resolve(c); }
      if (m.type === "state") c.states.push(m);
      if (m.type === "result") c.results.push(m);
    });
    ws.on("error", reject);
    setTimeout(() => reject(new Error("timeout join " + name)), 8000);
  });
}
const sleep = ms => new Promise(r => setTimeout(r, ms));
(async () => {
  const A = await client("StreamerA");
  const B = await client("KhanGiaB");
  console.log("welcome A:", A.welcome.you.disp, "@", A.welcome.map,
              "| B:", B.welcome.you.disp, "@", B.welcome.map);
  A.ws.send(JSON.stringify({ type: "travel", map: "quy-khu" }));
  B.ws.send(JSON.stringify({ type: "travel", map: "quy-khu" }));
  await sleep(1200);
  const st = A.states[A.states.length - 1];
  console.log("state A: map", st.map, "| players:", st.players.length,
              "| npcs:", st.npcs.length, "| you.power:", st.you.power);
  if (st.map !== "quy-khu") { console.log("FAIL map"); failures++; }
  if (st.players.length < 2) { console.log("FAIL players<2"); failures++; }
  if (!st.npcs.length) { console.log("FAIL no npc"); failures++; }
  A.ws.send(JSON.stringify({ type: "hunt", target: st.npcs[0].id }));
  await sleep(800);
  console.log("hunt result:", A.results.length ? A.results[A.results.length - 1].text : "(none)");
  if (!A.results.length) { console.log("FAIL no hunt result"); failures++; }
  A.ws.send(JSON.stringify({ type: "flee" }));
  await sleep(800);
  const st2 = A.states[A.states.length - 1];
  console.log("after flee map:", st2.map);
  if (st2.map === "quy-khu") { console.log("FAIL flee"); failures++; }
  A.ws.close(); B.ws.close();
  console.log(failures ? "TEST FAIL (" + failures + ")" : "TEST PASS");
  process.exit(failures ? 1 : 0);
})().catch(e => { console.error("ERR", e.message); process.exit(1); });
