"""Report queries. Reports are rows from the warehouse, at most a few thousand."""

from dataclasses import dataclass


@dataclass
class Report:
    id: int
    title: str
    rows: list[dict]


def get_report(report_id: int) -> Report:
    # Stand-in for the warehouse query.
    return Report(id=report_id, title=f"Report {report_id}", rows=[{"region": "EU", "total": 10}])


def to_csv(report: Report) -> str:
    if not report.rows:
        return ""
    cols = list(report.rows[0])
    lines = [",".join(cols)] + [",".join(str(r[c]) for c in cols) for r in report.rows]
    return "\n".join(lines) + "\n"
