// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

interface IUniswapPair {
    function getReserves() external view returns (uint112, uint112, uint32);
    function swap(uint256, uint256, address, bytes calldata) external;
}

contract OracleManipulation {
    IUniswapPair public pair;
    address public token0;
    address public token1;

    uint256 public lastPrice;
    uint256 public updatedAt;

    event PriceUpdated(uint256 price);

    constructor(address _pair) {
        pair = IUniswapPair(_pair);
    }

    // VULNERABILITY: uses spot price from a single AMM pool as oracle
    // An attacker can manipulate the pool reserves with a flash loan
    // and trigger a price update that benefits them
    function updatePrice() external {
        (uint112 reserve0, uint112 reserve1, ) = pair.getReserves();
        // VULNERABILITY: no TWAP, no multiple sources, no sanity check
        lastPrice = (uint256(reserve1) * 1e18) / reserve0;
        updatedAt = block.timestamp;
        emit PriceUpdated(lastPrice);
    }

    function getPrice() external view returns (uint256) {
        require(updatedAt > 0, "Price not set");
        return lastPrice;
    }

    // VULNERABILITY: uses manipulated oracle price
    // Borrower can deposit less collateral when price is manipulated high
    // or borrow more when price is manipulated
    mapping(address => uint256) public deposits;
    mapping(address => uint256) public borrows;
    uint256 public collateralRatio = 150; // 150%

    function depositCollateral() external payable {
        deposits[msg.sender] += msg.value;
    }

    function borrow(uint256 usdAmount) external {
        // VULNERABILITY: oracle price can be manipulated
        uint256 price = getPrice();
        // Collateral value in USD = deposit * price / 1e18
        uint256 collateralValue = (deposits[msg.sender] * price) / 1e18;
        require(
            collateralValue * 100 >= (borrows[msg.sender] + usdAmount) * collateralRatio,
            "Insufficient collateral"
        );
        borrows[msg.sender] += usdAmount;
        (bool ok, ) = msg.sender.call{value: usdAmount}("");
        require(ok, "Transfer failed");
    }

    // VULNERABILITY: no access control on liquidate
    function liquidate(address user) external {
        uint256 price = getPrice();
        uint256 collateralValue = (deposits[user] * price) / 1e18;
        if (collateralValue * 100 < borrows[user] * collateralRatio) {
            uint256 reward = deposits[user];
            deposits[user] = 0;
            borrows[user] = 0;
            (bool ok, ) = msg.sender.call{value: reward}("");
            require(ok, "Transfer failed");
        }
    }
}

contract OracleExploiter {
    OracleManipulation public target;
    IUniswapPair public pair;

    constructor(address _target, address _pair) {
        target = OracleManipulation(_target);
        pair = IUniswapPair(_pair);
    }

    // Exploit: manipulate pool reserves then borrow against inflated collateral
    function exploit() external payable {
        // 1. Manipulate price by swapping in the pool
        // (simplified — real attack uses flash loan for massive swap)

        // 2. Trigger price update
        target.updatePrice();

        // 3. Deposit small collateral
        target.depositCollateral{value: msg.value}();

        // 4. Borrow more than should be allowed
        target.borrow(address(this).balance * 10);
    }
}
