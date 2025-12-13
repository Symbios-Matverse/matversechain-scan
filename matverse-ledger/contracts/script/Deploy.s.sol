// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "forge-std/Script.sol";
import "../src/PoSERegistry.sol";
import "../src/PoLERegistry.sol";

contract Deploy is Script {
    function run() external {
        vm.startBroadcast();
        new PoSERegistry();
        new PoLERegistry();
        vm.stopBroadcast();
    }
}
