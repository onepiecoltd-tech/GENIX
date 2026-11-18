// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// @title GeneChain Token (GNCH)
/// @notice ERC-20 tiện ích của nền tảng GeneChain — xem TOKENOMICS.md (đã duyệt 18/11/2026).
/// Tổng cung cố định 1.000.000.000 GNCH, mint toàn bộ cho deployer trong constructor.
/// Không có hàm mint về sau, không có quyền admin rút tiền của người dùng.
/// Hàm burn() để bất kỳ ai cũng đốt được coin của chính mình (phục vụ cơ chế đốt 50% phí).
contract GeneChainToken {
    string public name = "GeneChain Token";
    string public symbol = "GNCH";
    uint8 public decimals = 18;
    uint256 public totalSupply;

    mapping(address => uint256) public balanceOf;
    mapping(address => mapping(address => uint256)) public allowance;

    event Transfer(address indexed from, address indexed to, uint256 value);
    event Approval(address indexed tokenOwner, address indexed spender, uint256 value);
    event Burn(address indexed from, uint256 value);

    constructor() {
        totalSupply = 1_000_000_000 * 10 ** uint256(decimals);
        balanceOf[msg.sender] = totalSupply;
        emit Transfer(address(0), msg.sender, totalSupply);
    }

    function transfer(address to, uint256 value) external returns (bool) {
        _transfer(msg.sender, to, value);
        return true;
    }

    function approve(address spender, uint256 value) external returns (bool) {
        allowance[msg.sender][spender] = value;
        emit Approval(msg.sender, spender, value);
        return true;
    }

    function transferFrom(address from, address to, uint256 value) external returns (bool) {
        uint256 allowed = allowance[from][msg.sender];
        require(allowed >= value, "GNCH: allowance vuot qua");
        if (allowed != type(uint256).max) {
            allowance[from][msg.sender] = allowed - value;
        }
        _transfer(from, to, value);
        return true;
    }

    /// @notice Đốt coin của chính người gọi — tổng cung giảm vĩnh viễn.
    function burn(uint256 value) external {
        require(balanceOf[msg.sender] >= value, "GNCH: so du khong du de dot");
        balanceOf[msg.sender] -= value;
        totalSupply -= value;
        emit Transfer(msg.sender, address(0), value);
        emit Burn(msg.sender, value);
    }

    function _transfer(address from, address to, uint256 value) internal {
        require(to != address(0), "GNCH: dia chi nhan khong hop le");
        require(balanceOf[from] >= value, "GNCH: so du khong du");
        balanceOf[from] -= value;
        balanceOf[to] += value;
        emit Transfer(from, to, value);
    }
}
