"""Reporter: HTML (Jinja2)."""
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape
from src.report.base import BaseReporter, ReportContext

TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"


class HtmlReporter(BaseReporter):

    def __init__(self, context: ReportContext, output_path: Path):
        super().__init__(context, output_path)
        self.env = Environment(
            loader=FileSystemLoader(str(TEMPLATES_DIR)),
            autoescape=select_autoescape(["html", "xml"]),
        )
        # Filtr do formatowania liczb z separatorami tysięcy
        self.env.filters["number"] = lambda v: f"{v:,}"

    def render(self) -> str:
        template = self.env.get_template("report.html.j2")
        return template.render(ctx=self.context)