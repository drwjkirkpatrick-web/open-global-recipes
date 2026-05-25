# Daily Curation Guide

The daily curation script picks 3 recipes from 3 different countries every day and renders a styled PDF or plain text output.

---

## Basic Usage

```bash
# Text to stdout
python3 scripts/daily_curation.py --text

# PDF to exports/daily_YYYY-MM-DD.pdf
python3 scripts/daily_curation.py --pdf

# Custom path
python3 scripts/daily_curation.py --pdf --output /tmp/today.pdf
```

---

## With Blood Type Filtering

```bash
python3 scripts/daily_curation.py --pdf --blood-type B
```

This queries `recipe_btd_scores` for `verdict IN ('green', 'yellow')`, guaranteeing zero avoid ingredients for that blood type.

---

## What the Output Looks Like

```
📅 Daily Global Recipe Trio — Monday, May 25, 2025
==================================================
Blood Type B | Green/Yellow only

  1. Green Curry Paste  🌍 Thailand
  2. Moussaka           🌍 Greece
  3. Feijoada           🌍 Brazil

Common thread — all three use: garlic, onion, olive oil

──────────────────────────────────────────────────
  1. Green Curry Paste (Thailand)
──────────────────────────────────────────────────
   Score: 85/100 | Verdict: green
   ✅ Beneficial: 6  🔴 Avoid: 0

   Ingredients:
     - 1/2 cup fresh cilantro
     - 2 green chilies
     ...

   Instructions:
     1. Blend all ingredients in a food processor.
     ...
```

---

## Cron Setup

### Standard crontab

```bash
0 8 * * * cd /path/to/open-global-recipes && python3 scripts/daily_curation.py --pdf --blood-type B >> /var/log/daily_recipes.log 2>&1
```

### Hermes cron

```bash
hermes cronjob create --name "Daily Type B Recipes" \
  --schedule "0 8 * * *" \
  --script "python3 /path/to/open-global-recipes/scripts/daily_curation.py --pdf --blood-type B"
```

### Systemd timer (headless server)

Create `/etc/systemd/system/open-recipes-daily.service`:

```ini
[Unit]
Description=Daily Open Global Recipes PDF

[Service]
Type=oneshot
ExecStart=/usr/bin/python3 /path/to/open-global-recipes/scripts/daily_curation.py --pdf
Environment=OPEN_GLOBAL_RECIPES_DB=/path/to/recipes.db
Environment=BTD_DIET_DB=/path/to/btdiet.db
```

Create `/etc/systemd/system/open-recipes-daily.timer`:

```ini
[Unit]
Description=Run daily recipe curator at 8:00 AM

[Timer]
OnCalendar=*-*-* 08:00:00
Persistent=true

[Install]
WantedBy=timers.target
```

Enable:
```bash
systemctl daemon-reload
systemctl enable --now open-recipes-daily.timer
```

---

## PDF Delivery Options

### Local file
The `--pdf` flag writes to `exports/daily_YYYY-MM-DD.pdf` by default.

### Telegram
If running under Hermes with Telegram integration, deliver via:
```python
# In a wrapper script:
import subprocess, datetime, os
from hermes_tools import send_message
subprocess.run(["python3", "scripts/daily_curation.py", "--pdf"])
path = f"exports/daily_{datetime.date.today().isoformat()}.pdf"
send_message(action="send", target="telegram", message=f"📅 Daily Recipe Trio\nMEDIA:{os.path.abspath(path)}")
```

### Email
Use `mutt`, `mail`, or Himalaya:
```bash
python3 scripts/daily_curation.py --pdf
echo "Your daily recipe PDF is attached." | mail -s "Daily Global Recipes" -A exports/daily_*.pdf user@example.com
```

### Discord / Slack
Upload as file attachment via webhook:
```bash
curl -F "file1=@exports/daily_$(date +%F).pdf" \
     -F "payload_json={\"content\":\"📅 Daily Recipes\"}" \
     $WEBHOOK_URL
```

---

## Customization

### Minimum recipes per country
Edit `MIN_RECIPES_PER_COUNTRY` in `scripts/daily_curation.py`. Default is 5.

### Flag output
Country emojis are not embedded in the database; the script uses a hardcoded `FLAG_MAP` for ~40 top cuisines. Add more as needed.

### PDF styling
The default uses weasyprint with inline CSS. Edit the `write_pdf()` function for custom fonts, headers, or images.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| "Not enough countries" | Lower `MIN_RECIPES_PER_COUNTRY` or run more imports |
| "BTD database not found" | Install BTD add-on or omit `--blood-type` |
| "weasyprint not installed" | `pip install weasyprint` or the script falls back to Markdown |
| PDF is huge | Reduce number of recipes per export; filter with `--blood-type` |
| Same countries every day | That's randomness — statistically normal over short windows |
| Missing ingredients | Use `ingredients_raw` JSON fallback when `recipe_ingredients` is empty |
