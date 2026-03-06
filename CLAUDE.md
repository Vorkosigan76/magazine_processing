# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A Dockerized Python application that monitors an `/import` folder for magazine PDFs, identifies them by filename pattern, renames them with a standardized format, and moves them to `/processed/<Magazine Name>/`.

Example: `lmnd06032026.pdf` -> `/processed/Le Monde/Le Monde - 2026-03-06.pdf`

## Commands

```bash
# Build and run
docker compose up --build

# Run locally (without Docker)
pip install -r requirements.txt
python -m app.main

# Run tests
python -m pytest tests/
```

## Architecture

- **`app/main.py`** — Entry point. Uses `watchdog` to monitor `/import` for new PDFs. Also processes any files already present on startup.
- **`app/processor.py`** — Core logic: loads magazine patterns from YAML config, matches filenames via regex, extracts dates, and moves files to the output directory.
- **`config/magazines.yaml`** — Magazine definitions. Each entry has a `name`, a `pattern` (regex with capture groups for date parts), `date_groups` mapping (ordered list of `day`/`month`/`year`), and an optional `template` for the output filename (placeholders: `{name}`, `{date}`, `{year}`, `{month}`, `{day}`, `{day_short}`, `{month_name}`; defaults to `{name} - {date}.pdf`).

## Adding a New Magazine

Add an entry to `config/magazines.yaml`:
```yaml
- name: "Magazine Display Name"
  pattern: "^prefix(\\d{2})(\\d{2})(\\d{4})\\.pdf$"
  date_groups: [day, month, year]
  template: "{name} - {date}.pdf"  # optional, default
```
The pattern must capture date components as groups. `date_groups` maps each group to `day`, `month`, `year`, `month_name`, `month_range`, `season`, or `year_short` (`day` is optional for monthlies; `month` defaults to January for year-only entries; `season` maps season names like "hiver"/"winter" to months). `template` controls the output filename. The config is mounted as a Docker volume so changes take effect on container restart. **Always keep entries in `magazines.yaml` sorted alphabetically by `name`.**

## Deleting Unwanted Magazines

Add an entry with `delete: true` to `config/magazines.yaml`:
```yaml
- name: "Unwanted Magazine"
  pattern: "^Unwanted.*\\.pdf$"
  delete: true
```
Matched files are automatically deleted from `/import`. No `date_groups` or `template` needed.

## Docker Volumes

| Container Path | Purpose |
|---|---|
| `/import` | Drop PDFs here for processing |
| `/processed` | Organized output (subfolders per magazine) |
| `/app/config` | Magazine pattern configuration |
