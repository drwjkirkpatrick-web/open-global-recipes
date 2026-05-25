#!/usr/bin/env python3
"""
Blood Type Diet compatibility scorer for the global recipe database.

Optional add-on. Connects to the global recipes.db and a BTD btdiet.db,
parses raw ingredient strings, matches each to canonical foods in the BTD
database, and writes per-recipe, per-blood-type compatibility scores into
recipe_btd_scores.

Usage:
    python scripts/btd_scorer.py --init          # Add recipe_btd_scores table
    python scripts/btd_scorer.py --batch 1000      # Score first 1000 unprocessed
    python scripts/btd_scorer.py --recipe 42 --bt O # Score single recipe for one BT
    python scripts/btd_scorer.py --backfill        # Score ALL unprocessed (hours)
    python scripts/btd_scorer.py --stats           # Show coverage stats

Environment:
    OPEN_GLOBAL_RECIPES_DB  - Path to recipes.db (default: local path)
    BTD_DIET_DB             - Path to btdiet.db (default: ~/.hermes/skills/...)
"""

import sqlite3
import os
import re
import json
import argparse
from pathlib import Path

# Paths ------------------------------------------------------------------
GR_DB = Path(os.environ.get(
    "OPEN_GLOBAL_RECIPES_DB",
    "recipes.db"
))
BTD_DB = Path(os.environ.get(
    "BTD_DIET_DB",
    os.path.expanduser("~/.hermes/skills/blood-type-diet/data/btdiet.db")
))

STOPWORDS = {
    "and", "the", "with", "finely", "chopped", "minced", "sliced", "diced",
    "fresh", "dried", "canned", "ground", "powdered", "whole", "small",
    "large", "medium", "pound", "pounds", "ounce", "ounces", "cup", "cups",
    "tablespoon", "tablespoons", "teaspoon", "teaspoons", "ml", "g", "kg",
    "pieces", "sticks", "cloves", "sprigs", "leaves", "bunch", "optional",
    "garnish", "to", "taste", "or", "as", "needed", "about", "approximately",
    "plus", "more", "thinly", "thickly", "roughly", "coarsely", "drained",
    "rinsed", "peeled", "seeded", "cored", "boneless", "skinless",
    "cooked", "raw", "frozen", "thawed", "pitted", "halved", "quartered",
}

EXTRACT_RE = re.compile(
    r'(?i)\b(\d+\/\d+|\d+\.\d+|\d+\s*[\u00bd\u00bc\u00be\u2153\u2154\u215b\u215c\u215d\u215e])?\s*'
    r'(oz\b|ounces?|pounds?|lb\b|cups?|tbsps?|tablespoons?|tsps?|teaspoons?|ml|g|kg)\.?\s*'
    r'(.+)'
)


def _canonicalize(name: str) -> str:
    name = name.strip().lower()
    name = re.sub(r'^[\d\s\u00bd\u00bc\u00be\u2153\u2154\u215b\u215c\u215d\u215e./-]+', '', name)
    name = re.sub(r'^(oz|ounces?|pounds?|lbs?|cups?|tbsps?|tablespoons?|tsps?|teaspoons?|ml|g|kg|pkg|pkgs|packages?|cans?|bottles?|jars?)s?\b\.?\s*', '', name)
    name = re.sub(r'\([^)]*\)', '', name)
    name = re.sub(r'\s+', ' ', name).strip()
    return name


def _extract_food_candidates(raw: str) -> list:
    clean = _canonicalize(raw)
    words = [w for w in clean.split() if w and w not in STOPWORDS]
    candidates = []
    for wlen in range(len(words), 0, -1):
        for start in range(len(words) - wlen + 1):
            phrase = " ".join(words[start:start + wlen])
            if len(phrase) >= 2:
                candidates.append(phrase)
    if clean:
        candidates.append(clean)
    return candidates


def load_btd_index(bt_conn):
    cur = bt_conn.cursor()
    cur.execute("""
        SELECT f.id, f.canonical_name, f.contains_gluten, f.contains_oats, f.is_dairy,
               r.blood_type, r.secretor_status, r.rating, r.frequency
        FROM foods f
        JOIN ratings r ON f.id = r.food_id
    """)
    rows = cur.fetchall()
    food_meta = {}
    for row in rows:
        fid, cname, gl, oats, dairy, bt, sec, rating, freq = row
        if fid not in food_meta:
            food_meta[fid] = {
                "canonical_name": cname,
                "gluten": bool(gl), "oats": bool(oats), "dairy": bool(dairy),
            }
        food_meta[fid].setdefault(bt, {})[sec] = {"rating": rating, "frequency": freq}
    return food_meta


def build_alias_index(bt_conn):
    cur = bt_conn.cursor()
    cur.execute("SELECT food_id, alias FROM food_aliases")
    alias_map = {}
    for fid, alias in cur.fetchall():
        alias_map[alias.lower()] = fid
    return alias_map


