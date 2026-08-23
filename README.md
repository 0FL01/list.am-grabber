# List.am Rental Monitor

Персональный монитор долгосрочной аренды жилья на List.am. Он открывает настроенные поисковые выдачи в headless Chromium и присылает новые объявления или изменения цены в Telegram.

## Что входит

- квартиры, дома или комнаты через готовые URL фильтров List.am;
- текстовые Telegram-алерты со ссылкой на объявление;
- номер телефона в формате `+374...`, когда он доступен;
- до 10 первых фотографий одним Telegram-альбомом;
- SQLite-дедупликация;
- запуск без авторизации и подготовленных cookies;
- постоянный мониторинг в Docker.

Первый успешный проход создаёт baseline без отправки текущих объявлений. После него новые объявления и изменения отображаемой цены отправляются в Telegram.
Телефон раскрывается только для объявления, которое нужно отправить, и показывается как копируемый code-фрагмент.
Если фотографий больше десяти, последние обрезаются до лимита Telegram. Подпись размещается только у первой фотографии, поэтому отдельное текстовое сообщение не создаётся. Если Telegram не принимает фотографии, бот отправляет один текстовый alert.

## Настройка

Создайте локальный конфиг из примера:

```bash
cp config.example.toml config.toml
```

Заполните Telegram credentials и URL поиска в `config.toml`:

```toml
[telegram]
bot_token = "123456:telegram-bot-token"
chat_id = "123456789"

[list_am]
search_urls = [
    "https://www.list.am/ru/category/56?n=43&srt=3",
    "https://www.list.am/ru/category/56?n=58&srt=3",
]
max_pages = 1
poll_interval_seconds = 60
database_path = "data/listings.db"
```

Фильтры района, цены, комнат и удобств задавайте на List.am и копируйте получившиеся URL в `search_urls`. `max_pages` применяется отдельно к каждой ссылке; совпавшие объявления дедуплицируются по ID.
`config.toml` добавлен в `.gitignore`; в Git хранится только `config.example.toml` без секретов.

## Запуск

```bash
docker compose up --build -d
docker compose logs -f list_am
```

Остановить монитор:

```bash
docker compose down
```

Однократная проверка выдачи:

```bash
docker compose run --rm list_am --once
```

List.am login, cookie-файл и browser profile не требуются. Состояние сохраняется в `./data`.

## Проверка

```bash
python -m unittest discover -s tests
```
