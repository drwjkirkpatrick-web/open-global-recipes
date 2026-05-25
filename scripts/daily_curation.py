#!/usr/bin/env python3
"""
Daily 3-recipe curator for open-global-recipes.

Picks 3 recipes from 3 different countries, optionally filtered by BTD score.
Finds a shared ingredient or theme across the trio and renders text or PDF.

Usage:
    python scripts/daily_curation.py --text
    python scripts/daily_curation.py --pdf
    python scripts/daily_curation.py --pdf --blood-type B
    python scripts/daily_curation.py --text --blood-type O --limit 3

Environment:
    OPEN_GLOBAL_RECIPES_DB  - Path to recipes.db
    BTD_DIET_DB             - Optional; needed only if --blood-type is used
"""

import sqlite3
import random
import re
import json
import os
import sys
import datetime
import argparse
from pathlib import Path

GR_DB = Path(os.environ.get("OPEN_GLOBAL_RECIPES_DB", "recipes.db"))
BTD_DB = Path(os.environ.get("BTD_DIET_DB",
    os.path.expanduser("~/.hermes/skills/blood-type-diet/data/btdiet.db")))
EXPORT_DIR = Path(os.environ.get("OPEN_GLOBAL_RECIPES_EXPORTS",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "exports")))
MIN_RECIPES_PER_COUNTRY = 5


def normalize_ingredient(raw):
    s = re.sub(r'^[\d\s\u00bd\u00bc\u00be\u2153\u2154\u215b\u215c\u215d\u215e./-]+', '', raw.lower())
    s = re.sub(r'^(tbsp|tsp|cup|oz|pound|lb|g|kg|ml|l|pinch|dash|can|package|bunch|clove|cloves)s?\s*', '', s)
    return s.strip()


def pick_recipes(conn, blood_type=None):
    c = conn.cursor()
    if blood_type:
        # Countries with enough green/yellow recipes for this blood type
        c.execute("""
            SELECT co.name, COUNT(*) as cnt
            FROM recipes r
            JOIN recipe_btd_scores rc ON r.id = rc.recipe_id
            JOIN countries co ON r.country_id = co.id
            WHERE rc.blood_type = ?
              AND rc.verdict IN ('green', 'yellow')
            GROUP BY co.name
            HAVING cnt >= ?
            ORDER BY cnt DESC
        """, (blood_type, MIN_RECIPES_PER_COUNTRY))
        countries = [row[0] for row in c.fetchall()]
        if len(countries) < 3:
            c.execute("""
                SELECT DISTINCT co.name
                FROM recipes r
                JOIN recipe_btd_scores rc ON r.id = rc.recipe_id
                JOIN countries co ON r.country_id = co.id
                WHERE rc.blood_type = ?
                  AND rc.verdict IN ('green', 'yellow')
            """, (blood_type,))
            countries = [row[0] for row in c.fetchall()]
    else:
        # Any countries with >= MIN_RECIPES_PER_COUNTRY total recipes
        c.execute("""
            SELECT co.name, COUNT(*) as cnt FROM recipes r
            JOIN countries co ON r.country_id = co.id
            GROUP BY co.name HAVING cnt >= ?
            ORDER BY cnt DESC
        """, (MIN_RECIPES_PER_COUNTRY,))
        countries = [row[0] for row in c.fetchall()]

    if len(countries) < 3:
        raise RuntimeError(f"Not enough countries with qualifying recipes (found {len(countries)}).")

    selected_countries = random.sample(countries, min(3, len(countries)))
    picked = []
    for country in selected_countries:
        if blood_type:
            c.execute("""
                SELECT r.id, r.title, r.instructions, r.ingredients_raw, co.name,
                       rc.score, rc.beneficial_count, rc.avoid_count, rc.verdict
                FROM recipes r
                JOIN recipe_btd_scores rc ON r.id = rc.recipe_id
                JOIN countries co ON r.country_id = co.id
                WHERE co.name = ? AND rc.blood_type = ? AND rc.verdict IN ('green','yellow')
                ORDER BY RANDOM()
                LIMIT 1
            """, (country, blood_type))
        else:
            c.execute("""
                SELECT r.id, r.title, r.instructions, r.ingredients_raw, co.name
                FROM recipes r
                JOIN countries co ON r.country_id = co.id
                WHERE co.name = ?
                ORDER BY RANDOM()
                LIMIT 1
            """, (country,))
        row = c.fetchone()
        if row:
            picked.append(row)
    return picked


