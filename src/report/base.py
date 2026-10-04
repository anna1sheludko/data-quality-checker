"""Bazowa klasa dla reporterów."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime
from typing import Optional


@dataclass
class ReportContext:
    """Kontekst raportu — wszystko, czego potrzebuje reporter."""
    source_name: str
    source_file: str
    file_format: str
    total_rows: int
    total_columns: int
    column_names: list
    detected_types: dict
    results: list          # lista CheckResult
    generated_at: datetime = None

    def __post_init__(self):
        if self.generated_at is None:
            self.generated_at = datetime.now()

    @property
    def overall_severity(self) -> str:
        """Najwyższy severity wśród wszystkich wyników."""
        ranks = {"ok": 0, "info": 1, "warning": 2, "critical": 3}
        if not self.results:
            return "ok"
        worst = max(self.results, key=lambda r: ranks[r.severity.value])
        return worst.severity.value

    @property
    def total_issues(self) -> int:
        return sum(len(r.issues) for r in self.results)

    @property
    def total_critical(self) -> int:
        return sum(
            1 for r in self.results for i in r.issues
            if i.severity.value == "critical"
        )

    @property
    def total_warnings(self) -> int:
        return sum(
            1 for r in self.results for i in r.issues
            if i.severity.value == "warning"
        )

    @property
    def total_info(self) -> int:
        return sum(
            1 for r in self.results for i in r.issues
            if i.severity.value == "info"
        )


class BaseReporter(ABC):
    """Interfejs każdego reportera."""

    def __init__(self, context: ReportContext, output_path: Path):
        self.context = context
        self.output_path = Path(output_path)
        self.output_path.parent.mkdir(parents=True, exist_ok=True)

    @abstractmethod
    def render(self) -> str:
        """Zwraca treść raportu jako string."""
        raise NotImplementedError

    def write(self) -> Path:
        """Renderuje i zapisuje do pliku. Zwraca ścieżkę."""
        content = self.render()
        self.output_path.write_text(content, encoding="utf-8")
        return self.output_path