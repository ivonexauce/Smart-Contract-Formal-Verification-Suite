#!/usr/bin/env bash
set -euo pipefail
# Echidna fuzzing runner for Smart Contract Formal Verification Suite
# Usage: ./run_echidna.sh <contract.sol> [contract_name]

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
CONTRACT="${1:-$PROJECT_DIR/contracts/vulnerable/Reentrancy.sol}"
CONTRACT_NAME="${2:-Reentrancy}"
CONFIG="$SCRIPT_DIR/echidna_config.yaml"
CORPUS_DIR="$SCRIPT_DIR/corpus"
REPORT_DIR="$PROJECT_DIR/reports/fuzzing"

mkdir -p "$CORPUS_DIR" "$REPORT_DIR"

echo "============================================"
echo "  Echidna Fuzzing Campaign"
echo "  Contract: $CONTRACT_NAME ($CONTRACT)"
echo "  Config:   $CONFIG"
echo "  Corpus:   $CORPUS_DIR"
echo "============================================"

if ! command -v echidna &>/dev/null && ! command -v echidna-test &>/dev/null; then
    echo "[ERROR] Echidna not found. Install from: https://github.com/crytic/echidna"
    echo "  macOS: brew install echidna"
    echo "  Docker: docker pull trailofbits/echidna"
    exit 1
fi

ECHIDNA_CMD="echidna-test"
command -v echidna &>/dev/null && ECHIDNA_CMD="echidna"

echo "[*] Running Echidna fuzzer..."
"$ECHIDNA_CMD" \
    "$CONTRACT" \
    --config "$CONFIG" \
    --contract "$CONTRACT_NAME" \
    --corpus-dir "$CORPUS_DIR" \
    2>&1 | tee "$REPORT_DIR/${CONTRACT_NAME}_echidna.log"

echo "[*] Fuzzing complete. Log: $REPORT_DIR/${CONTRACT_NAME}_echidna.log"
