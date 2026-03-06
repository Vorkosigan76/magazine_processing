# TODO

## Harmonize output filename templates

Currently 9 distinct template patterns across 189 magazines. A few outliers should be aligned:

### Outliers to fix

1. **China Today** (`{name} - {year}-{month}.pdf`) — drop the ` - ` to match the other 31 numeric monthlies: `{name} {year}-{month}.pdf`

2. **Daily Telegraph** (`{name} - {day_short} {month_name} {year}.pdf`) — switch to the default ISO daily format: `{name} - {date}.pdf`

3. **Micro Pratique** cross-year variant (`{name} {year}{month} - {month_range}.pdf`) — add trailing year to match the other 21 bimonthly magazines: `{name} {year}{month} - {month_range} {year}.pdf`

### Optional: unify daily formats

9 dailies (L'Equipe, Les Echos, Le Nouvel Economiste, etc.) use compact dates (`{name} - {year}{month}{day}.pdf` = `20260306`), while 59 dailies use ISO (`{name} - {date}.pdf` = `2026-03-06`). Could pick one for consistency. ISO is more readable; compact sorts identically.
