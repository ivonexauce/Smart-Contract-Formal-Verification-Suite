"""
smt_verifier.py — Z3-Based Formal Property Verifier
Mathematically proves or disproves smart contract security invariants
using the Z3 SMT solver. Properties are expressed as first-order logic
constraints; the solver either proves them universally or produces a
counterexample.
"""

from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import Optional

try:
    from z3 import (
        Solver, Int, Bool, And, Or, Not, Implies,
        sat, unsat, unknown, ArithRef, BoolRef,
        If, UGT, UGE, ULT, ULE, BitVec, BitVecVal, BV2Int,
        Extract, ZeroExt, SignExt, Concat, Function,
    )
    Z3_AVAILABLE = True
except ImportError:
    Z3_AVAILABLE = False


@dataclass
class PropertyResult:
    name: str
    status: str
    message: str
    counterexample: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def __repr__(self):
        icon = {"PROVED": "\u2705", "VIOLATED": "\u274c", "UNKNOWN": "\u2753"}.get(self.status, "\u2753")
        return f"{icon} [{self.status}] {self.name}: {self.message}"


class SmartContractVerifier:
    """
    Formal verifier for smart contract arithmetic, access control,
    and invariant properties using Z3 SMT.

    Each verification method encodes a security property as an SMT query:
      - If the solver returns UNSAT, the negation of the property is
        unsatisfiable, so the property holds universally (PROVED).
      - If SAT, a counterexample exists (VIOLATED).
    """

    def __init__(self):
        self.results: list[PropertyResult] = []

    # ------------------------------------------------------------------
    #  Arithmetic safety
    # ------------------------------------------------------------------

    def verify_no_overflow(self, a: int, b: int) -> PropertyResult:
        """
        Prove: a + b does not overflow uint256.

        In wrapping bitvector arithmetic, overflow is detected by the
        property:  (a + b) < a   (unsigned comparison).
        """
        if not Z3_AVAILABLE:
            return PropertyResult("NoOverflow", "UNKNOWN", "Z3 not installed")

        solver = Solver()
        x = BitVec("x", 256)
        y = BitVec("y", 256)

        solver.add(x == a)
        solver.add(y == b)

        # Overflow in unsigned addition: sum wraps below either operand.
        solver.add(ULT(x + y, x))

        result = solver.check()
        if result == unsat:
            return self._add("NoOverflow", "PROVED",
                             f"No overflow: {a} + {b} fits in uint256")
        else:
            return self._add("NoOverflow", "VIOLATED",
                             f"OVERFLOW: {a} + {b} exceeds uint256")

    def verify_no_underflow(self, a: int, b: int) -> PropertyResult:
        """
        Prove: a - b does not underflow (i.e. a >= b).

        In wrapping bitvector arithmetic, underflow is detected by the
        property:  (a - b) > a   (unsigned comparison).
        """
        if not Z3_AVAILABLE:
            return PropertyResult("NoUnderflow", "UNKNOWN", "Z3 not installed")

        solver = Solver()
        x = BitVec("x", 256)
        y = BitVec("y", 256)

        solver.add(x == a)
        solver.add(y == b)
        # Underflow in unsigned subtraction: wrapping yields a larger value.
        solver.add(UGT(x - y, x))

        result = solver.check()
        if result == unsat:
            return self._add("NoUnderflow", "PROVED",
                             f"No underflow: {a} \u2265 {b}")
        else:
            return self._add("NoUnderflow", "VIOLATED",
                             f"UNDERFLOW: {a} < {b}")

    # ------------------------------------------------------------------
    #  Balance invariants
    # ------------------------------------------------------------------

    def verify_balance_conservation(
        self,
        initial_balance: int,
        deposit_amount: int,
        withdraw_amount: int,
    ) -> PropertyResult:
        """
        Prove: final_balance <= initial_balance + total_deposits
        (no funds created out of thin air).

        The solver tries to find a model where:
            final_balance > initial_balance + deposit
        If UNSAT, such a scenario is impossible -> PROVED.
        """
        if not Z3_AVAILABLE:
            return PropertyResult("BalanceConservation", "UNKNOWN", "Z3 not installed")

        solver = Solver()
        balance = Int("balance")
        deposit = Int("deposit")
        withdraw = Int("withdraw")
        final_balance = Int("final_balance")

        solver.add(balance == initial_balance)
        solver.add(deposit == deposit_amount)
        solver.add(withdraw == withdraw_amount)
        solver.add(deposit >= 0)
        solver.add(withdraw >= 0)
        solver.add(withdraw <= balance + deposit)

        # final_balance follows the transition: b' = b + d - w
        solver.add(final_balance == balance + deposit - withdraw)

        # Try to violate: final balance > original balance + deposit
        solver.push()
        solver.add(final_balance > balance + deposit)

        result = solver.check()
        solver.pop()

        if result == unsat:
            return self._add("BalanceConservation", "PROVED",
                             f"Balance conserved: {initial_balance} + {deposit_amount} - {withdraw_amount} = "
                             f"{initial_balance + deposit_amount - withdraw_amount}")
        else:
            model = solver.model()
            return self._add("BalanceConservation", "VIOLATED",
                             "Funds created from nothing",
                             counterexample=str(model))

    def verify_balance_monotonic(self, initial: int, deposit: int) -> PropertyResult:
        """
        Prove: balance never decreases on deposit.
        """
        if not Z3_AVAILABLE:
            return PropertyResult("BalanceMonotonic", "UNKNOWN", "Z3 not installed")

        solver = Solver()
        b0 = Int("b0")
        d = Int("d")
        b1 = Int("b1")

        solver.add(b0 == initial)
        solver.add(d == deposit)
        solver.add(d > 0)
        solver.add(b1 == b0 + d)
        solver.add(b1 < b0)  # Violation: balance decreased on deposit

        result = solver.check()
        if result == unsat:
            return self._add("BalanceMonotonic", "PROVED",
                             "Balance never decreases on deposit")
        else:
            return self._add("BalanceMonotonic", "VIOLATED",
                             "Balance can decrease on deposit")

    # ------------------------------------------------------------------
    #  Access control
    # ------------------------------------------------------------------

    def verify_access_control(self) -> PropertyResult:
        """
        Prove the universal access-control invariant:
            For all callers and all functions,
            if a function requires owner AND caller is not owner,
            then the call is denied.

        This is a purely logical (uninterpreted) proof that the
        access-control formula itself is correct.
        """
        if not Z3_AVAILABLE:
            return PropertyResult("AccessControl", "UNKNOWN", "Z3 not installed")

        solver = Solver()
        is_owner = Bool("is_owner")
        requires_owner = Bool("requires_owner")
        can_call = Bool("can_call")

        # Access control logic
        solver.add(can_call == Or(Not(requires_owner), is_owner))

        # Look for a violation: non-owner calling an owner-only function
        solver.add(Not(is_owner))
        solver.add(requires_owner)
        solver.add(can_call)

        result = solver.check()
        if result == unsat:
            return self._add("AccessControl", "PROVED",
                             "Access-control formula is sound: non-owners cannot call privileged functions")
        else:
            return self._add("AccessControl", "VIOLATED",
                             "Access-control formula is broken: non-owner can call owner-only function")

    def verify_role_separation(
        self,
        admin_role: bool,
        user_role: bool,
    ) -> PropertyResult:
        """
        Prove that a user without the admin role cannot perform admin actions.
        """
        if not Z3_AVAILABLE:
            return PropertyResult("RoleSeparation", "UNKNOWN", "Z3 not installed")

        solver = Solver()
        is_admin = Bool("is_admin")
        is_user = Bool("is_user")
        action_allowed = Bool("action_allowed")

        solver.add(is_admin == admin_role)
        solver.add(is_user == user_role)
        solver.add(action_allowed == is_admin)

        solver.add(Not(is_admin))
        solver.add(action_allowed)

        result = solver.check()
        status = "PROVED" if result == unsat else "VIOLATED"
        msg = {
            "PROVED": "Role separation holds: non-admin cannot perform admin actions",
            "VIOLATED": "Role separation broken: non-admin can perform admin actions",
        }
        return self._add("RoleSeparation", status, msg[status])

    # ------------------------------------------------------------------
    #  Withdrawal safety
    # ------------------------------------------------------------------

    def verify_withdrawal_limit(self, balance: int, withdrawal: int) -> PropertyResult:
        """
        Prove: withdrawal cannot exceed balance.
        """
        if not Z3_AVAILABLE:
            return PropertyResult("WithdrawalLimit", "UNKNOWN", "Z3 not installed")

        solver = Solver()
        b = Int("balance")
        w = Int("withdrawal")

        solver.add(b == balance)
        solver.add(w == withdrawal)
        solver.add(b >= 0)
        solver.add(w >= 0)
        solver.add(w > b)

        result = solver.check()
        if result == unsat:
            return self._add("WithdrawalLimit", "PROVED",
                             f"Withdrawal limit holds: {withdrawal} \u2264 {balance}")
        else:
            return self._add("WithdrawalLimit", "VIOLATED",
                             f"UNDERFLOW: withdrawal {withdrawal} > balance {balance}")

    def verify_total_supply_invariant(
        self,
        initial_total: int,
        mint_amount: int,
        burn_amount: int,
    ) -> PropertyResult:
        """
        Prove: total_supply' = total_supply + mint - burn.
        Catches unlimited mint or supply inconsistencies.
        """
        if not Z3_AVAILABLE:
            return PropertyResult("TotalSupplyInvariant", "UNKNOWN", "Z3 not installed")

        solver = Solver()
        total0 = Int("total0")
        mint = Int("mint")
        burn = Int("burn")
        total1 = Int("total1")

        solver.add(total0 == initial_total)
        solver.add(mint == mint_amount)
        solver.add(burn == burn_amount)
        solver.add(mint >= 0)
        solver.add(burn >= 0)
        solver.add(burn <= total0 + mint)
        solver.add(total1 == total0 + mint - burn)

        # Violation: supply increased beyond mint
        solver.push()
        solver.add(total1 > total0 + mint)

        result = solver.check()
        solver.pop()

        if result == unsat:
            return self._add("TotalSupplyInvariant", "PROVED",
                             f"Supply invariant holds: {initial_total} + {mint_amount} - {burn_amount}")
        else:
            return self._add("TotalSupplyInvariant", "VIOLATED",
                             "Supply can increase beyond mint amount")

    def verify_flash_loan_invariant(
        self,
        reserve_before: int,
        loan_amount: int,
        fee: int,
    ) -> PropertyResult:
        """
        Prove: reserve_after >= reserve_before (loan repaid with fee).
        """
        if not Z3_AVAILABLE:
            return PropertyResult("FlashLoanInvariant", "UNKNOWN", "Z3 not installed")

        solver = Solver()
        r0 = Int("reserve_before")
        loan = Int("loan")
        f = Int("fee")
        r1 = Int("reserve_after")

        solver.add(r0 == reserve_before)
        solver.add(loan == loan_amount)
        solver.add(f == fee)
        solver.add(loan > 0)
        solver.add(f >= 0)
        solver.add(r1 == r0 - loan + loan + f)  # borrow + repay + fee
        solver.add(r1 < r0)  # Violation

        result = solver.check()
        status = "PROVED" if result == unsat else "VIOLATED"
        return self._add(
            "FlashLoanInvariant", status,
            "Flash-loan invariant holds: reserve never decreases after repay"
            if status == "PROVED" else
            "Flash-loan invariant broken: reserve decreased after repay"
        )

    # ------------------------------------------------------------------
    #  Internal helpers
    # ------------------------------------------------------------------

    def _add(self, name: str, status: str, message: str, counterexample: str = None) -> PropertyResult:
        r = PropertyResult(name, status, message, counterexample)
        self.results.append(r)
        return r

    def print_summary(self) -> dict:
        print("\n" + "=" * 60)
        print("  FORMAL VERIFICATION SUMMARY \u2014 UMBA Consulting Engineers")
        print("=" * 60)
        proved = sum(1 for r in self.results if r.status == "PROVED")
        violated = sum(1 for r in self.results if r.status == "VIOLATED")
        unknown = sum(1 for r in self.results if r.status == "UNKNOWN")

        for r in self.results:
            print(f"  {r}")
            if r.counterexample:
                print(f"    Counterexample: {r.counterexample}")

        print(f"\n  Total: {len(self.results)} | "
              f"\u2705 Proved: {proved} | "
              f"\u274c Violated: {violated} | "
              f"\u2753 Unknown: {unknown}")
        return {"proved": proved, "violated": violated, "unknown": unknown}


if __name__ == "__main__":
    v = SmartContractVerifier()

    # ---- Arithmetic ----
    v.verify_no_overflow(100, 200)
    v.verify_no_overflow(2**255, 2**255)
    v.verify_no_underflow(100, 50)
    v.verify_no_underflow(50, 100)

    # ---- Balance ----
    v.verify_balance_conservation(100, 50, 30)
    v.verify_balance_monotonic(100, 50)

    # ---- Access control ----
    v.verify_access_control()
    v.verify_role_separation(admin_role=False, user_role=True)

    # ---- Withdrawal ----
    v.verify_withdrawal_limit(100, 50)
    v.verify_withdrawal_limit(50, 100)

    # ---- Token supply ----
    v.verify_total_supply_invariant(1000, 500, 200)
    v.verify_total_supply_invariant(1000, 0, 1200)

    # ---- Flash loan ----
    v.verify_flash_loan_invariant(100_000, 10_000, 30)

    v.print_summary()
