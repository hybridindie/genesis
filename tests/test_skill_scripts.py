"""Deterministic evals for the skills that ship a script.

Fixture in, expected findings or files out — no model, no flakiness. These are
the parts of a skill a reviewer can actually hold to a contract.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys

from conftest import ROOT

HYGIENE = ROOT / "templates/_shared/skills/test-hygiene-scanner/scripts/scan.py"
E2E = ROOT / "templates/_shared/stacks/frontend/skills/e2e-assertion-audit/scripts/scan.py"
MIGRATION = ROOT / "templates/_shared/stacks/fastapi/skills/create-migration/scripts/new_migration.py"
CONTRACT = ROOT / "templates/_shared/stacks/fastapi/skills/gen-contract-test/scripts/scaffold_contract.py"


def run(script, *args, cwd=None):
    return subprocess.run([sys.executable, str(script), *args], cwd=cwd, capture_output=True, text=True)


# ── test-hygiene-scanner ──────────────────────────────────────────────────


def test_hygiene_flags_known_patterns(tmp_path):
    test_file = tmp_path / "tests" / "unit" / "test_a.py"
    test_file.parent.mkdir(parents=True)
    test_file.write_text(
        "def test_x():\n"
        "    assert row['created'] == \"2026-01-15\"\n"
        "    client = AsyncMock()\n"
    )
    result = run(HYGIENE, str(tmp_path / "tests"), "--json")
    hits = json.loads(result.stdout)
    categories = {hit["category"] for hit in hits}
    assert {"hardcoded-dates", "asyncmock"} <= categories


def test_hygiene_scans_pytest_files_from_a_relative_root(tmp_path):
    # Documented usage is `scan.py tests` from the repo root: the path is
    # relative, so matching on "/tests/" alone found nothing.
    test_file = tmp_path / "tests" / "test_a.py"
    test_file.parent.mkdir(parents=True)
    test_file.write_text('created = "2026-01-15"\n')
    result = run(HYGIENE, "tests", "--json", cwd=tmp_path)
    assert {hit["category"] for hit in json.loads(result.stdout)} == {"hardcoded-dates"}


def test_hygiene_ignores_non_test_files(tmp_path):
    source = tmp_path / "src" / "app.py"
    source.parent.mkdir(parents=True)
    source.write_text("created = '2026-01-15'\n")
    result = run(HYGIENE, str(tmp_path), "--json")
    assert json.loads(result.stdout) == []


def test_hygiene_survives_a_missing_root(tmp_path):
    result = run(HYGIENE, str(tmp_path / "nope"), "--json")
    assert result.returncode == 0
    assert json.loads(result.stdout) == []


# ── e2e-assertion-audit ───────────────────────────────────────────────────


def test_e2e_flags_the_three_weakness_classes(tmp_path):
    spec = tmp_path / "tests/e2e/flow.spec.ts"
    spec.parent.mkdir(parents=True)
    spec.write_text(
        "expect(true).toBe(true)\n"
        "expect(response.status()).toBeLessThan(500)\n"
        "await page.getByText('Submit').click()\n"
    )
    result = run(E2E, str(tmp_path / "tests/e2e"), "--json")
    categories = {hit["category"] for hit in json.loads(result.stdout)}
    assert categories == {"no-op", "permissive", "fragile-selector"}


def test_e2e_clean_spec_reports_nothing(tmp_path):
    spec = tmp_path / "tests/e2e/ok.spec.ts"
    spec.parent.mkdir(parents=True)
    spec.write_text("expect(page.getByRole('button', { name: 'Submit' })).toBeEnabled()\n")
    result = run(E2E, str(tmp_path / "tests/e2e"), "--json")
    assert json.loads(result.stdout) == []


# ── create-migration ──────────────────────────────────────────────────────


def test_migration_creates_a_stamped_skeleton(tmp_path):
    (tmp_path / "migrations").mkdir()
    result = run(MIGRATION, "--description", "add_flags", "--tables", "users,orders", "--root", str(tmp_path))
    assert result.returncode == 0, result.stderr
    created = list((tmp_path / "migrations").glob("*_add_flags.sql"))
    assert len(created) == 1
    assert re.match(r"^\d{14}_add_flags\.sql$", created[0].name)
    sql = created[0].read_text()
    assert "CREATE TABLE IF NOT EXISTS public.users" in sql
    assert "CREATE TABLE IF NOT EXISTS public.orders" in sql
    assert "-- DOWN" in sql


def test_migration_rejects_a_non_snake_case_description(tmp_path):
    (tmp_path / "migrations").mkdir()
    result = run(MIGRATION, "--description", "Add Flags", "--tables", "users", "--root", str(tmp_path))
    assert result.returncode == 1
    assert "snake_case" in result.stderr


def test_migration_rejects_a_bad_table_name(tmp_path):
    (tmp_path / "migrations").mkdir()
    result = run(MIGRATION, "--description", "add_flags", "--tables", "Users", "--root", str(tmp_path))
    assert result.returncode == 1
    assert "snake_case" in result.stderr


def test_migration_without_a_directory_explains_the_choice(tmp_path):
    result = run(MIGRATION, "--description", "add_flags", "--tables", "users", "--root", str(tmp_path))
    assert result.returncode == 2
    assert "no migrations directory" in result.stderr


def test_migration_defers_to_alembic(tmp_path):
    (tmp_path / "alembic").mkdir()
    result = run(MIGRATION, "--description", "add_flags", "--tables", "users", "--root", str(tmp_path))
    assert result.returncode == 2
    assert "alembic revision" in result.stderr


# ── gen-contract-test ─────────────────────────────────────────────────────


def test_contract_scaffold_fills_backend_placeholders(tmp_path):
    out = tmp_path / "tests/contract/test_billing.py"
    result = run(CONTRACT, "--stack", "backend", "--target", "BillingAccount",
                 "--path", "/v1/billing/accounts", "--method", "POST", "--status", "201", "--out", str(out))
    assert result.returncode == 0, result.stderr
    text = out.read_text()
    assert "__TARGET" not in text and "__PATH__" not in text and "__MET" not in text
    assert "BillingAccount" in text and "/v1/billing/accounts" in text


def test_contract_scaffold_refuses_to_overwrite(tmp_path):
    out = tmp_path / "contract.ts"
    args = ("--stack", "frontend", "--target", "Widget", "--path", "src/widget", "--out", str(out))
    assert run(CONTRACT, *args).returncode == 0
    second = run(CONTRACT, *args)
    assert second.returncode == 1
    assert "refusing to overwrite" in second.stderr
