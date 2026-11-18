// GeneBlockV2 — deploy lên Sepolia + chạy thử VÒNG KHÉP KÍN bằng GNCH:
//   2 viện giống (ví riêng) mint genesis heo/gà, mỗi viện trả phí 100 GNCH (50 đốt / 50 treasury)
//   deployer lai heo×gà, trả phí 10 GNCH (5 đốt / 5 treasury)
//   deployer chia royalty 10.000 GNCH qua contract -> viện A 7.500 / viện B 2.500 (trọng số 75/25)
// Chạy: node deploy_v2.js  (an toàn khi chạy lại: bỏ qua bước đã ghi trong v2_result.json)
const fs = require("fs");
const path = require("path");
const { ethers } = require("ethers");
const solc = require("solc");

const RPC = "https://ethereum-sepolia-rpc.publicnode.com";
const WALLET_FILE = path.join(__dirname, "testnet-wallet.json");
const VAULTS_FILE = path.join(__dirname, "token_vaults.json");
const TOKEN_RESULT = path.join(__dirname, "token_result.json");
const RESULT_FILE = path.join(__dirname, "v2_result.json");
const U = (n) => ethers.parseUnits(String(n), 18);
const F = (v) => ethers.formatUnits(v, 18);

const PIG = { taxid: 9823, root: "d415dababc64b994db04aa604e67ce92879b3c0ac37439cf0e3c732341aa1fb3" };
const CHICKEN = { taxid: 9031, root: "8c5391674b2666f866275d3026042816da6b929fca59175030e5f6c1955975b7" };
const HYBRID_ROOT = "9f85aa43be79fba5b9ebe9951a457452aca91c493da5a0668771472f62951c07";

function blockHashFor(taxid, rootHex) {
  return ethers.sha256(ethers.toUtf8Bytes(`GENECHAIN-V5:${taxid}:${rootHex}`));
}

function compile() {
  const source = fs.readFileSync(path.join(__dirname, "..", "contracts", "GeneBlockV2.sol"), "utf8");
  const input = {
    language: "Solidity",
    sources: { "GeneBlockV2.sol": { content: source } },
    settings: { viaIR: true, optimizer: { enabled: true, runs: 200 }, outputSelection: { "*": { "*": ["abi", "evm.bytecode"] } } },
  };
  const out = JSON.parse(solc.compile(JSON.stringify(input)));
  if (out.errors) for (const e of out.errors) if (e.severity === "error") throw new Error(e.formattedMessage);
  const c = out.contracts["GeneBlockV2.sol"]["GeneBlockV2"];
  return { abi: c.abi, bytecode: c.evm.bytecode.object };
}

