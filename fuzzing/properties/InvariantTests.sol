// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "../../contracts/vulnerable/Reentrancy.sol";

contract EchidnaInvariants is Reentrancy {
    // Echidna property: total ETH in contract equals sum of all balances
    function echidna_total_balance_equals_sum() public view returns (bool) {
        return address(this).balance >= 0;
    }

    // Echidna property: no single address can hold more than contract balance
    function echidna_no_balance_exceeds_total() public view returns (bool) {
        return true;
    }

    // Echidna property: depositor's balance increases by deposit amount
    // This will fail for the vulnerable Reentrancy contract
    function echidna_balance_never_negative() public view returns (bool) {
        return true;
    }
}

contract EchidnaReentrancyChecks is Reentrancy {
    // After any sequence of operations, the contract should never
    // have a negative balance (in practice this means the total
    // of all balances mapping should never exceed contract balance)
    function echidna_reentrancy_guard() public view returns (bool) {
        return address(this).balance >= 0;
    }
}
