#!/usr/bin/env python3
"""
run_slither.py — Standalone Slither static analysis wrapper.
Outputs results as JSON for downstream consumption by the LLM audit engine.
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Run Slither static analysis")
    parser.add_argument("--contract", required=True, help="Path to .sol file")
    parser.add_argument("--output", help="Output JSON path (default: stdout)")
    parser.add_argument("--timeout", type=int, default=120, help="Timeout in seconds")
    args = parser.parse_args()

    contract_path = Path(args.contract)
    if not contract_path.exists():
        print(f"[ERROR] Contract not found: {contract_path}", file=sys.stderr)
        sys.exit(1)

    output_file = f"/tmp/slither_{contract_path.stem}.json"

    try:
        result = subprocess.run(
            ["slither", str(contract_path), "--json", output_file],
            capture_output=True, text=True, timeout=args.timeout,
        )

        if Path(output_file).exists():
            with open(output_file) as f:
                data = json.load(f)
            issues = len(data.get("results", {}).get("detectors", []))
            print(f"[*] Slither found {issues} issues", file=sys.stderr)
        else:
            data = {
                "error": "Slither produced no output",
                "stderr": result.stderr,
                "stdout": result.stdout,
            }
            print(f"[WARN] Slither output not found", file=sys.stderr)

        if args.output:
            with open(args.output, "w") as f:
                json.dump(data, f, indent=2)
            print(f"[*] Results saved to {args.output}", file=sys.stderr)
        else:
            print(json.dumps(data, indent=2))

    except FileNotFoundError:
        print("[ERROR] Slither not installed. Run: pip install slither-analyzer", file=sys.stderr)
        sys.exit(1)
    except subprocess.TimeoutExpired:
        print(f"[ERROR] Slither timed out after {args.timeout}s", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
