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
