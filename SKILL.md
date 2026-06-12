---
name: security-intel-brief
description: Build a leadership-ready security intelligence brief (PDF) for selected vendors and software products, down to specific versions. Collects CVEs, CISA KEV (known exploited vulnerabilities) status, latest/fixed versions, end-of-life dates, vendor advisories, and recent security news, then assigns per-product risk ratings. Use this skill whenever the user wants security research on a vendor or product, asks about CVEs/KEVs/vulnerabilities affecting software they run, wants a patch/version exposure check, or asks for a security report or briefing for leadership — even if they don't say "PDF" or "brief". Trigger on phrases like "what vulnerabilities affect X", "security posture of [vendor/product]", "CVE report", "vulnerability briefing", "is [software version] safe/exposed".
---

# Security Intelligence Brief

Produce a polished PDF security brief covering one or more vendor/software targets (optionally pinned to specific versions). The audience is leadership: lead with risk and recommended actions, keep technical detail in well-organized tables.

## Workflow overview

1. **Collect targets** — interactive form (preferred) or chat questions
2. **Research each target** — CVEs, KEV status, versions/EOL, advisories, news
3. **Rate risk** — per-product rating with stated rationale
4. **Build report JSON** → **render PDF** with `scripts/build_report.py`
5. **Deliver** the PDF and a 3-sentence summary in chat

## Step 1: Collect targets

Preferred: render the interactive selection form so the user can add multiple vendor/product/version rows, choose a lookback window, and set a report title. Read `assets/selection_form.html` and display it with your HTML widget/visualization tool (it uses `sendPrompt` to submit the selection back to chat). If no widget tool is available, fall back to your question tool or plain chat to gather the same fields.

Fields to collect per target: **vendor**, **product**, **version** (optional — "all supported versions" if blank). Globally: **lookback window** (default 30 days), **report title**, optional **audience note** (e.g., "for CISO staff meeting").

If the user already named targets in their message, pre-fill the form rather than asking from scratch. If they gave a complete, unambiguous list and just want the report, skip the form — don't make them re-enter what they already typed.

## Step 2: Research each target

Run these lookups per target. `references/data-sources.md` has exact URLs, query parameters, and which JSON fields to read — consult it before fetching. Note: use your web-fetch tool for the APIs; the bash sandbox typically has no network access.

1. **Resolve the product to a CPE** (NVD CPE API) so CVE matching is precise. If no CPE matches, fall back to keyword search and say so in the report's methodology note.
2. **CVEs** (NVD CVE API 2.0): two queries —
   - *Recent*: CVEs published within the lookback window matching the product (any version) — this is the "what's new" picture.
   - *Version exposure*: if a version was given, all CVEs matching that exact version via `cpeName` — this is the "what are we exposed to" picture. Cap detailed listing at the ~15 highest-severity; report the total count.
3. **KEV status**: read `cisaExploitAdd` / `cisaActionDue` on each NVD record. Any KEV-listed CVE affecting the user's version is headline material — these are confirmed exploited in the wild.
4. **Versions & EOL** (endoflife.date): latest release per cycle, EOL dates, whether the user's version/cycle is EOL or behind.
5. **Advisories & news** (web search): vendor security advisories, CERT alerts, and notable security news from the lookback window. Search e.g. `"<product>" security advisory <Month Year>` and `"<product>" vulnerability exploited <Month Year>`. Keep only items with a real source URL — every claim in the report must be traceable.

Parallelize across targets with subagents if available (one subagent per target works well); otherwise research sequentially. Record every source URL as you go — the PDF has a sources section per product.

## Step 3: Rate risk

Assign each product one rating, with a one-sentence rationale that names the deciding factor:

- **Critical** — KEV-listed CVE affects the user's version, or actively exploited unpatched flaw
- **High** — CVSS ≥ 9.0 CVE affects their version with patch available but not applied, or version is EOL with known CVEs
- **Medium** — High-severity CVEs affect their version but require unusual preconditions, or version is several patch levels behind
- **Low** — current/near-current version, no significant open exposure

These are guidelines, not a formula — judgment is the point. A KEV on a component the version doesn't ship is not Critical; an EOL product facing the internet may deserve Critical. State your reasoning honestly, including uncertainty (e.g., CPE matching was fuzzy).

## Step 4: Build the report

Write a `report.json` matching the schema documented at the top of `scripts/build_report.py`, then run:

```bash
pip install reportlab --break-system-packages --quiet  # if not installed
python scripts/build_report.py report.json output.pdf
```

The script renders the full leadership layout: cover + executive summary, risk overview table, then per-product sections (version/patch status, CVE table with KEV flags, advisories & news, sources). Don't hand-roll PDF code — fix or extend the script if something's missing.

Writing the executive summary: 4–8 sentences, plain language, no CVE jargon without translation. Lead with the single most important finding (KEV exposures first), then overall posture, then the top 2–4 recommended actions with urgency ("patch within 7 days" beats "consider upgrading"). Leadership reads only this page — it must stand alone.

Accuracy matters more than completeness: every CVE ID, CVSS score, KEV date, version number, and EOL date in the report must come from a fetched source, never from memory — your training data is stale and vulnerability data changes daily. If a lookup failed, say so in the report rather than filling the gap.

## Step 5: Deliver

Save the PDF to the outputs folder with a dated name (e.g., `security-brief-2026-06-12.pdf`), present it to the user, and give a 2–3 sentence verbal summary: overall risk, the most urgent item, and the recommended next step. Offer to schedule this as a recurring brief if the user seems to want ongoing monitoring.
