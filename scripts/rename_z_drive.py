#!/usr/bin/env python3
"""Rename magazine folders and PDF files on Z: drive to match YAML templates.

Usage:
    python3 scripts/rename_z_drive.py --dry-run   # preview changes
    python3 scripts/rename_z_drive.py              # execute renames
"""
import argparse
import re
import sys
from pathlib import Path

# Allow importing from app/
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.processor import (
    DUPLICATE_SUFFIX,
    format_output_name,
    load_magazines,
    match_magazine,
)

Z_DRIVE = Path("/mnt/z")
CONFIG = Path(__file__).resolve().parent.parent / "config" / "magazines.yaml"

# Folders on Z: that don't match the YAML name field
FOLDER_RENAMES = {
    "National Georgraphic History": "National Geographic History",
    "Programmez! Hors-Série": "Programmez! Hors-Serie",
    "Que Choisir Hors-Série": "Que Choisir Hors-Serie",
    "Science & Vie Hors-serie Biologie": "Science & Vie Hors-Serie Biologie",
    "Sciences et Avenir Hors-serie": "Sciences et Avenir Hors-Serie",
    "PC-Tricks, Tipps und Anleitungen": "PC-Tricks Tipps und Anleitungen",
}

# Folders with no YAML entry — skip entirely
SKIP_FOLDERS = {
    "Electric Drive",
    "Men\u2019s Fitness Guide",
    "Yoga World",
    "\u200cAnthem Tech Guides",  # zero-width non-joiner prefix
    "RennRad",
    "Tele Magazine",
}


def rename_folders(dry_run: bool) -> dict[str, str]:
    """Rename folders that don't match YAML names. Returns mapping of old->new paths."""
    renamed = {}
    for old_name, new_name in FOLDER_RENAMES.items():
        old_path = Z_DRIVE / old_name
        new_path = Z_DRIVE / new_name
        if not old_path.exists():
            continue
        if new_path.exists():
            print(f"  SKIP folder (target exists): {old_name} -> {new_name}")
            continue
        print(f"  RENAME folder: {old_name} -> {new_name}")
        if not dry_run:
            old_path.rename(new_path)
        renamed[old_name] = new_name
    return renamed


def process_folder(folder: Path, magazines: list[dict], dry_run: bool) -> dict:
    """Process all PDFs in a folder. Returns stats dict."""
    stats = {"renamed": 0, "already_ok": 0, "unmatched": [], "skipped": 0}

    pdfs = sorted(folder.iterdir())
    for filepath in pdfs:
        if filepath.is_dir():
            continue
        # Only process PDF files (any case extension)
        if filepath.suffix.lower() != ".pdf":
            continue

        original_name = filepath.name
        # Normalize to .pdf for matching purposes (don't rename on disk)
        filename = filepath.stem + ".pdf" if filepath.suffix != ".pdf" else filepath.name

        # Strip duplicate suffixes like (1), (2) before matching
        cleaned = DUPLICATE_SUFFIX.sub(r".\1", filename)
        # Strip " - Copie" suffix (Windows copy marker)
        cleaned = re.sub(r" - Copie(\.\w+)$", r"\1", cleaned)
        # Collapse multiple spaces into one
        cleaned = re.sub(r"  +", " ", cleaned)

        result = match_magazine(cleaned, magazines)
        if result is None:
            stats["unmatched"].append(original_name)
            continue

        mag_name, pub_date, template, extra_vars = result
        new_name = format_output_name(mag_name, pub_date, template, cleaned, extra_vars)

        if new_name == original_name:
            stats["already_ok"] += 1
            continue

        target = filepath.parent / new_name
        if target.exists():
            print(f"    SKIP (target exists): {original_name} -> {new_name}")
            stats["skipped"] += 1
            continue

        print(f"    RENAME: {original_name} -> {new_name}")
        if not dry_run:
            filepath.rename(target)
        stats["renamed"] += 1

    return stats


def main():
    parser = argparse.ArgumentParser(description="Rename Z: drive magazine files to match YAML templates")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without renaming")
    args = parser.parse_args()

    if args.dry_run:
        print("=== DRY RUN (no changes will be made) ===\n")

    magazines = load_magazines(CONFIG)
    print(f"Loaded {len(magazines)} magazine definitions from {CONFIG}\n")

    # Step 1: Rename folders
    print("--- Folder renames ---")
    folder_renames = rename_folders(args.dry_run)
    if not folder_renames:
        print("  (none needed)")
    print()

    # Step 2: Process files in each folder
    print("--- File renames ---")
    totals = {"renamed": 0, "already_ok": 0, "unmatched": 0, "skipped": 0, "folders": 0}
    all_unmatched = []

    folders = sorted(Z_DRIVE.iterdir())
    for folder in folders:
        if not folder.is_dir():
            continue
        if folder.name in SKIP_FOLDERS:
            continue

        stats = process_folder(folder, magazines, args.dry_run)

        if stats["renamed"] or stats["unmatched"]:
            # Header already printed via individual RENAME lines
            pass

        if stats["unmatched"]:
            for f in stats["unmatched"]:
                print(f"    UNMATCHED: {folder.name}/{f}")
                all_unmatched.append(f"{folder.name}/{f}")

        totals["renamed"] += stats["renamed"]
        totals["already_ok"] += stats["already_ok"]
        totals["unmatched"] += len(stats["unmatched"])
        totals["skipped"] += stats["skipped"]
        totals["folders"] += 1

    # Summary
    print(f"\n--- Summary ---")
    print(f"Folders scanned:    {totals['folders']}")
    print(f"Files renamed:      {totals['renamed']}")
    print(f"Already correct:    {totals['already_ok']}")
    print(f"Skipped (dup):      {totals['skipped']}")
    print(f"Unmatched:          {totals['unmatched']}")

    if all_unmatched:
        print(f"\n--- Unmatched files ({len(all_unmatched)}) ---")
        for f in all_unmatched:
            print(f"  {f}")


if __name__ == "__main__":
    main()
