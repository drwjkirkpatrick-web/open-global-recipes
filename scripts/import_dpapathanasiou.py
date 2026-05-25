#!/usr/bin/env python3
"""
Import recipes from dpapathanasiou/recipes GitHub repo into global-recipe-db.
The repo has index .md files per cuisine that link to JSON recipe files.
"""

import sqlite3
import json
import re
import os
import sys
from pathlib import Path

DB_PATH = os.path.expanduser("~/projects/global-recipe-db/recipes.db")
REPO_PATH = os.path.expanduser("~/projects/global-recipe-db/raw_data/dpapathanasiou-recipes")

# Map cuisine keyword -> country_id (populated below)
COUNTRY_MAP = {
    "thai": None,
    "japanese": None,
    "mexican": None,
    "french": None,
    "german": None,
    "spanish": None,
    "peruvian": None,
}

SOURCE_NAME = "dpapathanasiou/recipes"
SOURCE_URL = "https://github.com/dpapathanasiou/recipes"
SOURCE_LICENSE = "MIT"


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def ensure_source(conn):
    c = conn.cursor()
    c.execute("SELECT id FROM data_sources WHERE name = ?", (SOURCE_NAME,))
    row = c.fetchone()
    if row:
        return row[0]
    c.execute(
        "INSERT INTO data_sources (name, url, license, description) VALUES (?,?,?,?)",
        (SOURCE_NAME, SOURCE_URL, SOURCE_LICENSE, "~78K JSON recipes scraped from various sites, organized by index"),
    )
    conn.commit()
    return c.lastrowid


def load_country_ids(conn):
    c = conn.cursor()
    for keyword in COUNTRY_MAP:
        # Match cuisine keyword to country cuisine_keywords column
        c.execute(
            "SELECT id FROM countries WHERE cuisine_keywords LIKE ?",
            (f"%{keyword}%",),
        )
        row = c.fetchone()
        if row:
            COUNTRY_MAP[keyword] = row[0]
        else:
            # Fallback: match common names
            name_map = {
                "thai": "Thailand",
                "japanese": "Japan",
                "mexican": "Mexico",
                "french": "France",
                "german": "Germany",
                "spanish": "Spain",
                "peruvian": "Peru",
            }
            c.execute("SELECT id FROM countries WHERE name = ?", (name_map[keyword],))
            row = c.fetchone()
            if row:
                COUNTRY_MAP[keyword] = row[0]
    print("Country ID mapping:", COUNTRY_MAP)


def parse_index_md(md_path):
    """Extract JSON relative paths from an index .md file."""
    paths = []
    with open(md_path, "r", encoding="utf-8") as f:
        for line in f:
            # Match markdown links like:
            # * [Title](../../index/x/x-file.json)
            m = re.search(r'\* \[.*?\]\((.*?\.json)\)', line)
            if m:
                rel = m.group(1)
                # The paths are relative to the index .md file location
                # e.g., ../../index/t/thai-beef.json
                # md_path is like .../index/t/thai.md
                base = os.path.dirname(md_path)
                full = os.path.normpath(os.path.join(base, rel))
                paths.append(full)
    return paths


def import_cuisine(conn, source_id, cuisine_keyword):
    country_id = COUNTRY_MAP.get(cuisine_keyword)
    if not country_id:
        print(f"SKIP: no country_id for {cuisine_keyword}")
        return 0

    index_md = os.path.join(REPO_PATH, "index", cuisine_keyword[0], f"{cuisine_keyword}.md")
    if not os.path.exists(index_md):
        print(f"SKIP: index file not found: {index_md}")
        return 0

    json_paths = parse_index_md(index_md)
    print(f"[{cuisine_keyword.upper()}] Found {len(json_paths)} recipes in index")

    c = conn.cursor()
    imported = 0
    skipped = 0
    errors = []

    for jpath in json_paths:
        if not os.path.exists(jpath):
            skipped += 1
            continue
        try:
            with open(jpath, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            errors.append(f"JSON error in {jpath}: {e}")
            skipped += 1
            continue

        title = data.get("title", "").strip()
        ingredients = data.get("ingredients", [])
        directions = data.get("directions", [])
        source = data.get("source", "")
        url = data.get("url", "")
        tags = data.get("tags", [])
        language = data.get("language", "en-US")

        if not title:
            skipped += 1
            continue

        ingredients_raw = json.dumps(ingredients)
        raw_json = json.dumps(data)
        tags_str = ",".join(tags) if isinstance(tags, list) else str(tags)

        try:
            c.execute(
                """
                INSERT INTO recipes
                (country_id, source_id, title, instructions, ingredients_raw,
                 source_url, source_name, license, language, cuisine_tag, raw_data_json)
                VALUES (?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    country_id,
                    source_id,
                    title,
                    "\n\n".join(directions) if isinstance(directions, list) else str(directions),
                    ingredients_raw,
                    url,
                    source,
                    SOURCE_LICENSE,
                    language,
                    tags_str,
                    raw_json,
                ),
            )
            imported += 1
        except sqlite3.IntegrityError as e:
            errors.append(f"DB error for {title}: {e}")
            skipped += 1
        except Exception as e:
            errors.append(f"Unexpected error for {title}: {e}")
            skipped += 1

    conn.commit()

    # Log import run
    c.execute(
        "INSERT INTO import_logs (source_id, country_id, records_imported, records_skipped, errors) VALUES (?,?,?,?,?)",
        (source_id, country_id, imported, skipped, "\n".join(errors[:20])),
    )
    conn.commit()

    print(f"[{cuisine_keyword.upper()}] Imported: {imported}, Skipped: {skipped}, Errors: {len(errors)}")
    return imported


def main(target_cuisine=None):
    conn = get_db()
    source_id = ensure_source(conn)
    load_country_ids(conn)

    if target_cuisine:
        if target_cuisine not in COUNTRY_MAP:
            print(f"Unknown cuisine: {target_cuisine}")
            sys.exit(1)
        import_cuisine(conn, source_id, target_cuisine)
    else:
        for cuisine in COUNTRY_MAP:
            import_cuisine(conn, source_id, cuisine)

    conn.close()
    print("Done.")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        main(sys.argv[1].lower())
    else:
        main()
