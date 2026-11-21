"""customize-harness inventory must survive odd configs instead of crashing."""

from __future__ import annotations

import json

from conftest import load

inv = load("templates/_shared/skills/customize-harness/scripts/inventory.py", "inventory")


def test_missing_config_is_reported(tmp_path):
    report = inv.lsp_report(tmp_path)
    assert report["config_present"] is False
    assert report["current"] == "<no-config>"


def test_non_object_json_is_invalid_not_a_crash(tmp_path):
    config = tmp_path / ".opencode" / "opencode.json"
    config.parent.mkdir()
    config.write_text('["not", "an", "object"]')
    report = inv.lsp_report(tmp_path)
    assert report["config_present"] is True
    assert report["config_parse_error"] is True
    assert report["current"] == "<invalid>"


def test_root_opencode_config_is_read(tmp_path):
    (tmp_path / "opencode.json").write_text(json.dumps({"lsp": {"my-bridge": {"command": ["x"]}}}))
    report = inv.lsp_report(tmp_path)
    assert report["config_present"] is True
    assert report["config_path"] == "opencode.json"
    assert "my-bridge" in report["current"]["servers_set"]


def test_absent_lsp_key_differs_from_invalid(tmp_path):
    config = tmp_path / ".opencode" / "opencode.json"
    config.parent.mkdir()
    config.write_text("{}")
    report = inv.lsp_report(tmp_path)
    assert report["current"] == "<absent>"
    assert report["config_parse_error"] is False


def test_language_scan_counts_files(tmp_path):
    (tmp_path / "a.py").write_text("")
    (tmp_path / "b.rs").write_text("")
    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "c.py").write_text("")
    servers, unsupported, scanned, truncated = inv.scan_languages(tmp_path)
    assert servers == {"pyright": 1, "rust": 1}
    assert scanned == 2
    assert truncated is False
