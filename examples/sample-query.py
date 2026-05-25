#!/usr/bin/env python3
"""Example: Query the database and print a random recipe."""
import sqlite3
import os
from pathlib import Path

DB = Path(os.environ.get("OPEN_GLOBAL_RECIPES_DB", "recipes.db"))

conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row
c = conn.cursor()

c.execute("""
    SELECT r.title, r.instructions, c.name as country
    FROM recipes r
    LEFT JOIN countries c ON r.country_id = c.id
    ORDER BY RANDOM()
    LIMIT 1
""")
row = c.fetchone()
if row:
    print(f"🍽  {row['title']}  ({row['country']})")
    print("  ", "=" * 50)
    steps = [s.strip() for s in str(row['instructions'] or '').split('\n\n') if s.strip()]
    for i, step in enumerate(steps, 1):
        print(f"  {i}. {step}")
else:
    print("No recipes found.")
conn.close()