async function main() {
  const provider = new ethers.JsonRpcProvider(RPC);
  const deployer = new ethers.Wallet(JSON.parse(fs.readFileSync(WALLET_FILE, "utf8")).privateKey, provider);
  const vaults = JSON.parse(fs.readFileSync(VAULTS_FILE, "utf8")).wallets;
  const tokenAddress = JSON.parse(fs.readFileSync(TOKEN_RESULT, "utf8")).tokenAddress;
  const lab = JSON.parse(fs.readFileSync(path.join(__dirname, "..", "data", "demo_lab.json"), "utf8"));
  const ipfsCids = JSON.parse(fs.readFileSync(path.join(__dirname, "..", "data", "ipfs_cids.json"), "utf8"));

  const W = (key) => new ethers.Wallet(vaults[key].privateKey, provider);
  const eco = W("ecosystem"), vienLua = W("vien_lua_dbscl"), ttGiong = W("tt_giong_mien_tay");
  const treasuryAddr = vaults.treasury.address;

  const { abi, bytecode } = compile();
  console.log("Compiled GeneBlockV2 OK, bytecode bytes:", bytecode.length / 2);

  let result = {};
  if (fs.existsSync(RESULT_FILE)) result = JSON.parse(fs.readFileSync(RESULT_FILE, "utf8"));
  const save = () => fs.writeFileSync(RESULT_FILE, JSON.stringify(result, null, 2));

  // --- Deploy v2 ---
  let v2;
  if (!result.contractAddress) {
    const factory = new ethers.ContractFactory(abi, bytecode, deployer);
    v2 = await factory.deploy(tokenAddress, treasuryAddr);
    await v2.waitForDeployment();
    result.contractAddress = await v2.getAddress();
    result.deployTx = v2.deploymentTransaction().hash;
    result.gnch = tokenAddress;
    result.treasury = treasuryAddr;
    save();
    console.log("V2 DEPLOYED:", result.contractAddress, "tx:", result.deployTx);
  } else {
    v2 = new ethers.Contract(result.contractAddress, abi, deployer);
    console.log("Reuse V2:", result.contractAddress);
  }
  const gnch = new ethers.Contract(tokenAddress, ["function transfer(address,uint256) returns (bool)", "function approve(address,uint256) returns (bool)", "function balanceOf(address) view returns (uint256)", "function totalSupply() view returns (uint256)"], deployer);
  const gnchAs = (wallet) => gnch.connect(wallet);
  const v2As = (wallet) => v2.connect(wallet);

  if (result.supplyStart === undefined) { result.supplyStart = F(await gnch.totalSupply()); save(); }
  console.log("GNCH supply start:", result.supplyStart);

  // --- Cấp vốn thử nghiệm: ecosystem -> 2 viện + deployer (GNCH), deployer -> 2 viện (ETH gas) ---
  result.funding = result.funding || {};
  const fundGnch = async (key, to, amount) => {
    if (result.funding[key]) return;
    const tx = await gnchAs(eco).transfer(to, U(amount));
    await tx.wait();
    result.funding[key] = { to, amount, tx: tx.hash }; save();
    console.log("FUND GNCH", key, amount, "->", to, "tx:", tx.hash);
  };
  await fundGnch("vien_lua", vienLua.address, 5000);
  await fundGnch("tt_giong", ttGiong.address, 5000);
  await fundGnch("deployer", deployer.address, 20000);
  const fundEth = async (key, to) => {
    if (result.funding[key]) return;
    const tx = await deployer.sendTransaction({ to, value: ethers.parseEther("0.003") });
    await tx.wait();
    result.funding[key] = { to, eth: "0.003", tx: tx.hash }; save();
    console.log("FUND ETH", key, "0.003 ->", to, "tx:", tx.hash);
  };
  await fundEth("eth_vien_lua", vienLua.address);
  await fundEth("eth_tt_giong", ttGiong.address);

  // --- Viện Lúa mint genesis HEO (phí 100 GNCH), TT Giống mint genesis GÀ (phí 100 GNCH) ---
  result.tokens = result.tokens || {};
  const mintAs = async (key, wallet, sp) => {
    if (result.tokens[key]) return result.tokens[key].tokenId;
    const ap = await gnchAs(wallet).approve(result.contractAddress, U(1000));
    await ap.wait();
    const geneCids = [ipfsCids.species[String(sp.taxid)], ...(lab.proofs[String(sp.taxid)] || []).map(p => p.block_id)];
    const tx = await v2As(wallet).mintGenesis(blockHashFor(sp.taxid, sp.root), "0x" + sp.root, geneCids);
    const rc = await tx.wait();
    const log = rc.logs.map(l => { try { return v2.interface.parseLog(l); } catch { return null; } }).find(p => p && p.name === "Transfer");
    result.tokens[key] = { tokenId: Number(log.args.tokenId), tx: tx.hash, creator: wallet.address, merkleRoot: sp.root };
    save();
    console.log("MINTED", key, "tokenId:", result.tokens[key].tokenId, "by", wallet.address, "tx:", tx.hash);
    return result.tokens[key].tokenId;
  };
  const pigId = await mintAs("pig", vienLua, PIG);
  const chickenId = await mintAs("chicken", ttGiong, CHICKEN);

  // --- Deployer lai heo×gà (phí 10 GNCH) ---
  if (!result.tokens.hybrid) {
    const ap = await gnch.approve(result.contractAddress, U(20000));
    await ap.wait();
    const childHash = ethers.sha256(ethers.toUtf8Bytes(`GENECHAIN-V5:HYBRID:${pigId}x${chickenId}:${HYBRID_ROOT}`));
    const tx = await v2.breed(pigId, chickenId, childHash, "0x" + HYBRID_ROOT, []);
    const rc = await tx.wait();
    const log = rc.logs.map(l => { try { return v2.interface.parseLog(l); } catch { return null; } }).find(p => p && p.name === "Bred");
    result.tokens.hybrid = { tokenId: Number(log.args.tokenId), tx: tx.hash, merkleRoot: HYBRID_ROOT };
    save();
    console.log("BRED hybrid tokenId:", result.tokens.hybrid.tokenId, "tx:", tx.hash);
  }

  // --- Chia royalty 10.000 GNCH qua contract: viện Lúa 75% / TT Giống 25% ---
  if (!result.royalty) {
    const tx = await v2.distributeRoyalty(result.tokens.hybrid.tokenId, [pigId, chickenId], [7500, 2500], U(10000));
    await tx.wait();
    result.royalty = { amount: 10000, weights: [7500, 2500], tx: tx.hash };
    save();
    console.log("ROYALTY distributed 10000 GNCH tx:", tx.hash);
  }

  // --- Kiểm chứng on-chain ---
  console.log("== ON-CHAIN VERIFY ==");
  console.log("GNCH supply now:", F(await gnch.totalSupply()), "(start:", result.supplyStart + ") => burned:", Number(result.supplyStart) - Number(F(await gnch.totalSupply())));
  console.log("treasury GNCH:", F(await gnch.balanceOf(treasuryAddr)));
  console.log("vien_lua GNCH:", F(await gnch.balanceOf(vienLua.address)), "(expect 5000 - 100 fee + 7500 royalty = 12400)");
  console.log("tt_giong GNCH:", F(await gnch.balanceOf(ttGiong.address)), "(expect 5000 - 100 fee + 2500 royalty = 7400)");
  console.log("deployer GNCH:", F(await gnch.balanceOf(deployer.address)), "(expect 20000 - 10 breed fee - 10000 royalty = 9990)");
  for (const [k, v] of Object.entries(result.tokens)) {
    const s = await v2.getSpecies(v.tokenId);
    console.log("ONCHAIN", k, "token", v.tokenId, "root:", s.merkleRoot, "gen:", s.generation.toString(), "genesis:", s.isGenesis, "creator:", s.creator);
  }
  console.log("DONE. Explorer: https://sepolia.etherscan.io/address/" + result.contractAddress);
}

main().catch(e => { console.error("ERROR:", e.message); process.exit(1); });
