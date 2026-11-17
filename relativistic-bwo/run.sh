#!/usr/bin/env bash
# Builds the designs, solves the runs the report draws and writes results/. Needs emcraft-cli
# (EMCRAFT_CLI; each run takes 10–20 minutes and under 0.3 GB of memory), SolidCraft (the flatpak
# io.tangencylabs.solidcraft, or solidcraft-cli on PATH), Python 3 with Pillow, and ffmpeg.
# The design scans (scripts/scan-*, sync-*, more-*, taper-*, collect-*, refine-*: results/*.out)
# are run one at a time with scripts/_scan.sh.
set -euo pipefail
cd "$(dirname "$0")"
EMCRAFT_CLI=${EMCRAFT_CLI:-emcraft-cli}
sc() { if command -v solidcraft-cli >/dev/null; then solidcraft-cli "$@"; else flatpak run --filesystem="$PWD" --command=solidcraft-cli io.tangencylabs.solidcraft "$@"; fi; }
python3 model/make.py
for n in ku sband ku-view sband-view; do sc run "$PWD/model/$n.script.json" --save "$PWD/model/$n.sc" > /dev/null; done
(cd scripts && for n in cell-44 final-ku final-sband anim-ku-growth anim-ku-rf anim-sband-growth anim-sband-rf; do
    "$EMCRAFT_CLI" run "$n.json" > "../results/$n.out"; done)
python3 scripts/principle.py
python3 scripts/views.py
python3 scripts/figures.py dispersion sections evolution animations final-ku final-sband
