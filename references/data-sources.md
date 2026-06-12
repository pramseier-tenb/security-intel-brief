# Data sources — endpoints, parameters, fields

All endpoints are free, no API key required (NVD is rate-limited to ~5 req/30s without a key — space out calls). Use the web-fetch tool, not bash.

## 1. NVD CPE resolution

Find the canonical CPE name for a product:

```
https://services.nvd.nist.gov/rest/json/cpes/2.0?keywordSearch=<vendor>+<product>&resultsPerPage=20
```

Read `products[].cpe.cpeName` (format `cpe:2.3:a:<vendor>:<product>:<version>:...`). Pick the entry whose vendor/product segments match; substitute the user's version into the version segment. Application CPEs start `cpe:2.3:a:`, operating systems `cpe:2.3:o:` (e.g., Cisco IOS XE), hardware `cpe:2.3:h:`.

## 2. NVD CVE API 2.0

**Version exposure** (all CVEs matching an exact version):

```
https://services.nvd.nist.gov/rest/json/cves/2.0?cpeName=cpe:2.3:a:apache:tomcat:9.0.85:*:*:*:*:*:*:*&resultsPerPage=50
```

**Recent CVEs** (lookback window, any version of the product):

```
https://services.nvd.nist.gov/rest/json/cves/2.0?virtualMatchString=cpe:2.3:a:apache:tomcat&pubStartDate=2026-05-12T00:00:00.000&pubEndDate=2026-06-12T00:00:00.000
```

Date range max 120 days per query. `totalResults` gives the full count; page with `startIndex` if needed.

Fields per `vulnerabilities[].cve`:

- `id` — CVE ID
- `descriptions[lang=en].value` — summary (often names fixed versions: "upgrade to X which fixes the issue")
- `metrics.cvssMetricV31[0].cvssData.baseScore` / `.baseSeverity` — prefer entries with `"type": "Primary"`; fall back to `cvssMetricV40` or `cvssMetricV2` if 3.1 absent
- `cisaExploitAdd`, `cisaActionDue`, `cisaRequiredAction` — **present only if the CVE is in the CISA KEV catalog**. This is the KEV check; no separate KEV feed needed.
- `configurations[].nodes[].cpeMatch[]` — `versionStartIncluding` / `versionEndExcluding` define affected ranges; `versionEndExcluding` is usually the fixed version
- `references[]` — URLs tagged `Vendor Advisory` are good advisory links
- `published`, `lastModified`

Filter shortcuts: `&hasKev` returns only KEV-listed CVEs; `&cvssV3Severity=CRITICAL` filters by severity.

## 3. endoflife.date — versions & EOL

```
https://endoflife.date/api/<product>.json
```

Product slugs are lowercase (`tomcat`, `windows-server`, `cisco-ios-xe` may not exist — try `https://endoflife.date/api/all.json` to list slugs, or just web-search "endoflife.date <product>"). Fields per cycle: `cycle`, `latest`, `latestReleaseDate`, `eol` (`false` or a date — a past date means EOL), `releaseDate`, `lts`.

Compare the user's version to `latest` within its cycle to compute patch lag. If the product isn't on endoflife.date, find the latest version from the vendor's release page via web search.

## 4. Advisories & news — web search

Useful query shapes (substitute current month/year):

- `"<product>" security advisory June 2026`
- `"<vendor> <product>" CVE exploited 2026`
- `<product> patch release notes <version>`
- site-scoped: vendor PSIRT pages (e.g., `sec.cloudapps.cisco.com`, `msrc.microsoft.com`, `tomcat.apache.org/security`), `cisa.gov` alerts

Prefer primary sources (vendor PSIRT, CISA, CERT) over news aggregators; include a reputable news article only when it adds context (active exploitation reports, breach attribution). Always capture the URL.

## Gotchas

- NVD keyword search is noisy — always prefer `cpeName`/`virtualMatchString` once the CPE is resolved.
- Some products (firmware, appliances) have spotty NVD CPE coverage; supplement with the vendor advisory page and note the limitation in the report.
- CVSS can be missing on very fresh CVEs ("Awaiting Analysis") — show "pending" rather than guessing.
- A CVE listing the product in `configurations` doesn't always mean the user's exact version is affected — check the version ranges.
