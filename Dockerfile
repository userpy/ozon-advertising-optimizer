FROM apache/airflow:2.10.5-python3.12

WORKDIR /opt/airflow

COPY --chown=airflow:root pyproject.toml README.md ./
COPY --chown=airflow:root alembic.ini ./alembic.ini
COPY --chown=airflow:root alembic ./alembic
COPY --chown=airflow:root db ./db
COPY --chown=airflow:root services ./services
COPY --chown=airflow:root scripts ./scripts

RUN pip install --no-cache-dir -e ".[dev]"
