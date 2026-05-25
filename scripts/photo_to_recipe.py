#!/usr/bin/env python3
"""
Photo-to-Recipe Import Pipeline for global-recipe-db.
Extracts recipe text from an image, parses into structured fields,
infers country of origin, and inserts into SQLite database.

OCR Backends (auto-detected in this order):
  1. pytesseract   — local, free, requires `apt install tesseract-ocr` + `pip install pytesseract`
  2. easyocr       — local, free, requires `pip install easyocr` (heavier, GPU-friendly)
  3. openai        — remote, requires OPENAI_API_KEY env var
  4. manual        — paste raw text with --text flag (no OCR install needed)

Parsing Backends:
  1. heuristic     — regex/rules based, free, fast
  2. llm           — OpenAI/compatible API for fuzzy extraction (requires OPENAI_API_KEY)

Usage:
  # OCR + heuristic parse (auto-detect best available OCR)
  python photo_to_recipe.py ~/photos/recipe_card.jpg

  # Manual text entry + heuristic parse
  python photo_to_recipe.py --text "Title: ... Ingredients: ... Instructions: ..."

  # OCR + LLM parse for messy/handwritten cards
  python photo_to_recipe.py ~/photos/recipe_card.jpg --parse llm --model gpt-4o

  # Specify OCR backend explicitly
  python photo_to_recipe.py ~/photos/recipe_card.jpg --ocr easyocr
"""

import argparse
import json
import os
import re
import sqlite3
import sys
from pathlib import Path

DB_PATH = os.path.expanduser("~/projects/global-recipe-db/recipes.db")

# ---------------------------------------------------------------------------
# OCR backends
# ---------------------------------------------------------------------------

def ocr_pytesseract(image_path):
    try:
        import pytesseract
        from PIL import Image
    except ImportError as e:
        raise RuntimeError("pytesseract not installed. Run: pip install pytesseract") from e
    img = Image.open(image_path)
    return pytesseract.image_to_string(img)


def ocr_easyocr(image_path):
    try:
        import easyocr
    except ImportError as e:
        raise RuntimeError("easyocr not installed. Run: pip install easyocr") from e
    reader = easyocr.Reader(["en"])
    results = reader.readtext(image_path, detail=0)
    return "\n".join(results)


def ocr_openai(image_path):
    import base64
    try:
        import openai
    except ImportError as e:
        raise RuntimeError("openai not installed. Run: pip install openai") from e
    client = openai.OpenAI()
    with open(image_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")
    resp = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Extract all text from this recipe image verbatim. Preserve line breaks."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}},
                ],
            }
        ],
        max_tokens=1500,
    )
    return resp.choices[0].message.content


def detect_ocr_backend(preferred=None):
    if preferred == "manual":
        return None
    if preferred == "pytesseract":
        return "pytesseract"
    if preferred == "easyocr":
        return "easyocr"
    if preferred == "openai":
        return "openai"
    # Auto-detect
    try:
        import pytesseract  # noqa
        return "pytesseract"
    except ImportError:
        pass
    try:
        import easyocr  # noqa
        return "easyocr"
    except ImportError:
        pass
    if os.environ.get("OPENAI_API_KEY"):
        return "openai"
    return None


def run_ocr(image_path, backend):
    if backend == "pytesseract":
        return ocr_pytesseract(image_path)
    if backend == "easyocr":
        return ocr_easyocr(image_path)
    if backend == "openai":
        return ocr_openai(image_path)
    raise RuntimeError(f"Unknown OCR backend: {backend}")


# ---------------------------------------------------------------------------
# Heuristic parser
# ---------------------------------------------------------------------------

