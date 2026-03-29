"""Tests for processor.py — covers French month abbreviations, seasons, year-only dates,
and sample filenames from each magazine group."""

import pytest
from pathlib import Path
from datetime import date
from unittest.mock import patch

from app.processor import (
    load_magazines,
    match_magazine,
    format_output_name,
    MONTH_NAMES,
    SEASONS,
    _parse_group,
)

CONFIG_PATH = Path(__file__).parent.parent / "config" / "magazines.yaml"


@pytest.fixture(scope="module")
def magazines():
    return load_magazines(CONFIG_PATH)


# ── French month abbreviations ──


class TestFrenchMonthAbbreviations:
    def test_fev(self):
        assert MONTH_NAMES["fev"] == 2

    def test_fev_accent(self):
        assert MONTH_NAMES["fév"] == 2

    def test_avr(self):
        assert MONTH_NAMES["avr"] == 4

    def test_juil(self):
        assert MONTH_NAMES["juil"] == 7

    def test_sept(self):
        assert MONTH_NAMES["sept"] == 9

    def test_aou(self):
        assert MONTH_NAMES["aou"] == 8

    def test_dec_accent(self):
        assert MONTH_NAMES["déc"] == 12

    def test_janv(self):
        assert MONTH_NAMES["janv"] == 1


# ── Seasons ──


class TestSeasons:
    def test_hiver(self):
        assert SEASONS["hiver"] == 1

    def test_winter(self):
        assert SEASONS["winter"] == 1

    def test_printemps(self):
        assert SEASONS["printemps"] == 4

    def test_ete(self):
        assert SEASONS["été"] == 7

    def test_automne(self):
        assert SEASONS["automne"] == 10

    def test_parse_group_season(self):
        key, val, extras = _parse_group("season", "Hiver")
        assert key == "month"
        assert val == 1


# ── German month names ──


class TestGermanMonths:
    def test_oktober(self):
        assert MONTH_NAMES["oktober"] == 10

    def test_dezember(self):
        assert MONTH_NAMES["dezember"] == 12

    def test_januar(self):
        assert MONTH_NAMES["januar"] == 1


# ── Year-only dates ──


class TestYearOnly:
    def test_air_traffic(self, magazines):
        result = match_magazine("Air Traffic Technology International - 2026.pdf", magazines)
        assert result is not None
        name, pub_date, template, _ = result
        assert name == "Air Traffic Technology International"
        assert pub_date == date(2026, 1, 1)

    def test_annonces_automobile(self, magazines):
        result = match_magazine("Annonces Automobile N382 • 2025.Pdf", magazines)
        assert result is not None
        name, pub_date, _, _ = result
        assert name == "Annonces Automobile"
        assert pub_date.year == 2025

    def test_whisky_magazine(self, magazines):
        result = match_magazine("Whisky Magazine N211 - 2026.pdf", magazines)
        assert result is not None
        name, pub_date, _, _ = result
        assert name == "Whisky Magazine"
        assert pub_date == date(2026, 1, 1)


# ── Season-based entries ──


class TestSeasonEntries:
    def test_programmez_hs(self, magazines):
        result = match_magazine("programmez! Hors-Serie N21 • Hiver 2026.pdf", magazines)
        assert result is not None
        name, pub_date, _, _ = result
        assert name == "Programmez! Hors-Serie"
        assert pub_date == date(2026, 1, 1)

    def test_whisky_advocate(self, magazines):
        result = match_magazine("Whisky Advocate Winter 2025.pdf", magazines)
        assert result is not None
        name, pub_date, _, _ = result
        assert name == "Whisky Advocate"
        assert pub_date == date(2025, 1, 1)

    def test_the_scientist(self, magazines):
        result = match_magazine("The Scientist – Winter 2025.pdf", magazines)
        assert result is not None
        name, pub_date, _, _ = result
        assert name == "The Scientist"
        assert pub_date == date(2025, 1, 1)

    def test_skieur_hs(self, magazines):
        result = match_magazine("Skieur magazine Hors-Serie N27 • Edition Hiver 2026.Pdf", magazines)
        assert result is not None
        name, pub_date, _, _ = result
        assert name == "Skieur Magazine Hors-Serie"
        assert pub_date == date(2026, 1, 1)


