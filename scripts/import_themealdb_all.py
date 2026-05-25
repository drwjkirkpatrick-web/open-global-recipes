#!/usr/bin/env python3
"""
Import ALL TheMealDB recipes (not just sparse countries).
"""

import sqlite3, json, urllib.request, time, urllib.parse
from datetime import datetime

DB = "/home/walker/projects/global-recipe-db/recipes.db"
API_BASE = "https://www.themealdb.com/api/json/v1/1"

AREA_TO_COUNTRY = {
    "Afghan": "Afghanistan",
    "Albanian": "Albania",
    "Algerian": "Algeria",
    "Andorran": "Andorra",
    "Angolan": "Angola",
    "Antiguan, Barbudan": "Antigua and Barbuda",
    "Argentine": "Argentina",
    "Armenian": "Armenia",
    "Australian": "Australia",
    "Austrian": "Austria",
    "Azerbaijani": "Azerbaijan",
    "Bahamian": "Bahamas",
    "Bahraini": "Bahrain",
    "Bangladeshi": "Bangladesh",
    "Barbadian": "Barbados",
    "Belarusian": "Belarus",
    "Belgian": "Belgium",
    "Belizean": "Belize",
    "Beninese": "Benin",
    "Bhutanese": "Bhutan",
    "Bolivian": "Bolivia",
    "Bosnian, Herzegovinian": "Bosnia and Herzegovina",
    "Motswana": "Botswana",
    "Brazilian": "Brazil",
    "Bruneian": "Brunei",
    "Bulgarian": "Bulgaria",
    "Burkinabe": "Burkina Faso",
    "Burundian": "Burundi",
    "Cambodian": "Cambodia",
    "Cameroonian": "Cameroon",
    "Canadian": "Canada",
    "Cape Verdian": "Cabo Verde",
    "Central African": "Central African Republic",
    "Chadian": "Chad",
    "Chilean": "Chile",
    "Chinese": "China",
    "Colombian": "Colombia",
    "Costa Rican": "Costa Rica",
    "Croatian": "Croatia",
    "Cuban": "Cuba",
    "Cypriot": "Cyprus",
    "Czech": "Czechia",
    "Danish": "Denmark",
    "Djibouti": "Djibouti",
    "Dominican": "Dominican Republic",
    "Ecuadorean": "Ecuador",
    "Egyptian": "Egypt",
    "Salvadoran": "El Salvador",
    "Equatorial Guinean": "Equatorial Guinea",
    "Eritrean": "Eritrea",
    "Estonian": "Estonia",
    "Ethiopian": "Ethiopia",
    "Fijian": "Fiji",
    "Finnish": "Finland",
    "French": "France",
    "Gabonese": "Gabon",
    "Gambian": "Gambia",
    "Georgian": "Georgia",
    "German": "Germany",
    "Ghanaian": "Ghana",
    "Greek": "Greece",
    "Grenadian": "Grenada",
    "Guatemalan": "Guatemala",
    "Guinean": "Guinea",
    "Guinea-Bissauan": "Guinea-Bissau",
    "Guyanese": "Guyana",
    "Haitian": "Haiti",
    "Honduran": "Honduras",
    "Hungarian": "Hungary",
    "Icelander": "Iceland",
    "Indian": "India",
    "Indonesian": "Indonesia",
    "Iranian": "Iran",
    "Iraqi": "Iraq",
    "Irish": "Ireland",
    "Israeli": "Israel",
    "Italian": "Italy",
    "Ivorian": "Cote d'Ivoire",
    "Jamaican": "Jamaica",
    "Japanese": "Japan",
    "Jordanian": "Jordan",
    "Kazakhstani": "Kazakhstan",
    "Kenyan": "Kenya",
    "Kuwaiti": "Kuwait",
    "Kirghiz": "Kyrgyzstan",
    "Laotian": "Laos",
    "Latvian": "Latvia",
    "Lebanese": "Lebanon",
    "Mosotho": "Lesotho",
    "Liberian": "Liberia",
    "Libyan": "Libya",
    "Liechtensteiner": "Liechtenstein",
    "Lithuanian": "Lithuania",
    "Luxembourger": "Luxembourg",
    "Malagasy": "Madagascar",
    "Malawian": "Malawi",
    "Malaysian": "Malaysia",
    "Maldivan": "Maldives",
    "Malian": "Mali",
    "Maltese": "Malta",
    "Mauritian": "Mauritius",
    "Mexican": "Mexico",
    "Moldovan": "Moldova",
    "Mongolian": "Mongolia",
    "Montenegrin": "Montenegro",
    "Moroccan": "Morocco",
    "Mozambican": "Mozambique",
    "Burmese": "Myanmar",
    "Namibian": "Namibia",
    "Nepalese": "Nepal",
    "Dutch": "Netherlands",
    "New Zealander": "New Zealand",
    "Nicaraguan": "Nicaragua",
    "Nigerien": "Niger",
    "Nigerian": "Nigeria",
    "Macedonian": "North Macedonia",
    "Norwegian": "Norway",
    "Omani": "Oman",
    "Pakistani": "Pakistan",
    "Panamanian": "Panama",
    "Papua New Guinean": "Papua New Guinea",
    "Paraguayan": "Paraguay",
    "Peruvian": "Peru",
    "Filipino": "Philippines",
    "Polish": "Poland",
    "Portuguese": "Portugal",
    "Puerto Rican": "Puerto Rico",
    "Qatari": "Qatar",
    "Congolese": "Congo",
    "Romanian": "Romania",
    "Russian": "Russian Federation",
    "Rwandan": "Rwanda",
    "Saint Lucian": "Saint Lucia",
    "Sammarinese": "San Marino",
    "Samoan": "Samoa",
    "Saudi Arabian": "Saudi Arabia",
    "Senegalese": "Senegal",
    "Serbian": "Serbia",
    "Seychellois": "Seychelles",
    "Sierra Leonean": "Sierra Leone",
    "Singaporean": "Singapore",
    "Slovak": "Slovakia",
    "Slovene": "Slovenia",
    "Solomon Islander": "Solomon Islands",
    "Somali": "Somalia",
    "South African": "South Africa",
    "South Korean": "Korea, Republic of",
    "South Sudanese": "South Sudan",
    "Spanish": "Spain",
    "Sri Lankan": "Sri Lanka",
    "Sudanese": "Sudan",
    "Surinamer": "Suriname",
    "Swedish": "Sweden",
    "Swiss": "Switzerland",
    "Syrian": "Syrian Arab Republic",
    "Taiwanese": "Taiwan",
    "Tadzhik": "Tajikistan",
    "Tanzanian": "Tanzania",
    "Thai": "Thailand",
    "Togolese": "Togo",
    "Tongan": "Tonga",
    "Trinidadian": "Trinidad and Tobago",
    "Tunisian": "Tunisia",
    "Turkish": "Turkey",
    "Turkmen": "Turkmenistan",
    "Tuvaluan": "Tuvalu",
    "Ugandan": "Uganda",
    "Ukrainian": "Ukraine",
    "Emirati": "United Arab Emirates",
    "British": "United Kingdom",
    "American": "United States of America",
    "Uruguayan": "Uruguay",
    "Uzbekistani": "Uzbekistan",
    "Ni-Vanuatu": "Vanuatu",
    "Venezuelan": "Venezuela",
    "Vietnamese": "Viet Nam",
    "Yemeni": "Yemen",
    "Zambian": "Zambia",
    "Zimbabwean": "Zimbabwe",
    "Caribbean": "Jamaica",  # generic mapping
    "Cajun": "United States of America",
    "African": "South Africa",  # generic
    "Argentinian": "Argentina",
    "Korean": "Korea, Republic of",
    "Palestinian": "Palestine",
    "Hong Konger": "Hong Kong",
}

