// GeneChain — deploy GeneBlock lên Ethereum Sepolia (TESTNET, coin không có giá trị)
// Chạy: node deploy.js          -> deploy + mint genesis + breed (cần ví đã có Sepolia ETH)
//       node deploy.js wallet   -> chỉ tạo ví testnet và in địa chỉ (để xin faucet)
const fs = require("fs");
const path = require("path");
const { ethers } = require("ethers");
const solc = require("solc");

const RPC = "https://ethereum-sepolia-rpc.publicnode.com";
const WALLET_FILE = path.join(__dirname, "testnet-wallet.json");
const RESULT_FILE = path.join(__dirname, "result.json");

// Dữ liệu thật từ Block Registry v5 (đã kiểm chứng)
const SPECIES = [
  { key: "pig", taxid: 9823, name: "Sus scrofa (Heo)",
    root: "d415dababc64b994db04aa604e67ce92879b3c0ac37439cf0e3c732341aa1fb3" },
  { key: "chicken", taxid: 9031, name: "Gallus gallus (Ga)",
    root: "8c5391674b2666f866275d3026042816da6b929fca59175030e5f6c1955975b7" },
  { key: "rice", taxid: 39947, name: "Oryza sativa Japonica (Lua)",
    root: "648ebf5b902e38ff7634de8f709fae436a83cef1dd7a4c68f87fa3ca9d2ee868" },
];
const HYBRID_PIG_CHICKEN = {
  root: "9f85aa43be79fba5b9ebe9951a457452aca91c493da5a0668771472f62951c07", // Merkle root tập union 54.112 block
};

function loadLab() {
  return JSON.parse(fs.readFileSync(path.join(__dirname, "..", "data", "demo_lab.json"), "utf8"));
}

function getWallet(provider) {
  if (fs.existsSync(WALLET_FILE)) {
    const w = JSON.parse(fs.readFileSync(WALLET_FILE, "utf8"));
    return new ethers.Wallet(w.privateKey, provider);
  }
  const wallet = ethers.Wallet.createRandom();
  fs.writeFileSync(WALLET_FILE, JSON.stringify({
    note: "TESTNET ONLY — vi tao rieng cho GeneChain testnet, khong dung cho mainnet/tien that",
    address: wallet.address,
    privateKey: wallet.privateKey,
    created: new Date().toISOString(),
  }, null, 2));
  return new ethers.Wallet(wallet.privateKey, provider);
}

function compile() {
  const source = fs.readFileSync(path.join(__dirname, "..", "contracts", "GeneBlock.sol"), "utf8");
  const input = {
    language: "Solidity",
    sources: { "GeneBlock.sol": { content: source } },
    settings: { viaIR: true, optimizer: { enabled: true, runs: 200 }, outputSelection: { "*": { "*": ["abi", "evm.bytecode"] } } },
  };
  const out = JSON.parse(solc.compile(JSON.stringify(input)));
  if (out.errors) {
    for (const e of out.errors) if (e.severity === "error") throw new Error(e.formattedMessage);
  }
  const c = out.contracts["GeneBlock.sol"]["GeneBlock"];
  return { abi: c.abi, bytecode: c.evm.bytecode.object };
}

function blockHashFor(taxid, rootHex) {
  return ethers.sha256(ethers.toUtf8Bytes(`GENECHAIN-V5:${taxid}:${rootHex}`));
}

