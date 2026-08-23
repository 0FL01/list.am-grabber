# List.am Rental Monitor

Docker-монитор аренды жилья на List.am: новые объявления и изменения цены приходят в Telegram со ссылкой, фотографиями и датами размещения/обновления.

## Настройка

```bash
cp config.example.toml config.toml
```

Заполните Telegram credentials и готовые URL поиска в `config.toml`. Можно указать несколько выдач:

```toml
[list_am]
search_urls = [
    "https://www.list.am/ru/category/56?n=43&srt=3",
    "https://www.list.am/ru/category/56?n=58&srt=3",
]
```

Полный шаблон: [`config.example.toml`](config.example.toml). Локальный `config.toml` и данные в `data/` не попадают в Git.

## Запуск

```bash
docker compose up --build -d
docker compose logs -f list_am
```

Однократный проход:

```bash
docker compose run --rm list_am --once
```

По умолчанию первый успешный проход создаёт baseline без алертов. `notify_existing_on_first_run = true` отправит все найденные объявления после очистки базы. Массовая пачка отправляется с джиттером 1–2 секунды между алертами. Далее бот отправляет новые объявления и изменения цены. До 10 фотографий группируются в один альбом. Авторизация и подготовленные cookies не нужны.

## Проверка

```bash
python -m unittest discover -s tests
```
