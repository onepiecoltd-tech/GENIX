// GeneChain Token (GNCH) — deploy lên Ethereum Sepolia + phân bổ on-chain theo TOKENOMICS.md đã duyệt.
// Chạy: node deploy_token.js   (an toàn khi chạy lại: bỏ qua bước đã ghi trong token_result.json)
const fs = require("fs");
const path = require("path");
const { ethers } = require("ethers");
const solc = require("solc");

const RPC = "https://ethereum-sepolia-rpc.publicnode.com";
const WALLET_FILE = path.join(__dirname, "testnet-wallet.json");
const VAULTS_FILE = path.join(__dirname, "token_vaults.json");
const RESULT_FILE = path.join(__dirname, "token_result.json");
const U = (n) => ethers.parseUnits(String(n), 18);

// Phân bổ đã duyệt (TOKENOMICS.md mục 3, bản tối ưu thương mại) — đơn vị GNCH
const ALLOCATIONS = [
  { key: "ecosystem", label: "He sinh thai & thuong lai tao/du lieu (30%)", amount: 300_000_000 },
  { key: "liquidity", label: "Thanh khoan (15%)", amount: 150_000_000 },
  { key: "treasury", label: "Kho bac & van hanh (15%)", amount: 150_000_000 },
  { key: "growth", label: "Cong dong & tang truong (13%)", amount: 130_000_000 },
  { key: "team", label: "Doi ngu & sang lap (12%, vesting)", amount: 120_000_000 },
  { key: "partners", label: "Doi tac chien luoc (10%)", amount: 100_000_000 },
  { key: "reserve", label: "Du phong (5%)", amount: 50_000_000 },
];
// Demo chia royalty bằng GNCH theo đúng ví dụ TOKENOMICS mục 4 (bán 100.000, royalty 10%)
const ROYALTY_DEMO = [
  { key: "vien_lua_dbscl", label: "Vien Lua DBSCL (demo, tao A+C = 75%)", amount: 7_500 },
  { key: "tt_giong_mien_tay", label: "Trung Tam Giong Mien Tay (demo, tao B = 25%)", amount: 2_500 },
];

function loadOrCreateVaults() {
  if (fs.existsSync(VAULTS_FILE)) return JSON.parse(fs.readFileSync(VAULTS_FILE, "utf8"));
  const vaults = { note: "TESTNET ONLY — cac vi quy demo cua GNCH tren Sepolia, khong dung cho mainnet/tien that", created: new Date().toISOString(), wallets: {} };
  for (const a of [...ALLOCATIONS, ...ROYALTY_DEMO]) {
    const w = ethers.Wallet.createRandom();
    vaults.wallets[a.key] = { label: a.label, address: w.address, privateKey: w.privateKey };
  }
  fs.writeFileSync(VAULTS_FILE, JSON.stringify(vaults, null, 2));
  return vaults;
}

function compile() {
  const source = fs.readFileSync(path.join(__dirname, "..", "contracts", "GeneChainToken.sol"), "utf8");
  const input = {
    language: "Solidity",
    sources: { "GeneChainToken.sol": { content: source } },
    settings: { optimizer: { enabled: true, runs: 200 }, outputSelection: { "*": { "*": ["abi", "evm.bytecode"] } } },
  };
  const out = JSON.parse(solc.compile(JSON.stringify(input)));
  if (out.errors) for (const e of out.errors) if (e.severity === "error") throw new Error(e.formattedMessage);
  const c = out.contracts["GeneChainToken.sol"]["GeneChainToken"];
  return { abi: c.abi, bytecode: c.evm.bytecode.object };
}

async function main() {
  const provider = new ethers.JsonRpcProvider(RPC);
  const deployer = new ethers.Wallet(JSON.parse(fs.readFileSync(WALLET_FILE, "utf8")).privateKey, provider);
  console.log("DEPLOYER:", deployer.address);
  const balance = await provider.getBalance(deployer.address);
  console.log("BALANCE (Sepolia ETH):", ethers.formatEther(balance));
  if (balance === 0n) { console.log("STATUS: NEED_FAUCET"); return; }

  const vaults = loadOrCreateVaults();
  const { abi, bytecode } = compile();
  console.log("Compiled GeneChainToken OK, bytecode bytes:", bytecode.length / 2);

  let result = {};
  if (fs.existsSync(RESULT_FILE)) result = JSON.parse(fs.readFileSync(RESULT_FILE, "utf8"));

  let token;
  if (!result.tokenAddress) {
    const factory = new ethers.ContractFactory(abi, bytecode, deployer);
    token = await factory.deploy();
    await token.waitForDeployment();
    result.tokenAddress = await token.getAddress();
    result.deployTx = token.deploymentTransaction().hash;
    result.network = "Ethereum Sepolia (chainId 11155111)";
    result.symbol = "GNCH";
    result.totalSupply = "1000000000";
    fs.writeFileSync(RESULT_FILE, JSON.stringify(result, null, 2));
    console.log("TOKEN DEPLOYED:", result.tokenAddress, "tx:", result.deployTx);
  } else {
    token = new ethers.Contract(result.tokenAddress, abi, deployer);
    console.log("Reuse token:", result.tokenAddress);
  }

  result.allocations = result.allocations || {};
  for (const a of ALLOCATIONS) {
    if (result.allocations[a.key]) continue;
    const to = vaults.wallets[a.key].address;
    const tx = await token.transfer(to, U(a.amount));
    await tx.wait();
    result.allocations[a.key] = { address: to, amount: a.amount, tx: tx.hash };
    fs.writeFileSync(RESULT_FILE, JSON.stringify(result, null, 2));
    console.log("ALLOC", a.key, a.amount, "GNCH ->", to, "tx:", tx.hash);
  }

  // Demo royalty: ví hệ sinh thái đóng vai người trả, chia cho 2 viện theo trọng số 75/25
  result.royaltyDemo = result.royaltyDemo || {};
  const ecoWallet = new ethers.Wallet(vaults.wallets.ecosystem.privateKey, provider);
  const ecoToken = new ethers.Contract(result.tokenAddress, abi, ecoWallet);
  for (const r of ROYALTY_DEMO) {
    if (result.royaltyDemo[r.key]) continue;
    const to = vaults.wallets[r.key].address;
    const tx = await ecoToken.transfer(to, U(r.amount));
    await tx.wait();
    result.royaltyDemo[r.key] = { address: to, amount: r.amount, tx: tx.hash };
    fs.writeFileSync(RESULT_FILE, JSON.stringify(result, null, 2));
    console.log("ROYALTY", r.key, r.amount, "GNCH ->", to, "tx:", tx.hash);
  }

  // Kiểm chứng on-chain
  console.log("totalSupply:", ethers.formatUnits(await token.totalSupply(), 18), "GNCH");
  console.log("deployer balance:", ethers.formatUnits(await token.balanceOf(deployer.address), 18), "GNCH");
  for (const a of ALLOCATIONS) {
    const b = await token.balanceOf(vaults.wallets[a.key].address);
    console.log("ONCHAIN", a.key, ethers.formatUnits(b, 18), "GNCH");
  }
  for (const r of ROYALTY_DEMO) {
    const b = await token.balanceOf(vaults.wallets[r.key].address);
    console.log("ONCHAIN", r.key, ethers.formatUnits(b, 18), "GNCH");
  }
  console.log("DONE. Explorer: https://sepolia.etherscan.io/token/" + result.tokenAddress);
}

main().catch(e => { console.error("ERROR:", e.message); process.exit(1); });
