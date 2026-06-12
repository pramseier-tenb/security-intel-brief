# security-intel-brief

A Claude skill that produces a leadership-ready **security intelligence brief (PDF)** for the vendors and software you choose — down to specific versions.

For each target it collects, from live sources at run time:

- CVEs from the NVD API (exact-version matching via CPE)
- CISA KEV status (known exploited vulnerabilities — confirmed in-the-wild)
- Latest versions and end-of-life dates (endoflife.date)
- Vendor security advisories and recent security news (web search)

It then assigns a per-product risk rating (Critical/High/Medium/Low) with stated rationale and renders a polished PDF: executive summary, risk overview table, recommended actions, and per-product detail sections (version/patch status, CVE tables with KEV flags, advisories, news, sources).

## Install

**Claude (Cowork / Claude Code):** download `security-intel-brief.skill` from this repo (or the latest release) and install it via your skills settings — or copy this folder into your skills directory.

## Use

Say something like:

> Security briefing on Cisco IOS XE 17.9.4a and Apache Tomcat 9.0.85 for Monday's leadership meeting

or just:

> What vulnerabilities affect our Tomcat servers?

If you don't name targets, the skill shows an interactive form to pick vendors, products, versions, lookback window, and report title.

## Contents

| Path | Purpose |
|---|---|
| `SKILL.md` | The skill instructions (workflow, risk-rating guidance, accuracy rules) |
| `references/data-sources.md` | API endpoints, query parameters, response fields, gotchas |
| `scripts/build_report.py` | Renders the report JSON to a branded PDF (reportlab) |
| `assets/selection_form.html` | Interactive target-selection form |
| `evals/evals.json` | Test prompts used during development |

## Notes

- All vulnerability data is fetched at run time — nothing is answered from model memory.
- The PDF builder needs `reportlab` (`pip install reportlab`); the skill installs it automatically when missing.
- NVD is rate-limited (~5 requests/30s without an API key); the skill spaces out calls.
