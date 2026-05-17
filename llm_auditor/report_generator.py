"""
report_generator.py — HTML Audit Report Builder
Produces a professional, self-contained HTML audit report.
"""

import html as html_mod
from datetime import datetime, timezone
from pathlib import Path


class HTMLReportGenerator:
    def __init__(self, contract_name, static_results, formal_results, llm_result):
        self.contract_name = contract_name
        self.static_results = static_results
        self.formal_results = formal_results
        self.llm_result = llm_result
        self.generated_at = datetime.now(timezone.utc).isoformat()

    def _esc(self, text: str) -> str:
        return html_mod.escape(text or "")

    def _formal_rows(self):
        rows = ""
        for r in self.formal_results.get("results", []):
            color = "#28a745" if r["status"] == "PROVED" else ("#dc3545" if r["status"] == "VIOLATED" else "#ffc107")
            icon = "\u2705" if r["status"] == "PROVED" else ("\u274c" if r["status"] == "VIOLATED" else "\u2753")
            rows += (
                "<tr>"
                f"<td>{self._esc(r['name'])}</td>"
                f'<td style="color:{color};font-weight:bold;">{icon} {self._esc(r["status"])}</td>'
                f"<td>{self._esc(r['message'])}</td>"
                "</tr>"
            )
        return rows

    def generate(self, output_path: str):
        vuln = self.llm_result.get("vulnerability_analysis", "LLM audit not run.")
        remed = self.llm_result.get("remediation_analysis", "")
        summary = self.formal_results.get("summary", {})
        proved = summary.get("proved", 0)
        violated = summary.get("violated", 0)
        total_checks = len(self.formal_results.get("results", []))

        html = (
            "<!DOCTYPE html>\n<html lang='en'>\n<head>\n"
            "<meta charset='UTF-8'>\n"
            "<meta name='viewport' content='width=device-width,initial-scale=1.0'>\n"
            f"<title>Smart Contract Audit \u2014 {self._esc(self.contract_name)}</title>\n"
            "<style>\n"
            "  *{box-sizing:border-box;margin:0;padding:0;}\n"
            "  body{font-family:'Segoe UI',sans-serif;background:#0d1117;color:#c9d1d9;line-height:1.6;}\n"
            "  .header{background:linear-gradient(135deg,#161b22,#1c2333);padding:40px;border-bottom:1px solid #30363d;}\n"
            "  .header h1{color:#58a6ff;font-size:2rem;}\n"
            "  .header p{color:#8b949e;margin-top:8px;}\n"
            "  .badge{display:inline-block;padding:4px 12px;border-radius:20px;font-size:12px;font-weight:bold;margin:4px;}\n"
            "  .badge-blue{background:#1f4a8a;color:#58a6ff;}\n"
            "  .badge-green{background:#1a4731;color:#3fb950;}\n"
            "  .badge-red{background:#4a1f1f;color:#f85149;}\n"
            "  .container{max-width:1100px;margin:0 auto;padding:40px 20px;}\n"
            "  .card{background:#161b22;border:1px solid #30363d;border-radius:8px;padding:24px;margin-bottom:24px;}\n"
            "  .card h2{color:#58a6ff;border-bottom:1px solid #30363d;padding-bottom:12px;margin-bottom:16px;font-size:1.2rem;}\n"
            "  .stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:16px;margin-bottom:24px;}\n"
            "  .stat{background:#0d1117;border:1px solid #30363d;border-radius:8px;padding:20px;text-align:center;}\n"
            "  .stat-value{font-size:2rem;font-weight:bold;color:#58a6ff;}\n"
            "  .stat-label{font-size:12px;color:#8b949e;margin-top:4px;}\n"
            "  table{width:100%;border-collapse:collapse;}\n"
            "  th{background:#0d1117;color:#8b949e;padding:10px;text-align:left;font-size:12px;border-bottom:1px solid #30363d;}\n"
            "  td{padding:10px;border-bottom:1px solid #21262d;font-size:13px;}\n"
            "  tr:hover td{background:#1c2333;}\n"
            "  .llm-content{background:#0d1117;border-radius:6px;padding:20px;font-size:14px;white-space:pre-wrap;word-wrap:break-word;}\n"
            "  .footer{text-align:center;padding:40px;color:#8b949e;font-size:12px;border-top:1px solid #30363d;}\n"
            "  .proved{color:#3fb950;} .violated{color:#f85149;}\n"
            "</style>\n</head>\n<body>\n"

            "<div class='header'>\n"
            "<h1>\U0001f510 Smart Contract Security Audit</h1>\n"
            f"<p>Contract: <strong>{self._esc(self.contract_name)}.sol</strong></p>\n"
            f"<p>Generated: {self._esc(self.generated_at)}</p>\n"
            "<p>Audited by: UMBA Consulting Engineers \u2014 AI Audit Engine</p>\n"
            "<div style='margin-top:16px;'>\n"
            "<span class='badge badge-blue'>Slither</span>\n"
            "<span class='badge badge-blue'>Mythril</span>\n"
            "<span class='badge badge-blue'>Z3 SMT</span>\n"
            "<span class='badge badge-green'>LLM Analysis</span>\n"
            "</div>\n</div>\n"

            "<div class='container'>\n"

            "<div class='stats'>\n"
            f"<div class='stat'><div class='stat-value proved'>{proved}</div><div class='stat-label'>Properties Proved</div></div>\n"
            f"<div class='stat'><div class='stat-value violated'>{violated}</div><div class='stat-label'>Properties Violated</div></div>\n"
            f"<div class='stat'><div class='stat-value' style='color:#ffa657;'>{total_checks}</div><div class='stat-label'>Total Checks</div></div>\n"
            "</div>\n"

            "<div class='card'>\n"
            "<h2>\u2699\ufe0f Formal Verification Results (Z3 SMT)</h2>\n"
            "<table><tr><th>Property</th><th>Status</th><th>Message</th></tr>\n"
            f"{self._formal_rows()}\n</table>\n</div>\n"

            "<div class='card'>\n"
            "<h2>\U0001f916 LLM Vulnerability Analysis</h2>\n"
            f"<div class='llm-content'>{self._esc(vuln)}</div>\n</div>\n"

            + (
                "<div class='card'>\n<h2>\U0001f527 Remediation Recommendations</h2>\n"
                f"<div class='llm-content'>{self._esc(remed)}</div>\n</div>\n"
                if remed else ""
            )
            + "</div>\n"

            "<div class='footer'>\n"
            "<p>UMBA Smart Contract Formal Verification Suite</p>\n"
            "<p>UMBA YANGA IVON EXAUCE | umbaconsulting.com | umbayanga6bio@gmail.com</p>\n"
            "</div>\n</body>\n</html>"
        )

        with open(output_path, "w") as f:
            f.write(html)
        print(f"[\u2713] HTML report saved: {output_path}")
        return output_path
