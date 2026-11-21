from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

from app.reports.service import get_report, to_csv

router = APIRouter()


@router.get("/{report_id}")
def read_report(report_id: int) -> dict:
    r = get_report(report_id)
    return {"id": r.id, "title": r.title, "rows": r.rows}


@router.get("/{report_id}/export.csv", response_class=PlainTextResponse)
def export_csv(report_id: int) -> str:
    return to_csv(get_report(report_id))
