# Data Sources

Every recipe imported into open-global-recipes goes through `data_sources` tracking to maintain provenance and license clarity.

---

## Primary Sources

### dpapathanasiou/recipes (GitHub)
- **License:** MIT
- **Records:** ~73,284 imported (~78K total in upstream)
- **Format:** JSON (one file per recipe)
- **Content:** Title, ingredients array, directions array, tags, source URL
- **Origin:** Scraped from Allrecipes, Epicurious, FoodNetwork
- **Notes:**
  - No explicit cuisine tags. Country inferred via title keywords → countries.cuisine_keywords.
  - ~92% default to USA (correct behavior — the corpus is mostly American crowd-pleasers).
  - Post-import reassignment script (`scripts/reassign_usa_recipes.py`) scans for international keywords and moves obvious mislabels.
- **Download:** https://github.com/dpapathanasiou/recipes
- **Import:** `python3 scripts/import_dpapathanasiou.py --db recipes.db`

### TheMealDB
- **License:** CC BY-SA-like / free
- **Records:** 472
- **Format:** JSON API
- **Content:** Meal name, thumbnail, category, area, ingredients+measures, instructions
- **Notes:**
  - Advertises ~195 areas, but most return zero meals. Only ~30 areas have actual data.
  - Area names are adjectives ("British", "Spanish", "Thai") mapped to country names.
  - Rate-limit: ~0.1s between API calls.
- **API:** https://www.themealdb.com/api.php
- **Import:** `python3 scripts/import_themealdb.py --db recipes.db`

### Wikibooks Cookbook
- **License:** CC BY-SA
- **Records:** 83
- **Format:** MediaWiki markdown
- **Content:** Ingredients section, procedure section, category metadata
- **Notes:**
  - Recipe pages use full parenthetical titles: `Cookbook:Yetsom_Shiro_(Ethiopian_Vegan_Chickpea_Stew)`.
  - Short titles often 404.
  - Alphabetic index pages are the best discovery mechanism.
- **URL:** https://en.wikibooks.org/wiki/Cookbook:Table_of_Contents
- **Import:** `python3 scripts/import_wikibooks.py --db recipes.db`

### world-wide-dishes (CSV)
- **License:** Unknown / assumed CC
- **Records:** 750
- **Format:** CSV with explicit country column
- **Content:** Dish name, ingredients list (comma-separated), often links to YouTube/blog
- **Notes:**
  - Heavy African coverage (Kenya +84, Algeria +84, South Africa +77, Nigeria +69).
  - Many rows lack full instructions; only links.
  - Good for country-gap filling where other sources are empty.
- **Import:** Manual CSV parse script (not yet automated)

---

## Secondary / Scraped Sources

### INLUS / Food.com (scraped gap-fill)
- **License:** Fair use / personal only
- **Records:** 20
- **Purpose:** Iceland targeted gap-fill (target was 30 recipes; 20 from INLUS + 10 from other sources = 30 achieved)
- **Notes:** Scraped for educational/research purposes.

### Hawaii Nutrition Center (CTAHR)
- **License:** None / fair use — University of Hawaiʻi extension
- **Records:** 8
- **Format:** Browser-rendered dynamic content
- **Notes:**
  - Filter to "Type: Recipes" only. "Type: Food" entries lack instructions.
  - Dynamic grid requires browser automation for discovery.
- **URL:** https://nutritioncenter.ctahr.hawaii.edu/

### blood-type-diet internal archive
- **License:** — (internal project data)
- **Records:** 674
- **Notes:** Recipes originally curated for BTD scoring; re-imported here for completeness.

### photo_import
- **License:** —
- **Records:** 1
- **Notes:** OCR pipeline test recipe.

---

## Deferred Sources

| Source | Why Deferred | Blocker |
|--------|-------------|---------|
| Food.com (Kaggle) | 180K+ recipes, rich tags | Requires Kaggle CLI + `~/.kaggle/kaggle.json` |
| RecipeNLG | 2.2M recipes | No cuisine tags; 2.3 GB CSV; needs keyword mining |
| Recipe1M+ | ~1M recipes | Heavy image focus; no cuisine tags |
| Allrecipes direct | Rich data | No public API; ToS prohibits scraping |
| USDA FoodData Central | Nutrition labels only | No recipe structure |

---

## License Summary

| Source | Code License | Data License | Commercial Use? |
|--------|-------------|--------------|-----------------|
| dpapathanasiou/recipes | MIT | MIT | Yes (attribution) |
| TheMealDB | — | CC BY-SA-like | Yes (attribution) |
| Wikibooks | — | CC BY-SA | Yes (share-alike) |
| world-wide-dishes | — | Unknown / CC assumed | Unknown — use with caution |
| Hawaii Nutrition Center | — | Fair use | No — personal only |
| INLUS / Food.com scrape | — | Fair use | No — personal only |
| blood-type-diet | — | Internal | — |

**Bottom line:** This database is for personal and research use only. Do not redistribute recipe text commercially without verifying per-source licenses.
