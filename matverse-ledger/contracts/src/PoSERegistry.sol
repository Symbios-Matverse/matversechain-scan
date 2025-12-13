// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

contract PoSERegistry {
    event PoSERegistered(
        bytes32 indexed claimHash,
        address indexed submitter,
        string metadataURI,
        bytes32 proofHash,
        uint256 timestamp
    );

    mapping(bytes32 => bool) public exists;

    function register(bytes32 claimHash, string calldata metadataURI, bytes32 proofHash) external {
        require(claimHash != bytes32(0), "claimHash=0");
        require(!exists[claimHash], "already registered");
        exists[claimHash] = true;

        emit PoSERegistered(claimHash, msg.sender, metadataURI, proofHash, block.timestamp);
    }
}
