# List.am Rental Monitor

Персональный монитор долгосрочной аренды жилья на List.am. Он открывает настроенные поисковые выдачи в headless Chromium и присылает новые объявления или изменения цены в Telegram.

## Что входит

- квартиры, дома или комнаты через готовые URL фильтров List.am;
- текстовые Telegram-алерты со ссылкой на объявление;
- SQLite-дедупликация;
- запуск без авторизации и подготовленных cookies;
- постоянный мониторинг в Docker.

Первый успешный проход создаёт baseline без отправки текущих объявлений. После него новые объявления и изменения отображаемой цены отправляются в Telegram.

## Настройка

Отредактируйте `config.toml`:

```toml
[list_am]
search_urls = [
    "https://www.list.am/ru/category/56",
]
max_pages = 1
poll_interval_seconds = 60
database_path = "data/listings.db"
```

Фильтры района, цены, комнат и удобств задавайте на List.am и копируйте получившийся URL в `search_urls`.

Перед запуском задайте Telegram credentials только через environment:

```bash
export TELEGRAM_BOT_TOKEN="..."
export TELEGRAM_CHAT_ID="..."
```

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
