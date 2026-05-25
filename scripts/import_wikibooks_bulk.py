#!/usr/bin/env python3
"""
Bulk import Wikibooks recipes into global-recipe-db.
Scrapes recipe pages and inserts into recipes.db.
"""
import sqlite3
import json
import time
from hermes_tools import web_extract

DB_PATH = "/home/walker/projects/global-recipe-db/recipes.db"

# URL-safe encoding helper
def wikibooks_url(title):
    """Convert a recipe title into a Wikibooks URL."""
    # Replace spaces with underscores and quote special chars
    import urllib.parse
    safe = title.replace(' ', '_')
    safe = safe.replace("'", '%27')
    return f"https://en.wikibooks.org/wiki/Cookbook:{safe}"

# Each recipe mapped to its country_id (and country name for verification)
# Country IDs verified earlier
RECIPE_MAP = {
    # === NIGERIA (128) ===
    "Nigerian achi soup": 128,
    "Nigerian Atama Abak soup": 128,
    "Nigerian Ayan Ekpang": 128,
    "Nigerian beans and plantain": 128,
    "Nigerian Boiled plantain and fish sauce": 128,
    "Nigerian Boiled plantain and vegetable sauce": 128,
    "Nigerian Boiled yam and Uyayak pepper soup": 128,
    "Nigerian Dry Atama and okra soup": 128,
    "Nigerian Dry fish stew": 128,
    "Nigerian Editan Soup": 128,
    "Nigerian Efere Nsana": 128,
    "Nigerian Egg and okra soup": 128,
    "Nigerian melon and bitter leaf soup": 128,
    "Nigerian plantain porridge": 128,
    "Nigerian Roasted Yam and red oil sauce": 128,
    "Nigerian waterleaf soup": 128,

    # === ETHIOPIA (58) ===
    "Yataklete Kilkil": 58,
    "Yemiser Selatta": 58,
    "Yetakelt Alicha": 58,
    "Yetsom Beyaynetu": 58,
    "Yetsom Shiro": 58,
    "Zilzil Tibs": 58,

    # === KENYA (88) ===
    "Chapati": 88,
    "Sukuma Wiki": 88,
    "Mishkaki": 88,
    "Sweet Potato Soup": 88,

    # === TANZANIA (171) ===
    "Ugali": 171,
    "East African Beef Pilaf": 171,

    # === GHANA (66) ===
    "Waakyne": 66,

    # === SENEGAL (152) ===
    "Yassa Poulet": 152,
    "Thiebou Yapp": 152,

    # === SOUTH AFRICA (161) ===
    "South African Curry and Rice": 161,
    "Peri-Peri Chicken": 161,

    # === ZAMBIA (192) ===
    "Zambian Beans and Rice": 192,
    "Zambian Tomato and Onion Salad": 192,
    "Zambian Vegetable Stir-Fry": 192,

    # === ZIMBABWE (193) ===
    "Zitumbuwa": 193,

    # === MALAWI (106) ===
    "Vitumbua": 106,
    "Nsima": 106,

    # === GAMBIA (65) ===
    "Wonjo Bissap": 65,

    # === EGYPT (57) ===
    "Umm Ali": 57,

    # === CÔTE D'IVOIRE (47) ===
    "Kedjenou Chicken": 47,
    "Ivorian Grilled Chicken": 47,
    "Poisson Braise": 47,

    # === ANGOLA (5) ===
    "Moambe": 5,
    "Funje": 5,

    # === LIBERIA (100) ===
    "Damoda": 100,
    "Fumbua": 100,

    # === WEST AFRICA / GENERAL — map to plausible countries with 0 ===
    # These are regional; assign to most representative 0-recipe country
    "African Cabbage Stew": 65,     # Gambia (general West African)
    "Maffé I": 65,
    "Maffé II": 65,
    "Maffé III": 65,
    "Kanda": 65,
    "N'gakasse": 65,
    "Palaver Sauce": 65,
    "Saka-Saka": 5,                 # Angola
    "Riz Gras": 65,
    "Ogolale": 65,
    "Sauce Feuilles": 5,
    "Sauce Gombo": 5,
    "Ngoundja": 5,                  # Fried plantains (Angola)
    "Chikwangue": 5,
    "Sosso-Ngondi": 5,
    "Wasawasa": 88,                 # Kenya
    "Yam and Egg Sauce": 128,       # Nigeria

    # === SOMALIA / EAST AFRICA ===
    "M'batata": 160,

    # === CARIBBEAN ===
    # Dominican Republic (50)
    "Sancocho": 50,
    "Arroz con Gandules": 50,
    "Arroz con Maiz": 50,
    "Tembleque": 50,
    "Mofongo": 50,

    # Trinidad and Tobago (176)
    "Doubles": 176,
    "Kurma": 176,
    "Macaroni Pie": 176,
    "Potato Samosas (Aloo Pies)": 176,
    "Shrimp Fritters (Accra)": 176,

    # Jamaica (84) - moderate count but authentic additions
    "Jamaican Banana Fritters": 84,
    "Callaloo": 84,
    "Rice an' Peas": 84,

    # Barbados (15) - only 4 recipes
    "Coconut Chicken": 15,
    "Hot Pepper Sauce": 15,
    "Chinese Chews (Nut and Date Bars)": 15,

    # Cuba (44) - 0 from Wikibooks
    "Chicken and Corn Empanadas": 44,
}


