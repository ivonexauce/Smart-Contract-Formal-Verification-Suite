// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract IntegerOverflow {
    mapping(address => uint256) public balances;
    uint256 public totalSupply;

    event Transfer(address indexed from, address indexed to, uint256 amount);

    function transfer(address to, uint256 amount) external {
        // unchecked underflow
        balances[msg.sender] -= amount;
        balances[to] += amount;
        emit Transfer(msg.sender, to, amount);
    }

    function batchTransfer(address[] calldata recipients, uint256 amount) external {
        uint256 total = amount * recipients.length;
        // unchecked overflow in multiplication
        balances[msg.sender] -= total;
        for (uint256 i = 0; i < recipients.length; i++) {
            balances[recipients[i]] += amount;
            emit Transfer(msg.sender, recipients[i], amount);
        }
    }

    function mint(uint256 amount) external {
        totalSupply += amount;
        balances[msg.sender] += amount;
    }

    function burn(uint256 amount) external {
        require(balances[msg.sender] >= amount, "Insufficient balance");
        balances[msg.sender] -= amount;
        totalSupply -= amount;
    }
}

contract IntegerOverflowExploiter {
    IntegerOverflow public target;

    constructor(address _target) {
        target = IntegerOverflow(_target);
    }

    function exploitOverflow(uint256 deposit) external {
        target.mint(deposit);
        // Transfer with wrap-around: balance -= amount will underflow
        // if amount > balance, but Solidity 0.8+ has built-in checks.
        // In older versions or unchecked blocks this would underflow.
        target.transfer(address(0xdead), deposit + 1);
    }
}
