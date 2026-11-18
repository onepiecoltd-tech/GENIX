// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * GeneBlock — Lớp 3 (On-chain) của hệ thống lai tạo gen bằng Merkle DAG.
 *
 * Thiết kế theo bản tóm tắt:
 * - Mỗi SpeciesBlock = 1 NFT ERC-721 (định danh giống loài duy nhất).
 *   File này tự chứa bản ERC-721 tối giản để đọc độc lập, không phụ thuộc
 *   thư viện ngoài. Khi deploy production, thay bằng OpenZeppelin ERC721
 *   + ERC-6551 (mỗi NFT có Token Bound Account giữ danh sách CID gen).
 * - On-chain CHỈ lưu: blockHash (Merkle root), danh sách CID gen (IPLD links),
 *   parents[2] và creator. Dữ liệu gen thô nằm off-chain trên IPFS (Lớp 1).
 * - Phả hệ là DAG (mỗi block có 2 parents), không phải chuỗi tuyến tính.
 * - distributeRoyalty(): chia royalty ngược cho creator của các Genesis
 *   tổ tiên theo tỉ lệ đóng góp gen (do client/off-chain tính từ DAG và
 *   contract kiểm chứng tổng trọng số = 10000 bps trước khi chi).
 *
 * Deploy gợi ý: Polygon Amoy / Base Sepolia (testnet) -> Polygon / Base (mainnet).
 * Cho mạng nghiên cứu cấp phép: port logic này sang Hyperledger Fabric chaincode.
 */
contract GeneBlock {
    // ---------- ERC-721 tối giản ----------
    string public name = "GeneBlock Species";
    string public symbol = "GENE";
    mapping(uint256 => address) public ownerOf;
    mapping(address => uint256) public balanceOf;
    mapping(uint256 => address) public getApproved;
    event Transfer(address indexed from, address indexed to, uint256 indexed tokenId);
    event Approval(address indexed owner, address indexed approved, uint256 indexed tokenId);

    // ---------- Dữ liệu giống loài ----------
    struct Species {
        bytes32 blockHash;      // Hash định danh block tính off-chain (Lớp 2)
        bytes32 merkleRoot;     // Merkle root của 300 gene CID — cam kết toàn bộ gene bằng 32 byte;
                                // kiểm chứng 1 gene thuộc block bằng Merkle proof O(log n)
        string[] geneCids;      // CID IPFS của từng cấu phần gen (IPLD links)
        uint256[2] parents;     // [0,0] nếu là Genesis
        address creator;
        uint16 generation;
        bool isGenesis;
    }

    uint256 public nextTokenId = 1;
    mapping(uint256 => Species) public species;

    event GenesisMinted(uint256 indexed tokenId, address indexed creator, bytes32 blockHash);
    event Bred(uint256 indexed tokenId, uint256 parentA, uint256 parentB, address indexed breeder);
    event RoyaltyDistributed(uint256 indexed tokenId, uint256 pool);

    modifier onlyOwner(uint256 tokenId) {
        require(ownerOf[tokenId] == msg.sender, "Not owner");
        _;
    }

    // ---------- Bước 1: Genesis ----------
    function mintGenesis(bytes32 blockHash, bytes32 merkleRoot, string[] calldata geneCids) external returns (uint256) {
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

    // ---------- Bước 2: Lai tạo A + B -> C ----------
    function breed(uint256 parentA, uint256 parentB, bytes32 childHash, bytes32 childMerkleRoot, string[] calldata childGeneCids)
        external returns (uint256)
    {
        require(parentA != parentB, "Parents must differ");
        require(ownerOf[parentA] != address(0) && ownerOf[parentB] != address(0), "Parent not exist");
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

    // ---------- Bước 3/4: Truy xuất & xác thực ----------
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
     * Chia royalty cho creator của các genesis tổ tiên.
     * @param genesisIds  danh sách tokenId genesis tổ tiên (truy từ DAG off-chain)
     * @param weightsBps  trọng số đóng góp gen, tổng phải = 10000 (100%)
     * Tiền gửi kèm msg.value là royalty pool; contract chia đúng tỉ lệ.
     */
    function distributeRoyalty(uint256 tokenId, uint256[] calldata genesisIds, uint256[] calldata weightsBps)
        external payable onlyOwner(tokenId)
    {
        require(genesisIds.length == weightsBps.length, "Length mismatch");
        uint256 total;
        for (uint256 i = 0; i < weightsBps.length; i++) total += weightsBps[i];
        require(total == 10_000, "Weights must sum to 100%");
        for (uint256 i = 0; i < genesisIds.length; i++) {
            require(species[genesisIds[i]].isGenesis, "Not a genesis block");
            address creator = species[genesisIds[i]].creator;
            uint256 amt = (msg.value * weightsBps[i]) / 10_000;
            if (amt > 0) {
                (bool ok, ) = payable(creator).call{value: amt}("");
                require(ok, "Payout failed");
            }
        }
        emit RoyaltyDistributed(tokenId, msg.value);
    }

    // ---------- Chuyển nhượng ERC-721 cơ bản ----------
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
