from pathlib import Path
import sys

import candidate_source_helper


logical_source = Path(__file__).resolve()
if Path(sys.argv[0]).resolve() != logical_source:
    raise SystemExit("logical argv/source mismatch")
root = logical_source.parents[1]
resource = (
    root
    / "tests/validation-integrity/fixtures/candidate-source-custody/probe_resource.txt"
).read_text(encoding="utf-8").strip()
output = Path(sys.argv[sys.argv.index("--outputs") + 1])
if not output.is_file():
    raise SystemExit("frozen output missing")
print(f"custody-source:{candidate_source_helper.VALUE}:{resource}")
