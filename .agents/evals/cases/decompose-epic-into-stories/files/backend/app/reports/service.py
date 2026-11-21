"""Report queries. Reports are rows from the warehouse, at most a few thousand."""

import csv
import io
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
    out = io.StringIO()
    writer = csv.DictWriter(out, fieldnames=list(report.rows[0]), restval="", lineterminator="\n")
    writer.writeheader()
    writer.writerows(report.rows)
    return out.getvalue()
