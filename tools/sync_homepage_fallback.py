#!/usr/bin/env python3
"""Registry no-JS article catalogs are retired.

Homepage, library, map, earnings, and series lists render in the browser from
registry.json. Adding a note is a registry edit; this command no longer writes
article markup into HTML.
"""

from __future__ import annotations

import argparse


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="kept for callers; catalogs are no longer generated")
    parser.parse_args()
    print("registry no-JS article catalogs are retired; hub lists render from registry.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
