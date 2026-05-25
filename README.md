# Open Global Recipes

A free, open-source recipe database for global cuisine — 75,000+ recipes from 137 countries, with optional Blood Type Diet (BTD) scoring and daily PDF curation.

**Live on:** https://github.com/drwjkirkpatrick-web/open-global-recipes

---

## What This Is

- **75,321 recipes** from open sources (MIT, CC BY-SA, and other permissive licenses)
- **137 countries** represented — from Afghanistan to Zambia
- **SQLite-based** — zero-dependency, runs anywhere Python 3 runs
- **Optional BTD add-on** — score any recipe for ABO blood type compatibility (beneficial / neutral / avoid)
- **Daily PDF generator** — cron-ready script to deliver a curated trio of recipes via Telegram, Discord, email, or local directory

**Not included in Git:** The actual `recipes.db` (276 MB) — see "Get the Database" below.

---

## Repository Layout

```
open-global-recipes/
├── README.md                 # This file
├── LICENSE                   # MIT (code), data provenance in docs/
├── .gitignore                # Ignores large DB files, exports, raw_data
├── .github/
│   └── workflows/
│       └── ci.yml            # Placeholder CI — tests schema integrity
├── schema/
│   └── 001_schema.sql        # Full SQLite schema + seed data (countries, data_sources)
├── scripts/
│   ├── import_dpapathanasiou.py       # Bulk import ~78K MIT-licensed dump
│   ├── import_themealdb.py            # TheMealDB area-by-area importer
│   ├── import_wikibooks.py            # Wikibooks Cookbook scraper
│   ├── btd_scorer.py                  # BTD scoring add-on (optional)
│   ├── btd_query.py                   # CLI for BTD-scored recipes
│   ├── query_export.py                # Country search, CSV/JSON/PDF export
│   └── daily_curation.py              # Daily 3-recipe PDF curation
├── docs/
│   ├── ARCHITECTURE.md                # Schema rationale, source decisions
│   ├── DATA_SOURCES.md                # Every source we imported, with license
│   ├── BTD_ADDON.md                   # How to enable blood-type scoring
│   ├── DAILY_CURATION.md              # Cron setup for PDF delivery
│   ├── CONTRIBUTING.md                # Add recipes, normalize, report gaps
│   └── KNOWN_ISSUES.md                # Sparse countries, unicode pitfalls
└── examples/
    ├── sample-query.py                # Python snippet for querying
    ├── sample-cron.sh                 # Daily cron example
    └── sample-pdf-output.txt          # What the daily PDF looks like
```

---

## Quick Start

### 1. Clone

```bash
git clone https://github.com/drwjkirkpatrick-web/open-global-recipes.git
cd open-global-recipes
```

### 2. Get the Database

The database is too large for Git. Download the latest dump:

```bash
# Option A: compressed SQL dump (~36 MB)
curl -L -o recipes.sql.gz https://github.com/drwjkirkpatrick-web/open-global-recipes/releases/download/v1.0.0/recipes.sql.gz
zcat recipes.sql.gz | sqlite3 recipes.db

# Option B: raw DB (if you have space)
curl -L -o recipes.db https://github.com/drwjkirkpatrick-web/open-global-recipes/releases/download/v1.0.0/recipes.db
```

### 3. Verify

```bash
sqlite3 recipes.db "SELECT COUNT(*) FROM recipes;"
# → 75321

sqlite3 recipes.db "SELECT name FROM countries WHERE id IN (SELECT country_id FROM recipes GROUP BY country_id) ORDER BY name LIMIT 10;"
# → Afghanistan, Algeria, Argentina, Australia, Austria, Bahamas, Bangladesh, Belarus, Belgium, Benin
```

### 4. Query

```bash
# List 10 Thai recipes
python3 scripts/query_export.py --country "Thailand" --limit 10

# Find recipes with lemongrass
python3 scripts/query_export.py --ingredient "lemongrass" --limit 10

# Pick one at random
python3 scripts/query_export.py --random

# Export a country to PDF
python3 scripts/query_export.py --pdf-book "Thailand"
```

**Note:** All scripts default to `~/projects/global-recipe-db/recipes.db` for historical convenience. Set `OPEN_GLOBAL_RECIPES_DB` to override:

```bash
export OPEN_GLOBAL_RECIPES_DB="$(pwd)/recipes.db"
python3 scripts/query_export.py --random
```

---

## Core Features

### Country Search & Export

| Flag | What it does |
|------|-------------|
| `--country "Japan"` | List recipes for a country |
| `--ingredient "ginger"` | Search normalized ingredient names |
| `--match-all "garlic,onion,tomato"` | Recipes containing ALL listed ingredients |
| `--random` | One random recipe with full details |
| `--id 42` | Full recipe by ID |
| `--export-csv "Mexico"` | Write `exports/Mexico_recipes.csv` |
| `--export-json "Mexico"` | Write `exports/Mexico_recipes.json` |
| `--pdf-book "Mexico"` | Styled PDF recipe book |

### Scripts are Modular

Every import script is independent. You can run just the sources you trust:

