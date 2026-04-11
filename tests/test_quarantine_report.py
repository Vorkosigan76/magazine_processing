import re
import pytest
from pathlib import Path

from app.quarantine_report import (
    _build_skeleton,
    _group_by_skeleton,
    _infer_name,
    _skeleton_to_pattern,
    _infer_date_groups,
    _suggest_template,
    _scan_quarantine,
    generate_quarantine_report,
    REPORT_FILENAME,
)


class TestBuildSkeleton:
    def test_french_monthly(self):
        skel = _build_skeleton("Science & Vie N1302 • Mars 2026")
        assert "{NUM}" in skel
        assert "{MONTH}" in skel
        assert "{YEAR}" in skel
        assert "Science & Vie" in skel

    def test_iso_date(self):
        skel = _build_skeleton("AI Magazine - 2026-03-15")
        assert "{ISODATE}" in skel
        assert "AI Magazine" in skel

    def test_compact_date(self):
        skel = _build_skeleton("lmnd20260210")
        assert "{COMPACTDATE}" in skel

    def test_dotted_date(self):
        skel = _build_skeleton("Auto Bild 2025.10.09")
        assert "{DOTTEDDATE}" in skel

    def test_dmy_date(self):
        skel = _build_skeleton("L'Express - 12-03-2026")
        assert "{DMYDATE}" in skel

    def test_season(self):
        skel = _build_skeleton("Whisky Advocate Winter 2025")
        assert "{SEASON}" in skel
        assert "{YEAR}" in skel

    def test_no_date(self):
        skel = _build_skeleton("xr7q_something_weird")
        assert "{YEAR}" not in skel
        assert "{MONTH}" not in skel

    def test_year_only(self):
        skel = _build_skeleton("Air Traffic Technology International - 2024")
        assert "{YEAR}" in skel
        assert "Air Traffic Technology International" in skel

    def test_year_month_numeric(self):
        skel = _build_skeleton("Magazine Test 2026-01")
        # The year should be captured; 01 is only 2 digits so it becomes {NUM}
        assert "{YEAR}" in skel

    def test_french_month_abbreviation(self):
        skel = _build_skeleton("Test Magazine Fev 2026")
        assert "{MONTH}" in skel
        assert "{YEAR}" in skel

    def test_german_month(self):
        skel = _build_skeleton("Test Magazin Oktober 2025")
        assert "{MONTH}" in skel
        assert "{YEAR}" in skel

    def test_same_skeleton_for_variants(self):
        skel1 = _build_skeleton("Science & Vie N1302 • Mars 2026")
        skel2 = _build_skeleton("Science & Vie N1303 • Avril 2026")
        assert skel1 == skel2


class TestGroupBySkeleton:
    def test_groups_similar_files(self):
        filenames = [
            "Science & Vie N1302 • Mars 2026.pdf",
            "Science & Vie N1303 • Avril 2026.pdf",
            "Science & Vie N1304 • Mai 2026.pdf",
            "Totally Different File.pdf",
        ]
        groups = _group_by_skeleton(filenames)
        assert len(groups) == 2
        # Largest group first
        assert len(groups[0][1]) == 3
        assert len(groups[1][1]) == 1

    def test_different_magazines_separate(self):
        filenames = [
            "Foo Magazine N12 Mars 2026.pdf",
            "Bar Magazine N13 Avril 2026.pdf",
        ]
        groups = _group_by_skeleton(filenames)
        assert len(groups) == 2

    def test_single_file_group(self):
        groups = _group_by_skeleton(["unique_file.pdf"])
        assert len(groups) == 1
        assert len(groups[0][1]) == 1

    def test_empty_list(self):
        groups = _group_by_skeleton([])
        assert groups == []


class TestInferName:
    def test_basic_prefix(self):
        assert _infer_name("Science & Vie N{NUM} • {MONTH} {YEAR}") == "Science & Vie"

    def test_dash_separator(self):
        assert _infer_name("AI Magazine - {ISODATE}") == "AI Magazine"

    def test_no_placeholder(self):
        assert _infer_name("some_weird_file") == "some_weird_file"

    def test_placeholder_at_start(self):
        assert _infer_name("{NUM}magazine") == "Unknown"

    def test_trailing_n_stripped(self):
        # "N" before issue number should be stripped
        name = _infer_name("Le Point N{NUM} - {MONTH} {YEAR}")
        assert name == "Le Point"


class TestSkeletonToPattern:
    def test_matches_original_french_monthly(self):
        skeleton = _build_skeleton("Science & Vie N1302 • Mars 2026")
        pattern = _skeleton_to_pattern(skeleton)
        regex = re.compile(pattern, re.IGNORECASE)
        assert regex.match("Science & Vie N1302 • Mars 2026.pdf")
        assert regex.match("Science & Vie N1303 · Avril 2026.pdf")

    def test_matches_iso_date(self):
        skeleton = _build_skeleton("AI Magazine - 2026-03-15")
        pattern = _skeleton_to_pattern(skeleton)
        regex = re.compile(pattern, re.IGNORECASE)
        assert regex.match("AI Magazine - 2026-03-15.pdf")
        assert regex.match("AI Magazine - 2025-12-01.Pdf")

    def test_matches_compact_date(self):
        skeleton = _build_skeleton("lmnd20260210")
        pattern = _skeleton_to_pattern(skeleton)
        regex = re.compile(pattern, re.IGNORECASE)
        assert regex.match("lmnd20260311.pdf")

    def test_special_chars_escaped(self):
        skeleton = _build_skeleton("C++ Magazine (FR) 2026")
        pattern = _skeleton_to_pattern(skeleton)
        # Should contain escaped ( and )
        assert r"\(" in pattern or "\\(" in pattern
        regex = re.compile(pattern, re.IGNORECASE)
        assert regex.match("C++ Magazine (FR) 2025.pdf")

    def test_captures_date_groups(self):
        skeleton = _build_skeleton("Test Mag Mars 2026")
        pattern = _skeleton_to_pattern(skeleton)
        regex = re.compile(pattern, re.IGNORECASE)
        m = regex.match("Test Mag Avril 2025.pdf")
        assert m is not None
        # Should capture month name and year
        groups = m.groups()
        assert "Avril" in groups
        assert "2025" in groups


