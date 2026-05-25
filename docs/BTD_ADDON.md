# Blood Type Diet Add-On

This add-on is **completely optional**. The core database works without it.

---

## What You Need

1. The BTD canonical food database (`btdiet.db`) — a separate SQLite file with foods, aliases, and ABO ratings.
2. The `btd_scorer.py` script in this repo.

---

## Installation

### 1. Obtain btdiet.db

The BTD food database is maintained in the `blood-type-diet` skill. You can:
- Build it from scratch using the skill's `scripts/load_seed.py`
- Ask someone who already has it to share a compressed SQL dump
- Use the data from dadamo.com under fair use for personal research

### 2. Set environment variable

```bash
export BTD_DIET_DB="/path/to/btdiet.db"
export OPEN_GLOBAL_RECIPES_DB="/path/to/recipes.db"
```

### 3. Initialize the score table

```bash
python3 scripts/btd_scorer.py --init
```

This creates `recipe_btd_scores` in your recipes.db.

### 4. Backfill scores (one-time)

```bash
python3 scripts/btd_scorer.py --backfill
```

Idempotent — re-running only scores recipes that don't already have rows.

---

## Scoring Algorithm

```python
score = int(((ben * 2 + neutral * 1 + avoid * -2 + untagged * 0) / total + 2) / 4 * 100)
```

Where:
- `ben` = count of beneficial ingredients
- `neutral` = count of neutral ingredients
- `avoid` = count of avoid ingredients
- `untagged` = ingredients that didn't match the BTD database

Verdict:
- **green** — zero avoid ingredients
- **yellow** — exactly 1 avoid, and at least 1 beneficial
- **mixed** — 1-2 avoid, no beneficial, or other edge case
- **red** — more than 2 avoid ingredients

---

## Ingredient Matching Heuristic

1. **Clean** — strip quantities, units, stopwords ("minced", "fresh", "chopped")
2. **Phrase candidates** — longest-ngram first (e.g. "red bell pepper" → "bell pepper" → "pepper")
3. **Exact alias** — compare against `food_aliases` table
4. **Token overlap** — longest matching phrase wins
5. **Untagged** — if nothing matches, ingredient is neutral for scoring purposes

**Accuracy:** ~25% exact match, ~60% partial match, ~15% untagged.

---

## Extending the Matcher

If an ingredient systematically mismatches (e.g. "bell pepper" matches "peppers" which is fine, but "jicama" is missing entirely):

```sql
-- In btdiet.db
INSERT INTO food_aliases (food_id, alias, alias_type)
SELECT id, 'jicama', 'common' FROM foods WHERE canonical_name = 'jicama';
```

Then re-run `btd_scorer.py --backfill`.

---

## Querying Scored Recipes

```bash
# Top 20 green recipes for Type B
python3 scripts/btd_query.py green B --limit 20

# Top 5 with full recipe
python3 scripts/btd_query.py top O --limit 5 --with-recipe

# Random 3 for meal planning
python3 scripts/btd_query.py any B --random --limit 3 --with-recipe
```

SQL if you want direct access:

```sql
-- Green Type B, sorted by score
SELECT r.title, rc.score
FROM recipes r
JOIN recipe_btd_scores rc ON r.id = rc.recipe_id
WHERE rc.blood_type = 'B'
  AND rc.verdict = 'green'
ORDER BY rc.score DESC
LIMIT 20;

-- Avoid-count drill-down
SELECT r.title, rc.avoid_count, rc.untagged_count
FROM recipes r
JOIN recipe_btd_scores rc ON r.id = rc.recipe_id
WHERE rc.blood_type = 'A'
  AND rc.verdict = 'red'
ORDER BY rc.avoid_count DESC
LIMIT 20;
```

---

## Gluten / Dairy / Oat Detection

`recipe_btd_scores` automatically flags:
- `gluten_conflict` — recipe contains a BTD food with `contains_gluten = 1`
- `dairy_conflict` — contains a food with `is_dairy = 1`
- `oat_conflict` — contains a food with `contains_oats = 1`

Note: `oat_conflict` is currently underpopulated in most BTD databases. Filter oat-free via ingredient subqueries instead.

---

## Database Size Impact

- Without BTD: `recipes.db` ~276 MB (75K recipes)
- With BTD: adds `recipe_btd_scores` index → ~+30 MB

---

## Troubleshooting

| Problem | Fix |
|---|---|
| "BTD database not found" | Set `BTD_DIET_DB` to the absolute path to `btdiet.db` |
| "No scorable ingredients" | Recipe has no `ingredients_raw`; rare for core dataset |
| Scores too low / all red | BTD alias coverage is thin for that cuisine; add aliases |
| `--backfill` takes hours | Normal for 75K recipes on ARM64; use `--batch 1000` to do it incrementally |
