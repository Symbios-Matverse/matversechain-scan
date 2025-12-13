// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

contract PoLERegistry {
    event PoLERecorded(
        bytes32 indexed claimHash,
        address indexed submitter,
        uint8 verdict,          // 1=ACCEPT, 0=REJECT
        uint256 omega_u6,       // Ω * 1e6
        uint256 psi_u6,         // Ψ * 1e6
        uint256 cvar_u6,        // CVaR * 1e6
        uint256 latency_ms,
        bytes32 runHash,
        uint256 timestamp
    );

    function record(
        bytes32 claimHash,
        uint8 verdict,
        uint256 omega_u6,
        uint256 psi_u6,
        uint256 cvar_u6,
        uint256 latency_ms,
        bytes32 runHash
    ) external {
        require(claimHash != bytes32(0), "claimHash=0");
        require(runHash != bytes32(0), "runHash=0");
        emit PoLERecorded(
            claimHash,
            msg.sender,
            verdict,
            omega_u6,
            psi_u6,
            cvar_u6,
            latency_ms,
            runHash,
            block.timestamp
        );
    }
}
