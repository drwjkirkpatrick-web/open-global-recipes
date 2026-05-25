#!/usr/bin/env python3
"""
Query the global recipe DB for BTD-scored recipes.

Usage:
    python scripts/btd_query.py green O --limit 20       # Green/good for Type O
    python scripts/btd_query.py red O --limit 20           # Red/avoid for Type O
    python scripts/btd_query.py yellow O --limit 20        # Yellow/neutral for Type O
    python scripts/btd_query.py any O --limit 20           # Any verdict, sorted by score
    python scripts/btd_query.py top O --limit 5 --with-recipe   # Top 5 greens with full recipe
    python scripts/btd_query.py any B --random --limit 3  # 3 random for Type B
"""
import sqlite3
import json
import argparse
from pathlib import Path
import os

GR_DB = Path(os.environ.get("OPEN_GLOBAL_RECIPES_DB", "recipes.db"))


def query_recipes(bt, verdict, limit, random_select=False, with_recipe=False):
    if not GR_DB.exists():
        raise FileNotFoundError(f"Database not found: {GR_DB}\nSet OPEN_GLOBAL_RECIPES_DB")
    conn = sqlite3.connect(GR_DB)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    base_sql = """
        SELECT r.id, r.title, r.instructions, r.ingredients_raw, r.cuisine_tag,
               rc.score, rc.beneficial_count, rc.neutral_count, rc.avoid_count,
               rc.untagged_count, rc.gluten_conflict, rc.dairy_conflict, rc.verdict
        FROM recipes r
        JOIN recipe_btd_scores rc ON r.id = rc.recipe_id
        WHERE rc.blood_type = ?
    """
    params = [bt]
    if verdict != "any":
        base_sql += " AND rc.verdict = ?"
        params.append(verdict)

    base_sql += " ORDER BY " + ("RANDOM()" if random_select else "rc.score DESC")
    base_sql += " LIMIT ?"
    params.append(limit)

    c.execute(base_sql, tuple(params))
    rows = c.fetchall()

    for row in rows:
        print(f"\n{'='*50}")
        print(f"📋 {row['title']}")
        print(f"   Blood Type {bt} | Score: {row['score']}/100 | Verdict: {row['verdict'].upper()}")
        print(f"   ✅ {row['beneficial_count']} | 🟡 {row['neutral_count']} | 🔴 {row['avoid_count']} | ❓ {row['untagged_count']}")
        if row['gluten_conflict']:
            print("   ⚠️ Contains gluten")
        if row['dairy_conflict']:
            print("   ⚠️ Contains dairy")
        if row['cuisine_tag']:
            print(f"   Tags: {row['cuisine_tag']}")
        if with_recipe:
            print("\n   Ingredients:")
            try:
                ings = json.loads(row['ingredients_raw']) if row['ingredients_raw'] else []
                for ing in ings:
                    print(f"     - {ing}")
            except (json.JSONDecodeError, TypeError):
                print(f"     {row['ingredients_raw']}")
            print("\n   Instructions:")
            steps = [s.strip() for s in str(row['instructions'] or '').split('\n\n') if s.strip()]
            for i, step in enumerate(steps, 1):
                print(f"     {i}. {step}")
    conn.close()


def main():
    p = argparse.ArgumentParser(description="Query BTD-scored recipes")
    p.add_argument("verdict", choices=["green", "yellow", "red", "mixed", "any"])
    p.add_argument("blood_type", choices=["A", "B", "AB", "O"])
    p.add_argument("--limit", type=int, default=10)
    p.add_argument("--random", dest="random_select", action="store_true")
    p.add_argument("--with-recipe", action="store_true")
    args = p.parse_args()
    query_recipes(args.blood_type, args.verdict, args.limit,
                  args.random_select, args.with_recipe)


if __name__ == "__main__":
    main()
