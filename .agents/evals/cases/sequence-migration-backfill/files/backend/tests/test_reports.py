from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_export_csv_has_header():
    res = client.get("/reports/1/export.csv")
    assert res.status_code == 200
    assert res.text.splitlines()[0] == "region,total"


def test_csv_quotes_values_that_contain_separators():
    from app.reports.service import Report, to_csv

    report = Report(id=1, title="t", rows=[{"region": "EU, West", "note": 'say "hi"'}, {"region": "US"}])
    assert to_csv(report).splitlines() == ["region,note", '"EU, West","say ""hi"""', "US,"]


def test_csv_includes_columns_that_only_later_rows_have():
    from app.reports.service import Report, to_csv

    report = Report(id=1, title="t", rows=[{"region": "EU"}, {"region": "US", "total": 3}])
    assert to_csv(report).splitlines() == ["region,total", "EU,", "US,3"]
