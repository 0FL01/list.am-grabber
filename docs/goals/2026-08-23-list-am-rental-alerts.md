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
  - Status: pending
  - Evidence:

- R2: Send Telegram-only alerts without repeatedly alerting an unchanged listing.
  - Source: User: "VK не нужен, только телеграмм бот для объявлений" and instruction to proceed with the audited minimal plan.
  - Acceptance: After initial baseline, a new listing or changed displayed price sends one text alert with a List.am link; unchanged listings do not resend; failed delivery is retried because it is not persisted as handled.
  - Primary evidence: Pipeline test with a temporary SQLite database and fake notifier covering baseline, unchanged, new, changed-price, and failed-delivery cases.
  - Status: pending
  - Evidence:

- R3: Run through a headless browser in Docker without List.am login or prepared cookies.
  - Source: User: "конечное решение должно работать с headless браузером и без авторизации в докер контейнере".
  - Acceptance: A fresh container with no List.am cookie/profile mount opens a configured category search and parses its cards using headless Chromium.
  - Primary evidence: Production-like Docker smoke command and observed parsed-listing counter; a Cloudflare challenge is a failure, not an empty successful scan.
  - Status: in_progress
  - Evidence: Current upstream Docker/runtime does not establish this contract; a bounded feasibility probe is the first checkpoint.

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

- Closes: R3.
- Smallest next action: Run a disposable production-like headless Playwright probe against one broad List.am rental category from a fresh browser context, first with vanilla Playwright and, only if blocked, one bounded probe with the already-present stealth mechanism.
- Expected evidence: At least one `favorite-ad-card-*` element is found without login/cookie preparation, or an exact Cloudflare/block outcome proves the contract blocked in this environment.
- Stop or replan if: Both bounded probes reach a Cloudflare challenge; do not build proxy, CAPTCHA, login, or cookie-persistence machinery.

## Current State

- Resolved: Upstream source is present at commit `a3ebe93579bd25e2b3e8ccf7529c65d920c85ac8`; the scope and minimum alert workflow are frozen.
- Last relevant evidence: Browser-assisted recon found server-rendered List.am cards and stable `data-testid` attributes, but an independent headless diagnostic reported a Cloudflare challenge; production Docker feasibility remains unresolved.
- Blocker: None while the bounded feasibility probe remains untried as the current checkpoint.
- Next: Execute the R3 probe and update this document with the result before product implementation.

## Material Decisions

- 2026-08-23: Use configured List.am search URLs as the authority for location, budget, rooms, and amenities; do not reproduce those filters locally.
- 2026-08-23: Parse category cards only for the first complete product slice. Telegram links to List.am provide the path to inspect details and call.
- 2026-08-23: First successful full scan creates a no-alert baseline to avoid an initial alert flood.
- 2026-08-23: Keep one state row per listing with its last handled displayed-price key; persist a new key only after successful Telegram delivery.
- 2026-08-23: Adapt only the active runtime. Dormant upstream GUI/Avito files are not a cleanup objective.

## Checkpoint History

- 2026-08-23: Contract frozen from the user request and audited minimal plan. Next checkpoint is the Docker/headless feasibility gate for R3.

## Completion

- Resolved outcomes:
- Commands and artifacts:
- Constraint and diff-scope check:
- Final status:
