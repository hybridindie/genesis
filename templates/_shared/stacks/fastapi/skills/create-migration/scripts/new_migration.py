#!/usr/bin/env python3
"""Create a timestamped Supabase migration skeleton; never overwrite."""

from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--description", required=True)
    parser.add_argument("--tables", required=True)
    parser.add_argument("--root", default=".")
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
    out = Path(args.root) / "supabase" / "migrations" / f"{stamp}_{desc}.sql"
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
