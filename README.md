# Data Quality Checker

[![Tests](https://github.com/anna1sheludko/data-quality-checker/actions/workflows/tests.yml/badge.svg)](https://github.com/anna1sheludko/data-quality-checker/actions/workflows/tests.yml)
![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python)
![Pandas](https://img.shields.io/badge/Pandas-2.2+-blue?logo=pandas)
![Docker](https://img.shields.io/badge/Docker-✓-blue?logo=docker)
![License](https://img.shields.io/badge/license-MIT-green)

CLI tool that analyzes CSV/Excel files and generates a data quality report
in HTML, JSON, and Markdown — so you can see exactly what's wrong with your
data before you load it anywhere.

Built as a portfolio project demonstrating:
- Modular code design (separate checks, reporters, loaders)
- Data validation with Pandera and custom rules
- Rich CLI output with progress indicators
- Multi-format report generation (HTML via Jinja2, JSON, Markdown)
- Testing with pytest (47 tests, 100% passing)
- Docker for reproducibility

---

## What it does

You point it at a file. It runs **6 independent checks** and produces a report:

| Check | Detects |
|---|---|
| **duplicates** | Full and partial duplicate rows |
| **missing** | Missing values per column, with severity |
| **types** | Null-like strings ("N/A"), mixed types in one column |
| **outliers** | Values outside Z-score or IQR bounds |
| **consistency** | Case variants ("Warsaw" vs "WARSAW"), whitespace |
| **suspicious** | Business-rule violations (negative prices, future dates, invalid emails) |

Each issue gets a severity: `info` / `warning` / `critical`.

---

## Example output

```
$ dqc --input data/sample_messy.csv

┏━━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Check        ┃ Status   ┃ Severity  ┃ Issues ┃ Message                       ┃
┡━━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ duplicates   │ ✗ failed │ warning   │ 1      │ Found 3 duplicate rows (9.1%) │
│ missing      │ ✗ failed │ warning   │ 4      │ 4 columns have missing values │
│ types        │ ✓ passed │ ok        │ 0      │ Types are consistent          │
│ outliers     │ ✗ failed │ warning   │ 1      │ 1 column contains outliers    │
│ consistency  │ ✗ failed │ warning   │ 1      │ 1 column has case issues      │
│ suspicious   │ ✗ failed │ critical  │ 2      │ 2 rule violations             │
└──────────────┴──────────┴───────────┴────────┴───────────────────────────────┘
```

HTML report includes KPI cards, per-check sections, and clickable issue lists.

---

## Architecture

```
        CSV / Excel
             │
             ▼
      ┌──────────────┐
      │   loader.py  │  reads CSV/Excel, detects column types
      └──────┬───────┘
             │ DataFrame
             ▼
      ┌──────────────┐
      │   checks/    │  6 independent checks, each returns CheckResult
      │  duplicates  │  (duplicates, missing, types, outliers,
      │   missing    │   consistency, suspicious)
      │    types     │
      │  outliers    │
      │ consistency  │
      │  suspicious  │
      └──────┬───────┘
             │ list[CheckResult]
             ▼
      ┌──────────────┐
      │  report/     │  renders results to 3 formats
      │ html_reporter│  via Jinja2 templates
      │ json_reporter│
      │  md_reporter │
      └──────┬───────┘
             │
             ▼
      reports/*.html · *.json · *.md
```

---

## Installation

### Local (Python)

```bash
git clone https://github.com/anna1sheludko/data-quality-checker.git
cd data-quality-checker
python -m venv .venv
source .venv/bin/activate    # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Docker

```bash
docker compose build
```

---

## Usage

### Analyze a file

```bash
python -m src.cli --input data/sample_messy.csv
```

### Or with the installed CLI (after `pip install -e .`)

```bash
dqc --input data/sample_messy.csv
```

### Custom output directory and formats

```bash
dqc --input data/sales.xlsx --output my-reports --formats html,json
```

### Custom rules file

```bash
dqc --input data/file.csv --rules config/custom_rules.yaml
```

### Full help

```bash
dqc --help
```

---

## Configuration

Rules are in `config/default_rules.yaml`:

```yaml
checks:
  duplicates:
    enabled: true
    subset: null

  missing:
    enabled: true
    threshold_warning: 10      # % → warning
    threshold_critical: 50     # % → critical

  outliers:
    enabled: true
    method: 'zscore'           # or 'iqr'
    zscore_threshold: 3

  suspicious:
    enabled: true
    rules:
      - column_pattern: '.*price.*'
        check: '>= 0'
        message: 'Price must be non-negative'
      - column_pattern: '.*email.*'
        check: 'valid_email'
        message: 'Email must be valid'
```

---

## Testing

```bash
pytest tests/ -v
pytest tests/ -v --cov=src --cov-report=term-missing
```

47 tests covering all checks, the loader, type detection, and report generation.

GitHub Actions runs the suite on Python 3.11 and 3.12.

---

## Project structure

```
data-quality-checker/
├── .github/workflows/tests.yml
├── config/
│   └── default_rules.yaml
├── data/
│   ├── sample_clean.csv
│   ├── sample_messy.csv
│   └── sample_with_outliers.csv
├── reports/                 # generated reports (gitignored)
├── src/
│   ├── cli.py               # CLI entry point
│   ├── config_loader.py
│   ├── loader.py
│   ├── runner.py            # orchestrates load → checks → report
│   ├── checks/
│   │   ├── base.py
│   │   ├── duplicates.py
│   │   ├── missing.py
│   │   ├── types.py
│   │   ├── outliers.py
│   │   ├── consistency.py
│   │   └── suspicious.py
│   └── report/
│       ├── base.py
│       ├── html_reporter.py
│       ├── json_reporter.py
│       ├── markdown_reporter.py
│       └── templates/report.html.j2
├── tests/
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
├── requirements.txt
└── README.md
```

---

## What this demonstrates

- **Modular architecture** — checks and reporters are swappable
- **Data validation** — custom rules driven by YAML config
- **Rich CLI** — progress indicators, colored tables, panels
- **Multi-format reports** — HTML (Jinja2), JSON, Markdown
- **Testing discipline** — 47 unit tests, all passing
- **Docker** — reproducible on any machine
- **Python packaging** — `pyproject.toml` with console script entry point

---

## License

MIT — see [LICENSE](LICENSE).

---

## Author

**Anna Sheludko**
- GitHub: [@anna1sheludko](https://github.com/anna1sheludko)
- Portfolio: [anna1sheludko.github.io](https://anna1sheludko.github.io)