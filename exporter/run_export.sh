#!/bin/bash
# Showcase refresh: index-only model from the 4 Horse bot, published with a 1-month delay.
# cron (weekdays 18:30 IST): ~/quant-showcase/exporter/run_export.sh >> ~/quant-showcase/exporter/export.log 2>&1
set -euo pipefail
cd "$(dirname "$0")"
OUT=~/quant-showcase/data/live
mkdir -p "$OUT"
echo "== $(date '+%F %T') export start"
U=$(docker exec marketdb printenv POSTGRES_USER); D=$(docker exec marketdb printenv POSTGRES_DB)
docker exec -i marketdb psql -U "$U" -d "$D" -tA -F, > /tmp/qs_nifty.csv <<'SQL'
select distinct on (c.ts::date) c.ts::date, c.close
from candles c join symbols s on s.id = c.symbol_id
where s.symbol = 'NIFTY50' and c.resolution = 30 and c.ts >= '2019-12-01'
order by c.ts::date, c.ts desc;
SQL
test "$(wc -l < /tmp/qs_nifty.csv)" -gt 1000
docker cp /tmp/qs_nifty.csv horse_apocalypse_container:/tmp/qs_nifty.csv
docker exec -i -w /app horse_apocalypse_container python - < export_model.py
docker cp horse_apocalypse_container:/tmp/qs_bundle.json /tmp/qs_bundle.json
python3 split_bundle.py /tmp/qs_bundle.json "$OUT"
echo "== $(date '+%F %T') export done"
