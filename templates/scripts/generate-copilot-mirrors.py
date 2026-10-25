#!/usr/bin/env python3
"""
Generate Copilot instruction mirrors from Claude rules.

Reads mirror pairs from templates/_shared/mirror-pairs.json (single source of truth),
reads every .claude/rules/**/*.md file, and writes corresponding
.github/instructions/*.instructions.md files with Copilot-style frontmatter.
"""

import json
import os
import re
import sys


def load_mirror_pairs(templates_dir):
    """Load mirror pairs from the canonical JSON file."""
    json_path = os.path.join(templates_dir, '_shared', 'mirror-pairs.json')
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    # Build lookup: claude_file (relative) -> entry dict
    pairs = {}
    for entry in data.get('entries', []):
        claude_rel = entry['claude_file']
        pairs[claude_rel] = entry
    return (
        pairs,
        data.get('copilot_instructions_dir', '.github/instructions'),
        data.get('agent_entries', []),
        data.get('command_entries', []),
    )


def extract_frontmatter_and_body(text):
    m = re.match(r'^---\n(.*?)\n---\n(.*)', text, re.DOTALL)
    if not m:
        return None, text
    return m.group(1), m.group(2)


def extract_paths(fm_text):
    lines = fm_text.split('\n')
    in_paths = False
    paths = []
    for line in lines:
        if line.strip().startswith('paths:'):
            in_paths = True
            continue
        if in_paths:
            stripped = line.strip()
            if stripped.startswith('- '):
                path = stripped[2:].strip().strip('"').strip("'")
                paths.append(path)
            elif stripped and not line.startswith(' '):
                break
    return paths


def generate_mirror(claude_file, out_dir, entry, instructions_dir):
    with open(claude_file, 'r', encoding='utf-8') as f:
        text = f.read()

    fm, body = extract_frontmatter_and_body(text)

    # Resolve description before branching (used in both paths)
    description = entry.get('copilot_description', '')
    if not description:
        title_match = re.search(r'^# (.+)$', body, re.MULTILINE)
        description = title_match.group(1).strip() if title_match else "Project rule"
    description = description.replace('"', '\\"')

    if fm is None:
        # Use mirror-pairs.json paths as fallback when source has no frontmatter
        fallback_paths = entry.get('paths', [])
        copilot_fm = f'---\ndescription: "{description}"\n'
        if fallback_paths:
            apply_to = ', '.join(fallback_paths)
            copilot_fm += f'applyTo: "{apply_to}"\n'
        copilot_fm += '---\n'
    else:
        paths = extract_paths(fm)

        copilot_fm = f'---\ndescription: "{description}"\n'
        if paths:
            apply_to = ', '.join(paths)
            copilot_fm += f'applyTo: "{apply_to}"\n'
        copilot_fm += '---\n'

    copilot_file = entry['copilot_file']
    out_file = os.path.join(out_dir, instructions_dir, copilot_file)

    os.makedirs(os.path.dirname(out_file), exist_ok=True)
    with open(out_file, 'w', encoding='utf-8') as f:
        f.write(copilot_fm + body)

    print(f"  Mirrored: .claude/rules/{entry['claude_file']} -> {instructions_dir}/{copilot_file}")


def generate_agent_mirror(claude_file, out_dir, entry):
    """Generate a Copilot .agent.md from a Claude agent source.

    Claude frontmatter: name, description, model, color
    Copilot frontmatter: name, description, argument-hint (model/color dropped)
    Body: identical
    """
    with open(claude_file, 'r', encoding='utf-8') as f:
        text = f.read()

    fm, body = extract_frontmatter_and_body(text)

    # Parse relevant fields from Claude frontmatter
    name = ''
    description = ''
    if fm:
        for line in fm.split('\n'):
            if line.startswith('name:'):
                name = line.split(':', 1)[1].strip().strip('"').strip("'")
            elif line.startswith('description:'):
                description = line.split(':', 1)[1].strip().strip('"').strip("'")

    argument_hint = entry.get('argument_hint', '')

    copilot_fm = '---\n'
    if name:
        copilot_fm += f'name: {name}\n'
    if description:
        copilot_fm += f'description: "{description}"\n'
    if argument_hint:
        copilot_fm += f'argument-hint: "{argument_hint}"\n'
    copilot_fm += '---\n'

    copilot_file = entry['copilot_file']
    out_file = os.path.join(out_dir, entry['copilot_dir'], copilot_file)

    os.makedirs(os.path.dirname(out_file), exist_ok=True)
    with open(out_file, 'w', encoding='utf-8') as f:
        f.write(copilot_fm + body)

    print(f"  Agent mirror: {entry['claude_dir']}/{entry['source_file']} -> {entry['copilot_dir']}/{copilot_file}")

    if entry.get('opencode_dir'):
        generate_opencode_agent_mirror(claude_file, out_dir, entry)


