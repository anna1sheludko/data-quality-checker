"""Bazowa klasa dla wszystkich checks — wspólny format wyniku."""
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Severity(str, Enum):
    """Poziom ważności problemu."""
    OK = "ok"
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class Issue:
    """Pojedynczy problem znaleziony w danych."""
    check: str                      # nazwa checka: 'duplicates', 'missing', ...
    severity: Severity
    column: str = ""                # której kolumny dotyczy (jeśli dotyczy)
    message: str = ""
    details: dict = field(default_factory=dict)


@dataclass
class CheckResult:
    """Wynik jednego checka."""
    name: str                       # np. 'duplicates'
    passed: bool                    # czy check przeszedł bez problemów
    severity: Severity               # najwyższy poziom wśród issues
    issues: list = field(default_factory=list)   # lista Issue
    metrics: dict = field(default_factory=dict)  # liczby, statystyki
    message: str = ""               # krótki opis wyniku

    def add_issue(self, issue: Issue) -> None:
        self.issues.append(issue)
        # Podnieś severity, jeśli issue jest poważniejsze
        if _severity_rank(issue.severity) > _severity_rank(self.severity):
            self.severity = issue.severity

    @property
    def has_problems(self) -> bool:
        return self.severity in (Severity.WARNING, Severity.CRITICAL)


def _severity_rank(sev: Severity) -> int:
    return {
        Severity.OK: 0,
        Severity.INFO: 1,
        Severity.WARNING: 2,
        Severity.CRITICAL: 3,
    }[sev]