def fetch_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        return None

def extract_ingredients(meal):
    ingredients = []
    for i in range(1, 21):
        ing = meal.get(f"strIngredient{i}", "") or ""
        meas = meal.get(f"strMeasure{i}", "") or ""
        ing = ing.strip()
        if ing:
            raw = f"{meas} {ing}".strip()
            ingredients.append(raw)
    return ingredients

def main():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # Country name → id
    c.execute("SELECT id, name FROM countries")
    name_to_id = {r["name"].lower(): r["id"] for r in c.fetchall()}
    # Fuzzy fallback
    def find_cid(name):
        cid = name_to_id.get(name.lower())
        if cid:
            return cid
        for db_name, db_id in name_to_id.items():
            if name.lower() in db_name or db_name in name.lower():
                return db_id
        return None

    # Resolve areas
    area_to_cid = {}
    for area, country in AREA_TO_COUNTRY.items():
        cid = find_cid(country)
        if cid:
            area_to_cid[area] = cid
    print(f"Mapped {len(area_to_cid)} areas")

    # Get or create source
    c.execute("SELECT id FROM data_sources WHERE name = 'TheMealDB'")
    row = c.fetchone()
    if row:
        source_id = row["id"]
    else:
        c.execute("INSERT INTO data_sources (name, url, license, total_records) VALUES (?, ?, ?, ?)",
                  ("TheMealDB", "https://www.themealdb.com", "CC BY-SA-like / free", 0))
        source_id = c.lastrowid
        conn.commit()

    # Dedup set
    c.execute("SELECT title, source_url FROM recipes WHERE source_id = ?", (source_id,))
    existing = {(r["title"].lower().strip(), r["source_url"]) for r in c.fetchall()}

    total_imported = 0
    total_skipped = 0
    errors = []

    for area, cid in sorted(area_to_cid.items()):
        list_url = f"{API_BASE}/filter.php?a={urllib.parse.quote(area)}"
        list_data = fetch_json(list_url)
        if not list_data or not list_data.get("meals"):
            continue

        meals = list_data["meals"]
        country_name = None
        for n, i in name_to_id.items():
            if i == cid:
                country_name = n
                break
        print(f"[{area} → {country_name}] {len(meals)} meals")

        imported_this = 0
        skipped_this = 0

        for m in meals:
            meal_id = m.get("idMeal")
            if not meal_id:
                continue

            url = f"https://www.themealdb.com/meal/{meal_id}"
            title = m.get("strMeal", "").strip()
            if (title.lower(), url) in existing:
                skipped_this += 1
                continue

            detail = fetch_json(f"{API_BASE}/lookup.php?i={meal_id}")
            time.sleep(0.1)
            if not detail or not detail.get("meals"):
                errors.append(f"No detail for {meal_id}")
                continue

            meal = detail["meals"][0]
            title = meal.get("strMeal", "").strip()
            instructions = meal.get("strInstructions", "").strip()
            ingredients = extract_ingredients(meal)
            source_url = meal.get("strSource", "") or url
            thumb = meal.get("strMealThumb", "")
            youtube = meal.get("strYoutube", "")

            if not ingredients or not instructions:
                skipped_this += 1
                continue

            raw_json = json.dumps({
                "idMeal": meal_id, "strMeal": title, "strCategory": meal.get("strCategory"),
                "strArea": meal.get("strArea"), "strTags": meal.get("strTags"),
                "strMealThumb": thumb, "strYoutube": youtube, "ingredients": ingredients,
            })

            c.execute("""
                INSERT INTO recipes (country_id, source_id, title, instructions, ingredients_raw,
                    source_url, source_name, license, language, cuisine_tag, raw_data_json, imported_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (cid, source_id, title, instructions, json.dumps(ingredients),
                  source_url, "TheMealDB", "CC BY-SA-like / free", "en",
                  meal.get("strCategory", ""), raw_json, datetime.now().isoformat()))

            imported_this += 1
            existing.add((title.lower(), url))

        total_imported += imported_this
        total_skipped += skipped_this
        print(f"  Imported: {imported_this}, Skipped: {skipped_this}")

    # Update source count
    c.execute("SELECT COUNT(*) FROM recipes WHERE source_id = ?", (source_id,))
    total_records = c.fetchone()[0]
    c.execute("UPDATE data_sources SET total_records = ? WHERE id = ?", (total_records, source_id))

    c.execute("""
        INSERT INTO import_logs (source_id, run_at, records_imported, records_skipped, errors)
        VALUES (?, ?, ?, ?, ?)
    """, (source_id, datetime.now().isoformat(), total_imported, total_skipped,
          json.dumps(errors) if errors else None))

    conn.commit()
    conn.close()
    print(f"\n=== DONE === Imported: {total_imported}, Skipped: {total_skipped}, Errors: {len(errors)}")

if __name__ == "__main__":
    main()