async function main() {
  const provider = new ethers.JsonRpcProvider(RPC);
  const wallet = getWallet(provider);
  console.log("WALLET:", wallet.address);
  if (process.argv[2] === "wallet") return;

  const balance = await provider.getBalance(wallet.address);
  console.log("BALANCE (Sepolia ETH):", ethers.formatEther(balance));
  if (balance === 0n) {
    console.log("STATUS: NEED_FAUCET — ví chưa có Sepolia ETH, xin faucet rồi chạy lại.");
    return;
  }

  const lab = loadLab();
  const { abi, bytecode } = compile();
  console.log("Compiled GeneBlock OK, bytecode bytes:", bytecode.length / 2);

  let result = {};
  if (fs.existsSync(RESULT_FILE)) result = JSON.parse(fs.readFileSync(RESULT_FILE, "utf8"));

  let contract;
  if (!result.contractAddress) {
    const factory = new ethers.ContractFactory(abi, bytecode, wallet);
    contract = await factory.deploy();
    await contract.waitForDeployment();
    result.contractAddress = await contract.getAddress();
    result.deployTx = contract.deploymentTransaction().hash;
    result.network = "Ethereum Sepolia (chainId 11155111)";
    result.deployer = wallet.address;
    fs.writeFileSync(RESULT_FILE, JSON.stringify(result, null, 2));
    console.log("DEPLOYED:", result.contractAddress, "tx:", result.deployTx);
  } else {
    contract = new ethers.Contract(result.contractAddress, abi, wallet);
    console.log("Reuse contract:", result.contractAddress);
  }

  const ipfsCids = JSON.parse(fs.readFileSync(path.join(__dirname, "..", "data", "ipfs_cids.json"), "utf8"));
  result.tokens = result.tokens || {};
  for (const sp of SPECIES) {
    if (result.tokens[sp.key]) continue;
    // CID đầu tiên = file IPFS chứa toàn bộ danh sách block của loài; tiếp theo là vài block_id mẫu
    const geneCids = [ipfsCids.species[String(sp.taxid)],
                      ...(lab.proofs[String(sp.taxid)] || []).map(p => p.block_id)];
    const tx = await contract.mintGenesis(blockHashFor(sp.taxid, sp.root), "0x" + sp.root, geneCids);
    const rc = await tx.wait();
    // tokenId = nextTokenId trước mint — suy từ log Transfer
    const log = rc.logs.map(l => { try { return contract.interface.parseLog(l); } catch { return null; } })
                        .find(p => p && p.name === "Transfer");
    result.tokens[sp.key] = { tokenId: Number(log.args.tokenId), tx: tx.hash, merkleRoot: sp.root, geneCids };
    fs.writeFileSync(RESULT_FILE, JSON.stringify(result, null, 2));
    console.log("MINTED", sp.key, "tokenId:", result.tokens[sp.key].tokenId, "tx:", tx.hash);
  }

  if (!result.tokens.hybrid_pig_chicken) {
    const a = result.tokens.pig.tokenId, b = result.tokens.chicken.tokenId;
    const childHash = ethers.sha256(ethers.toUtf8Bytes(`GENECHAIN-V5:HYBRID:${a}x${b}:${HYBRID_PIG_CHICKEN.root}`));
    const tx = await contract.breed(a, b, childHash, "0x" + HYBRID_PIG_CHICKEN.root, []);
    const rc = await tx.wait();
    const log = rc.logs.map(l => { try { return contract.interface.parseLog(l); } catch { return null; } })
                        .find(p => p && p.name === "Bred");
    result.tokens.hybrid_pig_chicken = { tokenId: Number(log.args.tokenId), tx: tx.hash, merkleRoot: HYBRID_PIG_CHICKEN.root };
    fs.writeFileSync(RESULT_FILE, JSON.stringify(result, null, 2));
    console.log("BRED hybrid pig x chicken tokenId:", result.tokens.hybrid_pig_chicken.tokenId, "tx:", tx.hash);
  }

  // Kiểm chứng on-chain: đọc lại getSpecies của từng token
  for (const [k, v] of Object.entries(result.tokens)) {
    const s = await contract.getSpecies(v.tokenId);
    console.log("ONCHAIN", k, "token", v.tokenId, "merkleRoot:", s.merkleRoot, "gen:", s.generation.toString(), "genesis:", s.isGenesis);
  }
  console.log("DONE. Explorer: https://sepolia.etherscan.io/address/" + result.contractAddress);
}

main().catch(e => { console.error("ERROR:", e.message); process.exit(1); });
