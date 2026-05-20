# dbt + DuckDB — Government Procurement Analytics Pipeline

> **Decoupled ELT pipeline** over real Brazilian government procurement data from the PNCP API —
> built with Python, dbt, and DuckDB following SOLID principles and Hexagonal Architecture.

---

## Overview

This project extracts **23,000+ real procurement records** from a local PostgreSQL database (fed daily by a production ETL pipeline), transforms them through a structured dbt modeling layer, and delivers analysis-ready data marts — all running locally on DuckDB with zero cloud infrastructure.

The pipeline was built with a focus on **architectural decoupling**: every component has a single responsibility and depends only on abstractions, not concrete implementations. Swapping the data source, the destination database, or any transformation layer requires changing a single class — nothing else.

---

## Lineage Graph

```
st_licitacoes  ──►  int_licitacoes_enriquecidas  ──►  mart_por_modalidade
                                                  ──►  mart_por_orgao
                                                  ──►  mart_por_uf
```



---

## Architecture

### Decoupled Python Pipeline

The extraction and load layer is built around four single-responsibility classes, each injected into the next — none of them knows about the others' internals.

```
DBConnectionParams          ← immutable Value Object — holds connection parameters
      │
      ▼
DatabaseConnector           ← manages the PostgreSQL connection pool
      │                       receives DBConnectionParams via dependency injection
      ▼
DataExtractor               ← extracts records from PostgreSQL
      │                       receives a DatabaseConnector — doesn't know where it came from
      ▼
DataTransformer             ← parses JSONB payload, normalizes text, casts types
      │                       receives a DataFrame — doesn't know the data source
      ▼
DuckDBLoader                ← loads transformed data into DuckDB
                              receives a DataFrame — doesn't know how it was built
```

**Switching data sources requires changing one line:**

```python
# Local database
params = DBConnectionParams.from_local()

# Production VPS — zero changes elsewhere
params = DBConnectionParams.from_vps()

# Any custom database
params = DBConnectionParams.from_custom(host=..., port=..., dbname=..., user=..., password=...)
```

### dbt Modeling Layers

| Layer | Materialization | Responsibility |
|---|---|---|
| `staging` | View | 1:1 source cleanup — renaming, type casting, enum decoding |
| `intermediate` | View | Business logic — enrichment, flags, regional classification |
| `marts` | Table | Aggregated analytical tables ready for consumption |

---

## Project Structure

```
dbt_duckdb/
├── engine_processamento_duck_db/
│   ├── __init__.py
│   ├── config.py                   ← environment config via .env
│   ├── db_connection_params.py     ← Value Object — immutable connection params
│   ├── database_manager.py         ← PostgreSQL connection pool (ThreadedConnectionPool)
│   ├── data_extractor.py           ← SQL extraction layer
│   ├── data_transformer.py         ← JSONB parsing + data normalization
│   └── duckdb_loader.py            ← DuckDB persistence layer
├── main.py                         ← Pipeline orchestrator
├── licitacoes_dbt/
│   ├── models/
│   │   ├── staging/
│   │   │   ├── st_licitacoes.sql   ← source cleanup
│   │   │   └── schema.yml          ← data quality tests
│   │   ├── intermediate/
│   │   │   └── int_licitacoes_enriquecidas.sql
│   │   └── marts/
│   │       ├── mart_por_uf.sql
│   │       ├── mart_por_modalidade.sql
│   │       └── mart_por_orgao.sql
│   └── dbt_project.yml
├── .env                            ← not committed
├── .gitignore
└── requirements.txt
```

---

## Components

### `DBConnectionParams` — Value Object

Immutable dataclass that holds database connection parameters. Provides factory methods for different environments — the rest of the pipeline never reads from `.env` directly.

```python
@dataclass(frozen=True)
class DBConnectionParams:
    host: str
    port: str
    dbname: str
    user: str
    password: str

    @classmethod
    def from_local(cls) -> "DBConnectionParams": ...

    @classmethod
    def from_vps(cls) -> "DBConnectionParams": ...

    @classmethod
    def from_custom(cls, host, port, dbname, user, password) -> "DBConnectionParams": ...
```

### `DatabaseConnector` — Connection Pool Manager

