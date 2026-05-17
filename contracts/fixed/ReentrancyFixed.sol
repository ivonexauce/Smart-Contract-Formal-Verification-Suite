// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title ReentrancyFixed — SECURE VERSION
 * @notice Demonstrates the correct fix for reentrancy using:
 *         1. Checks-Effects-Interactions (CEI) pattern
 *         2. ReentrancyGuard mutex lock
 */
contract ReentrancyGuard {
    bool private _locked;

    modifier nonReentrant() {
        require(!_locked, "ReentrancyGuard: reentrant call");
        _locked = true;
        _;
        _locked = false;
    }
}

contract ReentrancyFixed is ReentrancyGuard {
    mapping(address => uint256) public balances;

    event Deposited(address indexed user, uint256 amount);
    event Withdrawn(address indexed user, uint256 amount);

    function deposit() external payable {
        require(msg.value > 0, "Must deposit > 0");
        balances[msg.sender] += msg.value;
        emit Deposited(msg.sender, msg.value);
    }

    /**
     * @notice SECURE: Follows CEI pattern + nonReentrant guard.
     *         1. CHECK: Validate balance
     *         2. EFFECT: Update state BEFORE external call
     *         3. INTERACT: Transfer funds last
     */
    function withdraw(uint256 amount) external nonReentrant {
        // CHECK
        require(balances[msg.sender] >= amount, "Insufficient balance");

        // EFFECT — state updated BEFORE external call
        balances[msg.sender] -= amount;

        // INTERACT — external call LAST
        (bool success, ) = msg.sender.call{value: amount}("");
        require(success, "Transfer failed");

        emit Withdrawn(msg.sender, amount);
    }

    function getBalance() external view returns (uint256) {
        return address(this).balance;
    }
}
