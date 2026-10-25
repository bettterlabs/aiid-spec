#!/bin/sh
# Runs both reference validators over every shipped .aiid file and checks each verdict
# against where the file lives: test-vectors/valid and examples must pass, test-vectors/invalid
# must fail, and templates/starter.aiid must fail until a person fills in a name.
# Usage: sh test-vectors/run.sh        (from the repo root; needs python3 + pyyaml + jsonschema, node + the yaml package)
set -u
cd "$(dirname "$0")/.." || exit 2
PY="python3 validators/python/aiid_validator.py"
JS="node validators/javascript/aiid_validator.js"
fail=0; total=0
check() { # check <expected 0|1> <file>
  want=$1; f=$2; total=$((total+1))
  $PY "$f" --schema >/dev/null 2>&1; py=$?
  $JS "$f" >/dev/null 2>&1; js=$?
  [ "$py" -eq 2 ] && { echo "python validator: usage/dependency error on $f"; fail=$((fail+1)); return; }
  [ "$js" -eq 2 ] && { echo "node validator: usage/dependency error on $f (npm install yaml)"; fail=$((fail+1)); return; }
  if [ "$py" -ne "$want" ] || [ "$js" -ne "$want" ]; then
    echo "MISMATCH  $f  (expected exit $want; python $py, node $js)"; fail=$((fail+1))
  fi
}
for f in test-vectors/valid/*.aiid examples/*.aiid; do check 0 "$f"; done
for f in test-vectors/invalid/*.aiid templates/starter.aiid; do check 1 "$f"; done
$PY --test >/dev/null 2>&1 || { echo "python self-test failed"; fail=$((fail+1)); }
$JS --test >/dev/null 2>&1 || { echo "node self-test failed"; fail=$((fail+1)); }
echo "$total files checked by both validators, $fail problem(s)."
[ "$fail" -eq 0 ]
