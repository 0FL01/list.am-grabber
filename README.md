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

## Аналитик

Опциональная секция `[analyst]` отправляет модели текст, характеристики и фотографии нового лота, а затем отвечает reply на основной Telegram-алерт. Поддерживается любой model ID через современный OpenAI-compatible `POST /chat/completions`; prompt и `reasoning_effort` задаются в конфиге.

Режим выключен по умолчанию. Он не открывает браузер, не хранит историю и запускается только после доставки и сохранения всех основных алертов текущего scan. Если задан `LIST_AM_PROXY_URL`, фотографии загружаются через него в память и передаются модели как data URL; сам model request остаётся direct. Анализ best-effort: его ошибка не повторяет основной алерт и не блокирует следующие ответы.

`reply_format = "markdown"` преобразует CommonMark в разрешённый Telegram HTML; произвольный HTML модели экранируется. Значение `plain` сохраняет максимально надёжный ответ без форматирования. `max_images = 0` передаёт всю доступную галерею, положительное значение — первые N фото. `max_completion_tokens = 0` не отправляет ограничение провайдеру; положительный лимит включает скрытые reasoning tokens. Одновременные `analyst.enabled = true` и `notify_existing_on_first_run = true` могут создать платный запрос для каждого объявления первой пачки.

## Проверка

```bash
python -m unittest discover -s tests
```
