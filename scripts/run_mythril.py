#!/usr/bin/env python3
"""
run_mythril.py — Standalone Mythril symbolic analysis wrapper.
Outputs results as JSON for downstream consumption by the LLM audit engine.
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Run Mythril symbolic analysis")
    parser.add_argument("--contract", required=True, help="Path to .sol file")
    parser.add_argument("--output", help="Output JSON path (default: stdout)")
    parser.add_argument("--timeout", type=int, default=120, help="Execution timeout in seconds")
    args = parser.parse_args()

    contract_path = Path(args.contract)
    if not contract_path.exists():
        print(f"[ERROR] Contract not found: {contract_path}", file=sys.stderr)
        sys.exit(1)

    try:
        result = subprocess.run(
            [
                "myth", "analyze", str(contract_path),
                "-o", "json",
                "--execution-timeout", str(args.timeout),
            ],
            capture_output=True, text=True, timeout=args.timeout + 30,
        )

        data = {}
        if result.stdout:
            try:
                data = json.loads(result.stdout)
                issues = len(data.get("issues", []))
                print(f"[*] Mythril found {issues} issues", file=sys.stderr)
            except json.JSONDecodeError:
                data = {"raw_output": result.stdout}
                print("[WARN] Could not parse Mythril output as JSON", file=sys.stderr)
        else:
            data = {"error": "No Mythril output", "stderr": result.stderr}
            print("[WARN] No Mythril output", file=sys.stderr)

        if args.output:
            with open(args.output, "w") as f:
                json.dump(data, f, indent=2)
            print(f"[*] Results saved to {args.output}", file=sys.stderr)
        else:
            print(json.dumps(data, indent=2))

    except FileNotFoundError:
        print("[ERROR] Mythril not installed. Run: pip install mythril", file=sys.stderr)
        sys.exit(1)
    except subprocess.TimeoutExpired:
        print(f"[ERROR] Mythril timed out after {args.timeout}s", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
