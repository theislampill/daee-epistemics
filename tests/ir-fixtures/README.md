# Diagnostic IR Fixture Policy

`tools/check_ir_instance_integrity.py` validates positive IR fixtures under `valid/` and treats
JSON files under `invalid/` as expected-invalid regression fixtures. The compiled-map-missing
case is embedded in the checker because the current catalogue intentionally has no module absent
from `skill/compiled-module-map.json`; the embedded fixture removes one compiled-map entry in
memory to prove that failure mode.
