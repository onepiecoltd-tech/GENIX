// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * GeneBlockV2 — bản nâng cấp của GeneBlock (v1 giữ nguyên, không thay thế),
 * nối coin GNCH (GeneChain Token, ERC-20 — xem GeneChainToken.sol) vào vòng đời block:
 *
 * - mintGenesis(): thu phí đăng ký genesis bằng GNCH (mặc định 100 GNCH).
 * - breed(): thu phí lai tạo bằng GNCH (10 GNCH — theo TOKENOMICS.md đã duyệt 18/11/2026).
 * - Mọi khoản phí: 50% ĐỐT vĩnh viễn (gọi burn() của GNCH), 50% chuyển về ví treasury.
 * - distributeRoyalty(): chia royalty BẰNG GNCH cho creator của các genesis tổ tiên
 *   theo trọng số đóng góp gen (tổng bắt buộc = 10000 bps), thay cho bản trả ETH ở v1.
 *   Phần lẻ làm tròn (dust) chuyển về treasury.
 * - Chủ contract chỉnh được mức phí và ví treasury (setFees/setTreasury).
 *
 * Phần ERC-721, struct Species, phả hệ DAG và verifyProvenance giữ nguyên như v1.
 */

interface IGNCH {
    function transferFrom(address from, address to, uint256 value) external returns (bool);
    function transfer(address to, uint256 value) external returns (bool);
    function burn(uint256 value) external;
    function balanceOf(address account) external view returns (uint256);
}