Manages a `ThreadedConnectionPool` (1–20 connections). Receives `DBConnectionParams` via constructor injection — it does not read configuration itself.

```python
class DatabaseConnector:
    def __init__(self, params: DBConnectionParams): ...

    @contextmanager
    def get_connection(self): ...  # auto-rollback on error, auto-return to pool
```

### `DataExtractor` — Extraction Layer

Receives a `DatabaseConnector` — has no knowledge of connection details. Provides three extraction modes for different contexts.

```python
class DataExtractor:
    def __init__(self, db: DatabaseConnector): ...

    def extract(self) -> pd.DataFrame: ...              # full dataset
    def extract_by_uf(self, uf: str) -> pd.DataFrame:  # filtered by state
    def extract_sample(self, limit: int) -> pd.DataFrame: ...  # dev/test sample
```

### `DataTransformer` — Transformation Layer

Parses raw JSONB payloads into structured columns, normalizes text using `unicodedata.normalize('NFD')`, casts date types, and cleans numeric values. Receives a DataFrame — has no knowledge of the data source.

```python
class DataTransformer:
    def __init__(self, df: pd.DataFrame): ...
    def transform(self) -> pd.DataFrame: ...
```

**Transformation pipeline:**
1. `_parse_json()` — handles both string and dict JSONB
2. `_extract_json_fields()` — flattens 25+ nested JSONB fields into columns
3. `_normalize_text()` — strips diacritics, standardizes case
4. `_parse_dates()` — `pd.to_datetime` with `errors='coerce'`
5. `_clean_values()` — numeric nulls → `0.0`
6. `_drop_raw_json()` — removes raw payload after extraction
7. `_reorder_columns()` — deterministic column ordering

### `DuckDBLoader` — Load Layer

Creates the DuckDB file automatically on first run. Supports full reload (idempotent) and incremental load (inserts only new records by `id`).

```python
class DuckDBLoader:
    def load(self, df: pd.DataFrame) -> None: ...             # full reload
    def load_incremental(self, df: pd.DataFrame) -> None: ... # insert new only
```

---

## dbt Models

### Staging — `st_licitacoes`

Materialized as a **view**. One transformation per column — no business logic.

Key transformations:
- `orgao_esfera`: `'E'` → `'Estadual'`, `'F'` → `'Federal'`, `'M'` → `'Municipal'`
- `orgao_poder`: `'E'` → `'Executivo'`, `'L'` → `'Legislativo'`, `'J'` → `'Judiciário'`
- Date columns cast to `TIMESTAMP`
- Derived: `ano_publicacao`, `mes_publicacao`, `ano_encerramento`, `mes_encerramento`

**Data quality tests (9 passing):**
- `not_null` on `licitacao_id`, `numero_controle_pncp`, `uf`, `orgao_cnpj`, `modalidade_nome`, `valor_total_estimado`
- `unique` on `licitacao_id`
- `accepted_values` on `orgao_esfera` and `orgao_poder`

### Intermediate — `int_licitacoes_enriquecidas`

Materialized as a **view**. Adds business logic and derived fields on top of staging.

Enrichments:
- `faixa_valor` — value range classification (7 bands from `< R$ 10k` to `> R$ 1M`)
- `is_ativa` — `true` if `data_encerramento >= current_date`
- `is_alto_valor` — `true` if `valor_total_estimado >= R$ 100,000`
- `dias_para_encerramento` — days until deadline (active records only)
- `dias_desde_publicacao` — days since PNCP publication
- `regiao` — mapped from UF to Brazilian region (Norte / Nordeste / Centro-Oeste / Sudeste / Sul)

### Marts — Final Analytical Tables

Materialized as **tables**. Aggregated, analysis-ready — consumed directly by BI tools or downstream queries.

**`mart_por_uf`** — procurement volume and value by Brazilian state:

| Column | Description |
|---|---|
| `uf` / `uf_nome` / `regiao` | State identifiers |
| `total_licitacoes` | Total procurement notices |
| `total_ativas` | Currently active notices |
| `total_alto_valor` | Notices above R$ 100k |
| `valor_total` / `valor_medio` / `valor_maximo` | Value aggregations |
| `total_orgaos` | Distinct contracting entities |
| `pct_ativas` | % of active notices |

