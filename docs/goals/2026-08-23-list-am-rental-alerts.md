# Goal: List.am rental alerts

Status: active
Source: user instructions in the current session
Last updated: 2026-08-23

## Objective

Run a Dockerized headless-browser monitor for configured List.am long-term-rental searches and send useful Telegram alerts without List.am authentication.

## Execution Directive

Complete the frozen Required Outcomes using the listed Change Envelope and Primary Evidence. Work on the smallest unresolved outcome. Do not add requirements from reviews, tests, tools, speculative risks, or optional source text. Finish when every required outcome is resolved and affected constraints remain satisfied.

## Frozen Contract

### Required Outcomes

- R1: Monitor configured List.am long-term-rental result pages.
  - Source: User: "парсер объявлений для list.am" with scope "снять жильё в аренду для житья и удаленной работы".
  - Acceptance: A configured search is polled and its listing cards are parsed into stable IDs, canonical links, titles, prices, and summaries.
  - Primary evidence: Deterministic parser fixture test plus a live one-shot scan counter showing at least one parsed listing.
  - Status: verified
  - Evidence: The focused parser/config tests pass; the active CLI one-shot parsed and baselined 104 unique cards from the configured live search in a fresh Docker image.

- R2: Send Telegram-only alerts without repeatedly alerting an unchanged listing.
  - Source: User: "VK не нужен, только телеграмм бот для объявлений" and instruction to proceed with the audited minimal plan.
  - Acceptance: After initial baseline, a new listing or changed displayed price sends one text alert with a List.am link; unchanged listings do not resend; failed delivery is retried because it is not persisted as handled.
  - Primary evidence: Pipeline test with a temporary SQLite database and fake notifier covering baseline, unchanged, new, changed-price, and failed-delivery cases.
  - Status: verified
  - Evidence: Focused pipeline and Telegram tests pass for initial baseline, unchanged suppression, new listing, changed price, failed delivery remaining retryable, escaped text payloads, and sanitized transport failures.

- R3: Run through a headless browser in Docker without List.am login or prepared cookies.
  - Source: User: "конечное решение должно работать с headless браузером и без авторизации в докер контейнере".
  - Acceptance: A fresh container with no List.am cookie/profile mount opens a configured category search and parses its cards using headless Chromium.
  - Primary evidence: Production-like Docker smoke command and observed parsed-listing counter; a Cloudflare challenge is a failure, not an empty successful scan.
  - Status: verified
  - Evidence: `docker build -t list-am-search:dev .` followed by a fresh-container `ListAmScanner` one-shot parsed 104 unique cards using headless Chromium with stealth and no login, cookie file, or browser-profile mount.

- R4: Provide a repeatable monitoring container configuration.
  - Source: User instruction to build the solution from start to finish under the Docker constraint.
  - Acceptance: The local image starts the monitor with read-only search configuration, environment-provided Telegram credentials, persistent SQLite data, no auth/cookie mount, and clean SIGTERM handling.
  - Primary evidence: Docker build, `docker compose config`, one-shot smoke, and a two-cycle monitor shutdown check.
  - Status: in_progress
  - Evidence: Local slim-bookworm image builds; `pip check` reports no broken requirements; compose resolves to the local image with config/data mounts and no cookies; image inspection confirms config, Git metadata, environment files, cookies, and databases are absent; live one-shot parsed and baselined 105 cards.

### Constraints

- C1: Use a headless browser in Docker; do not require List.am authorization or prepared cookies.
- C2: Telegram is the only notification channel; VK is not part of the active runtime.
- C3: Keep the implementation minimal under KISS, YAGNI, and Pareto.
- C4: Make repository commits as checkpoints, as explicitly requested by the user.
- C5: Do not commit Telegram credentials, browser profiles, cookies, or generated databases.

### Non-goals

- Scraping phone numbers, full detail pages, or full image galleries.
- XLSX export, VK notifications, GUI support, or Avito compatibility in the active runtime.
- Currency conversion, proxy rotation, CAPTCHA services, account login, or a generic crawler framework.
- Physical cleanup or cosmetic renaming of every dormant upstream file.

## Change Envelope