def parse_recipe_from_markdown(md, url):
    """Extract title, ingredients, instructions from Wikibooks markdown."""
    lines = md.split('\n')
    title = "Unknown"
    ingredients = []
    instructions = []
    
    in_ingredients = False
    in_procedure = False
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Detect title from # header
        if line.startswith('# '):
            title = line[2:].strip()
            continue
        if line.startswith('## '):
            section = line[3:].lower()
            if 'ingredient' in section:
                in_ingredients = True
                in_procedure = False
                continue
            if any(x in section for x in ['procedure', 'preparation', 'instructions', 'directions', 'method']):
                in_procedure = True
                in_ingredients = False
                continue
            # Other section
            in_ingredients = False
            in_procedure = False
            continue
        
        if in_ingredients:
            # Clean markdown bullets, bold
            clean = line.lstrip('-*•\t ')
            clean = clean.replace('**', '').replace('*', '')
            if clean and len(clean) > 2:
                ingredients.append(clean)
            continue
        
        if in_procedure:
            clean = line.lstrip('-*•\t ')
            clean = clean.replace('**', '').replace('*', '')
            if clean and len(clean) > 2:
                instructions.append(clean)
            continue
        
        # Also detect bullet lists outside sections
        if line.startswith('- ') or line.startswith('* '):
            item = line[2:].replace('**', '').replace('*', '')
            if item and len(item) > 2:
                # Could be either; save for late categorization
                if not ingredients and not instructions:
                    ingredients.append(item)
                else:
                    ingredients.append(item)
    
    # If we have no ingredients or instructions, try to extract from raw text
    if not instructions:
        # Look for numbered steps anywhere
        steps = re.findall(r'\n\d+\.[\s\t]+(.+)', md)
        if steps:
            instructions = steps
    
    if not ingredients and not instructions:
        return None  # Unparseable
    
    full_instructions = '\n'.join(instructions) if instructions else ''
    
    return {
        'title': title,
        'ingredients_raw': json.dumps(ingredients),
        'instructions': full_instructions,
        'source_url': url,
        'source_name': 'Wikibooks Cookbook',
        'license': 'CC BY-SA',
        'language': 'en'
    }


def import_recipe(conn, recipe_data, country_id, source_id=2):
    """Insert a parsed recipe into the database."""
    c = conn.cursor()
    c.execute("""
        INSERT INTO recipes (country_id, source_id, title, instructions, ingredients_raw, source_url, source_name, license, language, imported_at, raw_data_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), ?)
    """, (
        country_id, source_id, recipe_data['title'], recipe_data['instructions'],
        recipe_data['ingredients_raw'], recipe_data['source_url'], recipe_data['source_name'],
        recipe_data['license'], recipe_data['language'],
        json.dumps(recipe_data)
    ))
    return c.lastrowid


def main():
    import sqlite3
    import json
    import time
    from hermes_tools import web_extract
    
    conn = sqlite3.connect(DB_PATH)
    imported = 0
    failed = []
    
    items = list(RECIPE_MAP.items())
    batch_size = 5
    total = len(items)
    
    for i in range(0, total, batch_size):
        batch = items[i:i+batch_size]
        urls = []
        for title, cid in batch:
            url = wikibooks_url(title)
            urls.append(url)
        
        print(f"\nBatch {i//batch_size + 1}/{(total+batch_size-1)//batch_size}: {len(urls)} URLs")
        try:
            results = web_extract(urls)
        except Exception as e:
            print(f"  Batch extract failed: {e}")
            for title, cid in batch:
                failed.append(f"{title}: batch error")
            continue
        
        for idx, (title, country_id) in enumerate(batch):
            if idx >= len(results.get('results', [])):
                failed.append(f"{title}: no result slot")
                continue
                
            res = results['results'][idx]
            content = res.get('content', '')
            url = urls[idx]
            
            if not content or 'Wikibooks does not have' in content or 'search for' in content.lower()[:200]:
                failed.append(f"{title}: page missing")
                continue
            
            parsed = parse_recipe_from_markdown(content, url)
            if not parsed or (not parsed['instructions'] and not parsed['ingredients_raw']):
                failed.append(f"{title}: unparseable (has instruction={bool(parsed['instructions'])}, has ingr={bool(parsed['ingredients_raw'])})" if parsed else f"{title}: parse returned None")
                continue
            
            rid = import_recipe(conn, parsed, country_id)
            imported += 1
            print(f"  ✓ {title} → recipe {rid}")
        
        time.sleep(1)
    
    # Log import
    c = conn.cursor()
    c.execute("""
        INSERT INTO import_logs (source_id, records_imported, records_skipped, errors, run_at)
        VALUES (?, ?, ?, ?, datetime('now'))
    """, (2, imported, len(failed), json.dumps(failed)))
    
    conn.commit()
    conn.close()
    
    print(f"\nDone: {imported} imported, {len(failed)} failed")
    if failed:
        print("Failures:")
        for f in failed:
            print(f"  {f}")


if __name__ == '__main__':
    main()