class TestInferDateGroups:
    def test_iso_date(self):
        skel = _build_skeleton("Mag - 2026-03-15")
        assert _infer_date_groups(skel) == ["year", "month", "day"]

    def test_dmy_date(self):
        skel = _build_skeleton("Mag - 15-03-2026")
        assert _infer_date_groups(skel) == ["day", "month", "year"]

    def test_month_name_year(self):
        skel = _build_skeleton("Mag Mars 2026")
        assert _infer_date_groups(skel) == ["month_name", "year"]

    def test_year_only(self):
        skel = _build_skeleton("Mag 2026")
        assert _infer_date_groups(skel) == ["year"]

    def test_season_year(self):
        skel = _build_skeleton("Mag Winter 2025")
        assert _infer_date_groups(skel) == ["season", "year"]

    def test_no_date(self):
        skel = _build_skeleton("random_file")
        assert _infer_date_groups(skel) == []

    def test_compact_date(self):
        skel = _build_skeleton("mag20260315")
        assert _infer_date_groups(skel) == ["year", "month", "day"]


class TestSuggestTemplate:
    def test_daily_default(self):
        assert _suggest_template(["year", "month", "day"]) is None

    def test_monthly_named(self):
        tmpl = _suggest_template(["month_name", "year"])
        assert tmpl is not None
        assert "{month_name_orig}" in tmpl

    def test_yearly(self):
        tmpl = _suggest_template(["year"])
        assert tmpl is not None
        assert "{year}" in tmpl

    def test_seasonal(self):
        tmpl = _suggest_template(["season", "year"])
        assert tmpl is not None

    def test_no_groups(self):
        assert _suggest_template([]) is None


class TestScanQuarantine:
    def test_scans_pdfs(self, tmp_path):
        (tmp_path / "a.pdf").touch()
        (tmp_path / "b.pdf").touch()
        (tmp_path / "c.txt").touch()  # not a PDF
        result = _scan_quarantine(tmp_path)
        assert result == ["a.pdf", "b.pdf"]

    def test_excludes_report_file(self, tmp_path):
        (tmp_path / REPORT_FILENAME).touch()
        (tmp_path / "a.pdf").touch()
        result = _scan_quarantine(tmp_path)
        assert result == ["a.pdf"]

    def test_empty_dir(self, tmp_path):
        assert _scan_quarantine(tmp_path) == []

    def test_nonexistent_dir(self, tmp_path):
        assert _scan_quarantine(tmp_path / "nope") == []


class TestGenerateQuarantineReport:
    def test_creates_report_file(self, tmp_path):
        (tmp_path / "Science & Vie N1302 • Mars 2026.pdf").touch()
        (tmp_path / "Science & Vie N1303 • Avril 2026.pdf").touch()
        (tmp_path / "Random Unknown File.pdf").touch()

        result = generate_quarantine_report(tmp_path)
        assert result is not None
        assert result.exists()
        assert result.name == REPORT_FILENAME

        content = result.read_text(encoding="utf-8")
        assert "Quarantine Report" in content
        assert "Total quarantined files: 3" in content
        assert "Groups identified: 2" in content
        assert "Science & Vie" in content
        assert "--- YAML START ---" in content
        assert "--- YAML END ---" in content
        assert "date_groups:" in content

    def test_empty_quarantine(self, tmp_path):
        result = generate_quarantine_report(tmp_path)
        assert result is not None
        content = result.read_text(encoding="utf-8")
        assert "Total quarantined files: 0" in content
        assert "No quarantined files found" in content

    def test_nonexistent_dir(self, tmp_path):
        result = generate_quarantine_report(tmp_path / "nope")
        assert result is None

    def test_report_contains_yaml_pattern(self, tmp_path):
        (tmp_path / "Le Monde - 2026-03-15.pdf").touch()
        result = generate_quarantine_report(tmp_path)
        content = result.read_text(encoding="utf-8")
        assert 'pattern:' in content
        assert 'name:' in content

    def test_report_groups_similar_files(self, tmp_path):
        for month in ["Janvier", "Fevrier", "Mars", "Avril"]:
            (tmp_path / f"Mon Magazine N100 - {month} 2026.pdf").touch()
        (tmp_path / "Outlier File.pdf").touch()

        result = generate_quarantine_report(tmp_path)
        content = result.read_text(encoding="utf-8")
        assert "Groups identified: 2" in content
        # The 4-file group should appear first
        assert content.index("4 files") < content.index("1 file")

    def test_delete_suggestion_for_no_date_single_file(self, tmp_path):
        (tmp_path / "xr7q_something_weird.pdf").touch()
        result = generate_quarantine_report(tmp_path)
        content = result.read_text(encoding="utf-8")
        assert "delete: true" in content

    def test_report_overwrites_previous(self, tmp_path):
        (tmp_path / "file1.pdf").touch()
        generate_quarantine_report(tmp_path)
        (tmp_path / "file2.pdf").touch()
        generate_quarantine_report(tmp_path)
        content = (tmp_path / REPORT_FILENAME).read_text(encoding="utf-8")
        assert "Total quarantined files: 2" in content
