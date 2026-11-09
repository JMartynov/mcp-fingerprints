# Daily Web Card Audit Verification Report — 2026-11-05

## 1. MISMATCH Verification (4 cards)
- **Servers**: `@dexical30/mcp-server-mysql`, `mcp-maigret`, `@chanmeng666/google-news-server`, `mcp-searxng`
- **Status**: Verified.
- **Root Cause**: `CONFIRMED_ZERO_TOOLS: REMOTE_GATEWAY_OR_SDK`. These servers operate as remote API gateways or wrappers and lack static/local tool definitions within the repository code. While their catalog cards list tools, the local source code contains zero tools, confirming a catalog card discrepancy versus the local source truth.

## 2. MISSED_TOOLS Verification (20 cards)
Differentiated between auditor false positives and real parser gaps:

- **Auditor False Positives (3 cards)**:
  - `michal-niedzwiedzki/visimark` (`docs/design/visimark-simulate-mcp-tool-plan.md`)
  - `@enderfga/claw-orchestrator` (`skills/references/autoloop.md`)
  - `@blockrun/mcp` (`skills/image-prompting/SKILL.md`)
  - *Analysis*: These files reside in `docs/design/`, `skills/`, or represent planning documents. They are design, specification, or prompt documentation, and **not** valid MCP tool definitions. They should be excluded from parsing.

- **Real Parser Gaps / Registrations (17 cards)**:
  - *True README markdown tables*: `@zvid/mcp`, `twelvetake-reaper-mcp`, `@samsadch/adb-mcp`, `agentblueprint`, `giorgio44/gateonai-mcp-server`, `ni-c/google-search-console-mcp`, `@jrpool/kilotest`, `nostrpulse-mcp`, `dbt-mcp`, `mcp-memory-service`.
  - *TypeScript explicit tool registrations*: `2dai-mcp-server`, `@micropage-sh/mcp`, `@sandboxapis/mcp`, `ai.agentblueprint/agent-blueprint`.
  - *JSON config / server card declarations*: `@burtthecoder/mcp-dnstwist` (`server.json`), `arkforge-mcp` (`.well-known/mcp/server-card.json`).

## 3. UNREACHABLE_REPO Verification (21 cards)
- **Status**: Verified.
- **Root Cause**: Genuine dead, private, or moved repositories returning HTTP 404. These are correctly categorized by the auditor. (e.g., `fettle-mcp`, `faxforagents-mcp`, `@tokenlabai/mcp-server`, etc.)

## 4. UNRESOLVED_SOURCE Verification (59 cards)
- **Status**: Verified.
- **Root Cause**: Registry packages entirely missing repository URLs or GitHub metadata. Correctly categorized by the auditor.

## 5. PERFECT_MATCH Verification (3 cards)
- **Servers**: `@deusflight/piratefly-mcp`, `ad.apogee/apogee`, `uploadkit`
- **Status**: Verified. Perfectly matching expectations.