# ── Group 1: French monthly N### • Month Year ──


class TestGroup1FrenchMonthly:
    def test_science_et_vie(self, magazines):
        result = match_magazine("Science & Vie N1302 • Mars 2026.Pdf", magazines)
        assert result is not None
        name, pub_date, template, extra = result
        assert name == "Science & Vie"
        assert pub_date == date(2026, 3, 1)
        output = format_output_name(name, pub_date, template, "", extra)
        assert output == "Science & Vie 202603 - Mars 2026.pdf"

    def test_que_choisir(self, magazines):
        result = match_magazine("Que Choisir N655 • Mars 2026.Pdf", magazines)
        assert result is not None
        assert result[0] == "Que Choisir"

    def test_canard_pc(self, magazines):
        result = match_magazine("Canard PC N474 • Janvier 2026.pdf", magazines)
        assert result is not None
        assert result[0] == "Canard PC"

    def test_capital(self, magazines):
        result = match_magazine("Capital N414 • Mars 2026.pdf", magazines)
        assert result is not None
        name, pub_date, _, _ = result
        assert name == "Capital"
        assert pub_date.year == 2026
        assert pub_date.month == 3

    def test_data_news_with_day(self, magazines):
        result = match_magazine("Data News N4 • 1 Octobre 2025.Pdf", magazines)
        assert result is not None
        name, pub_date, _, _ = result
        assert name == "Data News"
        assert pub_date == date(2025, 10, 1)

    def test_investir_with_dayname(self, magazines):
        result = match_magazine("Investir N2708 • Samedi 29 Novembre 2025.Pdf", magazines)
        assert result is not None
        name, pub_date, _, _ = result
        assert name == "Investir"
        assert pub_date == date(2025, 11, 29)


# ── Group 2: French bimonthly ──


class TestGroup2Bimonthly:
    def test_alpes_magazine(self, magazines):
        result = match_magazine("Alpes Magazine N217 • Mars-Avril 2026.pdf", magazines)
        assert result is not None
        name, pub_date, template, extra = result
        assert name == "Alpes Magazine"
        assert pub_date == date(2026, 3, 1)
        output = format_output_name(name, pub_date, template, "", extra)
        assert output == "Alpes Magazine 202603 - Mars-Avril 2026.pdf"

    def test_picsou_magazine(self, magazines):
        result = match_magazine("Picsou Magazine N591 • Janvier-Fevrier 2026.pdf", magazines)
        assert result is not None
        assert result[0] == "Picsou Magazine"
        assert result[1] == date(2026, 1, 1)

    def test_sciences_avenir_hs(self, magazines):
        result = match_magazine("Sciences et Avenir Hors-Serie N224 • Jan-Fev-Mar 2026.Pdf", magazines)
        assert result is not None
        assert result[0] == "Sciences et Avenir Hors-Serie"


# ── Group 3: ISO monthly ──


class TestGroup3ISOMonthly:
    def test_ai_business(self, magazines):
        result = match_magazine("AI Business Magazine - 2026-01.pdf", magazines)
        assert result is not None
        name, pub_date, template, _ = result
        assert name == "AI Business Magazine"
        assert pub_date == date(2026, 1, 1)
        output = format_output_name(name, pub_date, template, "", {})
        assert output == "AI Business Magazine 2026-01.pdf"

    def test_combat_aircraft(self, magazines):
        result = match_magazine("Combat Aircraft - 2026-03.pdf", magazines)
        assert result is not None
        assert result[0] == "Combat Aircraft"


# ── Group 4: Compact monthly ──


