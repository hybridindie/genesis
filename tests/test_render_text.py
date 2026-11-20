"""render_text must not reformat the content it renders.

It used to collapse every run of three or more newlines, which is exactly PEP 8's
two blank lines between top-level definitions: every rendered Python file failed
the ruff config genesis ships beside it.
"""

from __future__ import annotations

from conftest import load

render = load("templates/scripts/render.py", "render")


def test_untagged_python_is_byte_identical():
    source = "#!/usr/bin/env python3\n\nimport os\n\n\ndef main():\n    return 0\n\n\ndef other():\n    return 1\n"
    assert render.render_text(source, {}, {}) == source


def test_four_blank_lines_collapse_to_two():
    text = "a\n\n\n\n\nb\n"
    assert render.render_text(text, {}, {}) == "a\n\n\nb\n"


def test_placeholder_and_path_prefix():
    out = render.render_text("{{PROJECT_NAME}} in {{BACKEND_PATH}}/src", {"PROJECT_NAME": "Demo", "BACKEND_PATH": "."}, {})
    assert out == "Demo in src"


def test_conditional_block_follows_flags():
    text = "{{#STACK_PYTHON}}py{{/STACK_PYTHON}}{{#STACK_RUST}}rs{{/STACK_RUST}}"
    assert render.render_text(text, {}, {"STACK_PYTHON": True, "STACK_RUST": False}) == "py"
    assert render.render_text(text, {}, {"STACK_PYTHON": False, "STACK_RUST": True}) == "rs"


def test_unknown_flag_is_left_alone():
    text = "{{#SOMETHING_ELSE}}x{{/SOMETHING_ELSE}}"
    assert render.render_text(text, {}, {}) == text
