from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_export_csv_has_header():
    res = client.get("/reports/1/export.csv")
    assert res.status_code == 200
    assert res.text.splitlines()[0] == "region,total"
