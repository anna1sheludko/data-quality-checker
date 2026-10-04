"""
CLI dla Data Quality Checker.

Użycie:
    python -m src.cli --input data/sample_messy.csv
    python -m src.cli --input data/file.xlsx --formats html,json
    python -m src.cli --input data/file.csv --output reports/ --log-level DEBUG
"""
import argparse
import sys
import logging
from pathlib import Path
from datetime import datetime

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn

from src.logging_config import setup_logging
from src.config_loader import BASE_DIR
from src.runner import run_pipeline

logger = logging.getLogger(__name__)
console = Console()


BANNER = r"""
  ____        _          ___                   _
 |  _ \  __ _| |_ __ _  / _ \ _   _  __ _ _ __| |_ _   _
 | | | |/ _` | __/ _` || | | | | | |/ _` | '__| __| | | |
 | |_| | (_| | || (_| || |_| | |_| | (_| | |  | |_| |_| |
 |____/ \__,_|\__\__,_| \__\_\\__,_|\__,_|_|   \__|\__, |
                                                    |___/
               Data Quality Checker · v1.0
"""


SEVERITY_STYLE = {
    "ok": "green",
    "info": "cyan",
    "warning": "yellow",
    "critical": "red bold",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="data-quality-checker",
        description="Analyze CSV/Excel files and generate a data quality report.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m src.cli --input data/sample_messy.csv
  python -m src.cli --input data/sales.xlsx --formats html,json
  python -m src.cli --input data/file.csv --output reports/ --log-level DEBUG
        """,
    )

    parser.add_argument(
        "--input", "-i",
        type=str,
        required=True,
        help="Path to the CSV or Excel file to analyze.",
    )

    parser.add_argument(
        "--output", "-o",
        type=str,
        default=None,
        help="Directory where reports will be written (default: ./reports).",
    )

    parser.add_argument(
        "--formats", "-f",
        type=str,
        default="html,json,markdown",
        help="Comma-separated report formats: html, json, markdown (default: all).",
    )

    parser.add_argument(
        "--rules", "-r",
        type=str,
        default=None,
        help="Path to a custom YAML rules file (default: config/default_rules.yaml).",
    )

    parser.add_argument(
        "--log-level", "-l",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level (default: INFO).",
    )

    parser.add_argument(
        "--no-banner",
        action="store_true",
        help="Skip the ASCII banner.",
    )

    return parser


def parse_formats(raw: str) -> list:
    """'html,json' -> ['html', 'json'] z walidacją."""
    allowed = {"html", "json", "markdown"}
    parts = [p.strip().lower() for p in raw.split(",") if p.strip()]
    invalid = set(parts) - allowed
    if invalid:
        raise ValueError(
            f"Unknown format(s): {', '.join(sorted(invalid))}. "
            f"Allowed: {', '.join(sorted(allowed))}"
        )
    if not parts:
        raise ValueError("At least one format is required.")
    return parts


def print_banner() -> None:
    console.print(Text(BANNER, style="bold #4d7a60"))


def print_check_results(results: list) -> None:
    """Wyświetla wyniki wszystkich checków jako tabelę."""
    table = Table(
        show_header=True,
        header_style="bold #2b453a",
        border_style="#d1ccc0",
        show_lines=False,
        padding=(0, 2),
    )
    table.add_column("Check", style="bold")
    table.add_column("Status", justify="center")
    table.add_column("Severity", justify="center")
    table.add_column("Issues", justify="right")
    table.add_column("Message", overflow="fold")

    for result in results:
        sev = result.severity.value
        style = SEVERITY_STYLE.get(sev, "white")

        status = "✓ passed" if result.passed else "✗ failed"
        status_style = "green" if result.passed else "red"

        table.add_row(
            result.name,
            Text(status, style=status_style),
            Text(sev, style=style),
            str(len(result.issues)),
            Text(result.message, style="dim"),
        )

    console.print()
    console.print(table)


def print_summary(ctx) -> None:
    """Wyświetla podsumowanie po zakończeniu pipeline'u."""
    overall = ctx.overall_severity
    style = SEVERITY_STYLE.get(overall, "white")

    summary_lines = [
        f"[bold]Source:[/bold]     {ctx.source_file}",
        f"[bold]Rows:[/bold]       {ctx.total_rows:,}",
        f"[bold]Columns:[/bold]    {ctx.total_columns}",
        "",
        f"[bold {style}]Overall:[/bold {style}]    {overall.upper()}",
        f"[red]Critical:[/red]   {ctx.total_critical}",
        f"[yellow]Warnings:[/yellow]   {ctx.total_warnings}",
        f"[cyan]Info:[/cyan]       {ctx.total_info}",
    ]

    console.print(Panel(
        "\n".join(summary_lines),
        title="[bold #2b453a]Summary[/bold #2b453a]",
        border_style="#4d7a60",
        padding=(1, 3),
    ))


def print_reports(reports: dict) -> None:
    """Pokazuje listę wygenerowanych plików."""
    console.print()
    console.print("[bold #2b453a]Generated reports:[/bold #2b453a]")
    for fmt, path in reports.items():
        console.print(f"  [dim]{fmt:10s}[/dim] → [link=file://{path}]{path}[/link]")


def main(argv: list = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    # Logging
    log_dir = BASE_DIR / "logs"
    setup_logging(log_dir, args.log_level)

    # Banner
    if not args.no_banner:
        print_banner()

    # Walidacja inputu
    input_path = Path(args.input)
    if not input_path.exists():
        console.print(f"[red bold]Error:[/red bold] File not found: {input_path}")
        return 2

    # Walidacja formatów
    try:
        formats = parse_formats(args.formats)
    except ValueError as e:
        console.print(f"[red bold]Error:[/red bold] {e}")
        return 2

    # Output dir
    output_dir = Path(args.output) if args.output else BASE_DIR / "reports"

    # Rules path
    rules_path = Path(args.rules) if args.rules else None

    # Info
    console.print(f"[dim]Input:[/dim]    {input_path}")
    console.print(f"[dim]Output:[/dim]   {output_dir}")
    console.print(f"[dim]Formats:[/dim]  {', '.join(formats)}")
    console.print()

    # Uruchom pipeline z ładnym spinnerem
    try:
        with Progress(
            SpinnerColumn(style="#4d7a60"),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True,
        ) as progress:
            task = progress.add_task("Running pipeline...", total=None)

            progress.update(task, description="Loading file and running checks...")
            result = run_pipeline(
                filepath=input_path,
                output_dir=output_dir,
                formats=formats,
                rules_path=rules_path,
            )

        ctx = result["context"]

        # Wyniki checków
        console.print("[bold #2b453a]Checks:[/bold #2b453a]")
        print_check_results(ctx.results)

        # Podsumowanie
        print_summary(ctx)

        # Raporty
        print_reports(result["reports"])

        console.print()
        console.print("[bold green]✓ Done[/bold green]")
        return 0

    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
        return 130

    except FileNotFoundError as e:
        console.print(f"[red bold]Error:[/red bold] {e}")
        return 2

    except Exception as e:
        logger.exception("Pipeline failed")
        console.print(f"\n[red bold]Pipeline failed:[/red bold] {e}")
        if args.log_level == "DEBUG":
            console.print_exception()
        return 1


if __name__ == "__main__":
    sys.exit(main())