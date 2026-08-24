# List.am Rental Monitor

Headless Docker-монитор объявлений List.am с Telegram-алертами и SQLite-дедупликацией.

## Map

- `parser_cls.py` — CLI и polling loop.
- `parser/browser.py` — Playwright session, выдача и detail enrichment новых лотов.
- `parser/list_am.py` — чистый разбор карточек, пагинации, detail и изображений.
- `parser/pipeline.py`, `db_service.py` — baseline и состояние доставленных алертов.
- `integrations/notifications/list_am_telegram.py` — Telegram text/photo/album delivery.
- `analyst.py` — stateless OpenAI-compatible text/vision analysis новых лотов.
- `config.example.toml` — публичный шаблон runtime-конфига.

## Rules

- Активный runtime не должен импортировать старые Avito/VK/GUI/export paths.
- Фильтры поиска задаются URL List.am; `max_pages` применяется к каждому URL.
- Создавать новый Playwright context на каждый scan: Cloudflare блокирует повторные проходы в старом context.
- Первый полный scan создаёт baseline. Состояние обновляется только после успешного Telegram alert.
- Media enrichment не должен блокировать текстовый alert.
- Detail enrichment выполняется только для лотов, выбранных для отправки.
- Detail enrichment использует отдельный свежий context: context выдачи блокируется на detail navigation.
- Telegram album: максимум 10 первых фото, caption только у первого; analyst может получить полную галерею.
- Все Telegram sends проходят gate не меньше 1 секунды; batch jitter 1–2 секунды сохраняется.
- Analyst запускается после сохранения всех основных алертов и закрытия Playwright; не добавлять ему browser, persistent state или историю.
- Analyst image relay использует `LIST_AM_PROXY_URL` только для in-memory download; model requests остаются direct.
- Analyst failure/reply failure не должен откатывать основной alert или прерывать следующие analysis jobs.
- Markdown analyst reply конвертируется в whitelist Telegram HTML; не передавать raw model output через `parse_mode`.
- Не коммитить `config.toml`, `data/`, cookies, browser profiles или credentials.

## Deploy

- Сервис развёрнут в `/srv/compose/list.am-grabber`; remote доступен через SSH MCP `ssh-nc-lab`.

## Verify

- `python -m unittest discover -s tests` — после изменения Python runtime.
- `docker build -t list-am-search:local .` — после изменения runtime или Docker packaging.
- `docker compose config` — после изменения Compose или config mounts.
