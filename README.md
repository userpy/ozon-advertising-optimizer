# Ozon Advertising Optimizer

Production-like проект для расчета оптимального рекламного давления товаров Ozon.

Проект разбивает логику исходного SQL-представления
`public.v_oz_fcast_mart_fuji_oz_2232506` на независимые ETL-этапы:

- `categories` -> `services.extract.extract_categories`
- `adv_funnel` -> `services.extract.extract_advertising`
- `prices` -> `services.extract.extract_prices`
- `self_cost` -> `services.extract.extract_self_cost`
- `sales_funnel` -> `services.extract.extract_sales`
- `final_mart`, `daily_aggregated`, history features -> `services.preprocessing`
- прогнозы и выбор давления -> `services.predict` и `services.profit`

Монолитный SQL не используется в DAG. SQL находится только в `db/queries.py` и
разделен на небольшие запросы по источникам.

## Stack

- Python 3.12
- Apache Airflow
- PostgreSQL
- SQLAlchemy 1.4.x runtime, совместимый с Airflow 2.10
- Alembic
- Pandas
- psycopg
- Docker Compose
- Ruff, Black, pytest

## Quick Start

Создать файл `.env` из примера и при необходимости изменить настройки:

```bash
cp .env.example .env
```

Поднять окружение:

```bash
docker compose up -d
```

Применить миграции:

```bash
docker compose exec airflow-webserver alembic upgrade head
```

Сгенерировать тестовые данные:

```bash
docker compose exec airflow-webserver python scripts/seed_postgres.py
```

Открыть Airflow:

```text
http://localhost:8080
```

Порт задается переменной `AIRFLOW_HOST_PORT` в `.env`.

Логин и пароль по умолчанию:

```text
admin / admin
```

Учетные данные задаются переменными `AIRFLOW_ADMIN_USERNAME` и
`AIRFLOW_ADMIN_PASSWORD` в `.env`.

Запустить DAG:

```text
optimal_advertising_pressure_dag
```

## Запуск DAG

После запуска контейнеров, миграций и seed-скрипта DAG можно запустить вручную
через Airflow UI или через CLI.

### Запуск через Airflow UI

1. Открыть Airflow:

```text
http://localhost:8080
```

2. Войти под пользователем:

```text
username: admin
password: admin
```

3. Найти DAG:

```text
optimal_advertising_pressure_dag
```

4. Если DAG находится на паузе, выключить переключатель `Pause`.
5. Нажать кнопку запуска DAG.
6. После успешного выполнения результат появится в таблице:

```text
public.optimal_advertising_pressure
```

### Запуск через CLI

```bash
docker compose exec airflow-webserver airflow dags unpause optimal_advertising_pressure_dag
docker compose exec airflow-webserver airflow dags trigger optimal_advertising_pressure_dag
```

Проверить результат:

```bash
docker compose exec postgres psql -U airflow -d airflow -c \
"select * from public.optimal_advertising_pressure limit 10;"
```

## Примечание по исходному SQL

Исходный SQL-запрос создавал витрину признаков
`public.v_oz_fcast_mart_fuji_oz_2232506`. В нем была бизнес-логика получения
категорий, рекламной статистики, цен, себестоимости, воронки продаж,
агрегации по дням и исторических признаков.

В исходном SQL не было:

- оркестрации Airflow;
- отдельного слоя доступа к данным;
- сохранения результата в таблицу оптимального давления;
- перебора рекламного давления от `0` до `100`;
- прогнозных функций для позиции, показов, `CR1`, `CR2` и заказов;
- расчета ожидаемой прибыли;
- выбора оптимального рекламного давления;
- Alembic-миграций, Docker Compose и генератора тестовых данных.

В проект добавлено:

- разбиение монолитного SQL на небольшие запросы в `db/queries.py`;
- сервисный слой `services/` для ETL, preprocessing, predict, profit и save;
- DAG `optimal_advertising_pressure_dag` с отдельной задачей на каждый этап;
- таблица `public.optimal_advertising_pressure` для результата;
- seed-скрипт, создающий 100 логически связанных тестовых строк;
- тесты, линтеры и инструкция запуска.

## What The Pipeline Does

1. Извлекает категории, рекламу, цены, себестоимость и воронку продаж.
2. Собирает feature mart через Pandas merge.
3. Агрегирует метрики до уровня `sku + stats_date`.
4. Добавляет исторические признаки: вчера, `m2`, `m9`...`m14`, средние за 5/15/30 дней.
5. Для каждого SKU строит сценарии рекламного давления от `0` до `100`.
6. Считает прогнозы позиции, показов, `CR1`, `CR2`, заказов.
7. Рассчитывает ожидаемую прибыль для каждого сценария.
8. Выбирает давление с максимальной прибылью.
9. Сохраняет результат в `public.optimal_advertising_pressure`.

## Result Table

Миграция Alembic создает таблицу:

```text
public.optimal_advertising_pressure
```

Основные поля:

- `stats_date`
- `sku`
- `offer_id`
- `current_pressure`
- `optimal_pressure`
- `expected_position`
- `expected_impressions`
- `expected_cr1`
- `expected_cr2`
- `expected_orders`
- `expected_profit`
- `created_at`

Для идемпотентности используется уникальность `stats_date + sku`.

## Seed Data

`scripts/seed_postgres.py` создает исходные таблицы, очищает старые данные и
заполняет 100 строк продаж: 10 SKU за 10 дней.

Данные связаны логически:

- рост рекламного давления улучшает позицию;
- рост рекламного давления увеличивает показы;
- корзины и заказы считаются из показов и конверсий;
- рекламные расходы согласованы с выручкой.

## Структура проекта

```text
db/
  connection.py      настройка подключения к PostgreSQL
  models.py          объявления таблиц SQLAlchemy
  queries.py         небольшие SQL-запросы к источникам
  repository.py      репозиторий для чтения и записи данных

services/
  extract.py         извлечение данных из источников
  preprocessing.py   сборка витрины признаков и исторических признаков
  predict.py         заменяемые заглушки прогнозных моделей
  profit.py          расчет прибыли и оптимального давления
  save.py            сохранение результата

dags/
  optimal_advertising_pressure_dag.py

scripts/
  seed_postgres.py

alembic/
  versions/

tests/
```

## Development

Install dependencies locally:

```bash
python -m pip install -e ".[dev]"
```

Run tests:

```bash
pytest
```

Run formatting and linting:

```bash
black .
ruff check .
```

## Replacing Stubs With ML Models

`services.predict` exposes independent functions:

- `predict_position`
- `predict_impressions`
- `predict_cr1`
- `predict_cr2`
- `predict_orders`

Each prediction function accepts an optional model object with `.predict(...)`.
That allows replacing heuristics with scikit-learn `.pkl` models without changing
the Airflow DAG contract.
