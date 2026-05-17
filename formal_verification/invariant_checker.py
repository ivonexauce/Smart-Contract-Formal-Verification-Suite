"""
invariant_checker.py — On-Chain Invariant Verifier
Checks runtime invariants against deployed contracts via RPC,
complementing the SMT-based static formal verification.
"""

import os
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

try:
    from web3 import Web3
    from web3.exceptions import ContractLogicError
    WEB3_AVAILABLE = True
except ImportError:
    WEB3_AVAILABLE = False


class InvariantCheckResult:
    def __init__(self, name: str, passed: bool, message: str, detail: str = ""):
        self.name = name
        self.passed = passed
        self.message = message
        self.detail = detail
        self.timestamp = datetime.now(timezone.utc).isoformat()

    def __repr__(self):
        icon = "\u2705" if self.passed else "\u274c"
        return f"{icon} [{('PASS' if self.passed else 'FAIL')}] {self.name}: {self.message}"


class InvariantChecker:
    """
    Connects to an Ethereum RPC endpoint and checks on-chain invariants
    for a deployed contract at a given address.
    """

    def __init__(self, rpc_url: Optional[str] = None):
        self.rpc_url = rpc_url or os.environ.get("ETH_RPC_URL", "http://127.0.0.1:8545")
        self.w3: Optional[Web3] = None
        self.results: list[InvariantCheckResult] = []

    def connect(self) -> bool:
        if not WEB3_AVAILABLE:
            print("[WARN] web3.py not installed. Run: pip install web3")
            return False
        self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))
        if not self.w3.is_connected():
            print(f"[WARN] Cannot connect to {self.rpc_url}")
            return False
        print(f"[*] Connected to {self.rpc_url} (chain ID: {self.w3.eth.chain_id})")
        return True

    def check_total_supply(self, token_address: str, expected_supply: int = 0) -> InvariantCheckResult:
        """Verify totalSupply matches expected value."""
        if not self.w3 or not self.w3.is_connected():
            return InvariantCheckResult("TotalSupply", False, "Not connected to RPC")

        checksum = self.w3.to_checksum_address(token_address)
        abi = json.loads('[{"constant":true,"inputs":[],"name":"totalSupply","outputs":[{"name":"","type":"uint256"}],"type":"function"}]')
        contract = self.w3.eth.contract(address=checksum, abi=abi)

        try:
            actual = contract.functions.totalSupply().call()
            if expected_supply == 0 or actual == expected_supply:
                r = InvariantCheckResult("TotalSupply", True,
                                         f"totalSupply = {actual}")
            else:
                r = InvariantCheckResult("TotalSupply", False,
                                         f"totalSupply mismatch: got {actual}, expected {expected_supply}")
        except Exception as e:
            r = InvariantCheckResult("TotalSupply", False, f"Query failed: {e}")

        self.results.append(r)
        return r

    def check_balance_sum(self, token_address: str, holders: list[str]) -> InvariantCheckResult:
        """
        For ERC-20 tokens: verify that the sum of all holder balances
        does not exceed totalSupply (basic invariant).
        """
        if not self.w3 or not self.w3.is_connected():
            return InvariantCheckResult("BalanceSum", False, "Not connected to RPC")

        checksum = self.w3.to_checksum_address(token_address)
        abi = json.loads('[{"constant":true,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"","type":"uint256"}],"type":"function"},{"constant":true,"inputs":[],"name":"totalSupply","outputs":[{"name":"","type":"uint256"}],"type":"function"}]')
        contract = self.w3.eth.contract(address=checksum, abi=abi)

        try:
            total_supply = contract.functions.totalSupply().call()
            sum_balances = 0
            for h in holders:
                sum_balances += contract.functions.balanceOf(self.w3.to_checksum_address(h)).call()

            if sum_balances <= total_supply:
                r = InvariantCheckResult("BalanceSum", True,
                                         f"Sum balances ({sum_balances}) \u2264 totalSupply ({total_supply})")
            else:
                r = InvariantCheckResult("BalanceSum", False,
                                         f"Sum balances ({sum_balances}) > totalSupply ({total_supply})")
        except Exception as e:
            r = InvariantCheckResult("BalanceSum", False, f"Query failed: {e}")

        self.results.append(r)
        return r

    def check_ownership(self, contract_address: str, expected_owner: str) -> InvariantCheckResult:
        """Verify the contract owner matches the expected address."""
        if not self.w3 or not self.w3.is_connected():
            return InvariantCheckResult("Ownership", False, "Not connected to RPC")

        checksum = self.w3.to_checksum_address(contract_address)
        abi = json.loads('[{"constant":true,"inputs":[],"name":"owner","outputs":[{"name":"","type":"address"}],"type":"function"}]')
        contract = self.w3.eth.contract(address=checksum, abi=abi)

        try:
            actual_owner = contract.functions.owner().call()
            expected = self.w3.to_checksum_address(expected_owner)
            if actual_owner == expected:
                r = InvariantCheckResult("Ownership", True,
                                         f"Owner matches: {actual_owner}")
            else:
                r = InvariantCheckResult("Ownership", False,
                                         f"Owner mismatch: got {actual_owner}, expected {expected}")
        except Exception as e:
            r = InvariantCheckResult("Ownership", False, f"Query failed: {e}")

        self.results.append(r)
        return r

    def print_summary(self) -> dict:
        print("\n" + "=" * 60)
        print("  ON-CHAIN INVARIANT CHECK SUMMARY")
        print("=" * 60)
        passed = sum(1 for r in self.results if r.passed)
        failed = sum(1 for r in self.results if not r.passed)

        for r in self.results:
            print(f"  {r}")
            if r.detail:
                print(f"    Detail: {r.detail}")

        print(f"\n  Total: {len(self.results)} | \u2705 Passed: {passed} | \u274c Failed: {failed}")
        return {"passed": passed, "failed": failed, "total": len(self.results)}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="On-Chain Invariant Checker")
    parser.add_argument("--rpc", default="http://127.0.0.1:8545", help="Ethereum RPC URL")
    args = parser.parse_args()

    checker = InvariantChecker(rpc_url=args.rpc)
    if not checker.connect():
        print("[SKIP] No RPC connection. Run a local node (anvil/hardhat) or use --rpc")
        exit(0)

    print("[*] No contract address specified. Running in demo mode.")
    print("[*] Use via Python API: InvariantChecker().check_total_supply(...)")
    checker.print_summary()
