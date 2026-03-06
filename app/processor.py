import re
import shutil
import logging
from pathlib import Path
from datetime import date

import yaml

import calendar

MONTH_NAMES = {name.lower(): num for num, name in enumerate(calendar.month_name) if num}
MONTH_NAMES_FR = {
    "janvier": 1, "février": 2, "fevrier": 2, "mars": 3, "avril": 4,
    "mai": 5, "juin": 6, "juillet": 7, "août": 8, "aout": 8,
    "septembre": 9, "octobre": 10, "novembre": 11, "décembre": 12, "decembre": 12,
}
MONTH_NAMES.update(MONTH_NAMES_FR)

logger = logging.getLogger(__name__)

CONFIG_PATH = Path("/app/config/magazines.yaml")


def load_magazines(config_path: Path = CONFIG_PATH) -> list[dict]:
    with open(config_path) as f:
        config = yaml.safe_load(f)
    magazines = config.get("magazines", [])
    for mag in magazines:
        # Support single pattern or multiple patterns per magazine
        if "pattern" in mag:
            mag["_variants"] = [
                (re.compile(mag["pattern"], re.IGNORECASE), mag["date_groups"])
            ]
        else:
            mag["_variants"] = [
                (re.compile(v["pattern"], re.IGNORECASE), v["date_groups"])
                for v in mag["patterns"]
            ]
    return magazines


DEFAULT_TEMPLATE = "{name} - {date}.pdf"


def _parse_group(key: str, value: str) -> tuple[str, int, dict]:
    """Parse a captured group value.
    Returns (date_key, numeric_value, extra_template_vars).
    """
    if key == "month_name":
        month_num = MONTH_NAMES.get(value.lower())
        if month_num is None:
            raise ValueError(f"Unknown month name: {value}")
        return "month", month_num, {"month_name_orig": value}
    if key == "month_range":
        first_month = value.split("-")[0]
        month_num = MONTH_NAMES.get(first_month.lower())
        if month_num is None:
            raise ValueError(f"Unknown month name: {first_month}")
        return "month", month_num, {"month_range": value}
    if key == "year_short":
        return "year", 2000 + int(value), {}
    return key, int(value), {}


def match_magazine(filename: str, magazines: list[dict]) -> tuple[str, date, str, dict] | None:
    """Try to match a filename against known magazine patterns.
    Returns (magazine_name, publication_date, output_template, extra_vars) or None.
    """
    for mag in magazines:
        for compiled, date_groups in mag["_variants"]:
            m = compiled.match(filename)
            if m:
                groups = m.groups()
                date_map = {}
                extra_vars = {}
                for i, key in enumerate(date_groups):
                    date_key, parsed, extras = _parse_group(key, groups[i])
                    date_map[date_key] = parsed
                    extra_vars.update(extras)
                year = date_map.get("year", date.today().year)
                pub_date = date(year, date_map["month"], date_map.get("day", 1))
                template = mag.get("template", DEFAULT_TEMPLATE)
                return mag["name"], pub_date, template, extra_vars
    return None


def format_output_name(name: str, pub_date: date, template: str, original: str, extra_vars: dict = None) -> str:
    """Format the output filename using the template.
    Available placeholders: {name}, {date}, {year}, {month}, {day}, {month_name},
    plus any extra vars like {month_range}.
    """
    values = {
        "name": name,
        "original": original,
        "date": pub_date.isoformat(),
        "year": pub_date.year,
        "month": f"{pub_date.month:02d}",
        "day": f"{pub_date.day:02d}",
        "month_name": pub_date.strftime("%B"),
    }
    if extra_vars:
        values.update(extra_vars)
    return template.format(**values)


DUPLICATE_SUFFIX = re.compile(r"\(\d+\)\.(pdf)$", re.IGNORECASE)


def process_file(filepath: Path, magazines: list[dict], output_dir: Path, quarantine_dir: Path) -> bool:
    """Process a single PDF file: recognize, rename, and move it.
    Unrecognized files are moved to quarantine_dir.
    """
    filename = filepath.name
    # Strip duplicate suffixes like (1), (2) before matching
    cleaned = DUPLICATE_SUFFIX.sub(r".\1", filename)
    result = match_magazine(cleaned, magazines)

    if result is None:
        logger.warning("Unrecognized file, moving to quarantine: %s", filename)
        quarantine_dir.mkdir(parents=True, exist_ok=True)
        dest_path = quarantine_dir / filename
        if not dest_path.exists():
            shutil.move(str(filepath), str(dest_path))
        return False

    mag_name, pub_date, template, extra_vars = result
    dest_dir = output_dir / mag_name
    dest_dir.mkdir(parents=True, exist_ok=True)

    new_name = format_output_name(mag_name, pub_date, template, filename, extra_vars)
    dest_path = dest_dir / new_name

    if dest_path.exists():
        logger.info("Duplicate detected, deleting: %s", filename)
        filepath.unlink()
        return False

    shutil.move(str(filepath), str(dest_path))
    logger.info("Processed: %s -> %s", filename, dest_path)
    return True