def heuristic_parse(raw_text):
    """
    Parse raw OCR text into structured recipe dict.
    Returns dict with keys: title, ingredients[], instructions[], notes, country_hint
    """
    lines = [l.strip() for l in raw_text.splitlines()]
    lines = [l for l in lines if l]
    if not lines:
        return {"title": "", "ingredients": [], "instructions": [], "notes": "", "country_hint": ""}

    # Title = first non-empty line unless it looks like a header
    title = lines[0]
    if re.match(r"^(ingredients|instructions|directions|method|prep|notes|yield|serves)", title, re.I):
        title = lines[1] if len(lines) > 1 else "Untitled Recipe"

    text_lower = "\n".join(lines).lower()

    # Find ingredient section
    ing_start = None
    ing_end = None
    for i, line in enumerate(lines):
        if re.search(r"^(ingredients|what you need|you.ll need)", line, re.I):
            ing_start = i + 1
        elif ing_start is not None and re.search(r"^(instructions|directions|method|preparation|steps|procedure|notes|yield|serves|prep time|cook time)", line, re.I):
            ing_end = i
            break
    if ing_start is not None and ing_end is None:
        ing_end = len(lines)

    ingredients = []
    if ing_start is not None and ing_end is not None:
        for line in lines[ing_start:ing_end]:
            # Only strip bullets/whitespace — preserve quantities
            clean = re.sub(r"^[-–—•*·\s]+", "", line).strip()
            if clean and len(clean) > 2:
                ingredients.append(clean)

    # Find instruction section
    inst_start = None
    inst_end = None
    for i, line in enumerate(lines):
        if re.search(r"^(instructions|directions|method|preparation|steps|procedure)", line, re.I):
            inst_start = i + 1
        elif inst_start is not None and re.search(r"^(notes|yield|serves|prep time|cook time|total time|nutrition|source)", line, re.I):
            inst_end = i
            break
    if inst_start is not None and inst_end is None:
        inst_end = len(lines)

    instructions = []
    if inst_start is not None and inst_end is not None:
        for line in lines[inst_start:inst_end]:
            # Strip bullets and step numbers like "1. " or "2) " but preserve text
            clean = re.sub(r"^[-–—•*·\s]+", "", line).strip()
            clean = re.sub(r"^\d+[\.)\]]\s+", "", clean)
            if clean and len(clean) > 2:
                instructions.append(clean)

    # If we failed to find sections, do a best-effort split
    if not ingredients and not instructions:
        mid = len(lines) // 2
        ingredients = lines[1:mid]
        instructions = lines[mid:]

    # Country hint from text
    country_hint = ""
    country_keywords = {
        "thai": "Thailand", "thailand": "Thailand",
        "mexican": "Mexico", "mexico": "Mexico",
        "french": "France", "france": "France",
        "japanese": "Japan", "japan": "Japan",
        "italian": "Italy", "italy": "Italy",
        "german": "Germany", "germany": "Germany",
        "spanish": "Spain", "spain": "Spain",
        "indian": "India", "india": "India",
        "greek": "Greece", "greece": "Greece",
        "vietnamese": "Viet Nam", "vietnam": "Viet Nam",
        "korean": "Korea, Republic of",
        "chinese": "China", "china": "China",
        "peruvian": "Peru", "peru": "Peru",
        "moroccan": "Morocco", "morocco": "Morocco",
        "brazilian": "Brazil", "brazil": "Brazil",
        "turkish": "Turkey", "turkey": "Turkey",
        "ethiopian": "Ethiopia", "ethiopia": "Ethiopia",
        "lebanese": "Lebanon", "lebanon": "Lebanon",
    }
    for kw, country in country_keywords.items():
        if kw in text_lower:
            country_hint = country
            break

    return {
        "title": title,
        "ingredients": ingredients,
        "instructions": instructions,
        "notes": "",
        "country_hint": country_hint,
    }


# ---------------------------------------------------------------------------
# LLM parser
# ---------------------------------------------------------------------------

