"""Runner — uruchamia wszystkie checki i generuje raporty."""
import logging
from pathlib import Path
from datetime import datetime
from src.loader import load_file, detect_column_types, LoadedData
from src.config_loader import load_rules
from src.checks.duplicates import check_duplicates
from src.checks.missing import check_missing
from src.checks.types import check_types
from src.checks.outliers import check_outliers
from src.checks.consistency import check_consistency
from src.checks.suspicious import check_suspicious
from src.report.base import ReportContext
from src.report.json_reporter import JsonReporter
from src.report.markdown_reporter import MarkdownReporter
from src.report.html_reporter import HtmlReporter

logger = logging.getLogger(__name__)

CHECK_FUNCS = {
    "duplicates": check_duplicates,
    "missing": check_missing,
    "types": check_types,
    "outliers": check_outliers,
    "consistency": check_consistency,
    "suspicious": check_suspicious,
}


def run_checks(loaded: LoadedData, rules: dict) -> list:
    """Uruchamia wszystkie checki z konfiguracji."""
    results = []
    checks_config = rules.get("checks", {})

    for name, func in CHECK_FUNCS.items():
        cfg = checks_config.get(name, {})
        if not cfg.get("enabled", True):
            logger.info(f"Check '{name}' disabled — skipping")
            continue

        logger.info(f"Running check: {name}")
        result = func(loaded.df, cfg)
        results.append(result)

    return results


def build_context(loaded: LoadedData, results: list) -> ReportContext:
    """Buduje kontekst raportu z wyników."""
    return ReportContext(
        source_name=loaded.source_name,
        source_file=str(loaded.filepath.name),
        file_format=loaded.file_format,
        total_rows=loaded.original_rows,
        total_columns=loaded.original_columns,
        column_names=list(loaded.df.columns),
        detected_types=detect_column_types(loaded.df),
        results=results,
    )


def run_pipeline(
    filepath: Path,
    output_dir: Path = None,
    formats: list = None,
    rules_path: Path = None,
) -> dict:
    """
    Główna funkcja — uruchamia pełny pipeline.

    Args:
        filepath: ścieżka do pliku CSV/Excel.
        output_dir: katalog na raporty (domyślnie: ./reports).
        formats: lista formatów ('html', 'json', 'markdown'). Domyślnie wszystkie.
        rules_path: ścieżka do pliku YAML z regułami.

    Returns:
        dict z informacjami o wygenerowanych raportach.
    """
    filepath = Path(filepath)
    if output_dir is None:
        output_dir = filepath.parent.parent / "reports"
    if formats is None:
        formats = ["html", "json", "markdown"]

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Load
    logger.info(f"Loading: {filepath}")
    loaded = load_file(filepath)

    # 2. Load rules
    rules = load_rules(rules_path)

    # 3. Run checks
    results = run_checks(loaded, rules)

    # 4. Build context
    ctx = build_context(loaded, results)

    # 5. Generate reports
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_name = f"{loaded.source_name}_{timestamp}"

    written = {}

    if "json" in formats:
        path = output_dir / f"{base_name}.json"
        JsonReporter(ctx, path).write()
        written["json"] = path
        logger.info(f"JSON report: {path}")

    if "markdown" in formats:
        path = output_dir / f"{base_name}.md"
        MarkdownReporter(ctx, path).write()
        written["markdown"] = path
        logger.info(f"Markdown report: {path}")

    if "html" in formats:
        path = output_dir / f"{base_name}.html"
        HtmlReporter(ctx, path).write()
        written["html"] = path
        logger.info(f"HTML report: {path}")

    return {
        "source": str(filepath),
        "output_dir": str(output_dir),
        "reports": {k: str(v) for k, v in written.items()},
        "context": ctx,
    }