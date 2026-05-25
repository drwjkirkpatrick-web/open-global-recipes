# Known Issues

## Data Quality

### Sparse and Empty Countries

Out of 199 countries:
- **100 countries** have ≥ 5 recipes
- **37 countries** have &lt; 5 recipes (sparse)
- **63 countries** have zero recipes (empty)

**Top sparse:** Tanzania 2, Somalia 2, Nicaragua 2, Mozambique 2, Monaco 2, Malta 2, Laos 2, Guyana 2, Costa Rica 2, Burkina Faso 2, Bosnia and Herzegovina 2, Benin 2, Bangladesh 2, Angola 2

**Top empty:** Albania, Andorra, Antigua and Barbuda, Azerbaijan, Bahrain, Belarus, Bhutan, Botswana, Cabo Verde, Central African Republic, Comoros, Congo DRC, Cote d'Ivoire, Djibouti, Equatorial Guinea, Eritrea, Estonia, Eswatini, Gabon, Guinea-Bissau, Holy See, Iraq, Kiribati, North Korea, Kosovo, Kyrgyzstan, Lesotho, Libya, Liechtenstein, Luxembourg, Macao, Madagascar, Maldives, Mauritania, Mauritius, Micronesia, Moldova, Montenegro, Nauru, North Macedonia, Oman, Palau, Palestine, Panama, Papua New Guinea, Qatar, Saint Kitts and Nevis, Saint Lucia, Saint Vincent and the Grenadines, San Marino, Sao Tome and Principe, Seychelles, Sierra Leone, Slovenia, Solomon Islands, South Sudan, Suriname, Timor-Leste, Togo, Tonga, and 3 others.

**Mitigation:** Run source audits per the open-recipe-curation skill §9. Targeted web scraping is the last resort for microstates and conflict zones.

### Wrong-Country Recipes

Known false positives from keyword inference:
- "French Toast" / "French Fries" → assigned to France
- "German Chocolate Cake" → assigned to Germany
- "Spanish Rice" → assigned to Spain
- "Turkey" (the bird) → assigned to Turkey (the country)
- "Chili" (the pepper) → assigned to Chile

**Mitigation:** Post-import blocklists. See `scripts/quality_filter.py` and `references/country-cuisine-homonym-filter.md`.

### USA Bias

~61,036 recipes (81%) are United States. This is because the dpapathanasiou dump is ~92% American content. Keyword reassignment only recovered ~5,600. Other countries are not underrepresented — the corpus itself is America-centric.

**Mitigation:** Supplement with non-US sources (TheMealDB, Wikibooks, world-wide-dishes).

---

## Technical

### Unicode in PDFs

fpdf2 core fonts (Helvetica, Times, Courier) only support latin-1. Any non-ASCII characters (em-dashes, smart quotes, bullets, CJK, Arabic, Cyrillic) raise `FPDFUnicodeEncodingException`.

**Fix:** Use `weasyprint` for all PDF generation. It handles full Unicode.

### Missing Time / Servings Metadata

No `prep_time`, `cook_time`, or `servings` columns exist. None of the upstream sources reliably provide this.

**Mitigation:** Leave NULL or infer from recipe text if needed.

### No Description Column

The `recipes` table has no `description`. Use `instructions` or `ingredients_raw` instead.

### SQLite `sqlite_sequence` Table

`AUTOINCREMENT` creates a system table `sqlite_sequence`. It is harmless but appears in schema dumps. Ignore it.

### BTD `oat_conflict` Underpopulation

`recipe_btd_scores.oat_conflict` is currently all FALSE because the BTD `foods` table does not flag oat-containing foods reliably.

**Mitigation:** Filter oat-free via ingredient subqueries.

---

## Performance

### BTD Backfill on ARM64

75K recipes × 4 blood types takes ~30 minutes on Jetson Orin Nano (ARM64, 8 GB RAM). This is expected.

**Mitigation:** Use `--batch 1000` for incremental scoring.

### Large Database

`recipes.db` is 276 MB. GitHub file limit is 100 MB — the database cannot be stored in git.

**Mitigation:** Ship as a downloadable SQL dump or release artifact. See `README.md` under "Get the Database."

---

## Open Questions

- Should we add regional cuisines as pseudo-countries (Hawaii, Catalonia, Puerto Rico)? Currently done ad-hoc.
- Should Kaggle Food.com (180K recipes) be imported despite the auth barrier?
- Should RecipeNLG (2.2M recipes, no tags) be mined for keyword-country inference?
- Should we add user accounts for personal recipe collections?
