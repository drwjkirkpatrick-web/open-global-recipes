CREATE TABLE countries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    iso_code TEXT UNIQUE,
    name TEXT NOT NULL,
    region TEXT,
    cuisine_keywords TEXT,
    status TEXT DEFAULT 'pending',
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE data_sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    url TEXT,
    license TEXT,
    description TEXT,
    total_records INTEGER,
    format TEXT,
    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE import_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id INTEGER,
    country_id INTEGER,
    records_imported INTEGER DEFAULT 0,
    records_skipped INTEGER DEFAULT 0,
    errors TEXT,
    run_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (source_id) REFERENCES data_sources(id),
    FOREIGN KEY (country_id) REFERENCES countries(id)
);
CREATE TABLE ingredients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    normalized_name TEXT UNIQUE
);
CREATE TABLE recipe_btd_scores (
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
        );
CREATE TABLE recipe_ingredients (
    recipe_id INTEGER,
    ingredient_id INTEGER,
    quantity TEXT,
    unit TEXT,
    raw_text TEXT,
    PRIMARY KEY (recipe_id, ingredient_id, raw_text),
    FOREIGN KEY (recipe_id) REFERENCES recipes(id),
    FOREIGN KEY (ingredient_id) REFERENCES ingredients(id)
);
CREATE TABLE recipes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    country_id INTEGER,
    source_id INTEGER,
    title TEXT NOT NULL,
    instructions TEXT,
    ingredients_raw TEXT,
    source_url TEXT,
    source_name TEXT,
    license TEXT,
    language TEXT DEFAULT 'en',
    cuisine_tag TEXT,
    raw_data_json TEXT,
    imported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (country_id) REFERENCES countries(id),
    FOREIGN KEY (source_id) REFERENCES data_sources(id)
);
CREATE INDEX idx_btd_scores_recipe ON recipe_btd_scores(recipe_id)
    ;
CREATE INDEX idx_btd_scores_query ON recipe_btd_scores(blood_type, verdict, score)
    ;