- Target: The CLI monitor, List.am card parsing, delivery state, Telegram transport, and Docker execution path.
- Expected paths, symbols, and direct consumers: `parser_cls.py`, `models.py`, `dto.py`, `load_config.py`, `db_service.py`, `integrations/notifications/`, `config.toml` or a sample replacement, `requirements.txt`, `Dockerfile`, `docker-compose.yml`, `entrypoint.sh`, `.dockerignore`, `.gitignore`, focused tests/fixtures, and user-facing runtime documentation.
- Allowed artifacts: One SQLite state table, HTML fixtures without private data, a sample config without credentials, and the existing Python/Playwright/requests/loguru dependency family.
- Forbidden artifacts: New services, auth flows, bypass providers, proxy infrastructure, spreadsheet/export abstractions, secrets, cookies, browser profiles, or generated runtime data in Git.
- User or harness budget: No arbitrary LOC budget; each checkpoint must be the smallest change that closes or directly tests an unresolved required outcome.

## Current Checkpoint

- Closes: Remaining monitoring-lifecycle portion of R4.
- Smallest next action: Run the built image for two production-interval scan cycles against temporary state, send SIGTERM during its wait, and confirm both scans succeed and the process exits cleanly.
- Expected evidence: Two successful scan counter lines followed by exit status 0 after SIGTERM.
- Stop or replan if: A normal 60-second interval still triggers a repeatable Cloudflare block in the same in-memory browser context.

## Current State

- Resolved: R1-R3 are verified; Docker build, dependency integrity, secret-safe image contents, compose wiring, and live one-shot execution are verified for R4.
- Last relevant evidence: The final slim-bookworm image live one-shot logged `parsed=105 baselined=105 delivered=0 unchanged=0`; an artificial one-second polling test was blocked on its second scan, so the production interval remains to be checked.
- Blocker: None.
- Next: Verify two successful scans at the configured 60-second interval and clean SIGTERM handling.

## Material Decisions

- 2026-08-23: Use configured List.am search URLs as the authority for location, budget, rooms, and amenities; do not reproduce those filters locally.
- 2026-08-23: Parse category cards only for the first complete product slice. Telegram links to List.am provide the path to inspect details and call.
- 2026-08-23: First successful full scan creates a no-alert baseline to avoid an initial alert flood.
- 2026-08-23: Keep one state row per listing with its last handled displayed-price key; persist a new key only after successful Telegram delivery.
- 2026-08-23: Adapt only the active runtime. Dormant upstream GUI/Avito files are not a cleanup objective.
- 2026-08-23: Vanilla headless Chromium is blocked in the current Docker environment; use the existing `playwright-stealth` integration without adding broader bypass infrastructure.
- 2026-08-23: Use `python:3.11-slim-bookworm` with Playwright-managed headless-shell dependencies; the matching official Playwright image was disproportionately large for this personal monitor and its pull exceeded the bounded build attempt.

## Checkpoint History

- 2026-08-23: Contract frozen from the user request and audited minimal plan. Next checkpoint is the Docker/headless feasibility gate for R3.
- 2026-08-23: R3 feasibility gate passed with existing stealth support: HTTP 200 and 105 cards in a fresh headless container; vanilla headless returned Cloudflare HTTP 403. Next checkpoint is the deterministic card parser.
- 2026-08-23: R1 parser fixture checkpoint passed. The parser uses category-card data only and preserves actual pagination query parameters. Next checkpoint is R2 delivery state.
- 2026-08-23: R2 state checkpoint passed. A single SQLite table baselines the first scan, suppresses unchanged listings, alerts price changes, and records state only after notifier success. Next checkpoint is Telegram transport.
- 2026-08-23: R2 Telegram checkpoint passed. Alerts are text-only, escaped, linked to List.am, and transport failures do not expose the bot token. Next checkpoint is the configured browser scanner.
- 2026-08-23: R3 verified through the new scanner in a fresh Docker image; 104 live cards parsed without authentication or persisted cookies. Config validation also passes. Next checkpoint is active CLI integration.
- 2026-08-23: R1 and R2 verified after active CLI integration. Seven focused tests pass; a fresh Docker one-shot parsed and baselined 104 cards without Telegram side effects. Next checkpoint is R4 Docker delivery.
- 2026-08-23: R4 Docker delivery is implemented and verified except for the production-interval two-cycle lifecycle check. Build, `pip check`, compose config, secret-safe image inspection, and a 105-card live one-shot pass.

## Completion

- Resolved outcomes:
- Commands and artifacts:
- Constraint and diff-scope check:
- Final status:
