# List.am Rental Monitor

Headless Docker-монитор объявлений List.am с Telegram-алертами и SQLite-дедупликацией.

## Map

- `parser_cls.py` — CLI и polling loop.
- `parser/browser.py` — Playwright session, выдача и date enrichment новых лотов.
- `parser/list_am.py` — чистый разбор карточек, пагинации, изображений и дат.
- `parser/pipeline.py`, `db_service.py` — baseline и состояние доставленных алертов.
- `integrations/notifications/list_am_telegram.py` — Telegram text/photo/album delivery.
- `config.example.toml` — публичный шаблон runtime-конфига.

## Rules

- Активный runtime не должен импортировать старые Avito/VK/GUI/export paths.
- Фильтры поиска задаются URL List.am; `max_pages` применяется к каждому URL.
- Создавать новый Playwright context на каждый scan: Cloudflare блокирует повторные проходы в старом context.
- Первый полный scan создаёт baseline. Состояние обновляется только после успешного Telegram alert.
- Media enrichment не должен блокировать текстовый alert.
- Date enrichment выполняется только для лотов, выбранных для отправки.
- Telegram album: максимум 10 первых фото, caption только у первого.
- Между алертами одной пачки сохранять Telegram jitter не меньше 1 секунды.
- Не коммитить `config.toml`, `data/`, cookies, browser profiles или credentials.

## Verify

- `python -m unittest discover -s tests` — после изменения Python runtime.
- `docker build -t list-am-search:local .` — после изменения runtime или Docker packaging.
- `docker compose config` — после изменения Compose или config mounts.
