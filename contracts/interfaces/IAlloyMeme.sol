// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

interface IAlloyMeme {
    function name() external view returns (string memory);
    function symbol() external view returns (string memory);
    function totalSupply() external view returns (uint256);
    function backingStock() external view returns (address);
    function pendingDividends(address holder) external view returns (uint256);
    function claimDividends() external;
    function distribute(uint256 amount) external;

    event DividendDistributed(uint256 amount);
    event DividendClaimed(address indexed holder, uint256 amount);
}