class TestGroup4CompactMonthly:
    def test_alternatives_economiques(self, magazines):
        result = match_magazine("Alternatives Economiques - 202601.pdf", magazines)
        assert result is not None
        name, pub_date, _, _ = result
        assert name == "Alternatives Economiques"
        assert pub_date == date(2026, 1, 1)

    def test_national_geo_uk(self, magazines):
        result = match_magazine("National Geographic UK 202512.pdf", magazines)
        assert result is not None
        assert result[0] == "National Geographic UK"


# ── Group 5: German-style YYYY.MM.DD ──


class TestGroup5GermanStyle:
    def test_auto_bild(self, magazines):
        result = match_magazine("Auto Bild 2025.10.09.pdf", magazines)
        assert result is not None
        name, pub_date, _, _ = result
        assert name == "Auto Bild"
        assert pub_date == date(2025, 10, 9)

    def test_der_spiegel(self, magazines):
        result = match_magazine("Der Spiegel - 2025.10.10.pdf", magazines)
        assert result is not None
        assert result[0] == "Der Spiegel"
        assert result[1] == date(2025, 10, 10)


# ── Group 6: Compact daily ──


class TestGroup6CompactDaily:
    def test_apple_magazine(self, magazines):
        result = match_magazine("Apple Magazine N748 - 20260227.pdf", magazines)
        assert result is not None
        assert result[0] == "Apple Magazine"
        assert result[1] == date(2026, 2, 27)

    def test_die_welt(self, magazines):
        result = match_magazine("Die Welt - 20251212.pdf", magazines)
        assert result is not None
        assert result[0] == "Die Welt"

    def test_economist_usa(self, magazines):
        result = match_magazine("The Economist USA - 20260228.pdf", magazines)
        assert result is not None
        assert result[0] == "The Economist USA"


# ── Group 7: English text monthly ──


class TestGroup7EnglishMonthly:
    def test_pc_gamer_usa(self, magazines):
        result = match_magazine("PC Gamer USA - December 2025.pdf", magazines)
        assert result is not None
        name, pub_date, _, _ = result
        assert name == "PC Gamer USA"
        assert pub_date == date(2025, 12, 1)

    def test_stereo(self, magazines):
        result = match_magazine("Stereo - November 2025.pdf", magazines)
        assert result is not None
        assert result[0] == "Stereo"

    def test_pc_tricks_german_month(self, magazines):
        result = match_magazine("PC-Tricks, Tipps und Anleitungen - Oktober 2025.pdf", magazines)
        assert result is not None
        assert result[0] == "PC-Tricks Tipps und Anleitungen"
        assert result[1] == date(2025, 10, 1)


# ── Group 8: Weekly French ──


class TestGroup8WeeklyFrench:
    def test_courrier_international(self, magazines):
        result = match_magazine("Courrier International N1844 - 5 Mars 2026.pdf", magazines)
        assert result is not None
        assert result[0] == "Courrier International"
        assert result[1] == date(2026, 3, 5)

    def test_telerama(self, magazines):
        result = match_magazine("Telerama N3952 • 11 au 17 Octobre 2025.Pdf", magazines)
        assert result is not None
        assert result[0] == "Telerama"

    def test_handelsblatt_german(self, magazines):
        result = match_magazine("Handelsblatt N194 - 9 Oktober 2025.pdf", magazines)
        assert result is not None
        assert result[0] == "Handelsblatt"
        assert result[1] == date(2025, 10, 9)


# ── Group 9: Special patterns ──


class TestGroup9Special:
    def test_jeune_afrique(self, magazines):
        result = match_magazine("Jeune Afrique N3155 • 12-2025.pdf", magazines)
        assert result is not None
        assert result[0] == "Jeune Afrique"
        assert result[1] == date(2025, 12, 1)

    def test_planete_robots(self, magazines):
        result = match_magazine("Planete Robots N95 • 2026-01.pdf", magazines)
        assert result is not None
        assert result[0] == "Planete Robots"

    def test_modellfan(self, magazines):
        result = match_magazine("ModellFan - 2026.01.pdf", magazines)
        assert result is not None
        assert result[0] == "ModellFan"

    def test_silly_linguistics(self, magazines):
        result = match_magazine("Silly Linguistics N92.pdf", magazines)
        assert result is not None
        assert result[0] == "Silly Linguistics"


