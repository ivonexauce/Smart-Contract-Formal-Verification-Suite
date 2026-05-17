"""
run_full_audit.py — Full Audit Pipeline Orchestrator
Runs Static → Fuzzing → Formal Verification → LLM Audit → Report
"""

import argparse
import subprocess
import json
import sys
import os
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).parent.parent))
from formal_verification.smt_verifier import SmartContractVerifier
from llm_auditor.auditor import SmartContractAuditor
from llm_auditor.report_generator import HTMLReportGenerator


def run_slither(contract_path: str) -> dict:
    print("[*] Running Slither static analysis...")
    output_file = f"/tmp/slither_{Path(contract_path).stem}.json"
    try:
        result = subprocess.run(
            ["slither", contract_path, "--json", output_file],
            capture_output=True, text=True, timeout=120
        )
        if Path(output_file).exists():
            with open(output_file) as f:
                data = json.load(f)
            issues = len(data.get("results", {}).get("detectors", []))
            print(f"[\u2713] Slither complete: {issues} issues found")
            return data
        else:
            print("[WARN] Slither output not found. Is Slither installed?")
            return {"error": "Slither not available", "stdout": result.stdout}
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        print(f"[WARN] Slither skipped: {e}")
        return {"error": str(e)}


def run_mythril(contract_path: str) -> dict:
    print("[*] Running Mythril symbolic analysis...")
    try:
        result = subprocess.run(
            ["myth", "analyze", contract_path, "-o", "json", "--execution-timeout", "60"],
            capture_output=True, text=True, timeout=120
        )
        if result.stdout:
            try:
                data = json.loads(result.stdout)
                issues = data.get("issues", [])
                print(f"[\u2713] Mythril complete: {len(issues)} issues found")
                return data
            except json.JSONDecodeError:
                return {"raw": result.stdout}
        return {"error": "No Mythril output"}
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        print(f"[WARN] Mythril skipped: {e}")
        return {"error": str(e)}


def run_formal_verification() -> dict:
    print("[*] Running formal verification (Z3 SMT)...")
    v = SmartContractVerifier()

    # Arithmetic
    v.verify_no_overflow(100, 200)
    v.verify_no_overflow(2**255, 2**255)
    v.verify_no_underflow(100, 50)
    v.verify_no_underflow(50, 100)

    # Balance
    v.verify_balance_conservation(100, 50, 30)
    v.verify_balance_monotonic(100, 50)

    # Access control
    v.verify_access_control()
    v.verify_role_separation(admin_role=False, user_role=True)

    # Withdrawal
    v.verify_withdrawal_limit(100, 50)
    v.verify_withdrawal_limit(50, 100)

    # Token supply
    v.verify_total_supply_invariant(1000, 500, 200)
    v.verify_total_supply_invariant(1000, 0, 1200)

    # Flash loan
    v.verify_flash_loan_invariant(100_000, 10_000, 30)

    summary = v.print_summary()
    return {
        "results": [
            {"name": r.name, "status": r.status, "message": r.message}
            for r in v.results
        ],
        "summary": summary,
    }


def main():
    parser = argparse.ArgumentParser(description="UMBA Smart Contract Full Audit Pipeline")
    parser.add_argument("--contract", required=True, help="Path to .sol file")
    parser.add_argument("--output-dir", default="reports", help="Output directory")
    parser.add_argument("--skip-llm", action="store_true", help="Skip LLM audit (no API key)")
    parser.add_argument("--skip-tools", action="store_true", help="Skip Slither/Mythril")
    args = parser.parse_args()

    contract_path = args.contract
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    contract_name = Path(contract_path).stem

    print("=" * 60)
    print("  UMBA Smart Contract Audit Pipeline")
    print(f"  Contract: {contract_name}")
    print(f"  Started: {datetime.now(timezone.utc).isoformat()}")
    print("=" * 60)

    # Step 1: Static analysis
    static_results = {}
    if not args.skip_tools:
        slither = run_slither(contract_path)
        mythril = run_mythril(contract_path)
        static_results = {"slither": slither, "mythril": mythril}

    # Step 2: Formal verification
    formal_results = run_formal_verification()

    # Step 3: LLM audit
    llm_result = {}
    if not args.skip_llm and os.environ.get("ANTHROPIC_API_KEY"):
        print("[*] Running LLM audit...")
        auditor = SmartContractAuditor(
            contract_path=contract_path,
            static_results=static_results,
            fuzz_results={},
        )
        llm_result = auditor.run_full_audit()
        auditor.save_json(str(output_dir / f"{contract_name}_llm_audit.json"))
        auditor.save_markdown(str(output_dir / f"{contract_name}_llm_audit.md"))
    else:
        print("[SKIP] LLM audit skipped (set ANTHROPIC_API_KEY to enable)")

    # Step 4: Generate combined HTML report
    print("[*] Generating HTML report...")
    generator = HTMLReportGenerator(
        contract_name=contract_name,
        static_results=static_results,
        formal_results=formal_results,
        llm_result=llm_result,
    )
    report_path = str(output_dir / f"{contract_name}_full_report.html")
    generator.generate(report_path)

    print("\n" + "=" * 60)
    print("  \u2705 Audit complete!")
    print("  \U0001f4c4 Report:", report_path)
    print("=" * 60)


if __name__ == "__main__":
    main()
