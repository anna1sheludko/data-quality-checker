"""Reporter: JSON."""
import json
from src.report.base import BaseReporter, ReportContext


class JsonReporter(BaseReporter):

    def render(self) -> str:
        ctx = self.context
        data = {
            "generated_at": ctx.generated_at.isoformat(),
            "source": {
                "name": ctx.source_name,
                "file": ctx.source_file,
                "format": ctx.file_format,
                "rows": ctx.total_rows,
                "columns": ctx.total_columns,
                "column_names": ctx.column_names,
                "detected_types": ctx.detected_types,
            },
            "summary": {
                "overall_severity": ctx.overall_severity,
                "total_issues": ctx.total_issues,
                "critical": ctx.total_critical,
                "warnings": ctx.total_warnings,
                "info": ctx.total_info,
            },
            "checks": [
                {
                    "name": r.name,
                    "passed": r.passed,
                    "severity": r.severity.value,
                    "message": r.message,
                    "metrics": _to_serializable(r.metrics),
                    "issues": [
                        {
                            "severity": i.severity.value,
                            "column": i.column,
                            "message": i.message,
                            "details": _to_serializable(i.details),
                        }
                        for i in r.issues
                    ],
                }
                for r in ctx.results
            ],
        }
        return json.dumps(data, indent=2, ensure_ascii=False, default=str)


def _to_serializable(obj):
    """Konwertuje numpy/pandas typy na zwykłe Python typy."""
    import numpy as np
    if isinstance(obj, dict):
        return {k: _to_serializable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_to_serializable(x) for x in obj]
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    return obj