def get_ingredients_for_recipe(gr_conn, recipe_id):
    cur = gr_conn.cursor()
    # Prefer normalized rows
    cur.execute("""
        SELECT ri.raw_text, i.normalized_name
        FROM recipe_ingredients ri
        LEFT JOIN ingredients i ON ri.ingredient_id = i.id
        WHERE ri.recipe_id = ?
    """, (recipe_id,))
    rows = cur.fetchall()
    if rows:
        return [r[1] or r[0] for r in rows]
    # Fallback to JSON
    cur.execute("SELECT ingredients_raw FROM recipes WHERE id = ?", (recipe_id,))
    row = cur.fetchone()
    if row and row[0]:
        try:
            return json.loads(row[0])
        except json.JSONDecodeError:
            return [row[0]]
    return []


def score_recipe(ingredients, food_meta, alias_map, blood_type, secretor='secretor'):
    ben = neutral = avoid = untagged = 0
    gluten = oats = dairy = False
    matched = {}
    for raw in ingredients:
        if not raw:
            continue
        raw_clean = _canonicalize(raw)
        # Exact alias match
        fid = alias_map.get(raw_clean)
        if not fid:
            # Token overlap
            cands = _extract_food_candidates(raw)
            best_fid = None
            best_score = 0
            for cand in cands:
                if cand in alias_map:
                    fid2 = alias_map[cand]
                    sc = len(cand)
                    if sc > best_score:
                        best_score = sc
                        best_fid = fid2
            fid = best_fid
        if not fid:
            untagged += 1
            continue
        meta = food_meta.get(fid)
        if not meta:
            untagged += 1
            continue
        if meta.get('gluten'):
            gluten = True
        if meta.get('oats'):
            oats = True
        if meta.get('dairy'):
            dairy = True
        rating_info = meta.get(blood_type, {}).get(secretor)
        if not rating_info:
            untagged += 1
            continue
        rating = rating_info['rating']
        if rating == 'beneficial':
            ben += 1
        elif rating == 'neutral':
            neutral += 1
        elif rating == 'avoid':
            avoid += 1
        else:
            untagged += 1
    total = ben + neutral + avoid + untagged
    if total == 0:
        return None
    score = int(((ben * 2 + neutral * 1 + avoid * -2 + untagged * 0) / total + 2) / 4 * 100)
    if avoid == 0:
        verdict = 'green'
    elif avoid <= 1 and ben >= 1:
        verdict = 'yellow'
    elif avoid > 2:
        verdict = 'red'
    else:
        verdict = 'mixed'
    return {
        'score': score, 'beneficial_count': ben, 'neutral_count': neutral,
        'avoid_count': avoid, 'untagged_count': untagged,
        'gluten_conflict': gluten, 'oat_conflict': oats, 'dairy_conflict': dairy,
        'verdict': verdict,
    }


