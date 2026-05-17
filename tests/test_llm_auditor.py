"""
test_llm_auditor.py — Unit tests for the LLM auditor and report generator.
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from llm_auditor.prompt_templates import build_audit_prompt, build_remediation_prompt
from llm_auditor.report_generator import HTMLReportGenerator
import pytest


# ------------------------------------------------------------------
#  Prompt Templates
# ------------------------------------------------------------------

class TestBuildAuditPrompt:
    def test_includes_contract_name(self):
        prompt = build_audit_prompt(
            contract_name="TestContract",
            source_code="contract TestContract {}",
            static_results={"detectors": []},
            fuzz_results={},
        )
        assert "TestContract" in prompt
        assert "contract TestContract {}" in prompt
        assert "EXECUTIVE SUMMARY" in prompt
        assert "VULNERABILITY TABLE" in prompt

    def test_includes_static_results(self):
        static = {"detectors": [{"name": "reentrancy", "severity": "high"}]}
        prompt = build_audit_prompt(
            contract_name="Test", source_code="contract T {}", static_results=static, fuzz_results={}
        )
        assert "reentrancy" in prompt
        assert "high" in prompt

    def test_no_static_results(self):
        prompt = build_audit_prompt(
            contract_name="Test", source_code="contract T {}", static_results={}, fuzz_results={}
        )
        assert "No static analysis results" in prompt

    def test_no_fuzz_results(self):
        prompt = build_audit_prompt(
            contract_name="Test", source_code="contract T {}", static_results={}, fuzz_results={}
        )
        assert "No fuzzing results" in prompt


class TestBuildRemediationPrompt:
    def test_includes_contract_and_analysis(self):
        prompt = build_remediation_prompt(
            contract_name="TestContract",
            source_code="contract TestContract {}",
            vulnerability_analysis="Found critical reentrancy bug",
        )
        assert "TestContract" in prompt
        assert "contract TestContract {}" in prompt
        assert "Found critical reentrancy bug" in prompt
        assert "REMEDIATION CODE" in prompt
        assert "DEVELOPER CHECKLIST" in prompt


# ------------------------------------------------------------------
#  Report Generator
# ------------------------------------------------------------------

class TestHTMLReportGenerator:
    def test_generates_html(self, tmp_path):
        formal_results = {
            "results": [
                {"name": "NoOverflow", "status": "PROVED", "message": "No overflow"},
                {"name": "AccessControl", "status": "VIOLATED", "message": "Bypass found"},
            ],
            "summary": {"proved": 1, "violated": 1, "unknown": 0},
        }
        llm_result = {
            "vulnerability_analysis": "# Vuln Analysis\n\nCritical issue found.",
            "remediation_analysis": "## Fix\n\nAdd checks.",
        }

        gen = HTMLReportGenerator(
            contract_name="TestContract",
            static_results={},
            formal_results=formal_results,
            llm_result=llm_result,
        )
        out = tmp_path / "report.html"
        result_path = gen.generate(str(out))

        assert Path(result_path).exists()
        html = Path(result_path).read_text()

        # Check key sections in HTML
        assert "TestContract" in html
        assert "PROVED" in html
        assert "VIOLATED" in html
        assert "Vuln Analysis" in html
        assert "Fix" in html
        assert "No overflow" in html
        assert "Bypass found" in html
        assert "UMBA Consulting Engineers" in html

    def test_handles_empty_llm(self, tmp_path):
        gen = HTMLReportGenerator(
            contract_name="Empty", static_results={}, formal_results={"results": [], "summary": {}}, llm_result={}
        )
        out = tmp_path / "empty.html"
        gen.generate(str(out))
        html = Path(out).read_text()
        assert "LLM audit not run" in html

    def test_html_escapes_llm_output(self, tmp_path):
        malicious = "<script>alert('xss')</script>"
        gen = HTMLReportGenerator(
            contract_name="XSS",
            static_results={},
            formal_results={"results": [], "summary": {}},
            llm_result={"vulnerability_analysis": malicious},
        )
        out = tmp_path / "safe.html"
        gen.generate(str(out))
        html = Path(out).read_text()
        assert "<script>" not in html or "&lt;script&gt;" in html


# ------------------------------------------------------------------
#  Solidity contract reading (integration smoke test)
# ------------------------------------------------------------------

class TestAuditorIntegration:
    def test_can_read_solidity_source(self):
        reentrancy_path = Path(__file__).parent.parent / "contracts" / "vulnerable" / "Reentrancy.sol"
        assert reentrancy_path.exists(), "Reentrancy.sol must exist"
        source = reentrancy_path.read_text()
        assert "contract Reentrancy" in source
        assert "withdraw" in source
        # Check the source has reasonable length
        assert len(source) > 200, "Contract source too short"
