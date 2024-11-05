FROM python:3.11.3-slim-buster

WORKDIR /app

COPY epg_test_task epg_test_task
COPY async_alembic async_alembic
COPY alembic.ini alembic.ini

RUN apt-get update && apt-get install -y postgresql-client
RUN pip install --upgrade pip
RUN pip install -r epg_test_task/req/docker/requirements.txt

CMD ["uvicorn", "epg_test_task.src.main:app", "--host", "0.0.0.0", "--port", "8009", "--reload"]


