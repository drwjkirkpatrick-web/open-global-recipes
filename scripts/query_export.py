#!/usr/bin/env python3
"""
Query, export, and PDF book generator for open-global-recipes.

Search:
  --country "Thailand"           List recipes for a country
  --ingredient "lemongrass"      Find recipes containing an ingredient
  --match-all "a,b,c"            Recipes containing ALL listed ingredients
  --random                       One random recipe
  --id 42                        Full recipe details by ID

Export:
  --export-csv "Thailand"        Write exports/Thailand_recipes.csv
  --export-json "Thailand"       Write exports/Thailand_recipes.json

PDF / Markdown:
  --pdf-book "Thailand"          Write exports/Thailand_recipe_book.pdf
                                 Falls back to .md if fpdf2 is unavailable.
  --limit N                      Cap results (default 50, 0 = unlimited)

Examples:
  python scripts/query_export.py --country "Mexico" --limit 10
  python scripts/query_export.py --ingredient "cilantro" --limit 20
  python scripts/query_export.py --match-all "garlic,onion,tomato"
  python scripts/query_export.py --random
  python scripts/query_export.py --id 42
"""

import argparse
import csv
import json
import os
import sqlite3
import sys
from pathlib import Path

DB_PATH = os.environ.get("OPEN_GLOBAL_RECIPES_DB",
                         os.path.expanduser("~/projects/global-recipe-db/recipes.db"))
EXPORT_DIR = os.environ.get("OPEN_GLOBAL_RECIPES_EXPORTS",
                              os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "exports"))


def _ensure_dir(p):
    Path(p).parent.mkdir(parents=True, exist_ok=True)


def get_db():
    if not os.path.exists(DB_PATH):
        sys.exit(f"Database not found: {DB_PATH}\nSet OPEN_GLOBAL_RECIPES_DB to point to your recipes.db")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def fmt_recipe(row):
    lines = []
    lines.append(f"\n{'=' * 60}")
    lines.append(f"  {row['title']}")
    lines.append(f"{'=' * 60}")
    if row.get('name'):
        lines.append(f"  Origin: {row['name']}")
    if row.get('cuisine_tag'):
        lines.append(f"  Cuisine: {row['cuisine_tag']}")
    lines.append(f"  ID: {row['id']}")
    lines.append("")
    lines.append("  Ingredients:")
    try:
        ings = json.loads(row['ingredients_raw']) if row['ingredients_raw'] else []
        for ing in ings:
            lines.append(f"    - {ing}")
    except (json.JSONDecodeError, TypeError):
        lines.append(f"    {row['ingredients_raw']}")
    lines.append("")
    lines.append("  Instructions:")
    if row['instructions']:
        steps = [s.strip() for s in row['instructions'].split('\n\n') if s.strip()]
        for i, step in enumerate(steps, 1):
            lines.append(f"    {i}. {step}")
    else:
        lines.append("    (no instructions)")
    lines.append(f"{'=' * 60}\n")
    return "\n".join(lines)


def query_country(conn, country_name, limit):
    c = conn.cursor()
    sql = """
        SELECT r.*, c.name
        FROM recipes r
        LEFT JOIN countries c ON r.country_id = c.id
        WHERE c.name = ? COLLATE NOCASE
        ORDER BY r.title
    """
    if limit:
        sql += f" LIMIT {int(limit)}"
    c.execute(sql, (country_name,))
    return c.fetchall()


def query_ingredient(conn, ing_name, limit):
    c = conn.cursor()
    sql = """
        SELECT DISTINCT r.*, c.name
        FROM recipes r
        JOIN recipe_ingredients ri ON r.id = ri.recipe_id
        JOIN ingredients i ON ri.ingredient_id = i.id
        LEFT JOIN countries c ON r.country_id = c.id
        WHERE i.normalized_name LIKE ? OR i.name LIKE ?
        ORDER BY r.title
    """
    if limit:
        sql += f" LIMIT {int(limit)}"
    like = f"%{ing_name.lower()}%"
    c.execute(sql, (like, like))
    return c.fetchall()


def query_match_all(conn, ing_list, limit):
    c = conn.cursor()
    ing_list = [i.strip().lower() for i in ing_list.split(",") if i.strip()]
    place = ','.join('?' for _ in ing_list)
    sql = f"""
        SELECT r.*, c.name FROM recipes r
        LEFT JOIN countries c ON r.country_id = c.id
        WHERE r.id IN (
            SELECT ri.recipe_id FROM recipe_ingredients ri
            JOIN ingredients i ON ri.ingredient_id = i.id
            WHERE i.normalized_name IN ({place})
            GROUP BY ri.recipe_id
            HAVING COUNT(DISTINCT i.normalized_name) = {len(ing_list)}
        )
        ORDER BY r.title
    """
    if limit:
        sql += f" LIMIT {int(limit)}"
    c.execute(sql, ing_list)
    return c.fetchall()


def query_random(conn):
    c = conn.cursor()
    c.execute("SELECT r.*, c.name FROM recipes r LEFT JOIN countries c ON r.country_id = c.id ORDER BY RANDOM() LIMIT 1")
    return c.fetchall()