def init_table(gr_conn):
    cur = gr_conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS recipe_btd_scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recipe_id INTEGER NOT NULL REFERENCES recipes(id) ON DELETE CASCADE,
            blood_type TEXT NOT NULL CHECK(blood_type IN ('A','B','AB','O')),
            secretor_status TEXT DEFAULT 'secretor' CHECK(secretor_status IN ('secretor','non_secretor')),
            score INTEGER,
            beneficial_count INTEGER DEFAULT 0,
            neutral_count INTEGER DEFAULT 0,
            avoid_count INTEGER DEFAULT 0,
            untagged_count INTEGER DEFAULT 0,
            gluten_conflict BOOLEAN DEFAULT 0,
            oat_conflict BOOLEAN DEFAULT 0,
            dairy_conflict BOOLEAN DEFAULT 0,
            verdict TEXT,
            computed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(recipe_id, blood_type, secretor_status)
        )
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_btd_scores_recipe ON recipe_btd_scores(recipe_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_btd_scores_query ON recipe_btd_scores(blood_type, verdict, score)")
    gr_conn.commit()
    print("recipe_btd_scores table initialized.")


def score_single(gr_conn, bt_conn, recipe_id, blood_type, secretor='secretor'):
    food_meta = load_btd_index(bt_conn)
    alias_map = build_alias_index(bt_conn)
    ingredients = get_ingredients_for_recipe(gr_conn, recipe_id)
    result = score_recipe(ingredients, food_meta, alias_map, blood_type, secretor)
    if not result:
        print("No scorable ingredients.")
        return
    cur = gr_conn.cursor()
    cur.execute("""
        INSERT INTO recipe_btd_scores
        (recipe_id, blood_type, secretor_status, score, beneficial_count, neutral_count,
         avoid_count, untagged_count, gluten_conflict, oat_conflict, dairy_conflict, verdict)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
        ON CONFLICT(recipe_id, blood_type, secretor_status) DO UPDATE SET
        score=excluded.score, beneficial_count=excluded.beneficial_count,
        neutral_count=excluded.neutral_count, avoid_count=excluded.avoid_count,
        untagged_count=excluded.untagged_count, gluten_conflict=excluded.gluten_conflict,
        oat_conflict=excluded.oat_conflict, dairy_conflict=excluded.dairy_conflict,
        verdict=excluded.verdict, computed_at=excluded.computed_at
    """, (recipe_id, blood_type, secretor,
          result['score'], result['beneficial_count'], result['neutral_count'],
          result['avoid_count'], result['untagged_count'],
          result['gluten_conflict'], result['oat_conflict'], result['dairy_conflict'],
          result['verdict']))
    gr_conn.commit()
    print(f"Recipe {recipe_id} | Type {blood_type} | Score {result['score']} | {result['verdict']}")


def score_batch(gr_conn, bt_conn, limit=1000):
    food_meta = load_btd_index(bt_conn)
    alias_map = build_alias_index(bt_conn)
    cur = gr_conn.cursor()
    cur.execute("""
        SELECT id FROM recipes
        WHERE id NOT IN (SELECT DISTINCT recipe_id FROM recipe_btd_scores)
        LIMIT ?
    """, (limit,))
    ids = [r[0] for r in cur.fetchall()]
    if not ids:
        print("No unprocessed recipes.")
        return
    total = len(ids)
    for i, rid in enumerate(ids, 1):
        ingredients = get_ingredients_for_recipe(gr_conn, rid)
        for bt in ['A','B','AB','O']:
            res = score_recipe(ingredients, food_meta, alias_map, bt, 'secretor')
            if not res:
                continue
            cur.execute("""
                INSERT OR REPLACE INTO recipe_btd_scores
                (recipe_id, blood_type, secretor_status, score, beneficial_count, neutral_count,
                 avoid_count, untagged_count, gluten_conflict, oat_conflict, dairy_conflict, verdict)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
            """, (rid, bt, 'secretor',
                  res['score'], res['beneficial_count'], res['neutral_count'],
                  res['avoid_count'], res['untagged_count'],
                  res['gluten_conflict'], res['oat_conflict'], res['dairy_conflict'],
                  res['verdict']))
        if i % 100 == 0:
            gr_conn.commit()
            print(f"  {i}/{total} scored")
    gr_conn.commit()
    print(f"Done. Scored {total} recipes x 4 blood types.")


def stats(gr_conn):
    cur = gr_conn.cursor()
    cur.execute("SELECT COUNT(*) FROM recipes")
    total = cur.fetchone()[0]
    cur.execute("SELECT COUNT(DISTINCT recipe_id) FROM recipe_btd_scores")
    scored = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM recipe_btd_scores")
    rows = cur.fetchone()[0]
    print(f"Total recipes: {total}")
    print(f"Scored recipes: {scored}")
    print(f"Score rows: {rows}")
    for bt in ['A','B','AB','O']:
        cur.execute("SELECT verdict, COUNT(*) FROM recipe_btd_scores WHERE blood_type=? GROUP BY verdict", (bt,))
        for v, c in cur.fetchall():
            print(f"  {bt} {v}: {c}")


def main():
    p = argparse.ArgumentParser(description="BTD scorer for recipes.db")
    p.add_argument("--init", action="store_true", help="Init tables")
    p.add_argument("--batch", type=int, default=0, help="Batch size")
    p.add_argument("--backfill", action="store_true", help="Score all unprocessed")
    p.add_argument("--recipe", type=int, default=0, help="Single recipe ID")
    p.add_argument("--bt", default='B', help="Blood type for single scoring")
    p.add_argument("--stats", action="store_true", help="Show stats")
    p.add_argument("--verbose", action="store_true", help="Show per-recipe details")
    args = p.parse_args()

    if not GR_DB.exists():
        print(f"Database not found: {GR_DB}\nSet OPEN_GLOBAL_RECIPES_DB")
        return
    gr_conn = sqlite3.connect(GR_DB)

    if args.init:
        init_table(gr_conn)
        return

    if not BTD_DB.exists():
        print(f"BTD database not found: {BTD_DB}\nSet BTD_DIET_DB")
        return
    bt_conn = sqlite3.connect(BTD_DB)

    if args.stats:
        stats(gr_conn)
    elif args.recipe:
        score_single(gr_conn, bt_conn, args.recipe, args.bt)
    elif args.backfill:
        score_batch(gr_conn, bt_conn, limit=999999999)
    elif args.batch:
        score_batch(gr_conn, bt_conn, limit=args.batch)
    else:
        p.print_help()

    gr_conn.close()
    bt_conn.close()


if __name__ == "__main__":
    main()
