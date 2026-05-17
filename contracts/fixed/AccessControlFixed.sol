// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/utils/Pausable.sol";

contract AccessControlFixed is AccessControl, Pausable {
    bytes32 public constant ADMIN_ROLE = keccak256("ADMIN_ROLE");
    bytes32 public constant WITHDRAWER_ROLE = keccak256("WITHDRAWER_ROLE");

    uint256 public treasury;

    event Deposited(address indexed from, uint256 amount);
    event Withdrawn(address indexed to, uint256 amount);

    constructor() {
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _grantRole(ADMIN_ROLE, msg.sender);
        _grantRole(WITHDRAWER_ROLE, msg.sender);
    }

    function withdraw(uint256 amount) external onlyRole(WITHDRAWER_ROLE) whenNotPaused {
        require(amount <= treasury, "Insufficient funds");
        treasury -= amount;
        (bool ok, ) = msg.sender.call{value: amount}("");
        require(ok, "Transfer failed");
        emit Withdrawn(msg.sender, amount);
    }

    function kill() external onlyRole(DEFAULT_ADMIN_ROLE) {
        selfdestruct(payable(msg.sender));
    }

    // Uses msg.sender, not tx.origin
    function delegateWithdraw(address to, uint256 amount) external onlyRole(WITHDRAWER_ROLE) {
        require(amount <= treasury, "Insufficient funds");
        treasury -= amount;
        (bool ok, ) = to.call{value: amount}("");
        require(ok, "Transfer failed");
        emit Withdrawn(to, amount);
    }

    receive() external payable {
        treasury += msg.value;
        emit Deposited(msg.sender, msg.value);
    }
}
