#!/usr/bin/env python3
"""
Process Mustache-style conditional blocks in rendered templates.

Strips `{{#FLAG}}...{{/FLAG}}` wrappers and removes the block entirely
if the flag value is "no" (or any false-ish value).

Usage:
  python process-conditionals.py <directory> <key=value> [<key=value> ...]

Example:
  python process-conditionals.py /tmp/myproject-render \
    HAS_MLFLOW=no \
    HAS_LANGGRAPH=yes \
    TAILWIND=yes
"""

import os
import re
import sys


def parse_args(argv):
    if len(argv) < 3:
        print("Usage: python process-conditionals.py <dir> key=value [key=value ...]")
        sys.exit(1)
    target_dir = argv[1]
    flags = {}
    for arg in argv[2:]:
        if '=' in arg:
            k, v = arg.split('=', 1)
            flags[k] = v.strip()
    return target_dir, flags


def process_conditionals(text, flags):
    """
    Find all {{#KEY}}...{{/KEY}} blocks.
    If flag is truthy (yes, true, 1), keep inner content, strip delimiters.
    If flag is falsy (no, false, 0, empty), remove entire block.
    Unknown flags: keep delimiters and content unchanged (don't strip).
    """
    pattern = re.compile(r'\{\{#(\w+)\}\}(.*?)\{\{/\1\}\}', re.DOTALL)

    def replacer(m):
        key = m.group(1)
        inner = m.group(2)
        val = flags.get(key)
        if val is None:
            # Unknown flag — leave untouched
            return m.group(0)
        val_lower = val.lower()
        if val_lower in ('yes', 'true', '1', 'on'):
            return inner
        else:
            return ''

    return pattern.sub(replacer, text)


def process_all(text, flags):
    """Evaluate nested conditional blocks until stable, then tidy blank lines."""
    while True:
        new_text = process_conditionals(text, flags)
        if new_text == text:
            break
        text = new_text
    return re.sub(r"\n{3,}", "\n\n", text)


def process_directory(target_dir, flags):
    for root, _dirs, files in os.walk(target_dir):
        for fname in files:
            fpath = os.path.join(root, fname)
            # Only process text-ish files
            if fname.endswith(('.md', '.sh', '.json', '.js', '.ts', '.py', '.yml', '.yaml')):
                with open(fpath, 'r', encoding='utf-8') as f:
                    text = f.read()
                new_text = process_all(text, flags)
                if new_text != text:
                    with open(fpath, 'w', encoding='utf-8') as f:
                        f.write(new_text)
                    rel = os.path.relpath(fpath, target_dir)
                    print(f"  Processed: {rel}")


def main():
    target_dir, flags = parse_args(sys.argv)
    print(f"=== Processing Conditionals in {target_dir} ===")
    print(f"Flags: {flags}")
    process_directory(target_dir, flags)
    print("Done.")


if __name__ == '__main__':
    main()
