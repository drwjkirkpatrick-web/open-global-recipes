#!/usr/bin/env python3
"""
Quality filter for dpapathanasiou/recipes imports.
Removes or flags false positives (e.g., French toast != French cuisine).
"""

import sqlite3
import json
import re

DB_PATH = "/home/walker/projects/global-recipe-db/recipes.db"

# Define quality rules per country
# block_patterns: if title matches any of these, recipe is likely false positive
RULES = {
    "France": {
        "block": [
            r"\bFrench\s+Toast\b",
            r"\bFrench\s+Fries?\b",
            r"\bFrench\s+75\b",  # cocktail - could keep but usually American bar
            r"\bFrench\s+Bread\s+Pizza\b",
            r"\bFrench\s+Bread\s+Pudding\b",
            r"\bFrench\s+Toast\b",  # redundant but safe
        ],
        "require": None,  # no required patterns
    },
    "Germany": {
        "block": [
            r"\bGerman\s+Chocolate\s+Cake\b",
            r"\bGerman\s+Chocolate\s+Cookie\b",
            r"\bGerman\s+Chocolate\s+Cupcake\b",
            r"\bGerman\s+Chocolate\s+Frosting\b",
            r"\bGerman\s+Chocolate\s+Cookie\b",
            r"\bWhite\s+German\s+Chocolate\b",
        ],
        "require": None,
    },
    "Spain": {
        "block": [
            r"\bSpanish\s+Rice\b",  # Mexican-American dish, not Spanish
        ],
        "require": None,
    },
    # Other countries can be added as needed
}


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def filter_country(conn, country_name):
    rules = RULES.get(country_name)
    if not rules:
        print(f"No rules for {country_name}, skipping")
        return 0

    c = conn.cursor()
    c.execute("SELECT id FROM countries WHERE name = ?", (country_name,))
    country_id = c.fetchone()
    if not country_id:
        print(f"Country not found: {country_name}")
        return 0
    country_id = country_id[0]

    c.execute("SELECT id, title FROM recipes WHERE country_id = ?", (country_id,))
    rows = c.fetchall()

    removed = 0
    kept = 0

    for recipe_id, title in rows:
        should_remove = False

        # Check block patterns
        for pattern in rules.get("block", []):
            if re.search(pattern, title, re.IGNORECASE):
                should_remove = True
                break

        if should_remove:
            c.execute("DELETE FROM recipes WHERE id = ?", (recipe_id,))
            removed += 1
        else:
            kept += 1

    conn.commit()
    print(f"[{country_name}] Removed: {removed}, Kept: {kept}")
    return removed


def main():
    conn = get_db()
    total_removed = 0
    for country in RULES:
        total_removed += filter_country(conn, country)

    # Update country status
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM recipes")
    total = c.fetchone()[0]
    print(f"\nTotal recipes in DB after filtering: {total}")

    conn.close()
    print(f"Total removed across all countries: {total_removed}")


if __name__ == "__main__":
    main()
