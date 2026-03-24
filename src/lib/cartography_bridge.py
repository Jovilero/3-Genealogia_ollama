#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Bridge no destructivo para consumir CLI de repo 6 (genealogia-cartografia-pro)."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def _run_cli(args: list[str]) -> dict:
    cmd = [sys.executable, "-m", "genealogia_cartografia_pro.cli.main", *args]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    except Exception as exc:
        return {
            "ok": False,
            "returncode": 1,
            "stdout": "",
            "stderr": f"Could not execute cartography CLI: {exc}",
            "command": cmd,
        }

    return {
        "ok": proc.returncode == 0,
        "returncode": proc.returncode,
        "stdout": proc.stdout.strip(),
        "stderr": proc.stderr.strip(),
        "command": cmd,
    }


def generate_manifest(carto_root: Path, output_manifest: Path, strict: bool = False) -> dict:
    args = ["manifest", "--root", str(carto_root), "--out", str(output_manifest)]
    if strict:
        args.append("--strict")
    return _run_cli(args)


def run_qa(carto_root: Path, output_report: Path, strict: bool = False) -> dict:
    args = ["qa", "--root", str(carto_root), "--out", str(output_report)]
    if strict:
        args.append("--strict")
    return _run_cli(args)


def main() -> int:
    parser = argparse.ArgumentParser(description="Bridge cartografico para repo 3")
    parser.add_argument("--carto-root", required=True)
    parser.add_argument("--manifest-out", required=True)
    parser.add_argument("--qa-out", required=True)
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()

    manifest = generate_manifest(Path(args.carto_root), Path(args.manifest_out), strict=args.strict)
    qa = run_qa(Path(args.carto_root), Path(args.qa_out), strict=args.strict)

    result = {"manifest": manifest, "qa": qa}
    print(json.dumps(result, ensure_ascii=True, indent=2))
    return 0 if manifest["ok"] and qa["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
