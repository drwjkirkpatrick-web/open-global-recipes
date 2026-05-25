#!/usr/bin/env python3
"""
Reassign dpapathanasiou USA recipes to correct countries based on title keywords.
"""

import sqlite3, json, re
from collections import Counter

DB = "/home/walker/projects/global-recipe-db/recipes.db"

# Keyword → country name mapping
KEYWORD_MAP = {
    # European
    "italian": "Italy", "tuscan": "Italy", "sicilian": "Italy", "roman": "Italy",
    "florentine": "Italy", "milanese": "Italy", "bolognese": "Italy", "parmesan": "Italy",
    "ravioli": "Italy", "risotto": "Italy", "osso buco": "Italy", "bruschetta": "Italy",
    "tiramisu": "Italy", "gnocchi": "Italy", "polenta": "Italy", "lasagna": "Italy",
    "french": "France", "provencal": "France", "normandy": "France", "lyonnaise": "France",
    "coq au vin": "France", "cassoulet": "France", "bouillabaisse": "France", "ratatouille": "France",
    "spanish": "Spain", "paella": "Spain", "tapas": "Spain", "gazpacho": "Spain",
    "german": "Germany", "bavarian": "Germany", "sauerbraten": "Germany", "wiener schnitzel": "Germany",
    "greek": "Greece", "moussaka": "Greece", "tzatziki": "Greece", "spanakopita": "Greece",
    "swedish": "Sweden", "swiss": "Switzerland", "fondue": "Switzerland", "raclette": "Switzerland",
    "polish": "Poland", "pierogi": "Poland", "bigos": "Poland",
    "russian": "Russian Federation", "borscht": "Russian Federation", "stroganoff": "Russian Federation",
    "ukrainian": "Ukraine", "borscht": "Ukraine", "varenyky": "Ukraine",
    "hungarian": "Hungary", "goulash": "Hungary", "paprikash": "Hungary",
    "czech": "Czechia", "austrian": "Austria", "sacher": "Austria",
    "portuguese": "Portugal", "pasteis": "Portugal", "bacalhau": "Portugal",
    "british": "United Kingdom", "english": "United Kingdom", "scottish": "United Kingdom", "irish": "Ireland",
    "welsh": "United Kingdom", "shepherd": "United Kingdom", "yorkshire": "United Kingdom",
    "dutch": "Netherlands", "belgian": "Belgium", "liege": "Belgium",
    "danish": "Denmark", "smorrebrod": "Denmark",
    "finnish": "Finland", "norwegian": "Norway", "icelandic": "Iceland", "iceland": "Iceland",
    "estonian": "Estonia", "latvian": "Latvia", "lithuanian": "Lithuania",
    "serbian": "Serbia", "croatian": "Croatia", "bosnian": "Bosnia and Herzegovina",
    "slovenian": "Slovenia", "slovak": "Slovakia", "macedonian": "North Macedonia",
    "albanian": "Albania", "montenegrin": "Montenegro", "moldovan": "Moldova",
    "bulgarian": "Bulgaria", "macedonian": "Bulgaria", "shopska": "Bulgaria",
    "romanian": "Romania", "sarmale": "Romania", "mamaliga": "Romania",
    "turkish": "Turkey", "kebab": "Turkey", "doner": "Turkey", "lahmacun": "Turkey",
    "moroccan": "Morocco", "tagine": "Morocco", "couscous": "Morocco",
    "tunisian": "Tunisia", "algerian": "Algeria", "egyptian": "Egypt", "koshari": "Egypt",
    "ethiopian": "Ethiopia", "injera": "Ethiopia", "doro wat": "Ethiopia",
    "eritrean": "Eritrea", "sudanese": "Sudan", "somali": "Somalia",
    "nigerian": "Nigeria", "jollof": "Nigeria", "egusi": "Nigeria", "suya": "Nigeria",
    "ghanaian": "Ghana", "kenyan": "Kenya", "ugandan": "Uganda", "tanzanian": "Tanzania",
    "south african": "South Africa", "bobotie": "South Africa", "biltong": "South Africa",
    "zimbabwean": "Zimbabwe", "zambian": "Zambia", "malawian": "Malawi",
    "madagascan": "Madagascar", "mauritian": "Mauritius", "seychellois": "Seychelles",
    "namibian": "Namibia", "botswanan": "Botswana", "angolan": "Angola",
    "mozambican": "Mozambique", "burkinabe": "Burkina Faso", "beninese": "Benin",
    "togolese": "Togo", "liberian": "Liberia", "sierra leonean": "Sierra Leone",
    "gambian": "Gambia", "guinean": "Guinea", "senegalese": "Senegal", "thieboudienne": "Senegal",
    "malian": "Mali", "nigerien": "Niger", "chadian": "Chad", "central african": "Central African Republic",
    "cameroonian": "Cameroon", "congolese": "Congo", "equatorial guinean": "Equatorial Guinea",
    "gabonese": "Gabon", "ivorian": "Cote d'Ivoire",
    
    # Asian
    "chinese": "China", "sichuan": "China", "cantonese": "China", "hunan": "China",
    "mongolian": "China", "dim sum": "China", "kung pao": "China", "mapo tofu": "China",
    "japanese": "Japan", "sushi": "Japan", "ramen": "Japan", "tempura": "Japan", "teriyaki": "Japan",
    "tonkatsu": "Japan", "udon": "Japan", "soba": "Japan", "miso": "Japan", "yakitori": "Japan",
    "korean": "Korea, Republic of", "kimchi": "Korea, Republic of", "bulgogi": "Korea, Republic of",
    "bibimbap": "Korea, Republic of", "japchae": "Korea, Republic of",
    "vietnamese": "Viet Nam", "pho": "Viet Nam", "banh mi": "Viet Nam",
    "thai": "Thailand", "pad thai": "Thailand", "tom yum": "Thailand", "green curry": "Thailand",
    "red curry": "Thailand", "massaman": "Thailand",
    "indian": "India", "punjabi": "India", "bengali": "India", "tamil": "India",
    "gujarati": "India", "kerala": "India", "goan": "India", "hyderabadi": "India",
    "tandoori": "India", "biryani": "India", "samosa": "India", "naan": "India",
    "pakistani": "Pakistan", "karahi": "Pakistan",
    "bangladeshi": "Bangladesh", "sri lankan": "Sri Lanka", "nepalese": "Nepal", "nepali": "Nepal",
    "burmese": "Myanmar", "myanmar": "Myanmar",
    "malaysian": "Malaysia", "singaporean": "Singapore", "indonesian": "Indonesia",
    "filipino": "Philippines", "adobo": "Philippines", "sinigang": "Philippines",
    "laotian": "Laos", "cambodian": "Cambodia", "khmer": "Cambodia",
    "mongolian": "Mongolia", "kazakh": "Kazakhstan", "kyrgyz": "Kyrgyzstan",
    "tajik": "Tajikistan", "turkmen": "Turkmenistan", "uzbek": "Uzbekistan",
    "afghan": "Afghanistan", "persian": "Iran", "iranian": "Iran",
    "iraqi": "Iraq", "syrian": "Syrian Arab Republic", "lebanese": "Lebanon",
    "jordanian": "Jordan", "palestinian": "Palestine", "israeli": "Israel",
    "yemeni": "Yemen", "omani": "Oman", "qatari": "Qatar", "kuwaiti": "Kuwait",
    "bahraini": "Bahrain", "saudi": "Saudi Arabia", "emirati": "United Arab Emirates",
    "georgian": "Georgia", "armenian": "Armenia", "azerbaijani": "Azerbaijan",
    
    # Americas
    "mexican": "Mexico", "enchilada": "Mexico", "taco": "Mexico", "burrito": "Mexico",
    "tostada": "Mexico", "chilaquiles": "Mexico", "mole": "Mexico", "pozole": "Mexico",
    "cuban": "Cuba", "ropa vieja": "Cuba", "mojo": "Cuba",
    "jamaican": "Jamaica", "jerk": "Jamaica", "puerto rican": "Puerto Rico",
    "haitian": "Haiti", "dominican": "Dominican Republic",
    "brazilian": "Brazil", "feijoada": "Brazil", "moqueca": "Brazil", "pao de queijo": "Brazil",
    "argentinian": "Argentina", "asado": "Argentina", "empanada": "Argentina",
    "chilean": "Chile", "peruvian": "Peru", "ceviche": "Peru", "lomo saltado": "Peru",
    "colombian": "Colombia", "arepa": "Colombia", "bandeja paisa": "Colombia",
    "venezuelan": "Venezuela", "tequenos": "Venezuela", "pabellon": "Venezuela",
    "ecuadorean": "Ecuador", "bolivian": "Bolivia", "saltena": "Bolivia",
    "paraguayan": "Paraguay", "uruguayan": "Uruguay", "chivito": "Uruguay",
    "guatemalan": "Guatemala", "honduran": "Honduras", "salvadoran": "El Salvador",
    "pupusa": "El Salvador", "nicaraguan": "Nicaragua", "costa rican": "Costa Rica",
    "panamanian": "Panama",
    "canadian": "Canada", "poutine": "Canada", "nanaimo": "Canada",
    "hawaiian": "Hawaii",
    
    # Oceania
    "australian": "Australia", "new zealand": "New Zealand", "kiwi": "New Zealand",
    "fijian": "Fiji", "samoan": "Samoa", "tongan": "Tonga", "papua new guinean": "Papua New Guinea",
    
    # Middle East / Mediterranean
    "mediterranean": "Greece",
}

