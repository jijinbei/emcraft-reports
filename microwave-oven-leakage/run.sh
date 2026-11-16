#!/usr/bin/env bash
# Builds the designs, solves every model and writes results/. Needs emcraft-cli (EMCRAFT_CLI)
# and SolidCraft (the flatpak io.tangencylabs.solidcraft, or solidcraft-cli on PATH).
set -euo pipefail
cd "$(dirname "$0")"
EMCRAFT_CLI=${EMCRAFT_CLI:-emcraft-cli}
sc() { if command -v solidcraft-cli >/dev/null; then solidcraft-cli "$@"; else flatpak run --filesystem="$PWD" --command=solidcraft-cli io.tangencylabs.solidcraft "$@"; fi; }
python3 model/make.py
for n in oven-gap oven-choke oven-slotted; do sc run "$PWD/model/$n.script.json" --save "$PWD/model/$n.solidcraft" > /dev/null; done
python3 scripts/make.py
(cd scripts && for n in oven-gap oven-choke oven-slotted; do "$EMCRAFT_CLI" run "$n.json" > "../results/$n.out"; done)
python3 scripts/leak.py results/oven-gap.out results/oven-choke.out results/oven-slotted.out
EMCRAFT_CLI=$EMCRAFT_CLI python3 scripts/cell.py
