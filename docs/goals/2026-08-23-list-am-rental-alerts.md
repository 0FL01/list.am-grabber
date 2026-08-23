# Goal: List.am rental alerts

Status: complete
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
  - Acceptance: The local image starts the monitor with read-only configuration, persistent SQLite data, no auth/cookie mount, and clean SIGTERM handling.
  - Primary evidence: Docker build, `docker compose config`, one-shot smoke, and a two-cycle monitor shutdown check.
  - Status: verified
  - Evidence: Local slim-bookworm image builds; `pip check` reports no broken requirements; compose resolves to the local image with config/data mounts and no cookies; image inspection confirms config, Git metadata, environment files, cookies, and databases are absent; live one-shot parsed 105 cards; a production-interval lifecycle run survived a transient blocked scan, succeeded on the next scan with 105 cards, and exited cleanly on SIGTERM.

- R5: Keep Telegram credentials in an ignored local TOML config with a tracked example.
  - Source: User: "никаких export, переменные храним в config.toml для телеграмма" and "добавь конфиг томл в гит игнор и сделай с припиской example".
  - Acceptance: Runtime reads Telegram bot token and chat ID from ignored `config.toml`; `config.example.toml` is tracked without secrets; Docker Compose requires no Telegram environment variables.
  - Primary evidence: Config loader test, Git tracked/ignored file check, and `docker compose config`.
  - Status: verified
  - Evidence: Focused config tests pass; `config.toml` is ignored and untracked; `config.example.toml` is tracked; compose has no Telegram environment entries.

### Constraints

- C1: Use a headless browser in Docker; do not require List.am authorization or prepared cookies.
- C2: Telegram is the only notification channel; VK is not part of the active runtime.
- C3: Keep the implementation minimal under KISS, YAGNI, and Pareto.
- C4: Make repository commits as checkpoints, as explicitly requested by the user.
- C5: Do not commit Telegram credentials, browser profiles, cookies, or generated databases.
- C6: Telegram credentials are read from local `config.toml`, not exported environment variables.

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

- Closes: R1-R5.
- Smallest next action: None; run the closure check and stop.
- Expected evidence: All required outcomes are verified with current focused and Docker evidence.
- Stop or replan if: A closure command fails because of the final diff.

## Current State

- Resolved: R1-R5 are verified.
- Last relevant evidence: Seven focused tests pass; compose config has no Telegram environment entries; Git ignores `config.toml` but not `config.example.toml`.
- Blocker: None.
- Next: None.

## Material Decisions

- 2026-08-23: Use configured List.am search URLs as the authority for location, budget, rooms, and amenities; do not reproduce those filters locally.
- 2026-08-23: Parse category cards only for the first complete product slice. Telegram links to List.am provide the path to inspect details and call.
- 2026-08-23: First successful full scan creates a no-alert baseline to avoid an initial alert flood.
- 2026-08-23: Keep one state row per listing with its last handled displayed-price key; persist a new key only after successful Telegram delivery.
- 2026-08-23: Adapt only the active runtime. Dormant upstream GUI/Avito files are not a cleanup objective.
- 2026-08-23: Vanilla headless Chromium is blocked in the current Docker environment; use the existing `playwright-stealth` integration without adding broader bypass infrastructure.
- 2026-08-23: Use `python:3.11-slim-bookworm` with Playwright-managed headless-shell dependencies; the matching official Playwright image was disproportionately large for this personal monitor and its pull exceeded the bounded build attempt.
- 2026-08-23: Store Telegram credentials in ignored `config.toml`; track only `config.example.toml` and remove Telegram environment wiring from Compose.

## Checkpoint History

- 2026-08-23: Contract frozen from the user request and audited minimal plan. Next checkpoint is the Docker/headless feasibility gate for R3.
- 2026-08-23: R3 feasibility gate passed with existing stealth support: HTTP 200 and 105 cards in a fresh headless container; vanilla headless returned Cloudflare HTTP 403. Next checkpoint is the deterministic card parser.
- 2026-08-23: R1 parser fixture checkpoint passed. The parser uses category-card data only and preserves actual pagination query parameters. Next checkpoint is R2 delivery state.
- 2026-08-23: R2 state checkpoint passed. A single SQLite table baselines the first scan, suppresses unchanged listings, alerts price changes, and records state only after notifier success. Next checkpoint is Telegram transport.
- 2026-08-23: R2 Telegram checkpoint passed. Alerts are text-only, escaped, linked to List.am, and transport failures do not expose the bot token. Next checkpoint is the configured browser scanner.
- 2026-08-23: R3 verified through the new scanner in a fresh Docker image; 104 live cards parsed without authentication or persisted cookies. Config validation also passes. Next checkpoint is active CLI integration.
- 2026-08-23: R1 and R2 verified after active CLI integration. Seven focused tests pass; a fresh Docker one-shot parsed and baselined 104 cards without Telegram side effects. Next checkpoint is R4 Docker delivery.
- 2026-08-23: R4 Docker delivery is implemented and verified except for the production-interval two-cycle lifecycle check. Build, `pip check`, compose config, secret-safe image inspection, and a 105-card live one-shot pass.
- 2026-08-23: R4 lifecycle verified. At the production interval the monitor continued after a transient blocked scan, completed the next scan with 105 cards, and handled SIGTERM cleanly. Closure checks pass.
- 2026-08-23: R5 verified. Telegram credentials moved from environment variables to ignored `config.toml`; the tracked example contains empty values.

## Completion

- Resolved outcomes: R1 configured List.am scanning; R2 Telegram-only deduplicated delivery; R3 headless Docker operation without List.am auth or prepared cookies; R4 repeatable local container monitoring; R5 ignored TOML-based Telegram credentials with a tracked example.
- Commands and artifacts: `python -m unittest discover -s tests` (7 passing); `docker build -t list-am-search:local .`; image `pip check`; `docker compose config`; Git ignore checks; secret-safe image assertions; live `--once` scan with 105 parsed cards; production-interval lifecycle/SIGTERM run.
- Constraint and diff-scope check: Active runtime contains no VK, XLSX, detail/phone scraping, login, proxy, CAPTCHA service, persistent browser profile, or Telegram environment wiring. Telegram credentials and generated state are not committed. Dormant upstream files were not cosmetically cleaned up.
- Final status: complete
