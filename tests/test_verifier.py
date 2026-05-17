"""
test_verifier.py — Unit tests for the Z3 formal verifier.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from formal_verification.smt_verifier import SmartContractVerifier, PropertyResult, Z3_AVAILABLE
import pytest


@pytest.fixture
def verifier():
    return SmartContractVerifier()


# ------------------------------------------------------------------
#  Availability
# ------------------------------------------------------------------

def test_z3_available():
    assert Z3_AVAILABLE, "z3-solver must be installed to run tests"


# ------------------------------------------------------------------
#  Arithmetic
# ------------------------------------------------------------------

class TestNoOverflow:
    def test_safe_addition(self, verifier):
        r = verifier.verify_no_overflow(100, 200)
        assert r.status == "PROVED", f"Expected PROVED, got {r.status}: {r.message}"

    def test_overflow_detected(self, verifier):
        r = verifier.verify_no_overflow(2**255, 2**255)
        assert r.status == "VIOLATED", f"Expected VIOLATED, got {r.status}: {r.message}"

    def test_max_uint256_edge(self, verifier):
        r = verifier.verify_no_overflow(2**256 - 1, 0)
        assert r.status == "PROVED", f"Expected PROVED, got {r.status}: {r.message}"

    def test_overflow_by_one(self, verifier):
        r = verifier.verify_no_overflow(2**256 - 1, 1)
        assert r.status == "VIOLATED", f"Expected VIOLATED, got {r.status}: {r.message}"


class TestNoUnderflow:
    def test_safe_subtraction(self, verifier):
        r = verifier.verify_no_underflow(100, 50)
        assert r.status == "PROVED", f"Expected PROVED, got {r.status}: {r.message}"

    def test_underflow_detected(self, verifier):
        r = verifier.verify_no_underflow(50, 100)
        assert r.status == "VIOLATED", f"Expected VIOLATED, got {r.status}: {r.message}"

    def test_equal_values(self, verifier):
        r = verifier.verify_no_underflow(100, 100)
        assert r.status == "PROVED", f"Expected PROVED, got {r.status}: {r.message}"


# ------------------------------------------------------------------
#  Balance
# ------------------------------------------------------------------

class TestBalanceConservation:
    def test_conservation_holds(self, verifier):
        r = verifier.verify_balance_conservation(100, 50, 30)
        assert r.status == "PROVED", f"Expected PROVED, got {r.status}: {r.message}"

    def test_no_deposit_no_withdraw(self, verifier):
        r = verifier.verify_balance_conservation(100, 0, 0)
        assert r.status == "PROVED", f"Expected PROVED, got {r.status}: {r.message}"

    def test_full_withdraw(self, verifier):
        r = verifier.verify_balance_conservation(100, 50, 150)
        assert r.status == "PROVED", f"Expected PROVED, got {r.status}: {r.message}"


class TestBalanceMonotonic:
    def test_monotonic_holds(self, verifier):
        r = verifier.verify_balance_monotonic(100, 50)
        assert r.status == "PROVED", f"Expected PROVED, got {r.status}: {r.message}"

    def test_large_deposit(self, verifier):
        r = verifier.verify_balance_monotonic(0, 10**18)
        assert r.status == "PROVED", f"Expected PROVED, got {r.status}: {r.message}"


# ------------------------------------------------------------------
#  Access Control
# ------------------------------------------------------------------

class TestAccessControl:
    def test_formula_soundness(self, verifier):
        r = verifier.verify_access_control()
        assert r.status == "PROVED", f"Expected PROVED, got {r.status}: {r.message}"


class TestRoleSeparation:
    def test_non_admin_cannot_act(self, verifier):
        r = verifier.verify_role_separation(admin_role=False, user_role=True)
        assert r.status == "PROVED", f"Expected PROVED, got {r.status}: {r.message}"

    def test_admin_can_act(self, verifier):
        r = verifier.verify_role_separation(admin_role=True, user_role=True)
        assert r.status == "PROVED", f"Expected PROVED, got {r.status}: {r.message}"


# ------------------------------------------------------------------
#  Withdrawal
# ------------------------------------------------------------------

class TestWithdrawalLimit:
    def test_withdrawal_within_balance(self, verifier):
        r = verifier.verify_withdrawal_limit(100, 50)
        assert r.status == "PROVED", f"Expected PROVED, got {r.status}: {r.message}"

    def test_withdrawal_exceeds_balance(self, verifier):
        r = verifier.verify_withdrawal_limit(50, 100)
        assert r.status == "VIOLATED", f"Expected VIOLATED, got {r.status}: {r.message}"

    def test_zero_withdrawal(self, verifier):
        r = verifier.verify_withdrawal_limit(100, 0)
        assert r.status == "PROVED", f"Expected PROVED, got {r.status}: {r.message}"

    def test_zero_balance(self, verifier):
        r = verifier.verify_withdrawal_limit(0, 0)
        assert r.status == "PROVED", f"Expected PROVED, got {r.status}: {r.message}"


# ------------------------------------------------------------------
#  Token Supply
# ------------------------------------------------------------------

class TestTotalSupplyInvariant:
    def test_normal_mint_burn(self, verifier):
        r = verifier.verify_total_supply_invariant(1000, 500, 200)
        assert r.status == "PROVED", f"Expected PROVED, got {r.status}: {r.message}"

    def test_burn_exceeds_supply(self, verifier):
        r = verifier.verify_total_supply_invariant(1000, 0, 1200)
        assert r.status == "PROVED", f"Expected PROVED, got {r.status}: {r.message}"

    def test_massive_mint(self, verifier):
        r = verifier.verify_total_supply_invariant(0, 2**200, 0)
        assert r.status == "PROVED", f"Expected PROVED, got {r.status}: {r.message}"


# ------------------------------------------------------------------
#  Flash Loan
# ------------------------------------------------------------------

class TestFlashLoanInvariant:
    def test_repay_with_fee(self, verifier):
        r = verifier.verify_flash_loan_invariant(100_000, 10_000, 30)
        assert r.status == "PROVED", f"Expected PROVED, got {r.status}: {r.message}"

    def test_zero_fee(self, verifier):
        r = verifier.verify_flash_loan_invariant(100_000, 10_000, 0)
        assert r.status == "PROVED", f"Expected PROVED, got {r.status}: {r.message}"


# ------------------------------------------------------------------
#  Print Summary (smoke test)
# ------------------------------------------------------------------

def test_print_summary(verifier):
    verifier.verify_no_overflow(1, 2)
    verifier.verify_access_control()
    summary = verifier.print_summary()
    assert isinstance(summary, dict)
    assert "proved" in summary
    assert "violated" in summary
    assert "unknown" in summary
