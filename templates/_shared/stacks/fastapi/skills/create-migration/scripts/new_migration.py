#!/usr/bin/env python3
"""Create a timestamped SQL migration skeleton; never overwrite."""

from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
from pathlib import Path

# Raw-SQL migration directories, in lookup order.
CANDIDATES = ("supabase/migrations", "migrations", "db/migrations")


def find_dir(root: Path, explicit: str | None) -> Path | None:
    if explicit:
        return root / explicit
    for rel in CANDIDATES:
        if (root / rel).is_dir():
            return root / rel
    return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--description", required=True)
    parser.add_argument("--tables", required=True)
    parser.add_argument("--root", default=".")
    parser.add_argument("--dir", help="migrations directory relative to --root (default: auto-detect)")
    args = parser.parse_args()
    desc = args.description.strip()
    if not re.fullmatch(r"[a-z0-9]+(?:_[a-z0-9]+)*", desc):
        print("description must be snake_case", file=sys.stderr)
        return 1
    tables = [t.strip() for t in args.tables.split(",") if t.strip()]
    if not tables or any(not re.fullmatch(r"[a-z0-9_]+", t) for t in tables):
        print("tables must be comma-separated snake_case names", file=sys.stderr)
        return 1
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d%H%M%S")
    root = Path(args.root)
    mig_dir = find_dir(root, args.dir)
    if mig_dir is None:
        if (root / "alembic").is_dir() or (root / "alembic.ini").is_file():
            print("Alembic project: create the revision with `alembic revision -m`", file=sys.stderr)
        else:
            print(f"no migrations directory ({', '.join(CANDIDATES)}); pass --dir", file=sys.stderr)
        return 2
    out = mig_dir / f"{stamp}_{desc}.sql"
    if out.exists():
        print(f"exists: {out}", file=sys.stderr)
        return 1
    blocks = []
    for table in tables:
        blocks.append(
            f"""-- {table}
CREATE TABLE IF NOT EXISTS public.{table} (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
  -- TODO: columns, checks, foreign keys
);

CREATE OR REPLACE TRIGGER {table}_updated_at
  BEFORE UPDATE ON public.{table}
  FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

-- TODO: FK indexes
"""
        )
    header = (
        f"-- Migration: {desc}\n"
        "-- Generated skeleton: fill columns/constraints, validate against sql-standards.md.\n\n"
    )
    text = header + "\n".join(blocks)
    text += "\n-- DOWN\n" + "\n".join(f"-- DROP TABLE IF EXISTS public.{t} CASCADE;" for t in tables) + "\n"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
