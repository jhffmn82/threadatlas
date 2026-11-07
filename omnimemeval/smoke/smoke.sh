python - <<'PY'
import json
for path, keep in (("data/longmemeval/longmemeval_s_cleaned.json", 20), ("data/locomo/locomo10.json", 1)):
    rows = json.load(open(path, encoding="utf-8"))
    json.dump(rows[:keep], open(path, "w", encoding="utf-8"))
PY
./scripts/run_lme_eval.sh --lib threadatlas --env .env.threadatlas --version smoke --workers 4
./scripts/run_locomo_eval.sh --lib threadatlas --env .env.threadatlas --version smoke --workers 10
