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
  - Status: in_progress
  - Evidence: The focused parser/config tests pass; the new `ListAmScanner` parsed 104 unique cards from the configured live search in a fresh Docker image.

- R2: Send Telegram-only alerts without repeatedly alerting an unchanged listing.
  - Source: User: "VK не нужен, только телеграмм бот для объявлений" and instruction to proceed with the audited minimal plan.
  - Acceptance: After initial baseline, a new listing or changed displayed price sends one text alert with a List.am link; unchanged listings do not resend; failed delivery is retried because it is not persisted as handled.
  - Primary evidence: Pipeline test with a temporary SQLite database and fake notifier covering baseline, unchanged, new, changed-price, and failed-delivery cases.
  - Status: in_progress
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
  - Status: pending
  - Evidence:

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

- Closes: Runtime integration portions of R1 and R2.
- Smallest next action: Replace the active CLI with a thin monitor loop that loads List.am config, keeps one scanner context across cycles, runs the verified delivery pipeline, reads Telegram credentials from environment variables, supports `--once`, and exits non-zero on one-shot failure.
- Expected evidence: Existing focused tests remain green and a one-shot CLI run against an empty temporary database completes a live baseline without contacting Telegram.
- Stop or replan if: Integration requires reintroducing Avito factories, batch notification semantics, or persistent browser credentials.

## Current State

- Resolved: Scope is frozen; the configured stealth-enabled scanner, parser, delivery state, and text-only Telegram transport work independently; R3 is verified in Docker.
- Last relevant evidence: Fresh Docker scanner run parsed 104 live cards through the new runtime module.
- Blocker: None.
- Next: Integrate the modules in the active CLI monitor and verify a live baseline run.

## Material Decisions

- 2026-08-23: Use configured List.am search URLs as the authority for location, budget, rooms, and amenities; do not reproduce those filters locally.
- 2026-08-23: Parse category cards only for the first complete product slice. Telegram links to List.am provide the path to inspect details and call.
- 2026-08-23: First successful full scan creates a no-alert baseline to avoid an initial alert flood.
- 2026-08-23: Keep one state row per listing with its last handled displayed-price key; persist a new key only after successful Telegram delivery.
- 2026-08-23: Adapt only the active runtime. Dormant upstream GUI/Avito files are not a cleanup objective.
- 2026-08-23: Vanilla headless Chromium is blocked in the current Docker environment; use the existing `playwright-stealth` integration without adding broader bypass infrastructure.

## Checkpoint History

- 2026-08-23: Contract frozen from the user request and audited minimal plan. Next checkpoint is the Docker/headless feasibility gate for R3.
- 2026-08-23: R3 feasibility gate passed with existing stealth support: HTTP 200 and 105 cards in a fresh headless container; vanilla headless returned Cloudflare HTTP 403. Next checkpoint is the deterministic card parser.
- 2026-08-23: R1 parser fixture checkpoint passed. The parser uses category-card data only and preserves actual pagination query parameters. Next checkpoint is R2 delivery state.
- 2026-08-23: R2 state checkpoint passed. A single SQLite table baselines the first scan, suppresses unchanged listings, alerts price changes, and records state only after notifier success. Next checkpoint is Telegram transport.
- 2026-08-23: R2 Telegram checkpoint passed. Alerts are text-only, escaped, linked to List.am, and transport failures do not expose the bot token. Next checkpoint is the configured browser scanner.
- 2026-08-23: R3 verified through the new scanner in a fresh Docker image; 104 live cards parsed without authentication or persisted cookies. Config validation also passes. Next checkpoint is active CLI integration.

## Completion

- Resolved outcomes:
- Commands and artifacts:
- Constraint and diff-scope check:
- Final status:
