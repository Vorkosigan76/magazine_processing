import os
import re
import logging
import tempfile
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from app.processor import MONTH_NAMES, SEASONS

logger = logging.getLogger(__name__)

REPORT_FILENAME = "quarantine_report.txt"

# Build a regex alternation for all known month/season names (longest first to avoid partial matches)
_MONTH_WORDS = sorted(MONTH_NAMES.keys(), key=len, reverse=True)
_SEASON_WORDS = sorted(SEASONS.keys(), key=len, reverse=True)
_MONTH_RE = re.compile(
    r"\b(" + "|".join(re.escape(m) for m in _MONTH_WORDS) + r")\b", re.IGNORECASE
)
_SEASON_RE = re.compile(
    r"\b(" + "|".join(re.escape(s) for s in _SEASON_WORDS) + r")\b", re.IGNORECASE
)

# Date patterns (order matters: compound patterns before simple ones)
_ISO_DATE_RE = re.compile(r"\b(\d{4})-(\d{2})-(\d{2})\b")
_DMY_DATE_RE = re.compile(r"\b(\d{2})-(\d{2})-(\d{4})\b")
_DOTTED_DATE_RE = re.compile(r"\b(\d{4})\.(\d{2})\.(\d{2})\b")
_COMPACT_DATE_RE = re.compile(r"(?<!\d)(20\d{2})(\d{2})(\d{2})(?!\d)")
_YEAR_RE = re.compile(r"\b(20\d{2})\b")
_DIGITS_RE = re.compile(r"\d{2,}")


def _build_skeleton(stem: str) -> str:
    """Replace date-like and numeric tokens with placeholders to create a grouping key."""
    s = stem

    # 1. Compound date patterns (before individual components)
    s = _ISO_DATE_RE.sub("{ISODATE}", s)
    s = _DOTTED_DATE_RE.sub("{DOTTEDDATE}", s)
    s = _DMY_DATE_RE.sub("{DMYDATE}", s)
    s = _COMPACT_DATE_RE.sub("{COMPACTDATE}", s)

    # 2. Standalone years
    s = _YEAR_RE.sub("{YEAR}", s)

    # 3. Month names (before generic digit replacement)
    s = _SEASON_RE.sub("{SEASON}", s)
    s = _MONTH_RE.sub("{MONTH}", s)

    # 4. Remaining digit sequences (issue numbers, etc.)
    s = _DIGITS_RE.sub("{NUM}", s)

    return s


def _scan_quarantine(quarantine_dir: Path) -> list[str]:
    """Return sorted list of PDF filenames in the quarantine directory."""
    if not quarantine_dir.is_dir():
        return []
    return sorted(
        f.name
        for f in quarantine_dir.iterdir()
        if f.is_file() and f.suffix.lower() == ".pdf" and f.name != REPORT_FILENAME
    )


def _group_by_skeleton(filenames: list[str]) -> list[tuple[str, list[str]]]:
    """Group filenames by their skeleton. Returns groups sorted by size descending, then name."""
    groups = defaultdict(list)
    for fn in filenames:
        stem = fn.rsplit(".", 1)[0] if "." in fn else fn
        skeleton = _build_skeleton(stem)
        groups[skeleton].append(fn)
    return sorted(groups.items(), key=lambda g: (-len(g[1]), g[1][0]))


def _infer_name(skeleton: str) -> str:
    """Extract a suggested magazine name from the literal prefix before the first placeholder."""
    # Find the first placeholder
    idx = skeleton.find("{")
    if idx == -1:
        prefix = skeleton
    else:
        prefix = skeleton[:idx]
    # Strip trailing separators and whitespace
    prefix = re.sub(r"[\s•·–—\-_N#]+$", "", prefix)
    return prefix.strip() if prefix.strip() else "Unknown"


def _skeleton_to_pattern(skeleton: str) -> str:
    """Convert a skeleton string to a regex pattern for magazines.yaml."""
    # Split the skeleton into literal parts and placeholders
    parts = re.split(r"(\{[A-Z]+\})", skeleton)
    result = []
    for part in parts:
        if part == "{ISODATE}":
            result.append(r"(\d{4})-(\d{2})-(\d{2})")
        elif part == "{DOTTEDDATE}":
            result.append(r"(\d{4})\.(\d{2})\.(\d{2})")
        elif part == "{DMYDATE}":
            result.append(r"(\d{2})-(\d{2})-(\d{4})")
        elif part == "{COMPACTDATE}":
            result.append(r"(\d{4})(\d{2})(\d{2})")
        elif part == "{YEAR}":
            result.append(r"(\d{4})")
        elif part == "{MONTH}":
            result.append(r"([A-Za-z\u00C0-\u00FF]+)")
        elif part == "{SEASON}":
            result.append(r"([A-Za-z\u00C0-\u00FF]+)")
        elif part == "{NUM}":
            result.append(r"\d+")
        else:
            # Escape literal text, then generalize common separators
            escaped = re.escape(part)
            # Generalize bullet/dash separators to character classes
            # re.escape may or may not escape these Unicode chars depending on Python version
            escaped = re.sub(r"\\?[•·]", "[•·]", escaped)
            escaped = re.sub(r"\\?[–—]", "[–-]", escaped)
            result.append(escaped)
    return "^" + "".join(result) + r"\.[Pp]df$"


def _infer_date_groups(skeleton: str) -> list[str]:
    """Map placeholder sequence in the skeleton to a date_groups list."""
    placeholders = re.findall(r"\{([A-Z]+)\}", skeleton)
    groups = []
    for p in placeholders:
        if p == "ISODATE":
            groups.extend(["year", "month", "day"])
        elif p == "DOTTEDDATE":
            groups.extend(["year", "month", "day"])
        elif p == "DMYDATE":
            groups.extend(["day", "month", "year"])
        elif p == "COMPACTDATE":
            groups.extend(["year", "month", "day"])
        elif p == "YEAR":
            groups.append("year")
        elif p == "MONTH":
            groups.append("month_name")
        elif p == "SEASON":
            groups.append("season")
        # NUM is not a date component, skip
    return groups


def _suggest_template(date_groups: list[str]) -> str | None:
    """Return a template string based on inferred date groups, or None for the default."""
    has_day = "day" in date_groups
    has_month_name = "month_name" in date_groups
    has_season = "season" in date_groups
    has_year = "year" in date_groups
    has_month = "month" in date_groups

    if has_day:
        # Default template works: {name} - {date}.pdf
        return None
    if has_month_name and has_year:
        return "{name} {year}{month} - {month_name_orig} {year}.pdf"
    if has_season and has_year:
        return "{name} {year}-{month}.pdf"
    if has_month and has_year:
        return "{name} {year}-{month}.pdf"
    if has_year:
        return "{name} - {year}.pdf"
    return None


def _format_yaml_entry(name: str, pattern: str, date_groups: list[str], template: str | None,
                       sample_filename: str, is_single: bool) -> str:
    """Format a single YAML entry suggestion."""
    lines = []
    lines.append(f'  - name: "{name}"')
    lines.append(f"    # Matches: {sample_filename}")
    if is_single and not date_groups:
        lines.append(f'    pattern: "^{re.escape(sample_filename.rsplit(".", 1)[0])}\\\\.[Pp]df$"')
        lines.append("    delete: true")
    else:
        lines.append(f'    pattern: "{pattern}"')
        if date_groups:
            lines.append(f"    date_groups: [{', '.join(date_groups)}]")
        if template:
            lines.append(f'    template: "{template}"')
    return "\n".join(lines)


def _format_report(groups: list[tuple[str, list[str]]], quarantine_dir: Path) -> str:
    """Assemble the full report text."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    total_files = sum(len(files) for _, files in groups)

    lines = []
    lines.append("Quarantine Report")
    lines.append(f"Generated: {now}")
    lines.append(f"Total quarantined files: {total_files}")
    lines.append(f"Groups identified: {len(groups)}")
    lines.append("")

    if total_files == 0:
        lines.append("No quarantined files found. All PDFs matched known patterns.")
        return "\n".join(lines) + "\n"

    for i, (skeleton, filenames) in enumerate(groups, 1):
        name = _infer_name(skeleton)
        pattern = _skeleton_to_pattern(skeleton)
        date_groups = _infer_date_groups(skeleton)
        template = _suggest_template(date_groups)
        is_single = len(filenames) == 1

        lines.append("=" * 80)
        lines.append(f'Group {i}: "{name}" ({len(filenames)} file{"s" if len(filenames) != 1 else ""})')
        lines.append("=" * 80)
        lines.append("")
        lines.append("Files:")
        for fn in filenames:
            lines.append(f"  - {fn}")
        lines.append("")

        # Describe what was detected
        if not date_groups:
            lines.append("No date pattern detected.")
        else:
            desc_parts = []
            if "day" in date_groups:
                desc_parts.append("daily")
            elif "month_name" in date_groups:
                desc_parts.append("monthly (named month)")
            elif "season" in date_groups:
                desc_parts.append("seasonal")
            elif "month" in date_groups:
                desc_parts.append("monthly (numeric)")
            elif "year" in date_groups:
                desc_parts.append("yearly")
            lines.append(f"Detected frequency: {', '.join(desc_parts) if desc_parts else 'unknown'}")

        if is_single:
            lines.append("Note: Only 1 file in this group. Pattern may need refinement.")
        lines.append("")

        yaml_entry = _format_yaml_entry(name, pattern, date_groups, template, filenames[0], is_single)
        lines.append("Suggested YAML entry (copy to config/magazines.yaml):")
        lines.append("--- YAML START ---")
        lines.append(yaml_entry)
        lines.append("--- YAML END ---")
        lines.append("")

    return "\n".join(lines) + "\n"


def generate_quarantine_report(quarantine_dir: Path) -> Path | None:
    """Scan quarantine directory and write a report with YAML suggestions.

    Returns the report path, or None if the quarantine directory doesn't exist.
    """
    if not quarantine_dir.is_dir():
        return None

    filenames = _scan_quarantine(quarantine_dir)
    groups = _group_by_skeleton(filenames)
    report_text = _format_report(groups, quarantine_dir)

    report_path = quarantine_dir / REPORT_FILENAME

    # Atomic write: write to temp file, then rename
    try:
        fd, tmp_path = tempfile.mkstemp(dir=quarantine_dir, suffix=".tmp", prefix=".report_")
        try:
            with open(fd, "w", encoding="utf-8") as f:
                f.write(report_text)
            os.chmod(tmp_path, 0o666)
            Path(tmp_path).replace(report_path)
        except BaseException:
            Path(tmp_path).unlink(missing_ok=True)
            raise
    except OSError:
        # Fallback: direct write if atomic write fails (e.g. cross-device)
        report_path.write_text(report_text, encoding="utf-8")
        os.chmod(report_path, 0o666)

    total_files = sum(len(files) for _, files in groups)
    logger.info(
        "Quarantine report: %d file(s) in %d group(s) -> %s",
        total_files, len(groups), report_path,
    )
    return report_path