def shared_link(rows):
    terms = []
    for r in rows:
        try:
            ings = json.loads(r['ingredients_raw']) if r['ingredients_raw'] else []
            normed = [normalize_ingredient(i) for i in ings]
            terms.append(set(normed))
        except (json.JSONDecodeError, TypeError):
            terms.append(set())
    common = set.intersection(*terms) if terms else set()
    if common:
        return f"Common thread — all three use: {', '.join(sorted(common)[:3])}"
    # Fallback: keyword overlap in titles
    title_words = [set(r['title'].lower().split()) for r in rows]
    common = set.intersection(*title_words) if title_words else set()
    common -= {'and','the','with','of','in','a','to','for','-','recipe','style'}
    if common:
        return f"Common thread — shared title theme: {', '.join(sorted(common)[:3])}"
    return "Three distinct tastes — no common thread needed."


def fmt_text(rows, blood_type=None):
    date_str = datetime.date.today().strftime("%A, %B %d, %Y")
    lines = [
        f"📅 Daily Global Recipe Trio — {date_str}",
        "=" * 50,
    ]
    if blood_type:
        lines.append(f"Blood Type {blood_type} | Green/Yellow only")
    lines.append("")
    for i, r in enumerate(rows, 1):
        lines.append(f"  {i}. {r['title']}  🌍 {r['name']}")
    lines.append("")
    lines.append(shared_link(rows))
    lines.append("")
    for i, r in enumerate(rows, 1):
        lines.append(f"\n{'─'*50}")
        lines.append(f"  {i}. {r['title']} ({r['name']})")
        lines.append(f"{'─'*50}")
        if blood_type:
            lines.append(f"   Score: {r['score']}/100 | Verdict: {r['verdict']}")
            lines.append(f"   ✅ Beneficial: {r['beneficial_count']}  🔴 Avoid: {r['avoid_count']}")
        lines.append("")
        lines.append("   Ingredients:")
        try:
            ings = json.loads(r['ingredients_raw']) if r['ingredients_raw'] else []
            for ing in ings:
                lines.append(f"     - {ing}")
        except (json.JSONDecodeError, TypeError):
            lines.append(f"     {r['ingredients_raw']}")
        lines.append("")
        lines.append("   Instructions:")
        steps = [s.strip() for s in str(r['instructions'] or '').split('\n\n') if s.strip()]
        for n, step in enumerate(steps, 1):
            lines.append(f"     {n}. {step}")
        lines.append("")
    return '\n'.join(lines)


def write_pdf(text_content, path):
    try:
        from weasyprint import HTML
    except ImportError:
        sys.stderr.write("weasyprint not installed; falling back to Markdown\n")
        md_path = str(path).replace('.pdf', '.md')
        Path(md_path).parent.mkdir(parents=True, exist_ok=True)
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(text_content)
        print(f"Markdown: {md_path}")
        return
    html = f"""<html><head><meta charset="utf-8"><style>
    body {{ font-family: sans-serif; margin: 40px; line-height: 1.5; }}
    h1 {{ font-size: 22px; border-bottom: 2px solid #333; padding-bottom: 6px; }}
    h2 {{ font-size: 16px; margin-top: 24px; }}
    pre {{ white-space: pre-wrap; }}
    </style></head><body><pre>{text_content}</pre></body></html>"""
    path.parent.mkdir(parents=True, exist_ok=True)
    HTML(string=html).write_pdf(str(path))
    print(f"PDF: {path}")


def main():
    parser = argparse.ArgumentParser(description="Daily 3-recipe curation")
    parser.add_argument("--text", action="store_true", help="Print text to stdout")
    parser.add_argument("--pdf", action="store_true", help="Write PDF to exports/")
    parser.add_argument("--blood-type", choices=["A","B","AB","O"], default=None,
                        help="Optional BTD filter (requires BTD database)")
    parser.add_argument("--output", help="Override output path")
    args = parser.parse_args()

    if not GR_DB.exists():
        sys.exit(f"Database not found: {GR_DB}\nSet OPEN_GLOBAL_RECIPES_DB")

    conn = sqlite3.connect(GR_DB)
    conn.row_factory = sqlite3.Row

    if args.blood_type:
        if not BTD_DB.exists():
            sys.exit(f"BTD database not found: {BTD_DB}\nInstall the BTD add-on or omit --blood-type")

    rows = pick_recipes(conn, args.blood_type)
    text = fmt_text(rows, args.blood_type)

    if args.text or not (args.pdf or args.output):
        print(text)

    if args.pdf or args.output:
        date_str = datetime.date.today().strftime("%Y-%m-%d")
        out_path = Path(args.output) if args.output else EXPORT_DIR / f"daily_{date_str}.pdf"
        write_pdf(text, Path(out_path))

    conn.close()


if __name__ == "__main__":
    main()