contract GeneBlockV2 {
    // ---------- ERC-721 tối giản (như v1) ----------
    string public name = "GeneBlock Species";
    string public symbol = "GENE";
    mapping(uint256 => address) public ownerOf;
    mapping(address => uint256) public balanceOf;
    mapping(uint256 => address) public getApproved;
    event Transfer(address indexed from, address indexed to, uint256 indexed tokenId);
    event Approval(address indexed owner, address indexed approved, uint256 indexed tokenId);

    // ---------- Dữ liệu giống loài (như v1) ----------
    struct Species {
        bytes32 blockHash;
        bytes32 merkleRoot;
        string[] geneCids;
        uint256[2] parents;
        address creator;
        uint16 generation;
        bool isGenesis;
    }

    uint256 public nextTokenId = 1;
    mapping(uint256 => Species) public species;

    event GenesisMinted(uint256 indexed tokenId, address indexed creator, bytes32 blockHash);
    event Bred(uint256 indexed tokenId, uint256 parentA, uint256 parentB, address indexed breeder);
    event RoyaltyDistributed(uint256 indexed tokenId, uint256 pool);

    // ---------- GNCH: phí + royalty ----------
    IGNCH public gnch;
    address public treasury;
    address public contractOwner;
    uint256 public genesisFee; // GNCH (18 decimals)
    uint256 public breedFee;   // GNCH (18 decimals)
    event FeeCollected(address indexed payer, uint256 fee, uint256 burned, uint256 toTreasury);
    event FeesUpdated(uint256 genesisFee, uint256 breedFee);
    event TreasuryUpdated(address treasury);

    modifier onlyOwner(uint256 tokenId) {
        require(ownerOf[tokenId] == msg.sender, "Not owner");
        _;
    }

    modifier onlyContractOwner() {
        require(msg.sender == contractOwner, "Not contract owner");
        _;
    }

    constructor(address gnchAddress, address treasuryAddress) {
        gnch = IGNCH(gnchAddress);
        treasury = treasuryAddress;
        contractOwner = msg.sender;
        genesisFee = 100 * 10 ** 18; // 100 GNCH — phí đăng ký block genesis
        breedFee = 10 * 10 ** 18;    // 10 GNCH — phí lai tạo (TOKENOMICS.md đã duyệt)
    }

    function setFees(uint256 newGenesisFee, uint256 newBreedFee) external onlyContractOwner {
        genesisFee = newGenesisFee;
        breedFee = newBreedFee;
        emit FeesUpdated(newGenesisFee, newBreedFee);
    }

    function setTreasury(address newTreasury) external onlyContractOwner {
        treasury = newTreasury;
        emit TreasuryUpdated(newTreasury);
    }

    /// Thu phí GNCH từ người gọi: 50% đốt, 50% về treasury.
    function _collectFee(uint256 fee) internal {
        if (fee == 0) return;
        require(gnch.transferFrom(msg.sender, address(this), fee), "GNCH fee transfer failed");
        uint256 burnAmt = fee / 2;
        uint256 treasuryAmt = fee - burnAmt;
        if (burnAmt > 0) gnch.burn(burnAmt);
        if (treasuryAmt > 0) require(gnch.transfer(treasury, treasuryAmt), "GNCH treasury transfer failed");
        emit FeeCollected(msg.sender, fee, burnAmt, treasuryAmt);
    }

    // ---------- Bước 1: Genesis (có phí GNCH) ----------
    function mintGenesis(bytes32 blockHash, bytes32 merkleRoot, string[] calldata geneCids) external returns (uint256) {
        _collectFee(genesisFee);
        uint256 id = nextTokenId++;
        Species storage s = species[id];
        s.blockHash = blockHash;
        s.merkleRoot = merkleRoot;
        s.geneCids = geneCids;
        s.creator = msg.sender;
        s.isGenesis = true;
        ownerOf[id] = msg.sender;
        balanceOf[msg.sender]++;
        emit Transfer(address(0), msg.sender, id);
        emit GenesisMinted(id, msg.sender, blockHash);
        return id;
    }

    // ---------- Bước 2: Lai tạo A + B -> C (có phí GNCH) ----------
    function breed(uint256 parentA, uint256 parentB, bytes32 childHash, bytes32 childMerkleRoot, string[] calldata childGeneCids)
        external returns (uint256)
    {
        require(parentA != parentB, "Parents must differ");
        require(ownerOf[parentA] != address(0) && ownerOf[parentB] != address(0), "Parent not exist");
        _collectFee(breedFee);
        uint256 id = nextTokenId++;
        Species storage s = species[id];
        s.blockHash = childHash;
        s.merkleRoot = childMerkleRoot;
        s.geneCids = childGeneCids;
        s.parents = [parentA, parentB];
        s.creator = msg.sender;
        uint16 ga = species[parentA].generation;
        uint16 gb = species[parentB].generation;
        s.generation = (ga > gb ? ga : gb) + 1;
        ownerOf[id] = msg.sender;
        balanceOf[msg.sender]++;
        emit Transfer(address(0), msg.sender, id);
        emit Bred(id, parentA, parentB, msg.sender);
        return id;
    }

    // ---------- Bước 3/4: Truy xuất & xác thực (như v1) ----------
    function getSpecies(uint256 tokenId) external view returns (
        bytes32 blockHash, bytes32 merkleRoot, string[] memory geneCids, uint256[2] memory parents,
        address creator, uint16 generation, bool isGenesis)
    {
        Species storage s = species[tokenId];
        return (s.blockHash, s.merkleRoot, s.geneCids, s.parents, s.creator, s.generation, s.isGenesis);
    }

    function verifyProvenance(uint256 tokenId, bytes32 expectedHash) external view returns (bool) {
        return species[tokenId].blockHash == expectedHash;
    }

    /**
     * Chia royalty BẰNG GNCH cho creator của các genesis tổ tiên.
     * @param genesisIds  danh sách tokenId genesis tổ tiên (truy từ DAG off-chain)
     * @param weightsBps  trọng số đóng góp gen, tổng phải = 10000 (100%)
     * @param amount      tổng royalty pool (GNCH) — contract rút từ chủ token qua transferFrom
     */
    function distributeRoyalty(uint256 tokenId, uint256[] calldata genesisIds, uint256[] calldata weightsBps, uint256 amount)
        external onlyOwner(tokenId)
    {
        require(genesisIds.length == weightsBps.length, "Length mismatch");
        uint256 total;
        for (uint256 i = 0; i < weightsBps.length; i++) total += weightsBps[i];
        require(total == 10_000, "Weights must sum to 100%");
        require(gnch.transferFrom(msg.sender, address(this), amount), "GNCH royalty transfer failed");
        uint256 sent;
        for (uint256 i = 0; i < genesisIds.length; i++) {
            require(species[genesisIds[i]].isGenesis, "Not a genesis block");
            uint256 amt = (amount * weightsBps[i]) / 10_000;
            sent += amt;
            if (amt > 0) require(gnch.transfer(species[genesisIds[i]].creator, amt), "Royalty payout failed");
        }
        uint256 dust = amount - sent;
        if (dust > 0) require(gnch.transfer(treasury, dust), "Dust transfer failed");
        emit RoyaltyDistributed(tokenId, amount);
    }

    // ---------- Chuyển nhượng ERC-721 cơ bản (như v1) ----------
    function approve(address to, uint256 tokenId) external onlyOwner(tokenId) {
        getApproved[tokenId] = to;
        emit Approval(msg.sender, to, tokenId);
    }

    function transferFrom(address from, address to, uint256 tokenId) external {
        require(ownerOf[tokenId] == from, "Wrong from");
        require(msg.sender == from || msg.sender == getApproved[tokenId], "Not authorized");
        ownerOf[tokenId] = to;
        balanceOf[from]--;
        balanceOf[to]++;
        getApproved[tokenId] = address(0);
        emit Transfer(from, to, tokenId);
    }
}
