# EMCraft reports

Engineering analysis reports made with [EMCraft](https://github.com/jijinbei/emcraft), the
open-source electromagnetic field simulator, with models designed in SolidCraft, the parametric
CAD application. The published reports, as PDFs: **https://site.jijinbei.jp/emcraft-reports/**

Every number a report draws a conclusion from is checked the way EMCraft's own solvers are:
against a closed form or a published result where one exists, and by refining the mesh.

| Report | Question | Status |
|---|---|---|
| [microwave-oven-leakage](microwave-oven-leakage/) | Does a household microwave oven's door keep its 2.45 GHz field inside, below 5 mW/cm² at 5 cm? | v0.1: the whole oven (2.3 million unknowns), three doors, solved with EMCraft v0.1 |
| [relativistic-bwo](relativistic-bwo/) | Does EMCraft's r–z particle simulation reproduce a published relativistic BWO, and can it design one from rules of thumb? | Ku band: 15.32 GHz against 15.575 GHz published; S band designed: 3.40 GHz, 0.64 GW, 17 % (Japanese draft) |

These are simulation studies. They show how a design behaves and why; they are not
certification tests, which need measurements on the real product.

## The form of a report

A report is a folder you can run again from scratch:

| Path | What it is |
|---|---|
| `report.py` | its recipe (`REPORT = Report(…)`, from `emreports`): the steps that write its scripts, the SolidCraft designs, the EMCraft runs, the analysis, the figures, the documents and which one is published |
| `model/` | the 3D models: SolidCraft command scripts (`*.script.json`, written by `model/make.py`) and the designs they build |
| `scripts/` | the EMCraft scripts (`<run>.json`, written by `scripts/make.py`) and the Python that draws the figures |
| `results/<run>.out` | EMCraft's replies to a run, beside its record `<run>.run.json` (the script's hash, the EMCraft version, the time and the peak memory) |
| `results/*.png, *.svg, *.mp4` | the figures and animations the report shows |
| `report.typ` | the report in English, in [Typst](https://typst.app); `report.ja.typ` the Japanese draft |

Results are kept in the repository, so a report builds without solving again; tables too large
to keep (particles and fields, tens of MB) are ignored and made again by the runs. Every number a
report draws a conclusion from is checked against a closed form or a published result where one
exists. Only the English report is published; a report without one is a draft.

## Building a report

[uv](https://docs.astral.sh/uv/) makes the Python environment (`pyproject.toml`, `uv.lock`)
and runs `report`, the one tool every report is built with. It needs `emcraft-cli` (on the
PATH or as `EMCRAFT_CLI`), SolidCraft (`solidcraft-cli`, or the flatpak
`io.tangencylabs.solidcraft`) and `typst`.

```sh
uv run report list                    # the reports
uv run report bwo run                 # designs, then the runs not done yet (a part of the name will do)
uv run report bwo run final-ku --again
uv run report bwo run --scans -j 3    # the design study's runs too, three at a time
uv run report bwo status              # each run: done or not, its version and numbers
uv run report bwo figures             # the pictures, from the results
uv run report bwo pdf                 # report.typ → report.pdf
uv run report site                    # the published PDFs and their index, into _site/
```

A run whose record matches its script is not solved again; change the script (or pass
`--again`) to solve it again. Mind a run's memory before `-j`: an oven takes up to 26 GB.

## Licence

The scripts and tooling are MIT OR Apache-2.0, as EMCraft is. The reports' text and figures
are CC BY 4.0.