# ── Existing entries with Z: drive patterns ──


class TestZDrivePatterns:
    def test_le_monde_z(self, magazines):
        result = match_magazine("Le Monde • 20260210.pdf", magazines)
        assert result is not None
        assert result[0] == "Le Monde"
        assert result[1] == date(2026, 2, 10)

    def test_les_echos_z(self, magazines):
        result = match_magazine("Les Echos • 20260102.pdf", magazines)
        assert result is not None
        assert result[0] == "Les Echos"

    def test_ft_uk_z(self, magazines):
        result = match_magazine("FT UK 20260303.pdf", magazines)
        assert result is not None
        assert result[0] == "Financial Times UK"
        assert result[1] == date(2026, 3, 3)

    def test_ft_eu(self, magazines):
        result = match_magazine("FT EU 20260303.pdf", magazines)
        assert result is not None
        assert result[0] == "Financial Times EU"

    def test_economist_z(self, magazines):
        result = match_magazine("The Economist-2026-02-07.pdf", magazines)
        assert result is not None
        assert result[0] == "The Economist"
        assert result[1] == date(2026, 2, 7)

    def test_wsj_z(self, magazines):
        result = match_magazine("The Wall Street Journal 20251203.pdf", magazines)
        assert result is not None
        assert result[0] == "The Wall Street Journal"
        assert result[1] == date(2025, 12, 3)

    def test_newsweek_z(self, magazines):
        result = match_magazine("Newsweek 20260123.pdf", magazines)
        assert result is not None
        assert result[0] == "Newsweek"

    def test_china_daily_z(self, magazines):
        result = match_magazine("China Daily 2025-12-13.pdf", magazines)
        assert result is not None
        assert result[0] == "China Daily"

    def test_science_z(self, magazines):
        result = match_magazine("Science – 2026-01-08.pdf", magazines)
        assert result is not None
        assert result[0] == "Science"

    def test_scmp_z(self, magazines):
        result = match_magazine("South China Morning Post 20260129.pdf", magazines)
        assert result is not None
        assert result[0] == "South China Morning Post"

    def test_le_journal_mickey_z(self, magazines):
        result = match_magazine("Le Journal de Mickey N3826-3827 • 15 Oct 2025.Pdf", magazines)
        assert result is not None
        assert result[0] == "Le Journal de Mickey"

    def test_vocable_z(self, magazines):
        result = match_magazine("Vocable Anglais N917 • Janvier 2026.Pdf", magazines)
        assert result is not None
        assert result[0] == "Vocable Anglais"


# ── Existing patterns still work ──


class TestExistingPatternsUnbroken:
    def test_le_monde_lmnd(self, magazines):
        result = match_magazine("lmnd06032026.pdf", magazines)
        assert result is not None
        assert result[0] == "Le Monde"
        assert result[1] == date(2026, 3, 6)

    def test_le_monde_lmnd_short(self, magazines):
        result = match_magazine("lmnd060326.pdf", magazines)
        assert result is not None
        assert result[0] == "Le Monde"

    def test_lequipe(self, magazines):
        result = match_magazine("lequipe050326.pdf", magazines)
        assert result is not None
        assert result[0] == "L Equipe"

    def test_lequipe_eq_format(self, magazines):
        result = match_magazine("EQ12032026.pdf", magazines)
        assert result is not None
        name, pub_date, _, _ = result
        assert name == "L Equipe"
        assert pub_date == date(2026, 3, 12)

    def test_les_echos_compact(self, magazines):
        result = match_magazine("LesEchos05032026.pdf", magazines)
        assert result is not None
        assert result[0] == "Les Echos"

    def test_auto_plus_original(self, magazines):
        result = match_magazine("Auto Plus - 6 Mars 2026.pdf", magazines)
        assert result is not None
        assert result[0] == "Auto Plus"

    def test_economist_original(self, magazines):
        result = match_magazine("TEcon Web Edition 07_03_26.pdf", magazines)
        assert result is not None
        assert result[0] == "The Economist"

    def test_ft_uk_original(self, magazines):
        result = match_magazine("FT UK.pdf", magazines)
        assert result is not None
        assert result[0] == "Financial Times UK"

    def test_liberation(self, magazines):
        result = match_magazine("lib050326.pdf", magazines)
        assert result is not None
        assert result[0] == "Liberation"

    def test_sante_magazine_original(self, magazines):
        result = match_magazine("Santé Magazine - Avril 2026.pdf", magazines)
        assert result is not None
        assert result[0] == "Sante Magazine"