```bash
python3 scripts/import_themealdb.py --db recipes.db       # ~470 recipes
python3 scripts/import_wikibooks.py --db recipes.db       # ~80 recipes (slower, web rate-limits)
# dpapathanasiou_bulk is ~78K — see docs/DATA_SOURCES.md for download link
```

---

## Optional: Blood Type Diet Scoring

The BTD add-on is **completely optional**. The core database works without it.

### What It Does

For any recipe in the database, the scorer:
1. Parses each raw ingredient string
2. Matches it to canonical foods in a BTD food database
3. Computes a composite compatibility score (0–100) for each ABO blood type
4. Labels the recipe **green** (0 avoid ingredients), **yellow**, **red**, or **mixed**

### How to Enable

1. **Get the BTD food database** (separate project, not included here). See `docs/BTD_ADDON.md` for instructions.
2. **Set the BTD database path:**
   ```bash
   export BTD_DIET_DB="/path/to/btdiet.db"
   ```
3. **Initialize the score table:**
   ```bash
   python3 scripts/btd_scorer.py --init
   ```
4. **Backfill all recipes (one-time, ~30 minutes):**
   ```bash
   python3 scripts/btd_scorer.py --backfill
   ```
5. **Query:**
   ```bash
   python3 scripts/btd_query.py green B --limit 20
   python3 scripts/btd_query.py top O --limit 5 --with-recipe
   ```

See `docs/BTD_ADDON.md` for the full matching heuristic, alias expansion, and confidence levels.

---

## Daily PDF Curation

A cron-ready script picks **3 recipes from 3 different countries** each day and renders a styled PDF.

### Basic usage

```bash
python3 scripts/daily_curation.py --text     # Print to stdout
python3 scripts/daily_curation.py --pdf      # Write to exports/daily_<date>.pdf
```

### With BTD filtering

```bash
export BTD_BLOOD_TYPE=B
python3 scripts/daily_curation.py --pdf --blood-type B
```

### Cron setup (daily 8:00 AM PT)

```bash
# Add to crontab
crontab -e
0 8 * * * cd /path/to/open-global-recipes && python3 scripts/daily_curation.py --pdf --blood-type B >> /var/log/daily_recipes.log 2>&1
```

Or use Hermes cron:
```bash
hermes cronjob create --name "Daily Type B Recipes" \
  --schedule "0 8 * * *" \
  --script "python3 /path/to/open-global-recipes/scripts/daily_curation.py --pdf --blood-type B"
```

See `docs/DAILY_CURATION.md` for Telegram/Discord delivery, flag maps, and customization.

---

## Data Sources & Licenses

| Source | License | Recipes | Notes |
|--------|---------|---------|-------|
| dpapathanasiou/recipes | MIT | ~73,284 | Scraped Allrecipes/Epicurious. Keyword-inferred country. |
| world-wide-dishes | Unknown / CC | 750 | Explicit country fields. Heavy African coverage. |
| TheMealDB | CC BY-SA-like | 472 | Area-tagged; ~30 areas have data. |
| Wikibooks Cookbook | CC BY-SA | 83 | Manual scrape. Structured but thin. |
| Hawaii Nutrition Center | None / fair use | 8 | Filtered to actual "Recipes" type only. |
| INLUS / Food.com | Fair use | 20 | Iceland gap-fill. |
| blood-type-diet | — | 674 | Internal BTD recipes (separate project). |
| photo_import | — | 1 | OCR pipeline test. |

**All data is for personal use only.** Do not redistribute recipe text commercially.

See `docs/DATA_SOURCES.md` for full provenance and download instructions.

---

## Contributing

1. **Add a country** — check `schema/001_schema.sql` for the country list; PR with additions
2. **Import a new source** — write a script in `scripts/`, document it in `docs/DATA_SOURCES.md`
3. **Normalize ingredients** — the `recipe_ingredients` table is partially populated; help fill gaps
4. **Report sparse coverage** — open an issue for countries with < 5 recipes

See `docs/CONTRIBUTING.md` for the full workflow.

---

## Known Issues

- **Sparse countries:** 37 countries have < 5 recipes; 63 have zero. See `docs/KNOWN_ISSUES.md`
- **Unicode in PDFs:** fpdf2 core fonts only support latin-1. Use `weasyprint` for non-ASCII recipes.
- **Country inference errors:** ~92% of dpapathanasiou recipes default to USA. Post-import reassign scripts help, but bias remains.
- **BTD alias gaps:** Non-Western ingredients under-match. Add aliases to your BTD `food_aliases` table.

---

## Roadmap

- [ ] Kaggle Food.com import (180K+ recipes, requires API key)
- [ ] Full ingredient normalization pipeline (quantity + unit parsing)
- [ ] Web UI for browsing
- [ ] Weekly meal-plan PDF generator
- [ ] Nutrition data overlay (USDA FoodData Central?)
- [ ] RecipeNLG gap-fill (2.2M untagged recipes)

---

## License

Code in this repository is released under the **MIT License**.

Recipe data is compiled from multiple open sources with mixed licenses (MIT, CC BY-SA, and fair-use scraped content). See `docs/DATA_SOURCES.md` for per-source licensing. **Do not redistribute recipe text commercially without verifying source licenses.**

---

Made with curiosity and stomachs growling. Bon appetit.
