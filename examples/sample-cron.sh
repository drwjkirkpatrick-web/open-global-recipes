#!/bin/bash
# Example daily cron script for open-global-recipes curation.
# Install with: crontab -e
#   0 8 * * * /path/to/open-global-recipes/examples/sample-cron.sh

cd "$(dirname "$0")/.." || exit 1
export OPEN_GLOBAL_RECIPES_DB="${HOME}/projects/global-recipe-db/recipes.db"
export BTD_DIET_DB="${HOME}/.hermes/skills/blood-type-diet/data/btdiet.db"

today=$(date +%F)
python3 scripts/daily_curation.py --pdf --blood-type B --output "exports/daily_${today}.pdf"
