"""
prompt_templates.py — Structured Audit Prompt Builder
Produces consistent, high-quality prompts for LLM security analysis.
"""

import json


def build_audit_prompt(
    contract_name: str,
    source_code: str,
    static_results: dict,
    fuzz_results: dict,
) -> str:
    static_section = (
        json.dumps(static_results, indent=2) if static_results
        else "No static analysis results provided."
    )
    fuzz_section = (
        json.dumps(fuzz_results, indent=2) if fuzz_results
        else "No fuzzing results provided."
    )

    return f"""You are a senior smart contract security auditor with expertise in Solidity, EVM internals, DeFi protocols, and formal verification. You have conducted audits for top-tier Web3 firms including Trail of Bits, OpenZeppelin, and Consensys Diligence.

Audit the following Solidity smart contract and provide a comprehensive, structured security report.

## Contract Name
{contract_name}

## Source Code
```solidity
{source_code}
```

## Static Analysis Results (Slither/Mythril)
```json
{static_section}
```

## Fuzzing Results (Echidna)
```json
{fuzz_section}
```

---

## Required Output Format

Provide your analysis in the following structured format:

### 1. EXECUTIVE SUMMARY
Brief 2-3 sentence overview of the contract's purpose and overall security posture.

### 2. RISK SCORE
Overall security score: X/100 (where 100 = perfectly secure)
Breakdown: Critical: N | High: N | Medium: N | Low: N | Info: N

### 3. VULNERABILITY TABLE
For each finding:
| ID | Title | Severity | Location | CWE |
|---|---|---|---|---|

### 4. DETAILED FINDINGS
For each vulnerability (ID, Severity, Description, Impact, Attack Vector):

**[VUL-001] [SEVERITY] Title**
- **Description:** What the vulnerability is
- **Location:** Function/line reference
- **Impact:** What an attacker can accomplish
- **Attack Vector:** Step-by-step exploitation scenario

### 5. COMPLIANCE CHECK
- SWC Registry compliance (list applicable SWC IDs)
- EIP standard compliance (if applicable)
- OpenZeppelin best practices adherence

### 6. POSITIVE FINDINGS
What the contract does well from a security perspective.

Be precise, technical, and actionable. Reference specific line numbers and function names where possible.
"""


def build_remediation_prompt(
    contract_name: str,
    source_code: str,
    vulnerability_analysis: str,
) -> str:
    return f"""You are a senior Solidity developer and security engineer. Based on the vulnerability analysis below, provide specific remediation code and a developer checklist.

## Contract: {contract_name}

## Original Source
```solidity
{source_code}
```

## Vulnerability Analysis
{vulnerability_analysis}

---

## Required Output

### 1. REMEDIATION CODE
For each vulnerability identified, provide the corrected Solidity code with inline comments explaining the fix.

### 2. DEVELOPER CHECKLIST
A prioritized list of action items in order of severity.

### 3. SECURE PATTERNS APPLIED
List which security patterns were applied (e.g., CEI, ReentrancyGuard, AccessControl, SafeMath, etc.)

### 4. TESTING RECOMMENDATIONS
Specific test cases that should be written to verify each fix.

Provide production-quality, auditable Solidity code. Reference OpenZeppelin libraries where appropriate.
"""
