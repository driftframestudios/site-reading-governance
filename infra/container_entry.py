"""Select the standard-library validation job or the confined Pages projection."""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
from container_runtime import run
from validate_governance import validate_pair


def produce(output):
    pairs=(("schemas/receipt.schema.json","examples/receipt.json"),("schemas/bounded-caller.schema.json","examples/bounded-caller.json"))
    for schema,document in pairs:
        errors=validate_pair(Path(schema),Path(document))
        if errors: raise ValueError("governance-example-admission")
    (output/"validation.json").write_text(json.dumps({"status":"passed","pairs":[{"schema":s,"document":d} for s,d in pairs]},sort_keys=True,indent=2)+"\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", choices=("validation", "projection"), default="validation")
    args = parser.parse_args()
    if args.profile == "projection":
        from container_projection import run_projection
        run_projection()
    else:
        run(produce)