# ── New magazines ──


class TestNewMagazines:
    def test_air_force_times(self, magazines):
        result = match_magazine("Air Force Times – Vol. 87, Issue 2, March 2026.pdf", magazines)
        assert result is not None
        name, pub_date, template, _ = result
        assert name == "Air Force Times"
        assert pub_date == date(2026, 3, 1)
        output = format_output_name(name, pub_date, template, "", {})
        assert output == "Air Force Times 2026-03.pdf"

    def test_fou_de_patisserie(self, magazines):
        result = match_magazine("Fou de Patisserie N75 • Mars-Avril 2026.pdf", magazines)
        assert result is not None
        name, pub_date, _, _ = result
        assert name == "Fou de Patisserie"
        assert pub_date == date(2026, 3, 1)

    def test_mon_air_fryer(self, magazines):
        result = match_magazine("Mon Air Fryer N11 • Mars-Avril 2026.pdf", magazines)
        assert result is not None
        name, pub_date, _, _ = result
        assert name == "Mon Air Fryer"
        assert pub_date == date(2026, 3, 1)

    def test_the_american_scholar(self, magazines):
        result = match_magazine("The American Scholar – Spring 2026.pdf", magazines)
        assert result is not None
        name, pub_date, _, _ = result
        assert name == "The American Scholar"
        assert pub_date == date(2026, 4, 1)

    def test_the_guardian_uk(self, magazines):
        result = match_magazine("The Guardian UK_1003.pdf", magazines)
        assert result is not None
        name, pub_date, _, _ = result
        assert name == "The Guardian UK"
        assert pub_date.month == 3
        assert pub_date.day == 10

    def test_vtt_mag(self, magazines):
        result = match_magazine("VTT Mag - avril-mai 2026.pdf", magazines)
        assert result is not None
        name, pub_date, _, _ = result
        assert name == "VTT Mag"
        assert pub_date == date(2026, 4, 1)

    def test_world_air_news(self, magazines):
        result = match_magazine("World Air News – Vol. 54 Issue 01 March 2026.pdf", magazines)
        assert result is not None
        name, pub_date, _, _ = result
        assert name == "World Air News"
        assert pub_date == date(2026, 3, 1)

    def test_world_soccer(self, magazines):
        result = match_magazine("World Soccer_Feb 2026.pdf", magazines)
        assert result is not None
        name, pub_date, _, _ = result
        assert name == "World Soccer"
        assert pub_date == date(2026, 2, 1)


# ── Additional patterns for existing magazines ──