def llm_parse(raw_text, model="gpt-4o-mini"):
    try:
        import openai
    except ImportError as e:
        raise RuntimeError("openai not installed. Run: pip install openai") from e
    client = openai.OpenAI()
    system_prompt = (
        "You are a recipe parser. Extract structured data from messy OCR text. "
        "Return ONLY a JSON object with keys: title (string), ingredients (list of strings), "
        "instructions (list of strings), notes (string), country_hint (string). "
        "For country_hint, infer the origin country from recipe name, ingredients, or explicit tags. "
        "If unknown, use empty string."
    )
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Parse this recipe text:\n\n{raw_text}"},
        ],
        response_format={"type": "json_object"},
        max_tokens=1500,
    )
    try:
        return json.loads(resp.choices[0].message.content)
    except json.JSONDecodeError:
        return heuristic_parse(raw_text)


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def ensure_photo_source(conn):
    c = conn.cursor()
    c.execute("SELECT id FROM data_sources WHERE name = ?", ("photo_import",))
    row = c.fetchone()
    if row:
        return row[0]
    c.execute(
        "INSERT INTO data_sources (name, url, license, description) VALUES (?,?,?,?)",
        ("photo_import", "", "unknown", "Recipes imported from user-submitted photos via OCR"),
    )
    conn.commit()
    return c.lastrowid


def resolve_country(conn, hint, title, ingredients, instructions):
    c = conn.cursor()
    if hint:
        c.execute("SELECT id FROM countries WHERE name = ? COLLATE NOCASE", (hint,))
        row = c.fetchone()
        if row:
            return row[0]
        c.execute("SELECT id FROM countries WHERE cuisine_keywords LIKE ?", (f"%{hint.lower()}%",))
        row = c.fetchone()
        if row:
            return row[0]
    # Fallback: search title for country names
    all_text = f"{title} {' '.join(ingredients)} {' '.join(instructions)}".lower()
    c.execute("SELECT id, name, cuisine_keywords FROM countries")
    best_id = None
    best_score = 0
    for cid, cname, ckw in c.fetchall():
        score = 0
        if cname.lower() in all_text:
            score += 5
        if ckw:
            for kw in ckw.split(","):
                if kw.strip().lower() in all_text:
                    score += 2
        if score > best_score:
            best_score = score
            best_id = cid
    return best_id


