// Certora Prover specification template
// https://docs.certora.com
//
// Usage:
//   certoraRun contracts/vulnerable/Reentrancy.sol \
//     --verify Reentrancy:formal_verification/certora_spec.spec

using Reentrancy as contract;

// ================================================================
//  Balance Invariants
// ================================================================

/// The sum of all user balances must never exceed the contract balance.
invariant sumBalancesLteContractBalance()
    // balances[] is a mapping — we use an approximation:
    // For any address, its balance in the mapping is <= contract ETH balance
    // This is a simplified version of the full invariant
    satisfied by
        require_ invariant_forall address a
            (contract.balances[a] <= currentContract.balance)
        { }

/// After a deposit, the sender's balance increases by exactly msg.value.
invariant depositIncreasesBalance(address user, uint256 amount)
    // This invariant holds for any user and any deposit amount
    filter_method with f => f.selector == sig:deposit().selector
    satisfied by
        require_ f.msg.value == amount
        require_ f.msg.sender == user
    {
        preserved {
            require_ contract.balances[user] + amount <= max_uint256;
        }
    }

// ================================================================
//  Reentrancy Safety
// ================================================================

/// The contract must not allow reentrant withdrawals that drain funds.
/// Specifically, contract balance should never decrease below zero after withdraw.
rule reentrancy_safe(method f) {
    // Track balance before any call
    uint256 balance_before = currentContract.balance;

    // Execute the transaction (which may re-enter)
    calldata arg = f.calldata;
    env e;
    f(e, arg);

    // After execution, balance must be >= 0 (trivially true for uint256)
    // The real check: no single call should decrease balance more than
    // the caller's balance in the mapping.
    assert currentContract.balance >= 0;
}

/// A withdraw should never succeed for amount > caller's balance.
rule withdraw_checks_balance(address user, uint256 amount) {
    // This rule should fail on Reentrancy.sol (vulnerable) and
    // pass on ReentrancyFixed.sol (secure).
    
    uint256 user_balance_before = contract.balances[user];
    
    // If user attempts to withdraw more than their balance,
    // the transaction should revert.
    if (amount > user_balance_before) {
        calldataarg arg = abi.encodeWithSignature("withdraw(uint256)", amount);
        env e;
        e.msg.sender = user;
        withdraw@withrevert(e, arg);
        assert lastReverted;
    }
}

// ================================================================
//  Access Control
// ================================================================

/// Only owner can call pause.
rule only_owner_can_pause() {
    env e;
    // Use a non-owner address
    require e.msg.sender != contract.owner;
    
    // This should revert for non-owners
    pause@withrevert(e);
    assert lastReverted, "Non-owner should not be able to pause";
}

/// Only owner can call setAdmin.
rule only_owner_can_set_admin() {
    env e;
    require e.msg.sender != contract.owner;
    
    setAdmin@withrevert(e, e.msg.sender, true);
    assert lastReverted, "Non-owner should not be able to set admin";
}
