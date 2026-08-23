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
  - Acceptance: The default first scan creates a baseline, while explicit `notify_existing_on_first_run` sends current listings; afterward a new listing or changed displayed price sends one alert; unchanged listings do not resend; failed delivery is retried because it is not persisted as handled.
  - Primary evidence: Pipeline test with a temporary SQLite database and fake notifier covering baseline, unchanged, new, changed-price, and failed-delivery cases.
  - Status: verified
  - Evidence: Focused pipeline and Telegram tests pass for initial baseline, unchanged suppression, new listing, changed price, failed delivery remaining retryable, escaped text payloads, and sanitized transport failures.

- R3: Run through a headless browser in Docker without List.am login or prepared cookies.
  - Source: User: "конечное решение должно работать с headless браузером и без авторизации в докер контейнере".
  - Acceptance: A fresh container with no List.am cookie/profile mount opens a configured category search and parses its cards using headless Chromium.
  - Primary evidence: Production-like Docker smoke command and observed parsed-listing counter; a Cloudflare challenge is a failure, not an empty successful scan.
  - Status: verified
  - Evidence: Fresh-container and remote-host probes parsed 104-105 cards using full headless Chromium with stealth and no login, cookie file, or browser-profile mount. The lighter `chromium-headless-shell` was rejected by Cloudflare on the remote host and is not used.

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

- R6: Include a callable Armenian phone number in alerts when List.am exposes one.
  - Source: User: "номер телефона извлекать" in format `+37493939319` and make it copyable with one backtick pair.
  - Acceptance: Before sending a new or price-changed listing, runtime reveals its first available phone without login, normalizes Armenian local numbers to `+374...`, and renders it as a Telegram inline-code value; missing phone does not suppress the alert.
  - Primary evidence: Phone normalization and Telegram formatting tests plus one live headless phone-reveal smoke.
  - Status: superseded
  - Evidence: Superseded by the user's 2026-08-23 instruction to remove phone acquisition under KISS after remote `/rtam` began requiring List.am authorization.

- R7: Include listing photos without producing separate-message clutter.
  - Source: User: "поддержку скриншотов из лота", respect Telegram limits, trim last images, and "не плодить хаос из сообщений".
  - Acceptance: Alerts use up to the first 10 listing photos in one Telegram album with the alert caption only on the first item; one photo uses one photo message; media failure falls back to one text alert.
  - Primary evidence: Category image extraction fixture and mocked Telegram payload tests against the documented Bot API limits.
  - Status: verified
  - Evidence: Ten focused tests pass for first-10 extraction, one-caption album payload, single-photo delivery, and text fallback; generated live URL `https://img.list.am/f/897/100886897.webp` returned HTTP 200 as a 720×960 image; the final Docker image builds.

### Constraints

- C1: Use a headless browser in Docker; do not require List.am authorization or prepared cookies.
- C2: Telegram is the only notification channel; VK is not part of the active runtime.
- C3: Keep the implementation minimal under KISS, YAGNI, and Pareto.
- C4: Make repository commits as checkpoints, as explicitly requested by the user.
- C5: Do not commit Telegram credentials, browser profiles, cookies, or generated databases.
- C6: Telegram credentials are read from local `config.toml`, not exported environment variables.

### Non-goals

- Full detail-page parsing or sending more than Telegram's first 10 album images.
- Phone extraction or List.am authentication.
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

- Closes: R1-R7.
- Smallest next action: None; closure evidence is current.
- Expected evidence: All required outcomes are verified.
- Stop or replan if: A final diff check fails.

## Current State

- Resolved: R1-R5 and R7 are verified; R6 is superseded by the no-phone KISS decision.
- Last relevant evidence: Nine tests pass; active runtime no longer opens detail pages or calls the authorization-gated phone endpoint.
- Blocker: None.
- Next: None.

## Material Decisions

- 2026-08-23: Use configured List.am search URLs as the authority for location, budget, rooms, and amenities; do not reproduce those filters locally.
- 2026-08-23: Parse category cards only for the first complete product slice. Telegram links to List.am provide the path to inspect details and call.
- 2026-08-23: First successful full scan creates a no-alert baseline to avoid an initial alert flood.
- 2026-08-23: Keep one state row per listing with its last handled displayed-price key; persist a new key only after successful Telegram delivery.
- 2026-08-23: Adapt only the active runtime. Dormant upstream GUI/Avito files are not a cleanup objective.
- 2026-08-23: Vanilla headless Chromium is blocked in the current Docker environment; use the existing `playwright-stealth` integration without adding broader bypass infrastructure.
- 2026-08-23: Use `python:3.11-slim-bookworm` with Playwright-managed full Chromium. `chromium-headless-shell` was reproducibly blocked on the deployment host while full Chromium returned HTTP 200 with 105 cards under otherwise identical settings.
- 2026-08-23: Store Telegram credentials in ignored `config.toml`; track only `config.example.toml` and remove Telegram environment wiring from Compose.
- 2026-08-23: Reveal a phone only for listings selected for delivery, normalize the first Armenian number to `+374...`, and render it with Telegram inline-code semantics; phone failure remains non-fatal.
- 2026-08-23: Send at most the first 10 List.am photos as one Telegram album with one caption; use one photo message for a single image and one text fallback if media delivery fails.
- 2026-08-23: Keep baseline as the safe default, but allow an explicit first-run mode that sends all current listings and persists each only after successful delivery.
- 2026-08-23: After one blocked phone reveal, skip phone enrichment for the rest of that scan so bulk delivery continues without repeated 15-second challenge waits.
- 2026-08-23: Space multi-alert batches with a random 1-2 second delay between successful Telegram deliveries; do not delay a single alert or sleep after the last item.
- 2026-08-23: Remove phone acquisition entirely after the user chose KISS over introducing List.am authorization; alerts retain the direct listing link.

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
- 2026-08-23: R6 verified. Phone normalization/inline-code tests pass; Docker headless reveal produced `+37455502560` without List.am authorization.
- 2026-08-23: R7 verified. Ten tests cover extraction and grouped delivery; a generated live full-size image URL returned HTTP 200 and the final image builds.
- 2026-08-23: Remote production diagnosis isolated Cloudflare blocking to `chromium-headless-shell`; full headless Chromium passed twice with 105 cards, so Docker packaging and launch now pin the full browser executable.
- 2026-08-23: The tracked config example now demonstrates two independent regional search URLs and documents per-URL `max_pages` behavior.
- 2026-08-23: R6 superseded by explicit user instruction. Phone code and detail-page navigation were removed after remote verification showed `/rtam` requires authorization.

## Completion

- Resolved outcomes: R1 configured List.am scanning; R2 Telegram-only deduplicated delivery; R3 headless Docker operation without List.am auth or prepared cookies; R4 repeatable local container monitoring; R5 ignored TOML-based Telegram credentials with a tracked example; R6 superseded; R7 grouped listing photos within Telegram limits.
- Commands and artifacts: `python -m unittest discover -s tests` (9 passing); `docker build -t list-am-search:local .`; image `pip check`; `docker compose config`; Git ignore checks; secret-safe image assertions; live `--once` scan with 105 parsed cards; production-interval lifecycle/SIGTERM run; live generated List.am image HTTP 200.
- Constraint and diff-scope check: Active runtime contains no VK, XLSX, detail/phone scraping, login, proxy, CAPTCHA service, persistent browser profile, or Telegram environment wiring. Telegram credentials and generated state are not committed. Dormant upstream files were not cosmetically cleaned up.
- Final status: complete