class TestAdditionalPatterns:
    def test_boston_globe_ddmm(self, magazines):
        result = match_magazine("Boston Globe_0203.pdf", magazines)
        assert result is not None
        name, pub_date, _, _ = result
        assert name == "Boston Globe"
        assert pub_date.day == 2
        assert pub_date.month == 3

    def test_aujourdhui_with_timestamp(self, magazines):
        result = match_magazine("Aujourd hui en France • Vendredi 6 Mars 2026_260306_043349.pdf", magazines)
        assert result is not None
        name, pub_date, _, _ = result
        assert name == "Aujourd'hui en France"
        assert pub_date == date(2026, 3, 6)

    def test_ft_eu_tp_format(self, magazines):
        result = match_magazine("FT EU 06-03-2026.pdf", magazines)
        assert result is not None
        name, pub_date, _, _ = result
        assert name == "Financial Times EU"
        assert pub_date == date(2026, 3, 6)

    def test_ft_us_tp_format(self, magazines):
        result = match_magazine("FT US 06-03-2026.pdf", magazines)
        assert result is not None
        name, pub_date, _, _ = result
        assert name == "Financial Times US"
        assert pub_date == date(2026, 3, 6)

    def test_ideal_home_uk_text_month(self, magazines):
        result = match_magazine("Ideal Home UK – March 2026.pdf", magazines)
        assert result is not None
        name, pub_date, _, _ = result
        assert name == "Ideal Home UK"
        assert pub_date == date(2026, 3, 1)

    def test_le_figaro_with_timestamp(self, magazines):
        result = match_magazine("Le Figaro • Mardi 10 Mars 2026_260310_043349.pdf", magazines)
        assert result is not None
        name, pub_date, _, _ = result
        assert name == "Le Figaro"
        assert pub_date == date(2026, 3, 10)

    def test_le_figaro_sport_tp(self, magazines):
        result = match_magazine("Le Figaro Sport - 06-03-2026 - TP.pdf", magazines)
        assert result is not None
        name, pub_date, _, _ = result
        assert name == "Le Figaro Sport"
        assert pub_date == date(2026, 3, 6)

    def test_lequipe_with_timestamp(self, magazines):
        result = match_magazine("lequipe050326_260305_043349.pdf", magazines)
        assert result is not None
        name, pub_date, _, _ = result
        assert name == "L Equipe"
        assert pub_date == date(2026, 3, 5)

    def test_les_echos_tp(self, magazines):
        result = match_magazine("Les Echos - 06-03-2026 - TP.pdf", magazines)
        assert result is not None
        name, pub_date, _, _ = result
        assert name == "Les Echos"
        assert pub_date == date(2026, 3, 6)

    def test_les_echos_with_timestamp(self, magazines):
        result = match_magazine("Les Echos • Lundi 9 Mars 2026_260309_043349.pdf", magazines)
        assert result is not None
        name, pub_date, _, _ = result
        assert name == "Les Echos"
        assert pub_date == date(2026, 3, 9)

    def test_liberation_tp(self, magazines):
        result = match_magazine("Libération - 06-03-2026 - TP.pdf", magazines)
        assert result is not None
        name, pub_date, _, _ = result
        assert name == "Liberation"
        assert pub_date == date(2026, 3, 6)

    def test_liberation_with_timestamp(self, magazines):
        result = match_magazine("Liberation • Vendredi 6 Mars 2026_260306_043349.pdf", magazines)
        assert result is not None
        name, pub_date, _, _ = result
        assert name == "Liberation"
        assert pub_date == date(2026, 3, 6)

    def test_spirou_tp(self, magazines):
        result = match_magazine("Spirou - 06-03-2026 - TP.pdf", magazines)
        assert result is not None
        name, pub_date, _, _ = result
        assert name == "Le Journal de Spirou"
        assert pub_date == date(2026, 3, 6)

    def test_whisky_advocate_dash(self, magazines):
        result = match_magazine("Whisky Advocate – Spring 2026.pdf", magazines)
        assert result is not None
        name, pub_date, _, _ = result
        assert name == "Whisky Advocate"
        assert pub_date == date(2026, 4, 1)


# ── TP suffix stripping in process_file ──