-- Seed countries
INSERT INTO countries VALUES (1, 'AFG', 'Afghanistan', 'Asia', 'Afghan', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (2, 'ALB', 'Albania', 'Europe', 'Albanian', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (3, 'DZA', 'Algeria', 'Africa', 'Algerian', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (4, 'AND', 'Andorra', 'Europe', 'Andorran', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (5, 'AGO', 'Angola', 'Africa', 'Angolan', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (6, 'ATG', 'Antigua and Barbuda', 'Americas', 'Antiguan', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (7, 'ARG', 'Argentina', 'Americas', 'Argentine', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (8, 'ARM', 'Armenia', 'Asia', 'Armenian', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (9, 'AUS', 'Australia', 'Oceania', 'Australian', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (10, 'AUT', 'Austria', 'Europe', 'Austrian', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (11, 'AZE', 'Azerbaijan', 'Asia', 'Azerbaijani', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (12, 'BHS', 'Bahamas', 'Americas', 'Bahamian', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (13, 'BHR', 'Bahrain', 'Asia', 'Bahraini', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (14, 'BGD', 'Bangladesh', 'Asia', 'Bangladeshi', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (15, 'BRB', 'Barbados', 'Americas', 'Barbadian', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (16, 'BLR', 'Belarus', 'Europe', 'Belarusian', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (17, 'BEL', 'Belgium', 'Europe', 'Belgian', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (18, 'BLZ', 'Belize', 'Americas', 'Belizean', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (19, 'BEN', 'Benin', 'Africa', 'Beninese', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (20, 'BTN', 'Bhutan', 'Asia', 'Bhutanese', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (21, 'BOL', 'Bolivia', 'Americas', 'Bolivian', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (22, 'BIH', 'Bosnia and Herzegovina', 'Europe', 'Bosnian', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (23, 'BWA', 'Botswana', 'Africa', 'Botswana', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (24, 'BRA', 'Brazil', 'Americas', 'Brazilian', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (25, 'BRN', 'Brunei', 'Asia', 'Bruneian', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (26, 'BGR', 'Bulgaria', 'Europe', 'Bulgarian', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (27, 'BFA', 'Burkina Faso', 'Africa', 'Burkinabe', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (28, 'BDI', 'Burundi', 'Africa', 'Burundian', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (29, 'CPV', 'Cabo Verde', 'Africa', 'Cape Verdean', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (30, 'KHM', 'Cambodia', 'Asia', 'Cambodian', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (31, 'CMR', 'Cameroon', 'Africa', 'Cameroonian', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (32, 'CAN', 'Canada', 'Americas', 'Canadian', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (33, 'CAF', 'Central African Republic', 'Africa', 'Central African', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (34, 'TCD', 'Chad', 'Africa', 'Chadian', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (35, 'CHL', 'Chile', 'Americas', 'Chilean', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (36, 'CHN', 'China', 'Asia', 'Chinese', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (37, 'COL', 'Colombia', 'Americas', 'Colombian', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (38, 'COM', 'Comoros', 'Africa', 'Comoran', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (39, 'COG', 'Congo', 'Africa', 'Congolese', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (40, 'COD', 'Congo, Democratic Republic of the', 'Africa', 'Congolese', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (41, 'CRI', 'Costa Rica', 'Americas', 'Costa Rican', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (42, 'CIV', "Cote d'Ivoire", 'Africa', 'Ivorian', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (43, 'HRV', 'Croatia', 'Europe', 'Croatian', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (44, 'CUB', 'Cuba', 'Americas', 'Cuban', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (45, 'CYP', 'Cyprus', 'Europe', 'Cypriot', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (46, 'CZE', 'Czech Republic', 'Europe', 'Czech', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (47, 'DNK', 'Denmark', 'Europe', 'Danish', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (48, 'DJI', 'Djibouti', 'Africa', 'Djiboutian', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (49, 'DMA', 'Dominica', 'Americas', 'Dominican', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (50, 'DOM', 'Dominican Republic', 'Americas', 'Dominican', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (51, 'ECU', 'Ecuador', 'Americas', 'Ecuadorian', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (52, 'EGY', 'Egypt', 'Africa', 'Egyptian', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (53, 'SLV', 'El Salvador', 'Americas', 'Salvadoran', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (54, 'GNQ', 'Equatorial Guinea', 'Africa', 'Equatorial Guinean', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (55, 'ERI', 'Eritrea', 'Africa', 'Eritrean', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (56, 'EST', 'Estonia', 'Europe', 'Estonian', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (57, 'SWZ', 'Eswatini', 'Africa', 'Swazi', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (58, 'ETH', 'Ethiopia', 'Africa', 'Ethiopian', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (59, 'FJI', 'Fiji', 'Oceania', 'Fijian', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (60, 'FIN', 'Finland', 'Europe', 'Finnish', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (61, 'FRA', 'France', 'Europe', 'French', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (62, 'GAB', 'Gabon', 'Africa', 'Gabonese', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (63, 'GMB', 'Gambia', 'Africa', 'Gambian', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (64, 'GEO', 'Georgia', 'Asia', 'Georgian', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (65, 'DEU', 'Germany', 'Europe', 'German', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (66, 'GHA', 'Ghana', 'Africa', 'Ghanaian', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (67, 'GRC', 'Greece', 'Europe', 'Greek', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (68, 'GRD', 'Grenada', 'Americas', 'Grenadian', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (69, 'GTM', 'Guatemala', 'Americas', 'Guatemalan', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (70, 'GIN', 'Guinea', 'Africa', 'Guinean', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (71, 'GNB', 'Guinea-Bissau', 'Africa', 'Guinea-Bissauan', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (72, 'GUY', 'Guyana', 'Americas', 'Guyanese', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (73, 'HTI', 'Haiti', 'Americas', 'Haitian', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (74, 'HND', 'Honduras', 'Americas', 'Honduran', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (75, 'HUN', 'Hungary', 'Europe', 'Hungarian', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (76, 'ISL', 'Iceland', 'Europe', 'Icelandic', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (77, 'IND', 'India', 'Asia', 'Indian', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (78, 'IDN', 'Indonesia', 'Asia', 'Indonesian', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (79, 'IRN', 'Iran', 'Asia', 'Iranian', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (80, 'IRQ', 'Iraq', 'Asia', 'Iraqi', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (81, 'IRL', 'Ireland', 'Europe', 'Irish', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (82, 'ISR', 'Israel', 'Asia', 'Israeli', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (83, 'ITA', 'Italy', 'Europe', 'Italian', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (84, 'JAM', 'Jamaica', 'Americas', 'Jamaican', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (85, 'JPN', 'Japan', 'Asia', 'Japanese', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (86, 'JOR', 'Jordan', 'Asia', 'Jordanian', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (87, 'KAZ', 'Kazakhstan', 'Asia', 'Kazakhstani', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (88, 'KEN', 'Kenya', 'Africa', 'Kenyan', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (89, 'KIR', 'Kiribati', 'Oceania', 'I-Kiribati', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (90, 'PRK', "Korea, Democratic People's Republic of", 'Asia', 'North Korean', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (91, 'KOR', 'Korea, Republic of', 'Asia', 'Korean,South Korean', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (92, 'KWT', 'Kuwait', 'Asia', 'Kuwaiti', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (93, 'KGZ', 'Kyrgyzstan', 'Asia', 'Kyrgyzstani', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (94, 'LAO', 'Laos', 'Asia', 'Lao,Laotian', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (95, 'LVA', 'Latvia', 'Europe', 'Latvian', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (96, 'LBN', 'Lebanon', 'Asia', 'Lebanese', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (97, 'LSO', 'Lesotho', 'Africa', 'Basotho', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (98, 'LBR', 'Liberia', 'Africa', 'Liberian', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (99, 'LBY', 'Libya', 'Africa', 'Libyan', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (100, 'LIE', 'Liechtenstein', 'Europe', 'Liechtenstein', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (101, 'LTU', 'Lithuania', 'Europe', 'Lithuanian', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (102, 'LUX', 'Luxembourg', 'Europe', 'Luxembourg', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (103, 'MDG', 'Madagascar', 'Africa', 'Malagasy', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (104, 'MWI', 'Malawi', 'Africa', 'Malawian', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (105, 'MYS', 'Malaysia', 'Asia', 'Malaysian', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (106, 'MDV', 'Maldives', 'Asia', 'Maldivian', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (107, 'MLI', 'Mali', 'Africa', 'Malian', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (108, 'MLT', 'Malta', 'Europe', 'Maltese', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (109, 'MHL', 'Marshall Islands', 'Oceania', 'Marshallese', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (110, 'MRT', 'Mauritania', 'Africa', 'Mauritanian', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (111, 'MUS', 'Mauritius', 'Africa', 'Mauritian', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (112, 'MEX', 'Mexico', 'Americas', 'Mexican', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (113, 'FSM', 'Micronesia, Federated States of', 'Oceania', 'Micronesian', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (114, 'MDA', 'Moldova', 'Europe', 'Moldovan', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (115, 'MCO', 'Monaco', 'Europe', 'Monegasque', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (116, 'MNG', 'Mongolia', 'Asia', 'Mongolian', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (117, 'MNE', 'Montenegro', 'Europe', 'Montenegrin', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (118, 'MAR', 'Morocco', 'Africa', 'Moroccan', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (119, 'MOZ', 'Mozambique', 'Africa', 'Mozambican', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (120, 'MMR', 'Myanmar', 'Asia', 'Burmese', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (121, 'NAM', 'Namibia', 'Africa', 'Namibian', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (122, 'NRU', 'Nauru', 'Oceania', 'Nauruan', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (123, 'NPL', 'Nepal', 'Asia', 'Nepali,Nepalese', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (124, 'NLD', 'Netherlands', 'Europe', 'Dutch', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (125, 'NZL', 'New Zealand', 'Oceania', 'New Zealand', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (126, 'NIC', 'Nicaragua', 'Americas', 'Nicaraguan', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (127, 'NER', 'Niger', 'Africa', 'Nigerien', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (128, 'NGA', 'Nigeria', 'Africa', 'Nigerian', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (129, 'MKD', 'North Macedonia', 'Europe', 'Macedonian', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (130, 'NOR', 'Norway', 'Europe', 'Norwegian', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (131, 'OMN', 'Oman', 'Asia', 'Omani', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (132, 'PAK', 'Pakistan', 'Asia', 'Pakistani', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (133, 'PLW', 'Palau', 'Oceania', 'Palauan', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (134, 'PAN', 'Panama', 'Americas', 'Panamanian', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (135, 'PNG', 'Papua New Guinea', 'Oceania', 'Papua New Guinean', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (136, 'PRY', 'Paraguay', 'Americas', 'Paraguayan', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (137, 'PER', 'Peru', 'Americas', 'Peruvian', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (138, 'PHL', 'Philippines', 'Asia', 'Filipino,Philippine', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (139, 'POL', 'Poland', 'Europe', 'Polish', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (140, 'PRT', 'Portugal', 'Europe', 'Portuguese', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (141, 'QAT', 'Qatar', 'Asia', 'Qatari', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (142, 'ROU', 'Romania', 'Europe', 'Romanian', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (143, 'RUS', 'Russian Federation', 'Europe', 'Russian', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (144, 'RWA', 'Rwanda', 'Africa', 'Rwandan', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (145, 'KNA', 'Saint Kitts and Nevis', 'Americas', 'Saint Kitts and Nevis', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (146, 'LCA', 'Saint Lucia', 'Americas', 'Saint Lucian', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (147, 'VCT', 'Saint Vincent and the Grenadines', 'Americas', 'Saint Vincentian', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (148, 'WSM', 'Samoa', 'Oceania', 'Samoan', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (149, 'SMR', 'San Marino', 'Europe', 'Sammarinese', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (150, 'STP', 'Sao Tome and Principe', 'Africa', 'Sao Tomean', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (151, 'SAU', 'Saudi Arabia', 'Asia', 'Saudi Arabian', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (152, 'SEN', 'Senegal', 'Africa', 'Senegalese', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (153, 'SRB', 'Serbia', 'Europe', 'Serbian', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (154, 'SYC', 'Seychelles', 'Africa', 'Seychellois', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (155, 'SLE', 'Sierra Leone', 'Africa', 'Sierra Leonean', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (156, 'SGP', 'Singapore', 'Asia', 'Singaporean', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (157, 'SVK', 'Slovakia', 'Europe', 'Slovak', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (158, 'SVN', 'Slovenia', 'Europe', 'Slovenian', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (159, 'SLB', 'Solomon Islands', 'Oceania', 'Solomon Islander', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (160, 'SOM', 'Somalia', 'Africa', 'Somali', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (161, 'ZAF', 'South Africa', 'Africa', 'South African', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (162, 'SSD', 'South Sudan', 'Africa', 'South Sudanese', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (163, 'ESP', 'Spain', 'Europe', 'Spanish', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (164, 'LKA', 'Sri Lanka', 'Asia', 'Sri Lankan', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (165, 'SDN', 'Sudan', 'Africa', 'Sudanese', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (166, 'SUR', 'Suriname', 'Americas', 'Surinamese', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (167, 'SWE', 'Sweden', 'Europe', 'Swedish', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (168, 'CHE', 'Switzerland', 'Europe', 'Swiss', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (169, 'SYR', 'Syrian Arab Republic', 'Asia', 'Syrian', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (170, 'TJK', 'Tajikistan', 'Asia', 'Tajikistani', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (171, 'TZA', 'Tanzania', 'Africa', 'Tanzanian', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (172, 'THA', 'Thailand', 'Asia', 'Thai', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (173, 'TLS', 'Timor-Leste', 'Asia', 'Timorese', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (174, 'TGO', 'Togo', 'Africa', 'Togolese', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (175, 'TON', 'Tonga', 'Oceania', 'Tongan', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (176, 'TTO', 'Trinidad and Tobago', 'Americas', 'Trinidadian,Tobagonian', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (177, 'TUN', 'Tunisia', 'Africa', 'Tunisian', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (178, 'TUR', 'Turkey', 'Asia', 'Turkish', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (179, 'TKM', 'Turkmenistan', 'Asia', 'Turkmen', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (180, 'TUV', 'Tuvalu', 'Oceania', 'Tuvaluan', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (181, 'UGA', 'Uganda', 'Africa', 'Ugandan', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (182, 'UKR', 'Ukraine', 'Europe', 'Ukrainian', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (183, 'ARE', 'United Arab Emirates', 'Asia', 'Emirati', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (184, 'GBR', 'United Kingdom', 'Europe', 'British', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (185, 'USA', 'United States of America', 'Americas', 'American', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (186, 'URY', 'Uruguay', 'Americas', 'Uruguayan', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (187, 'UZB', 'Uzbekistan', 'Asia', 'Uzbekistani', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (188, 'VUT', 'Vanuatu', 'Oceania', 'Ni-Vanuatu', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (189, 'VEN', 'Venezuela', 'Americas', 'Venezuelan', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (190, 'VNM', 'Viet Nam', 'Asia', 'Vietnamese', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (191, 'YEM', 'Yemen', 'Asia', 'Yemeni', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (192, 'ZMB', 'Zambia', 'Africa', 'Zambian', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (193, 'ZWE', 'Zimbabwe', 'Africa', 'Zimbabwean', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (194, 'PSE', 'Palestine, State of', 'Asia', 'Palestinian', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (195, 'VAT', 'Holy See', 'Europe', 'Vatican', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (196, 'TWN', 'Taiwan', 'Asia', 'Taiwanese', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (197, 'KOS', 'Kosovo', 'Europe', 'Kosovar', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (198, 'HKG', 'Hong Kong', 'Asia', 'Hong Kong', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (199, 'MAC', 'Macao', 'Asia', 'Macanese', 'pending', NULL, '2026-05-17 02:50:56');
INSERT INTO countries VALUES (200, NULL, 'Hawaii', NULL, 'Hawaiian, Local Hawaii, Hawaiʻi', 'pending', NULL, '2026-05-17 21:39:24');

-- Seed data sources
INSERT INTO data_sources VALUES (1, 'dpapathanasiou/recipes', 'https://github.com/dpapathanasiou/recipes', 'MIT', '~78K JSON recipes scraped from various sites, organized by index', 73284, NULL, '2026-05-17 02:54:11');
INSERT INTO data_sources VALUES (2, 'Wikibooks Cookbook', 'https://en.wikibooks.org/wiki/Cookbook', 'CC BY-SA', 'Community-contributed open cookbook', 82, NULL, '2026-05-17 03:06:38');
INSERT INTO data_sources VALUES (3, 'blood-type-diet', 'file:///home/walker/.hermes/skills/blood-type-diet/data/btdiet.db', 'Unknown', 'Recipes from the blood-type-diet skill database (themealdb, dadamo, allrecipes sources)', 674, 'SQLite', '2026-05-16T20:26:17.751386');
INSERT INTO data_sources VALUES (4, 'blood-type-diet', 'file:///home/walker/.hermes/skills/blood-type-diet/data/btdiet.db', 'Unknown', 'Recipes from the blood-type-diet skill database (themealdb, dadamo, allrecipes sources)', 0, 'SQLite', '2026-05-16T20:26:37.483609');
INSERT INTO data_sources VALUES (5, 'photo_import', '', 'unknown', 'Recipes imported from user-submitted photos via OCR', NULL, NULL, '2026-05-17 18:59:36');
INSERT INTO data_sources VALUES (6, 'Hawaii Nutrition Center', NULL, NULL, NULL, 8, NULL, '2026-05-17 21:39:24');
INSERT INTO data_sources VALUES (7, 'TheMealDB', 'https://www.themealdb.com', 'CC BY-SA-like / free', NULL, 472, NULL, '2026-05-18 00:12:36');
INSERT INTO data_sources VALUES (8, 'world-wide-dishes', 'https://github.com/shawngraham/world-wide-dishes', 'Unknown / CC', NULL, 750, NULL, '2026-05-18 00:25:56');
INSERT INTO data_sources VALUES (9, 'INLUS / Food.com (scraped)', 'https://inlus.org / https://food.com', 'Fair use / personal', NULL, 20, NULL, '2026-05-18 00:36:45');
INSERT INTO data_sources VALUES (10, 'Scraped Web Sources', 'various', 'Fair use / personal', NULL, 29, NULL, '2026-05-18 00:39:52');