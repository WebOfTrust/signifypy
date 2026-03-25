#!/usr/bin/env python3
"""Extract a version section from docs/changelog.md."""

from __future__ import annotations

import argparse
from pathlib import Path


def extract_section(text: str, version: str) -> str:
    heading = f"## {version}"
    lines = text.splitlines()
    start = None
    end = None

    for index, line in enumerate(lines):
        if line.strip() == heading:
            start = index
            continue
        if start is not None and line.startswith("## "):
            end = index
            break

    if start is None:
        raise ValueError(f"Version section '{heading}' not found.")

    if end is None:
        end = len(lines)

    section = "\n".join(lines[start:end]).strip()
    if not section:
        raise ValueError(f"Version section '{heading}' is empty.")

    return section + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", required=True, help="Bare package version like 0.5.0")
    parser.add_argument("--input", required=True, help="Path to changelog markdown")
    parser.add_argument("--output", required=True, help="Path to write the extracted section")
    args = parser.parse_args()

    if args.version.startswith("v"):
        raise ValueError("Expected a bare package version without the 'v' prefix.")

    input_path = Path(args.input)
    output_path = Path(args.output)
    output_path.write_text(extract_section(input_path.read_text(), args.version))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
