"""Split the exporter bundle into the showcase's live/*.json files (written atomically)."""
import json, os, sys
src, out = sys.argv[1], sys.argv[2]
b = json.load(open(src))
assert b["trades"] and b["summary_metrics"] and b["equity_series"]["dates"], "empty bundle"
for k, v in b.items():
    tmp = os.path.join(out, f".{k}.json.tmp")
    with open(tmp, "w") as f:
        json.dump(v, f, separators=(",", ":"))
    os.replace(tmp, os.path.join(out, f"{k}.json"))
print("split:", ", ".join(sorted(b)))
