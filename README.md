# 🔐 Smart-Contract-Formal-Verification-Suite

![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![Solidity](https://img.shields.io/badge/Solidity-0.8.x-purple.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)
![Status](https://img.shields.io/badge/Status-Active-green.svg)

> **Beyond Slither — Multi-Layer Smart Contract Security: Fuzzing + Formal Verification + LLM-Assisted Audit Reports**

Built by **UMBA YANGA IVON EXAUCE** — Deep-Tech Systems Architect & Innovation Strategist | UMBA Consulting Engineers

---

## 🎯 Overview

Most smart contract audit tools operate at a single layer. This suite combines **three complementary security methodologies** into one unified pipeline:

| Layer | Tool | Technique |
|---|---|---|
| Static Analysis | Slither | Pattern-based vulnerability detection |
| Fuzzing | Echidna | Property-based random input testing |
| Formal Verification | Custom SMT | Mathematical correctness proofs |
| LLM Audit | Claude/GPT API | Plain-English vulnerability explanations |

This moves your security posture from **"we ran Slither"** to **"we formally verified correctness and have an LLM-generated executive audit report"** — the standard used by top-tier Web3 security firms like Trail of Bits and OpenZeppelin.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│              INPUT: Solidity Smart Contract               │
└──────────────────────────┬──────────────────────────────┘
                           │
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
  ┌───────────────┐ ┌─────────────┐ ┌──────────────────┐
  │ STATIC LAYER  │ │ FUZZ LAYER  │ │  FORMAL LAYER    │
  │   Slither     │ │   Echidna   │ │  SMT / Z3        │
  │   Mythril     │ │   Medusa    │ │  Invariant check │
  └──────┬────────┘ └──────┬──────┘ └────────┬─────────┘
         │                 │                  │
         └─────────────────┼──────────────────┘
                           ▼
              ┌────────────────────────┐
              │   LLM AUDIT ENGINE     │
              │  Plain-English Report  │
              │  Severity Scoring      │
              │  Remediation Advice    │
              └────────────┬───────────┘
                           ▼
              ┌────────────────────────┐
              │   HTML/PDF REPORT      │
              │   Executive Summary    │
              │   Developer Checklist  │
              └────────────────────────┘
```

---

## 📁 Project Structure

```
Smart-Contract-Formal-Verification-Suite/
│
├── contracts/
│   ├── vulnerable/
│   │   ├── Reentrancy.sol           # Classic reentrancy attack
│   │   ├── IntegerOverflow.sol      # Overflow/underflow vulnerability
│   │   ├── AccessControl.sol        # Broken access control
│   │   ├── FlashLoanVuln.sol        # Flash loan attack surface
│   │   └── OracleManipulation.sol   # Price oracle manipulation
│   └── fixed/
│       ├── ReentrancyFixed.sol      # Patched with ReentrancyGuard
│       └── AccessControlFixed.sol   # Patched with OpenZeppelin
│
├── fuzzing/
│   ├── echidna_config.yaml          # Echidna fuzzer configuration
│   ├── properties/
│   │   ├── InvariantTests.sol       # Property-based invariant tests
│   │   └── FuzzTargets.sol          # Custom fuzzing targets
│   └── run_echidna.sh               # Fuzzing runner script
│
├── formal_verification/
│   ├── smt_verifier.py              # Z3-based property prover
│   ├── invariant_checker.py         # On-chain invariant verifier
│   └── certora_spec.spec            # Certora Prover spec (template)
│
├── llm_auditor/
│   ├── auditor.py                   # LLM audit engine (Anthropic API)
│   ├── prompt_templates.py          # Structured audit prompts
│   └── report_generator.py          # HTML/PDF report builder
│
├── scripts/
│   ├── run_slither.py               # Slither wrapper with JSON output
│   ├── run_mythril.py               # Mythril symbolic analysis
│   └── run_full_audit.py            # Orchestrates full pipeline
│
├── reports/
│   └── sample_audit_report.html     # Example generated report
│
├── tests/
│   ├── test_verifier.py
│   └── test_llm_auditor.py
│
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

---

## 🚀 Quick Start

```bash
git clone https://github.com/ivonexauce/Smart-Contract-Formal-Verification-Suite.git
cd Smart-Contract-Formal-Verification-Suite
cp .env.example .env   # Add your ANTHROPIC_API_KEY
docker-compose up --build
```

### Run Full Audit Pipeline

```bash
# Full audit on a contract
python scripts/run_full_audit.py --contract contracts/vulnerable/Reentrancy.sol

# Static only
python scripts/run_slither.py --contract contracts/vulnerable/Reentrancy.sol

# LLM audit only
python llm_auditor/auditor.py --contract contracts/vulnerable/Reentrancy.sol

# Generate HTML report
python llm_auditor/report_generator.py --output reports/my_audit.html
```

---

## 🧠 LLM Audit Engine

The LLM auditor reads Solidity source code and static/fuzzing output, then produces a structured report including:

- **Executive Summary** — non-technical overview for stakeholders
- **Vulnerability Table** — severity, location, CWE reference
- **Attack Scenario** — how an attacker would exploit each finding
- **Remediation Code** — specific Solidity fix for each issue
- **Risk Score** — composite 0-100 security score

---

## 🔬 Formal Verification

The SMT verifier uses **Z3** to mathematically prove or disprove contract properties such as:
- Balance conservation (no funds created from nothing)
- Access control invariants (only owner can call admin functions)
- State machine correctness (valid state transitions only)
- Arithmetic safety (no overflow under any input)

---

## 🎯 Benchmark Contracts

The suite includes deliberately vulnerable contracts modeled after real DeFi exploits:

| Contract | Vulnerability | Real-World Analog |
|---|---|---|
| `Reentrancy.sol` | Reentrancy | The DAO Hack ($60M) |
| `FlashLoanVuln.sol` | Flash loan | bZx Protocol ($8M) |
| `OracleManipulation.sol` | Price manipulation | Cream Finance ($130M) |
| `IntegerOverflow.sol` | Arithmetic | BECToken Overflow |
| `AccessControl.sol` | Missing modifiers | Parity Wallet Freeze |

---

## 📜 License
MIT License — free to use, distribute, and modify.

---

## 🙌 Author

**UMBA YANGA IVON EXAUCE (Ebb)**  
Deep-Tech Systems Architect & Innovation Strategist  
Founder & CEO — UMBA Consulting Engineers

🌐 [umbaconsulting.com](https://umbaconsulting.com) | 📧 umbayanga6bio@gmail.com

> *"Security is not a feature — it is an architecture."*