class TestTPSuffixStripping:
    """Test that process_file strips ' - TP' suffix before matching."""

    def test_tp_suffix_stripped_and_matched(self, magazines, tmp_path):
        from app.processor import process_file

        import_dir = tmp_path / "import"
        import_dir.mkdir()
        output_dir = tmp_path / "processed"
        output_dir.mkdir()
        quarantine_dir = tmp_path / "quarantine"

        # Create a file with TP suffix
        tp_file = import_dir / "Newsweek EU - 20-03-2026 - TP.pdf"
        tp_file.write_bytes(b"%PDF-fake")

        result = process_file(tp_file, magazines, output_dir, quarantine_dir)
        assert result is True

        dest = output_dir / "Newsweek EU" / "Newsweek EU - 2026-03-20.pdf"
        assert dest.exists()

    def test_tp_suffix_case_insensitive(self, magazines, tmp_path):
        from app.processor import process_file

        import_dir = tmp_path / "import"
        import_dir.mkdir()
        output_dir = tmp_path / "processed"
        output_dir.mkdir()
        quarantine_dir = tmp_path / "quarantine"

        tp_file = import_dir / "Newsweek EU - 20-03-2026 - tp.pdf"
        tp_file.write_bytes(b"%PDF-fake")

        result = process_file(tp_file, magazines, output_dir, quarantine_dir)
        assert result is True


# ── Flag emoji prefix stripping in process_file ──


class TestFlagPrefixStripping:
    """Test that process_file strips country flag emoji prefixes."""

    def test_flag_prefix_stripped_and_matched(self, magazines, tmp_path):
        from app.processor import process_file

        import_dir = tmp_path / "import"
        import_dir.mkdir()
        output_dir = tmp_path / "processed"
        output_dir.mkdir()
        quarantine_dir = tmp_path / "quarantine"

        flag_file = import_dir / "🇰🇼 Newsweek EU - 20-03-2026.pdf"
        flag_file.write_bytes(b"%PDF-fake")

        result = process_file(flag_file, magazines, output_dir, quarantine_dir)
        assert result is True

        dest = output_dir / "Newsweek EU" / "Newsweek EU - 2026-03-20.pdf"
        assert dest.exists()


# ── Duplicate suffix stripping in process_file ──


class TestDuplicateSuffixStripping:
    """Test that process_file handles browser duplicate suffixes like (1), (2)."""

    def test_duplicate_suffix_no_space(self, magazines, tmp_path):
        """Capital(1).pdf -> Capital.pdf (no space before parenthesis)."""
        from app.processor import process_file

        import_dir = tmp_path / "import"
        import_dir.mkdir()
        output_dir = tmp_path / "processed"
        output_dir.mkdir()
        quarantine_dir = tmp_path / "quarantine"

        # Create a file with (1) suffix but no space
        dup_file = import_dir / "Newsweek EU - 20-03-2026(1).pdf"
        dup_file.write_bytes(b"%PDF-fake")

        result = process_file(dup_file, magazines, output_dir, quarantine_dir)
        assert result is True

        dest = output_dir / "Newsweek EU" / "Newsweek EU - 2026-03-20.pdf"
        assert dest.exists()
        # Original (1) file should no longer exist
        assert not dup_file.exists()

    def test_duplicate_suffix_with_space(self, magazines, tmp_path):
        """Capital (1).pdf -> Capital.pdf (space before parenthesis)."""
        from app.processor import process_file

        import_dir = tmp_path / "import"
        import_dir.mkdir()
        output_dir = tmp_path / "processed"
        output_dir.mkdir()
        quarantine_dir = tmp_path / "quarantine"

        # Create a file with " (1)" suffix (browser-style duplicate)
        dup_file = import_dir / "Newsweek EU - 20-03-2026 (1).pdf"
        dup_file.write_bytes(b"%PDF-fake")

        result = process_file(dup_file, magazines, output_dir, quarantine_dir)
        assert result is True

        dest = output_dir / "Newsweek EU" / "Newsweek EU - 2026-03-20.pdf"
        assert dest.exists()
        # Original " (1)" file should no longer exist
        assert not dup_file.exists()

    def test_duplicate_suffix_deleted_when_original_exists(self, magazines, tmp_path):
        """If original file exists, the (1) duplicate is deleted."""
        from app.processor import process_file

        import_dir = tmp_path / "import"
        import_dir.mkdir()
        output_dir = tmp_path / "processed"
        output_dir.mkdir()
        quarantine_dir = tmp_path / "quarantine"

        # Create both the original and duplicate
        original_file = import_dir / "Newsweek EU - 20-03-2026.pdf"
        original_file.write_bytes(b"%PDF-original")
        dup_file = import_dir / "Newsweek EU - 20-03-2026 (1).pdf"
        dup_file.write_bytes(b"%PDF-duplicate")

        result = process_file(dup_file, magazines, output_dir, quarantine_dir)
        assert result is False  # duplicate was deleted, not processed

        # Duplicate should be gone, original untouched
        assert not dup_file.exists()
        assert original_file.exists()


