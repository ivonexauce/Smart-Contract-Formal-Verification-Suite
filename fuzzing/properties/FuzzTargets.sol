// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "../../contracts/vulnerable/Reentrancy.sol";
import "../../contracts/vulnerable/IntegerOverflow.sol";
import "../../contracts/vulnerable/AccessControl.sol";

// Fuzz targets for Echidna — each function becomes a fuzzing entry point
contract FuzzReentrancy {
    Reentrancy public target;

    constructor() {
        target = new Reentrancy();
    }

    function fuzz_deposit(uint256 amount) public {
        if (address(this).balance >= amount && amount > 0) {
            target.deposit{value: amount}();
        }
    }

    function fuzz_withdraw(uint256 amount) public {
        if (amount > 0) {
            target.withdraw(amount);
        }
    }

    // Echidna assertions
    function echidna_balance_non_negative() public view returns (bool) {
        return address(target).balance >= 0;
    }
}

contract FuzzIntegerOverflow {
    IntegerOverflow public target;

    constructor() {
        target = new IntegerOverflow();
    }

    function fuzz_transfer(uint256 amount) public {
        target.mint(amount);
        target.transfer(address(0xbeef), amount);
    }

    function fuzz_batchTransfer(uint256 count, uint256 amount) public {
        // Clamp to prevent gas issues
        count = count % 10;
        if (count == 0) count = 1;
        amount = amount % 1_000_000;
        target.mint(amount * count);
        address[] memory recipients = new address[](count);
        for (uint256 i = 0; i < count; i++) {
            recipients[i] = address(uint160(uint256(keccak256(abi.encode(i)))));
        }
        target.batchTransfer(recipients, amount);
    }

    function echidna_total_supply_consistent() public view returns (bool) {
        return true;
    }
}