def main():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # Get USA id
    c.execute("SELECT id FROM countries WHERE name = 'United States of America'")
    usa_id = c.fetchone()["id"]

    # Get country name → id
    c.execute("SELECT id, name FROM countries")
    name_to_id = {r["name"].lower(): r["id"] for r in c.fetchall()}

    # Build keyword → cid mapping
    kw_to_cid = {}
    for kw, country_name in KEYWORD_MAP.items():
        cid = name_to_id.get(country_name.lower())
        if cid:
            kw_to_cid[kw.lower()] = cid

    # Compile regex patterns per country
    cid_patterns = {}
    for kw, cid in kw_to_cid.items():
        cid_patterns.setdefault(cid, []).append(re.compile(r'\b' + re.escape(kw) + r'\b', re.I))

    # Find USA dpapathanasiou recipes
    c.execute("""
        SELECT id, title
        FROM recipes
        WHERE country_id = ? AND source_id = (SELECT id FROM data_sources WHERE name = 'dpapathanasiou/recipes')
    """, (usa_id,))

    usa_recipes = c.fetchall()
    print(f"USA dpapathanasiou recipes: {len(usa_recipes)}")

    reassigned = Counter()
    batch_updates = []

    for row in usa_recipes:
        rid = row["id"]
        title_lower = row["title"].lower()

        # Score each country
        best_cid = None
        best_score = 0
        for cid, pats in cid_patterns.items():
            score = sum(1 for p in pats if p.search(title_lower))
            if score > best_score:
                best_score = score
                best_cid = cid

        if best_cid:
            batch_updates.append((best_cid, rid))
            reassigned[best_cid] += 1

    print(f"Recipes to reassign: {len(batch_updates)}")

    # Batch update
    c.executemany("UPDATE recipes SET country_id = ? WHERE id = ?", batch_updates)
    conn.commit()

    # Show results
    print("\nTop 20 reassigned countries:")
    for cid, cnt in reassigned.most_common(20):
        c.execute("SELECT name FROM countries WHERE id = ?", (cid,))
        name = c.fetchone()["name"]
        print(f"  {name}: {cnt}")

    conn.close()
    print(f"\nDone! Reassigned {len(batch_updates)} recipes from USA to their correct countries.")

if __name__ == "__main__":
    main()