def generate_command_mirror(claude_file, out_dir, entry):
    """Generate a Copilot .prompt.md from a Claude command source.

    Frontmatter and body are identical between platforms — only the filename
    and target directory differ.
    """
    with open(claude_file, 'r', encoding='utf-8') as f:
        text = f.read()

    copilot_file = entry['copilot_file']
    out_file = os.path.join(out_dir, entry['copilot_dir'], copilot_file)

    os.makedirs(os.path.dirname(out_file), exist_ok=True)
    with open(out_file, 'w', encoding='utf-8') as f:
        f.write(text)

    print(f"  Command mirror: {entry['claude_dir']}/{entry['source_file']} -> {entry['copilot_dir']}/{copilot_file}")

    if entry.get('opencode_dir'):
        generate_opencode_command_mirror(claude_file, out_dir, entry)


def generate_opencode_agent_mirror(claude_file, out_dir, entry):
    """Generate an opencode .opencode/agents/*.md from a Claude agent source.

    opencode agent frontmatter: description, mode: subagent, permission block.
    The filename becomes the agent name — no 'name:' field needed.
    model/color from Claude frontmatter are dropped (opencode uses different model IDs).
    Body: identical to shared source.
    """
    with open(claude_file, 'r', encoding='utf-8') as f:
        text = f.read()

    fm, body = extract_frontmatter_and_body(text)

    description = ''
    if fm:
        for line in fm.split('\n'):
            if line.startswith('description:'):
                description = line.split(':', 1)[1].strip().strip('"').strip("'")

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
    opencode_dir = entry['opencode_dir']
    out_file = os.path.join(out_dir, opencode_dir, source_file)

    os.makedirs(os.path.dirname(out_file), exist_ok=True)
    with open(out_file, 'w', encoding='utf-8') as f:
        f.write(oc_fm + body)

    print(f"  OpenCode agent: {entry['claude_dir']}/{source_file} -> {opencode_dir}/{source_file}")


def generate_opencode_command_mirror(claude_file, out_dir, entry):
    """Generate an opencode .opencode/commands/*.md from a Claude command source.

    opencode command frontmatter: description only (Claude-specific fields stripped).
    Same filename as Claude source. Body: identical.
    """
    with open(claude_file, 'r', encoding='utf-8') as f:
        text = f.read()

    fm, body = extract_frontmatter_and_body(text)

    description = ''
    if fm:
        for line in fm.split('\n'):
            if line.startswith('description:'):
                description = line.split(':', 1)[1].strip().strip('"').strip("'")

    oc_fm = '---\n'
    if description:
        oc_fm += f'description: "{description}"\n'
    oc_fm += '---\n'

    source_file = entry['source_file']
    opencode_dir = entry['opencode_dir']
    out_file = os.path.join(out_dir, opencode_dir, source_file)

    os.makedirs(os.path.dirname(out_file), exist_ok=True)
    with open(out_file, 'w', encoding='utf-8') as f:
        f.write(oc_fm + body)

    print(f"  OpenCode command: {entry['claude_dir']}/{source_file} -> {opencode_dir}/{source_file}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python generate-copilot-mirrors.py <output_dir> [templates_dir]")
        sys.exit(1)

    out_dir = sys.argv[1]
    # Default templates_dir is the templates/ sibling of this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    templates_dir = sys.argv[2] if len(sys.argv) > 2 else os.path.dirname(script_dir)

    pairs, copilot_dir, agent_entries, command_entries = load_mirror_pairs(templates_dir)
    rules_dir = os.path.join(out_dir, '.claude', 'rules')
    instructions_out = os.path.join(out_dir, copilot_dir)

    if not os.path.isdir(rules_dir):
        print(f"Rules directory not found: {rules_dir}")
        sys.exit(1)

    mirrored = 0
    skipped = 0
    for root, _dirs, files in os.walk(rules_dir):
        # Doctrine files are referenced by articles/agents, not mirrored to
        # Copilot as path-targeted instructions. Skip the doctrine/ subdir
        # entirely so it doesn't print noisy "Skipped" lines.
        if os.path.relpath(root, start=rules_dir).split(os.sep)[0] == 'doctrine':
            continue
        for fname in files:
            if not fname.endswith('.md'):
                continue
            rel = os.path.relpath(os.path.join(root, fname), start=rules_dir)
            claude_path = rel.replace(os.sep, '/')

            if claude_path not in pairs:
                print(f"  Skipped:  .claude/rules/{claude_path} (no mirror-pairs.json entry)")
                skipped += 1
                continue

            entry = pairs[claude_path]
            generate_mirror(os.path.join(root, fname), out_dir, entry, copilot_dir)
            mirrored += 1

    print(f"\nSummary: {mirrored} mirrored, {skipped} skipped")

    # Generate agent mirrors
    if agent_entries:
        print("\n=== Generating Agent Mirrors ===")
        for entry in agent_entries:
            source_path = os.path.join(out_dir, entry['claude_dir'], entry['source_file'])
            if not os.path.isfile(source_path):
                print(f"  Skipped (not found): {entry['claude_dir']}/{entry['source_file']}")
                continue
            generate_agent_mirror(source_path, out_dir, entry)

    # Generate command mirrors
    if command_entries:
        print("\n=== Generating Command Mirrors ===")
        for entry in command_entries:
            source_path = os.path.join(out_dir, entry['claude_dir'], entry['source_file'])
            if not os.path.isfile(source_path):
                print(f"  Skipped (not found): {entry['claude_dir']}/{entry['source_file']}")
                continue
            generate_command_mirror(source_path, out_dir, entry)


if __name__ == '__main__':
    main()