def insert_recipe(conn, source_id, parsed, country_id, raw_text, image_path):
    c = conn.cursor()
    title = parsed.get("title", "Untitled")
    ingredients = parsed.get("ingredients", [])
    instructions = parsed.get("instructions", [])
    notes = parsed.get("notes", "")
    country_hint = parsed.get("country_hint", "")

    ingredients_raw = json.dumps(ingredients)
    instructions_text = "\n\n".join(instructions)
    raw_json = json.dumps({
        "ocr_text": raw_text,
        "parsed": parsed,
        "image_path": str(image_path) if image_path else None,
        "notes": notes,
        "country_hint": country_hint,
    })

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
            instructions_text,
            ingredients_raw,
            str(image_path) if image_path else "",
            "photo_import",
            "unknown",
            "en",
            country_hint if country_hint else None,
            raw_json,
        ),
    )
    recipe_id = c.lastrowid
    conn.commit()

    # Populate ingredients + recipe_ingredients if we have them
    for ing in ingredients:
        if not ing or len(ing) < 2:
            continue
        # Normalize: lowercase, strip quantities for lookup
        normalized = re.sub(r"^[\d\s./-]+\s*(tsp|tbsp|cup|oz|lb|g|kg|ml|l|pint|quart|gallon|pinch|dash|can|jar|bunch|slice|piece|clove|head|stalk|stick|strip|packet|pack|ounce|pound)s?\s*", "", ing.lower()).strip()
        normalized = re.sub(r"^\d+[\d\s./-]*\s*", "", normalized)
        normalized = normalized.strip(",. ")
        if not normalized:
            normalized = ing.lower().strip(",. ")

        c.execute("SELECT id FROM ingredients WHERE normalized_name = ?", (normalized,))
        row = c.fetchone()
        if row:
            ing_id = row[0]
        else:
            c.execute("INSERT INTO ingredients (name, normalized_name) VALUES (?,?)", (ing, normalized))
            ing_id = c.lastrowid

        # Extract quantity + unit heuristically
        qty_match = re.match(r"([\d\s./-]+)\s*(tsp|tbsp|cup|oz|lb|g|kg|ml|l|pint|quart|gallon|pinch|dash|can|jar|bunch|slice|piece|clove|head|stalk|stick|strip|packet|pack|ounce|pound)s?\b", ing, re.I)
        quantity = qty_match.group(1).strip() if qty_match else ""
        unit = qty_match.group(2).lower() if qty_match else ""

        try:
            c.execute(
                "INSERT INTO recipe_ingredients (recipe_id, ingredient_id, quantity, unit, raw_text) VALUES (?,?,?,?,?)",
                (recipe_id, ing_id, quantity, unit, ing),
            )
        except sqlite3.IntegrityError:
            pass  # duplicate
    conn.commit()
    return recipe_id


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Photo-to-Recipe Import Pipeline")
    parser.add_argument("image", nargs="?", help="Path to recipe image")
    parser.add_argument("--text", help="Raw OCR text (skip OCR step)")
    parser.add_argument("--ocr", choices=["pytesseract", "easyocr", "openai", "manual"], help="OCR backend")
    parser.add_argument("--parse", choices=["heuristic", "llm"], default="heuristic", help="Parsing backend")
    parser.add_argument("--model", default="gpt-4o-mini", help="LLM model for OCR or parse")
    parser.add_argument("--country", help="Force country name")
    parser.add_argument("--dry-run", action="store_true", help="Print parsed recipe without inserting")
    parser.add_argument("--db", default=DB_PATH, help="Path to SQLite database")
    args = parser.parse_args()

    db_path = args.db

    # Validate inputs
    if not args.text and not args.image:
        parser.error("Provide either an image path or --text")

    # --- OCR step ---
    if args.text:
        raw_text = args.text
        image_path = None
        print("=== Using provided text (OCR skipped) ===")
    else:
        image_path = Path(args.image)
        if not image_path.exists():
            print(f"Error: file not found: {image_path}")
            sys.exit(1)

        backend = detect_ocr_backend(args.ocr)
        if backend is None:
            print(
                "Error: No OCR backend available. Options:\n"
                "  1. Install tesseract:  sudo apt install tesseract-ocr && pip install pytesseract\n"
                "  2. Install easyocr:     pip install easyocr\n"
                "  3. Set OPENAI_API_KEY for vision API\n"
                "  4. Use --text to paste raw OCR text manually"
            )
            sys.exit(1)
        print(f"=== OCR backend: {backend} ===")
        raw_text = run_ocr(str(image_path), backend)

    print("\n--- RAW OCR TEXT ---")
    print(raw_text)
    print("--- END RAW ---\n")

    # --- Parse step ---
    if args.parse == "llm":
        print("=== Parsing with LLM ===")
        parsed = llm_parse(raw_text, model=args.model)
    else:
        print("=== Parsing with heuristics ===")
        parsed = heuristic_parse(raw_text)

    print("\n--- PARSED RECIPE ---")
    print(json.dumps(parsed, indent=2))
    print("--- END PARSED ---\n")

    if args.dry_run:
        print("Dry run complete. No database changes.")
        return

    # --- Database insert ---
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    source_id = ensure_photo_source(conn)

    country_hint = args.country or parsed.get("country_hint", "")
    country_id = resolve_country(conn, country_hint, parsed["title"], parsed["ingredients"], parsed["instructions"])

    if country_id:
        c = conn.cursor()
        c.execute("SELECT name FROM countries WHERE id = ?", (country_id,))
        country_name = c.fetchone()[0]
        print(f"Resolved country: {country_name}")
    else:
        print("Warning: Could not resolve country. Recipe will have NULL country_id.")
        country_name = None

    recipe_id = insert_recipe(conn, source_id, parsed, country_id, raw_text, image_path)
    print(f"Inserted recipe id={recipe_id} ({parsed['title']}) -> {country_name or 'Unknown'}")

    # Log
    c = conn.cursor()
    c.execute(
        "INSERT INTO import_logs (source_id, country_id, records_imported, records_skipped) VALUES (?,?,?,?)",
        (source_id, country_id, 1, 0),
    )
    conn.commit()
    conn.close()
    print("Done.")


if __name__ == "__main__":
    main()