def query_id(conn, rid):
    c = conn.cursor()
    c.execute("SELECT r.*, c.name FROM recipes r LEFT JOIN countries c ON r.country_id = c.id WHERE r.id = ?", (rid,))
    return c.fetchall()


def export_csv(rows, path):
    _ensure_dir(path)
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['id','title','country','ingredients_raw','instructions','source_url','cuisine_tag'])
        for r in rows:
            writer.writerow([r['id'], r['title'], r.get('name',''),
                             r['ingredients_raw'], r['instructions'],
                             r['source_url'], r['cuisine_tag']])
    print(f"CSV exported: {path}")


def export_json(rows, path):
    _ensure_dir(path)
    out = []
    for r in rows:
        out.append({
            'id': r['id'], 'title': r['title'], 'country': r.get('name',''),
            'ingredients_raw': r['ingredients_raw'], 'instructions': r['instructions'],
            'source_url': r['source_url'], 'cuisine_tag': r['cuisine_tag']
        })
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    print(f"JSON exported: {path}")


def export_pdf(rows, path, country_name):
    try:
        from fpdf import FPDF
    except ImportError:
        md_path = path.replace('.pdf', '.md')
        export_markdown(rows, md_path, country_name)
        print(f"fpdf2 not installed; wrote Markdown instead: {md_path}")
        return
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    for r in rows:
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 14)
        pdf.cell(0, 10, r['title'], ln=True)
        pdf.set_font("Helvetica", "", 10)
        if r.get('name'):
            pdf.cell(0, 6, f"Origin: {r['name']}", ln=True)
        pdf.ln(2)
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 8, "Ingredients:", ln=True)
        pdf.set_font("Helvetica", "", 10)
        try:
            ings = json.loads(r['ingredients_raw']) if r['ingredients_raw'] else []
            for ing in ings:
                pdf.multi_cell(0, 5, f"- {ing}")
        except (json.JSONDecodeError, TypeError):
            pdf.multi_cell(0, 5, str(r['ingredients_raw']))
        pdf.ln(2)
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 8, "Instructions:", ln=True)
        pdf.set_font("Helvetica", "", 10)
        steps = [s.strip() for s in str(r['instructions'] or '').split('\n\n') if s.strip()]
        for step in steps:
            pdf.multi_cell(0, 5, step)
        pdf.ln(3)
    _ensure_dir(path)
    pdf.output(path)
    print(f"PDF exported: {path}")


def export_markdown(rows, path, country_name):
    _ensure_dir(path)
    lines = [f"# {country_name or 'Recipes'} Recipe Book\n"]
    for r in rows:
        lines.append(f"\n## {r['title']}\n")
        if r.get('name'):
            lines.append(f"**Origin:** {r['name']}  \n")
        lines.append("**Ingredients:**\n")
        try:
            ings = json.loads(r['ingredients_raw']) if r['ingredients_raw'] else []
            for ing in ings:
                lines.append(f"- {ing}")
        except (json.JSONDecodeError, TypeError):
            lines.append(f"- {r['ingredients_raw']}")
        lines.append("\n**Instructions:**\n")
        steps = [s.strip() for s in str(r['instructions'] or '').split('\n\n') if s.strip()]
        for i, step in enumerate(steps, 1):
            lines.append(f"{i}. {step}")
        lines.append("")
    with open(path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))


def main():
    parser = argparse.ArgumentParser(description="Query and export open-global-recipes")
    parser.add_argument("--country", help="Country name")
    parser.add_argument("--ingredient", help="Ingredient keyword")
    parser.add_argument("--match-all", dest="match_all", help="Comma-separated ingredients (ALL must match)")
    parser.add_argument("--random", action="store_true", help="One random recipe")
    parser.add_argument("--id", type=int, help="Recipe ID")
    parser.add_argument("--export-csv", dest="export_csv", help="Export country to CSV")
    parser.add_argument("--export-json", dest="export_json", help="Export country to JSON")
    parser.add_argument("--pdf-book", dest="pdf_book", help="Export country to PDF")
    parser.add_argument("--limit", type=int, default=50, help="Max results (0=unlimited)")
    args = parser.parse_args()

    conn = get_db()
    rows = None
    target = None

    if args.country:
        rows = query_country(conn, args.country, args.limit)
        target = args.country
    elif args.ingredient:
        rows = query_ingredient(conn, args.ingredient, args.limit)
        target = args.ingredient
    elif args.match_all:
        rows = query_match_all(conn, args.match_all, args.limit)
        target = args.match_all
    elif args.random:
        rows = query_random(conn)
        target = "random"
    elif args.id is not None:
        rows = query_id(conn, args.id)
        target = str(args.id)
    else:
        parser.print_help()
        sys.exit(0)

    if not rows:
        print("No results found.")
        sys.exit(0)

    for r in rows:
        print(fmt_recipe(r))

    if args.export_csv:
        export_csv(rows, os.path.join(EXPORT_DIR, f"{args.export_csv}_recipes.csv"))
    if args.export_json:
        export_json(rows, os.path.join(EXPORT_DIR, f"{args.export_json}_recipes.json"))
    if args.pdf_book:
        export_pdf(rows, os.path.join(EXPORT_DIR, f"{args.pdf_book}_recipe_book.pdf"), args.pdf_book)


if __name__ == "__main__":
    main()
