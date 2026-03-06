# Magazine Processing

A Dockerized Python application that monitors a folder for magazine PDFs, identifies them by filename pattern, renames them with a standardized format, and organizes them into folders.

## Example

Drop `lmnd06032026.pdf` into `./import/` and it will be moved to:
```
./processed/Le Monde/Le Monde - 2026-03-06.pdf
```

## Quick Start

```bash
docker compose up --build
```

This creates two local folders:
- `./import/` — drop PDFs here
- `./processed/` — organized output (subfolders per magazine)

## Adding a New Magazine

Edit `config/magazines.yaml` and add an entry:

```yaml
- name: "Magazine Display Name"
  pattern: "^prefix(\\d{2})(\\d{2})(\\d{4})\\.pdf$"
  date_groups: [day, month, year]
  template: "{name} - {date}.pdf"        # optional, this is the default
```

- **name**: the display name used for the folder and renamed file
- **pattern**: a regex matching the original filename, with capture groups for date components
- **date_groups**: an ordered list mapping each capture group to `day`, `month`, or `year`
- **template**: output filename format (optional). Available placeholders: `{name}`, `{date}` (YYYY-MM-DD), `{year}`, `{month}`, `{day}`, `{month_name}` (e.g. March)

Template examples by frequency:

| Frequency | Template | Result |
|---|---|---|
| Daily | `{name} - {date}.pdf` | Le Monde - 2026-03-06.pdf |
| Monthly | `{name} - {year}-{month}.pdf` | National Geographic - 2026-03.pdf |
| Monthly (named) | `{name} - {month_name} {year}.pdf` | Science & Vie - March 2026.pdf |

Restart the container after changes:
```bash
docker compose restart
```

## Running Without Docker

```bash
pip install -r requirements.txt
python -m app.main
```

When running locally, the app uses `/import` and `/processed` as absolute paths. You can test by creating those directories or adjusting the paths in `app/main.py`.

## How It Works

1. On startup, any PDFs already in `/import` are processed immediately
2. The app then watches `/import` for new files using `watchdog`
3. Each filename is matched against the regex patterns defined in `config/magazines.yaml`
4. On match, the date is extracted, the file is renamed using the magazine's output template, and moved to `/processed/<Magazine Name>/`
5. Unrecognized files are logged as warnings and left in place
6. Duplicate destinations (file already exists) are skipped
