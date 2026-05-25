# Architecture Overview

## Design Goals

1. **Zero-dependency core** — SQLite + Python stdlib works on any machine.
2. **Modular imports** — Each source gets its own script; run only the ones you want.
3. **Optional BTD** — Blood Type Diet scoring is an add-on, not a requirement.
4. **Cron-friendly** — Daily curation script runs headless, outputs PDF or text.

---

## Schema

### countries
- 199 sovereign states + UN observers (Taiwan, Palestine, Vatican, Hong Kong, Macao, Kosovo)
- `cuisine_keywords` field for country inference from free-text sources
- `region` = Africa, Americas, Asia, Europe, Oceania

### data_sources
Provenance tracking for every imported dataset. Required fields:
- `name`, `url`, `license` (e.g. MIT, CC BY-SA)

### recipes
- `instructions` and `ingredients_raw` (JSON array) are the primary content fields
- No `description` column exists — use those fields instead
- `cuisine_tag` is free-form keywords (e.g., "Condiment/Spread,Sauce,Ginger")
- `raw_data_json` stores the full upstream record for auditability

### recipe_ingredients (optional normalization)
- `quantity`, `unit`, `raw_text` — populated by running ingredient normalization
- Many recipes still only have `ingredients_raw` JSON

### recipe_btd_scores (optional add-on)
- Created by `scripts/btd_scorer.py --init`
- Populated idempotently via `--backfill`
- 4 rows per recipe (one per blood type), expandable to 8 with non-secretor later

### import_logs
- Every import run writes here with counts and errors
- Used for data quality audits and source reconciliation

---

## Import Pipeline

Each script follows the same contract:

1. **Discover** — list index / API / CSV rows
2. **Parse** — extract title, ingredients, instructions
3. **Map** — infer `country_id` from keywords, tags, or title
4. **Validate** — require BOTH ingredients and instructions (skip stubs)
5. **Deduplicate** — optional placeholder for fuzzy title matching
6. **Insert** — batch insert with `source_id` → `data_sources`
7. **Log** — write `import_logs` entry

---

## Key Decisions

| Decision | Why |
|---|---|
| SQLite instead of PostgreSQL | Zero install, portable, single-file delivery |
| JSON `ingredients_raw` instead of full normalization | Normalization is hard and source-specific; raw JSON preserves provenance |
| No `description` column | Not available in upstream MIT dump; instructions are the content field |
| Country-based grouping (not cuisine) | Reliable join on `countries.id`; `cuisine_tag` is too noisy for grouping |
| BTD as add-on | Keeps core repo small and unencumbered; BTD is an opinionated extra |
| weasyprint for PDF (not fpdf2) | Unicode safety (em-dashes, non-ASCII, bullets) |

---

## Performance Notes

- Bulk import 78K JSON recipes via `executemany()` batches of 500: ~15 min on Jetson Orin Nano (ARM64)
- BTD backfill of 75K recipes × 4 blood types: ~30 min
- Daily curation SQL uses indexed `recipe_btd_scores(blood_type, verdict, score)` — subsecond

---

## Future Schema Changes

- `prep_time`, `cook_time`, `servings` columns (currently missing from all sources)
- `nutrition_json` column for USDA FoodData Central overlay
- `image_url` column if we add public-domain imagery
- `verified` boolean flag for human-reviewed recipes
