import re
import shutil
import logging
import unicodedata
from pathlib import Path
from datetime import date

import yaml

import calendar

MONTH_NAMES = {name.lower(): num for num, name in enumerate(calendar.month_name) if num}
MONTH_ABBR = {name.lower(): num for num, name in enumerate(calendar.month_abbr) if num}
MONTH_NAMES.update(MONTH_ABBR)
MONTH_NAMES_FR = {
    "janvier": 1, "février": 2, "fevrier": 2, "mars": 3, "avril": 4,
    "mai": 5, "juin": 6, "juillet": 7, "août": 8, "aout": 8,
    "septembre": 9, "octobre": 10, "novembre": 11, "décembre": 12, "decembre": 12,
}
MONTH_NAMES.update(MONTH_NAMES_FR)

MONTH_ABBR_FR = {
    "janv": 1, "fev": 2, "fév": 2, "avr": 4,
    "juil": 7, "aou": 8, "aoû": 8, "sept": 9, "déc": 12,
}
MONTH_NAMES.update(MONTH_ABBR_FR)

# German month names
MONTH_NAMES_DE = {
    "januar": 1, "februar": 2, "märz": 3, "marz": 3, "april": 4,
    "mai": 5, "juni": 6, "juli": 7, "august": 8,
    "september": 9, "oktober": 10, "november": 11, "dezember": 12,
}
MONTH_NAMES.update(MONTH_NAMES_DE)

SEASONS = {
    "printemps": 4, "spring": 4,
    "été": 7, "ete": 7, "summer": 7,
    "automne": 10, "autumn": 10, "fall": 10,
    "hiver": 1, "winter": 1,
}

logger = logging.getLogger(__name__)

CONFIG_PATH = Path("/app/config/magazines.yaml")


def load_magazines(config_path: Path = CONFIG_PATH) -> list[dict]:
    with open(config_path) as f:
        config = yaml.safe_load(f)
    magazines = config.get("magazines", [])
    for mag in magazines:
        if mag.get("delete"):
            # Delete-only entries: just need compiled patterns, no date groups
            if "pattern" in mag:
                mag["_compiled_patterns"] = [re.compile(mag["pattern"], re.IGNORECASE)]
            else:
                mag["_compiled_patterns"] = [
                    re.compile(v["pattern"], re.IGNORECASE) for v in mag["patterns"]
                ]
            mag["_variants"] = []
        elif "pattern" in mag:
            # Support single pattern or multiple patterns per magazine
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
        first_month = re.split(r"[-\s]", value)[0]
        month_num = MONTH_NAMES.get(first_month.lower())
        if month_num is None:
            raise ValueError(f"Unknown month name: {first_month}")
        return "month", month_num, {"month_range": value}
    if key == "season":
        month_num = SEASONS.get(value.lower())
        if month_num is None:
            raise ValueError(f"Unknown season: {value}")
        return "month", month_num, {}
    if key == "year_short":
        return "year", 2000 + int(value), {}
    if key == "month":
        month_num = MONTH_NAMES.get(value.lower())
        if month_num is not None:
            return "month", month_num, {"month_name_orig": value}
    return key, int(value), {}


def match_magazine(filename: str, magazines: list[dict]) -> tuple[str, date, str, dict] | None:
    """Try to match a filename against known magazine patterns.
    Returns (magazine_name, publication_date, output_template, extra_vars) or None.
    """
    for mag in magazines:
        if mag.get("delete"):
            continue
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
                today = date.today()
                if not date_map:
                    pub_date = today
                else:
                    year = date_map.get("year", today.year)
                    month = date_map.get("month", 1)
                    day = date_map.get("day", 1)
                    # Clamp day to valid range for the month
                    max_day = calendar.monthrange(year, month)[1]
                    if day > max_day:
                        day = max_day
                    pub_date = date(year, month, day)
                template = mag.get("template", DEFAULT_TEMPLATE)
                return mag["name"], pub_date, template, extra_vars
    return None


def format_output_name(name: str, pub_date: date, template: str, original: str, extra_vars: dict = None) -> str:
    """Format the output filename using the template.
    Available placeholders: {name}, {date}, {year}, {month}, {day}, {day_short}, {month_name},
    plus any extra vars like {month_range}.
    """
    month_name = pub_date.strftime("%B")
    values = {
        "name": name,
        "original": original,
        "date": pub_date.isoformat(),
        "year": pub_date.year,
        "month": f"{pub_date.month:02d}",
        "day": f"{pub_date.day:02d}",
        "day_short": str(pub_date.day),
        "month_name": month_name,
        "month_name_orig": month_name,  # fallback if no month_name captured
        "month_range": month_name,  # fallback if no month_range captured
    }
    if extra_vars:
        values.update(extra_vars)
    return template.format(**values)


def match_delete(filename: str, magazines: list[dict]) -> str | None:
    """Check if a filename matches a magazine marked for deletion.
    Returns the magazine name if matched, None otherwise.
    """
    for mag in magazines:
        if not mag.get("delete"):
            continue
        for compiled in mag["_compiled_patterns"]:
            if compiled.match(filename):
                return mag["name"]
    return None


DUPLICATE_SUFFIX = re.compile(r"\(\d+\)\.(pdf)$", re.IGNORECASE)


def process_file(filepath: Path, magazines: list[dict], output_dir: Path, quarantine_dir: Path) -> bool:
    """Process a single PDF file: recognize, rename, and move it.
    Unrecognized files are moved to quarantine_dir.
    """
    # Normalize .Pdf / .PDF etc. to .pdf on disk
    if filepath.suffix.lower() == ".pdf" and filepath.suffix != ".pdf":
        corrected = filepath.with_name(filepath.stem + ".pdf")
        logger.info("Renamed extension: %s -> %s", filepath.name, corrected.name)
        filepath = filepath.rename(corrected)

    filename = filepath.name

    # Normalize Unicode to NFC so accented characters (e.g. é) match patterns
    filename_nfc = unicodedata.normalize("NFC", filename)
    if filename_nfc != filename:
        corrected = filepath.with_name(filename_nfc)
        logger.info("Normalized Unicode: %s -> %s", filename, filename_nfc)
        filepath = filepath.rename(corrected)
        filename = filename_nfc

    # Check for duplicate suffix like (1), (2)
    if DUPLICATE_SUFFIX.search(filename):
        original_name = DUPLICATE_SUFFIX.sub(r".\1", filename)
        original_path = filepath.parent / original_name
        if original_path.exists():
            logger.info("Duplicate file (original exists), deleting: %s", filename)
            filepath.unlink()
            return False

    # Strip duplicate suffixes like (1), (2) before matching
    cleaned = DUPLICATE_SUFFIX.sub(r".\1", filename)

    # Check if file matches a magazine marked for deletion
    delete_name = match_delete(cleaned, magazines)
    if delete_name:
        logger.info("Unwanted magazine '%s', deleting: %s", delete_name, filename)
        filepath.unlink()
        return False

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
