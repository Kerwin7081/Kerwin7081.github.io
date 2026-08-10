#!/usr/bin/env python3
"""Audit only production pages affected by a pull request."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import timedelta
from pathlib import Path, PurePosixPath


TEMP_ROOTS = {"preview", "previews", "publish", "staging"}
FROZEN_V2_ASSETS = {
    PurePosixPath("assets/kerwin-system-v2.css"),
    PurePosixPath("assets/kerwin-system-v2.js"),
}
REGISTRY_REQUIRED_FIELDS = {
    "slug",
    "title",
    "date",
    "deck",
    "tag",
    "source",
    "homepage_approved",
    "published_at",
}
NEW_META_REQUIRED_FIELDS = {
    "title",
    "slug",
    "date",
    "homepage_approved",
    "published_at",
    "updated_at",
}


def git_output(root: Path, *args: str, check: bool = True) -> bytes:
    completed = subprocess.run(
        ["git", "-C", str(root), *args],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if check and completed.returncode:
        detail = completed.stderr.decode("utf-8", "replace").strip()
        raise RuntimeError(detail or f"git {' '.join(args)} failed")
    return completed.stdout


def changed_paths(root: Path, base: str, head: str, diff_filter: str) -> list[PurePosixPath]:
    raw = git_output(
        root,
        "diff",
        "--name-only",
        "-z",
        f"--diff-filter={diff_filter}",
        f"{base}...{head}",
        "--",
    )
    return [
        PurePosixPath(item.decode("utf-8", "surrogateescape"))
        for item in raw.split(b"\0")
        if item
    ]


def path_exists_at_ref(root: Path, ref: str, path: PurePosixPath) -> bool:
    completed = subprocess.run(
        ["git", "-C", str(root), "cat-file", "-e", f"{ref}:{path.as_posix()}"],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return completed.returncode == 0


def under_temp_root(path: PurePosixPath) -> bool:
    return bool(path.parts) and path.parts[0] in TEMP_ROOTS


def load_json(path: Path) -> tuple[object | None, str | None]:
    try:
        return json.loads(path.read_text(encoding="utf-8")), None
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return None, str(exc)


def is_hong_kong_timestamp(value: object) -> bool:
    if not isinstance(value, str):
        return False
    try:
        from datetime import datetime

        parsed = datetime.fromisoformat(value)
    except ValueError:
        return False
    return parsed.utcoffset() == timedelta(hours=8)


def validate_new_page(root: Path, page: PurePosixPath) -> list[str]:
    errors: list[str] = []
    if page == PurePosixPath("index.html"):
        return errors
    if page.name != "index.html":
        if page != PurePosixPath("404.html"):
            errors.append(
                f"{page}: new production HTML must use <stable-slug>/index.html"
            )
        return errors

    meta_path = root / Path(*page.parent.parts) / "meta.json"
    if not meta_path.is_file():
        return [f"{page}: new production page is missing sibling meta.json"]

    meta, parse_error = load_json(meta_path)
    if parse_error:
        return [f"{meta_path.relative_to(root).as_posix()}: invalid JSON: {parse_error}"]
    if not isinstance(meta, dict):
        return [f"{meta_path.relative_to(root).as_posix()}: metadata must be an object"]

    missing = sorted(NEW_META_REQUIRED_FIELDS.difference(meta))
    if missing:
        errors.append(
            f"{meta_path.relative_to(root).as_posix()}: missing required fields: "
            + ", ".join(missing)
        )

    expected_slug = page.parent.as_posix()
    if meta.get("slug") != expected_slug:
        errors.append(
            f"{meta_path.relative_to(root).as_posix()}: slug must equal {expected_slug!r}"
        )
    for field in ("published_at", "updated_at"):
        if field in meta and not is_hong_kong_timestamp(meta[field]):
            errors.append(
                f"{meta_path.relative_to(root).as_posix()}: {field} must be ISO 8601 "
                "with an explicit +08:00 offset"
            )
    return errors


def validate_registry(root: Path) -> list[str]:
    path = root / "registry.json"
    registry, parse_error = load_json(path)
    if parse_error:
        return [f"registry.json: invalid JSON: {parse_error}"]
    if not isinstance(registry, list):
        return ["registry.json: top-level value must be an array"]

    errors: list[str] = []
    seen: set[str] = set()
    featured_ranks: dict[int, str] = {}
    for index, item in enumerate(registry):
        label = f"registry.json entry {index + 1}"
        if not isinstance(item, dict):
            errors.append(f"{label}: entry must be an object")
            continue
        missing = sorted(REGISTRY_REQUIRED_FIELDS.difference(item))
        if missing:
            errors.append(f"{label}: missing required fields: {', '.join(missing)}")
        slug = item.get("slug")
        if not isinstance(slug, str) or not slug.strip():
            errors.append(f"{label}: slug must be a non-empty string")
            continue
        if slug in seen:
            errors.append(f"registry.json: duplicate slug {slug!r}")
        seen.add(slug)
        if item.get("homepage_approved") is True:
            slug_path = PurePosixPath(slug)
            if slug_path.is_absolute() or ".." in slug_path.parts:
                errors.append(f"{label}: slug must be a safe repository-relative path")
                continue

            route = item.get("path")
            if route is not None:
                if (
                    not isinstance(route, str)
                    or not route.startswith("/")
                    or route.startswith("//")
                    or "?" in route
                    or "#" in route
                ):
                    errors.append(
                        f"{label}: path must be a safe root-relative public route"
                    )
                    continue
                route_path = PurePosixPath(route.lstrip("/"))
                if not route_path.parts or ".." in route_path.parts:
                    errors.append(
                        f"{label}: path must be a safe root-relative public route"
                    )
                    continue
                target = root / Path(*route_path.parts)
                if route.endswith("/"):
                    target /= "index.html"
            else:
                target = root / Path(*slug_path.parts) / "index.html"
            if not target.is_file():
                errors.append(
                    f"registry.json: approved slug {slug!r} has no public target "
                    f"{target.relative_to(root).as_posix()}"
                )

        featured_rank = item.get("featured_rank")
        if featured_rank is not None:
            if (
                isinstance(featured_rank, bool)
                or not isinstance(featured_rank, int)
                or featured_rank not in {1, 2, 3}
            ):
                errors.append(f"{label}: featured_rank must be one of 1, 2, or 3")
            elif item.get("homepage_approved") is not True:
                errors.append(f"{label}: featured entries must be homepage approved")
            elif featured_rank in featured_ranks:
                errors.append(
                    f"registry.json: duplicate featured_rank {featured_rank} for "
                    f"{featured_ranks[featured_rank]!r} and {slug!r}"
                )
            else:
                featured_ranks[featured_rank] = slug
    return errors


def validate_homepage_loader(root: Path) -> list[str]:
    candidates = (
        root / "assets" / "kerwin-home-v4.js",
        root / "assets" / "kerwin-home-v3.js",
    )
    path = next((candidate for candidate in candidates if candidate.is_file()), candidates[0])
    try:
        source = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        return [f"{path.relative_to(root).as_posix()}: unable to read homepage loader: {exc}"]

    errors: list[str] = []
    is_v4 = path.name == "kerwin-home-v4.js"
    for obsolete in ("var legacyPages", "registry.concat(legacyPages)", "source === 'codex'"):
        if obsolete in source:
            errors.append(
                f"{path.relative_to(root).as_posix()}: homepage content must come from "
                f"registry.json; obsolete loader logic remains: {obsolete}"
            )
    required = (
        ("Array.isArray(registry)", "homepage_approved", "function renderRecent",
         "function renderEarnings", "function renderLibrary")
        if is_v4
        else ("Array.isArray(registry)", "p.featured_rank", "p.path")
    )
    for token in required:
        if token not in source:
            errors.append(
                f"{path.relative_to(root).as_posix()}: missing homepage loader contract support: {token}"
            )
    return errors


def pages_referencing_assets(
    root: Path, asset_paths: set[PurePosixPath]
) -> set[PurePosixPath]:
    names = {path.name for path in asset_paths}
    pages: set[PurePosixPath] = set()
    for candidate in root.rglob("*.html"):
        relative = PurePosixPath(candidate.relative_to(root).as_posix())
        if under_temp_root(relative):
            continue
        try:
            html = candidate.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            continue
        if any(name in html for name in names):
            pages.add(relative)
    return pages


def run_page_auditor(root: Path, pages: list[PurePosixPath]) -> int:
    if not pages:
        print("[INFO] No production HTML page was affected by this pull request.")
        return 0
    command = [
        sys.executable,
        str(root / "tools" / "audit_pages.py"),
        "--root",
        str(root),
        *[path.as_posix() for path in pages],
    ]
    print(f"[INFO] Auditing {len(pages)} affected production page(s).")
    return subprocess.run(command, check=False).returncode


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", required=True, help="Pull request base commit SHA")
    parser.add_argument("--head", required=True, help="Pull request head commit SHA")
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Checked-out repository root",
    )
    args = parser.parse_args()
    root = args.root.resolve()

    try:
        changed = changed_paths(root, args.base, args.head, "ACMR")
        changed_with_deletions = changed_paths(root, args.base, args.head, "ACMRD")
    except RuntimeError as exc:
        print(f"[FAIL] Unable to resolve pull request diff: {exc}", file=sys.stderr)
        return 1

    errors: list[str] = []
    new_paths = {
        path
        for path in changed
        if not path_exists_at_ref(root, args.base, path)
    }

    new_temp_paths = sorted(path for path in new_paths if under_temp_root(path))
    for path in new_temp_paths:
        errors.append(
            f"{path}: new files are not allowed under preview/previews/publish/staging"
        )

    frozen_changes = sorted(
        path for path in changed_with_deletions if path in FROZEN_V2_ASSETS
    )
    for path in frozen_changes:
        errors.append(f"{path}: frozen legacy v2 asset must not be changed or deleted")

    for path in sorted(new_paths):
        if path.suffix.lower() == ".html" and not under_temp_root(path):
            errors.extend(validate_new_page(root, path))

    for path in sorted(changed):
        if path.suffix.lower() != ".json" or under_temp_root(path):
            continue
        _, parse_error = load_json(root / Path(*path.parts))
        if parse_error:
            errors.append(f"{path}: invalid JSON: {parse_error}")

    if PurePosixPath("registry.json") in changed:
        errors.extend(validate_registry(root))
    if any(
        path in changed
        for path in (
            PurePosixPath("assets/kerwin-home-v3.js"),
            PurePosixPath("assets/kerwin-home-v4.js"),
        )
    ):
        errors.extend(validate_homepage_loader(root))

    affected_pages: set[PurePosixPath] = {
        path
        for path in changed
        if path.suffix.lower() == ".html"
        and not under_temp_root(path)
        and (root / Path(*path.parts)).is_file()
    }
    for path in changed:
        if path.name == "meta.json" and not under_temp_root(path):
            sibling = path.parent / "index.html"
            if (root / Path(*sibling.parts)).is_file():
                affected_pages.add(sibling)

    if any(path.as_posix().startswith("assets/kerwin-home-") for path in changed):
        affected_pages.add(PurePosixPath("index.html"))

    changed_v3_assets = {
        path
        for path in changed
        if path.as_posix().startswith("assets/kerwin-system-v3.")
    }
    if changed_v3_assets:
        affected_pages.update(pages_referencing_assets(root, changed_v3_assets))

    print(
        f"[INFO] Pull request diff: {len(changed_with_deletions)} changed path(s); "
        f"{len(new_paths)} new path(s)."
    )
    if errors:
        for error in errors:
            print(f"[FAIL] {error}")

    audit_status = run_page_auditor(root, sorted(affected_pages))
    if errors or audit_status:
        return 1
    print("[PASS] Changed-page release guard passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
