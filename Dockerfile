FROM python:3.11-slim-bookworm

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
RUN python -m playwright install --with-deps chromium

COPY parser_cls.py analyst.py db_service.py dto.py load_config.py models.py /app/
COPY parser/__init__.py parser/browser.py parser/list_am.py parser/pipeline.py /app/parser/
COPY integrations/notifications/__init__.py integrations/notifications/list_am_telegram.py /app/integrations/notifications/
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
