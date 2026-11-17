"""A report's recipe: what it builds, solves and draws, declared once in `<report>/report.py` as

    REPORT = Report(
        title="…", question="…", status="…",
        prepare=[Step("model/make.py")],                         # writes designs' and runs' scripts
        designs=[Design("model/ku.script.json", "model/ku.sc")],  # SolidCraft builds
        runs=[Run("final-ku")],                                  # scripts/final-ku.json → results/final-ku.out
        analysis=[Step("scripts/leak.py", "results/a.out")],     # numbers from the runs
        figures=[Step("scripts/figures.py")],                    # pictures into results/
        documents=["report.typ", "report.ja.typ"],               # Typst → PDF
        published="report.typ",                                  # the one the site lists
    )

Every path is relative to the report's folder. A run is EMCraft solving one script: it runs in
the script's folder (so the script names the designs and exports relative to it), its replies go
to `out`, and a record beside them (`<out without .out>.run.json`) keeps the script's hash, the
EMCraft version, the time and the peak memory; a run whose record matches its script is done and
is not solved again."""
from dataclasses import dataclass, field
import os


@dataclass(frozen=True)
class Step:
    """A Python script of the report's, run with the report's environment from its folder."""

    script: str
    args: tuple = ()

    def __init__(self, script, *args):
        object.__setattr__(self, "script", script)
        object.__setattr__(self, "args", tuple(str(a) for a in args))


@dataclass(frozen=True)
class Design:
    """A SolidCraft command script and the design it builds (`solidcraft-cli run … --save …`)."""

    script: str
    design: str


@dataclass(frozen=True)
class Run:
    """EMCraft solving `script` (default scripts/<name>.json) into `out` (default
    results/<name>.out). `scan`: a design study's run, solved only when asked for by name or with
    --scans, not by a plain `run`."""

    name: str
    script: str = ""
    out: str = ""
    scan: bool = False

    def __post_init__(self):
        if not self.script:
            object.__setattr__(self, "script", f"scripts/{self.name}.json")
        if not self.out:
            object.__setattr__(self, "out", f"results/{self.name}.out")

    @property
    def record(self):
        return os.path.splitext(self.out)[0] + ".run.json"


@dataclass
class Report:
    title: str
    question: str
    status: str
    prepare: list = field(default_factory=list)
    designs: list = field(default_factory=list)
    runs: list = field(default_factory=list)
    analysis: list = field(default_factory=list)
    figures: list = field(default_factory=list)
    documents: list = field(default_factory=lambda: ["report.typ"])
    published: str | None = None
    folder: str = ""

    @property
    def name(self):
        return os.path.basename(self.folder)

    def path(self, relative):
        return os.path.join(self.folder, relative)