**`mart_por_modalidade`** — distribution by procurement modality (Pregão, Credenciamento, etc.):

Includes `pct_do_total` window function showing each modality's share of all notices.

**`mart_por_orgao`** — top contracting entities ranked by volume:

Includes `primeira_publicacao` / `ultima_publicacao` for activity timeline analysis.

---

## Data Quality Results

```
dbt test --select staging

9 of 9 PASS  ✓  not_null_licitacao_id
             ✓  unique_licitacao_id
             ✓  not_null_numero_controle_pncp
             ✓  not_null_uf
             ✓  not_null_orgao_cnpj
             ✓  not_null_modalidade_nome
             ✓  not_null_valor_total_estimado
             ✓  accepted_values_orgao_esfera
             ✓  accepted_values_orgao_poder
```

---

## Production Metrics

| Metric | Value |
|---|---|
| Records loaded | 23,913 procurement notices |
| Data source | PNCP API — Brazilian Federal Government |
| Pipeline execution | ~30s end-to-end (extract → transform → load → dbt run) |
| dbt models | 5 (1 staging + 1 intermediate + 3 marts) |
| Data quality tests | 9 (all passing) |
| Infrastructure | Single DuckDB file — zero cloud, zero servers |

---

## Design Patterns Applied

| Pattern | Where |
|---|---|
| **Value Object** | `DBConnectionParams` — immutable, no behavior, pure data |
| **Dependency Injection** | `DatabaseConnector` receives params; `DataExtractor` receives connector |
| **Factory Method** | `from_local()`,  `from_custom()` on `DBConnectionParams` |
| **Context Manager** | `get_connection()` — auto-return to pool, auto-rollback |
| **Repository Pattern** | `DataExtractor` — all SQL in one place, views and services never write queries |
| **SOLID — SRP** | Each class has one reason to change |
| **SOLID — OCP** | New data source = new factory method, no changes to existing code |
| **SOLID — DIP** | `DataExtractor` depends on `DatabaseConnector` abstraction, not psycopg2 directly |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.12 |
| Data manipulation | pandas |
| Source database | PostgreSQL (psycopg2 — ThreadedConnectionPool) |
| Analytical database | DuckDB |
| Data modeling | dbt-core 1.11 + dbt-duckdb |
| Configuration | python-dotenv |
| Pipeline orchestration | Single `Pipeline` class — sequential, no external scheduler |

---

## Setup

**1. Clone and install dependencies:**
```bash
git clone https://github.com/PJKTDELFOS/dbt-licitacoes
cd dbt-licitacoes
pip install -r requirements.txt
```

**2. Configure environment:**
```bash
cp .env.example .env
# Edit .env with your PostgreSQL credentials
```

**3. Run the Python pipeline (PostgreSQL → DuckDB):**
```bash
python main.py
```

**4. Run dbt transformations:**
```bash
cd licitacoes_dbt
dbt run
dbt test
```

**5. Explore the lineage graph:**
```bash
dbt docs generate
dbt docs serve
```

---

## Key dbt Commands

```bash
dbt run                          # run all models
dbt run --select staging         # run a specific layer
dbt run --select mart_por_uf     # run a specific model
dbt test                         # run all data quality tests
dbt build                        # run + test together
dbt show --select mart_por_uf --limit 20   # preview data
dbt docs generate && dbt docs serve        # generate and open lineage graph
```

---

## About

Built by **Albert Pimentel França** — Data Engineer and Python developer with 12 years of domain expertise in Brazilian government procurement (B2G).

- GitHub: [@PJKTDELFOS](https://github.com/PJKTDELFOS)
- LinkedIn: [albert-pimentel-franca](https://www.linkedin.com/in/albertpimentel-franca/)
- Open to remote **Data Engineering** and **Data Analyst** opportunities in Brazil,Portugal and Spain 🇧🇷🇵🇹

> *Developed with AI-assisted coding (Claude) for model generation, test design, and documentation — reflecting real-world engineering workflows where AI accelerates production without replacing domain judgment.*

---

© 2026 Albert Pimentel França. MIT License.