# ── Near-duplicate detection (same size) ──


class TestNearDuplicateDetection:
    def test_near_duplicate_blocked_same_size(self, magazines, tmp_path):
        """If a file with the same size exists in destination, incoming file is deleted."""
        from app.processor import process_file

        import_dir = tmp_path / "import"
        import_dir.mkdir()
        output_dir = tmp_path / "processed"
        output_dir.mkdir()
        quarantine_dir = tmp_path / "quarantine"

        # Create existing file in destination
        dest_dir = output_dir / "Le Monde"
        dest_dir.mkdir()
        existing_file = dest_dir / "Le Monde - 20260305.pdf"
        existing_file.write_bytes(b"%PDF-1234567890")  # 18 bytes

        # Create incoming file with same size but different date
        incoming_file = import_dir / "lmnd06032026.pdf"  # Will parse as 2026-03-06
        incoming_file.write_bytes(b"%PDF-1234567890")  # Same 18 bytes

        result = process_file(incoming_file, magazines, output_dir, quarantine_dir)
        assert result is False  # Near-duplicate detected, file deleted

        # Incoming file should be deleted
        assert not incoming_file.exists()
        # Existing file should remain
        assert existing_file.exists()
        # No new file should be created
        new_file = dest_dir / "Le Monde - 20260306.pdf"
        assert not new_file.exists()

    def test_different_size_passes(self, magazines, tmp_path):
        """If existing file has different size, incoming file is processed normally."""
        from app.processor import process_file

        import_dir = tmp_path / "import"
        import_dir.mkdir()
        output_dir = tmp_path / "processed"
        output_dir.mkdir()
        quarantine_dir = tmp_path / "quarantine"

        # Create existing file in destination with different size
        dest_dir = output_dir / "Le Monde"
        dest_dir.mkdir()
        existing_file = dest_dir / "Le Monde - 20260305.pdf"
        existing_file.write_bytes(b"%PDF-short")  # 10 bytes

        # Create incoming file with different size
        incoming_file = import_dir / "lmnd06032026.pdf"
        incoming_file.write_bytes(b"%PDF-much-longer-content")  # 24 bytes

        result = process_file(incoming_file, magazines, output_dir, quarantine_dir)
        assert result is True  # Different size, should be processed

        new_file = dest_dir / "Le Monde - 20260306.pdf"
        assert new_file.exists()

    def test_exact_duplicate_still_works(self, magazines, tmp_path):
        """Exact same destination filename still triggers the original duplicate check."""
        from app.processor import process_file

        import_dir = tmp_path / "import"
        import_dir.mkdir()
        output_dir = tmp_path / "processed"
        output_dir.mkdir()
        quarantine_dir = tmp_path / "quarantine"

        # Create existing file at exact destination path
        dest_dir = output_dir / "Le Monde"
        dest_dir.mkdir()
        existing_file = dest_dir / "Le Monde - 20260306.pdf"
        existing_file.write_bytes(b"%PDF-existing")

        # Create incoming file that will produce the same destination name
        incoming_file = import_dir / "lmnd06032026.pdf"
        incoming_file.write_bytes(b"%PDF-incoming-different-size")

        result = process_file(incoming_file, magazines, output_dir, quarantine_dir)
        assert result is False  # Exact duplicate detected

        assert not incoming_file.exists()
        assert existing_file.exists()
