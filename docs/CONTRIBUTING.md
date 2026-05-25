# Contributing

Thank you for considering improving open-global-recipes! This guide covers adding recipes, normalizing ingredients, and reporting coverage gaps.

---

## Quick Ways to Help

### 1. Report a sparse country

Open an issue with:
- Country name
- Current recipe count (if known)
- Suggested open source where recipes could be found

### 2. Add missing data sources

Want to import a new open dataset?

1. Create a script in `scripts/import_<source>.py`
2. Follow the import pipeline contract:
   - Discover → Parse → Map → Validate → Deduplicate → Insert → Log
3. Update `docs/DATA_SOURCES.md`
4. Update `schema/001_schema.sql` if any new `data_sources` rows are required
5. Test locally:
   ```bash
   python3 scripts/import_<source>.py --db recipes.db --dry-run
   ```
6. Open a PR

### 3. Normalize ingredients

Many recipes only have `ingredients_raw` JSON and no `recipe_ingredients` rows.

```python
import sqlite3
conn = sqlite3.connect('recipes.db')
c = conn.cursor()

# Parse a raw ingredient line
c.execute("SELECT id, ingredients_raw FROM recipes LIMIT 5")
for rid, raw in c.fetchall():
    if not raw:
        continue
    import json
    for line in json.loads(raw):
        # Strip quantity, unit, insert into ingredients + recipe_ingredients
        pass
```

A full quantity-unit parser is on the roadmap. Contributions welcome.

### 4. Fix wrong-country assignments

Some recipes are clearly mis-assigned (e.g. "French Toast" in France). These are tracked in `docs/KNOWN_ISSUES.md`.

To fix:

```sql
-- Find candidates
SELECT r.id, r.title, c.name
FROM recipes r
JOIN countries c ON r.country_id = c.id
WHERE (r.title LIKE '%French Toast%' AND c.name = 'France');
```

Then either:
- Delete the row
- Reassign to `country_id = (SELECT id FROM countries WHERE name = 'United States of America')`

### 5. Improve BTD aliases

If you're running the BTD add-on and notice ingredients scoring as untagged that should match:

```sql
-- In btdiet.db
INSERT OR IGNORE INTO food_aliases (food_id, alias, alias_type)
VALUES ((SELECT id FROM foods WHERE canonical_name = 'peppers'), 'bell pepper', 'common');
```

Re-run `btd_scorer.py --backfill`.

---

## Development Setup

```bash
git clone https://github.com/drwjkirkpatrick-web/open-global-recipes.git
cd open-global-recipes
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt  # when available
```

---

## Code Style

- Python: PEP 8, type hints where helpful, docstrings for public functions
- SQL: lowercase keywords, snake_case identifiers
- Markdown: ATX headers (`#`), fenced code blocks, 80-ish line soft limit

---

## PR Checklist

- [ ] Script runs without errors on Python 3.10+
- [ ] Database integrity checks pass (`PRAGMA integrity_check`)
- [ ] New sources documented in `docs/DATA_SOURCES.md`
- [ ] New schema changes reflected in `schema/001_schema.sql`
- [ ] `.gitignore` updated if new artifacts are generated
- [ ] No raw recipe text is added without license confirmation

---

## License Reminder

All imported data must have a confirmed open license or fair-use justification.
Do not scrape sites with rate limits or Terms of Service prohibitions.
