#!/usr/bin/env python3
"""
Generate the OpenCode harness mirrors from the shared Claude sources.

Single source: `templates/_shared/{agents,commands}` → rendered by bootstrap into
`.claude/{agents,commands}`. This script mirrors those rendered files into
`.opencode/{agents,commands}` with the frontmatter OpenCode expects (the body
stays identical).
"""

import json
import os
import re
import sys


def load_entries(templates_dir):
    json_path = os.path.join(templates_dir, '_shared', 'mirror-pairs.json')
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data.get('agent_entries', []), data.get('command_entries', [])


def extract_frontmatter_and_body(text):
    m = re.match(r'^---\n(.*?)\n---\n(.*)', text, re.DOTALL)
    if not m:
        return None, text
    return m.group(1), m.group(2)


def frontmatter_field(fm, field):
    if not fm:
        return ''
    for line in fm.split('\n'):
        if line.startswith(f'{field}:'):
            return line.split(':', 1)[1].strip().strip('"').strip("'")
    return ''


def write(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)


def generate_agent(claude_file, out_dir, entry):
    """OpenCode agent frontmatter: description, mode: subagent, permissions.

    The filename becomes the agent name (no `name:` field). `model`/`color` from
    the Claude source are dropped — OpenCode uses provider-qualified model IDs.
    """
    with open(claude_file, 'r', encoding='utf-8') as f:
        text = f.read()

    fm, body = extract_frontmatter_and_body(text)
    description = frontmatter_field(fm, 'description')

    oc_fm = '---\n'
    if description:
        oc_fm += f'description: "{description}"\n'
    oc_fm += 'mode: subagent\n'
    # OpenCode v2 uses the ordered permissions array (the v1 `permission:` object
    # is not read). Read/glob/grep stay allowed; edits and shell are denied.
    oc_fm += 'permissions:\n'
    oc_fm += '  - action: edit\n'
    oc_fm += '    resource: "*"\n'
    oc_fm += '    effect: deny\n'
    oc_fm += '  - action: shell\n'
    oc_fm += '    resource: "*"\n'
    oc_fm += '    effect: deny\n'
    oc_fm += '---\n'

    source_file = entry['source_file']
    out_file = os.path.join(out_dir, entry['opencode_dir'], source_file)
    write(out_file, oc_fm + body)
    print(f"  OpenCode agent: {entry['claude_dir']}/{source_file} -> {entry['opencode_dir']}/{source_file}")


def generate_command(claude_file, out_dir, entry):
    """OpenCode command frontmatter: description only. Body identical."""
    with open(claude_file, 'r', encoding='utf-8') as f:
        text = f.read()

    fm, body = extract_frontmatter_and_body(text)
    description = frontmatter_field(fm, 'description')

    oc_fm = '---\n'
    if description:
        oc_fm += f'description: "{description}"\n'
    oc_fm += '---\n'

    source_file = entry['source_file']
    out_file = os.path.join(out_dir, entry['opencode_dir'], source_file)
    write(out_file, oc_fm + body)
    print(f"  OpenCode command: {entry['claude_dir']}/{source_file} -> {entry['opencode_dir']}/{source_file}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python generate-harness-mirrors.py <output_dir> [templates_dir]")
        sys.exit(1)

    out_dir = sys.argv[1]
    script_dir = os.path.dirname(os.path.abspath(__file__))
    templates_dir = sys.argv[2] if len(sys.argv) > 2 else os.path.dirname(script_dir)

    agent_entries, command_entries = load_entries(templates_dir)

    if agent_entries:
        print("=== Generating OpenCode agent mirrors ===")
        for entry in agent_entries:
            source = os.path.join(out_dir, entry['claude_dir'], entry['source_file'])
            if not os.path.isfile(source):
                print(f"  Skipped (not found): {entry['claude_dir']}/{entry['source_file']}")
                continue
            generate_agent(source, out_dir, entry)

    if command_entries:
        print("\n=== Generating OpenCode command mirrors ===")
        for entry in command_entries:
            source = os.path.join(out_dir, entry['claude_dir'], entry['source_file'])
            if not os.path.isfile(source):
                print(f"  Skipped (not found): {entry['claude_dir']}/{entry['source_file']}")
                continue
            generate_command(source, out_dir, entry)


if __name__ == '__main__':
    main()
