# EMCraft reports

Engineering analysis reports made with [EMCraft](https://github.com/jijinbei/emcraft), the
open-source electromagnetic field simulator, and its sibling CAD application SolidCraft. Each
report is a folder you can run again from scratch:

- `model/` — the 3D models, as SolidCraft designs;
- `scripts/` — the EMCraft scripts that solve them (`emcraft-cli run scripts/<name>.json`);
- `results/` — what the scripts wrote (tables, pictures), kept so the report builds without
  solving again;
- `report.typ` — the report, in [Typst](https://typst.app) (`typst compile --root .. report.typ`).

Every number a report draws a conclusion from is checked the way EMCraft's own solvers are:
against a closed form or a published result where one exists, and by refining the mesh.

| Report | Question | Status |
|---|---|---|
| [microwave-oven-leakage](microwave-oven-leakage/) | Does a household microwave oven's door keep its 2.45 GHz field inside, below 5 mW/cm² at 5 cm? | v0.1: the whole oven (2.3 million unknowns), three doors, solved with EMCraft v0.1 |

These are simulation studies. They show how a design behaves and why; they are not
certification tests, which need measurements on the real product.

## Building a report

```sh
cd microwave-oven-leakage
./run.sh            # solves every model with emcraft-cli and writes results/
typst compile --root .. report.typ
```

## Licence

The scripts and tooling are MIT OR Apache-2.0, as EMCraft is. The reports' text and figures
are CC BY 4.0.
