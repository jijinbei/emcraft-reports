"""uv run report — builds the reports.

    uv run report list
    uv run report <report> run [RUN…] [-j N] [--again] [--scans]   designs, then the runs not done
    uv run report <report> status                                  each run: done or not, its numbers
    uv run report <report> figures                                 the pictures, from the results
    uv run report <report> pdf                                     every document to PDF
    uv run report <report> all                                     run, figures, pdf
    uv run report <report> adopt VERSION                           records for runs solved without one
    uv run report site [--out _site]                               the published PDFs and their index

<report> is a report's folder name or a part of it (`bwo` for relativistic-bwo)."""
import argparse, importlib.util, os, sys

from . import build, site, tools
from .recipe import Report


def load(folder):
    spec = importlib.util.spec_from_file_location(f"report_{os.path.basename(folder).replace('-', '_')}", os.path.join(folder, "report.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    report = module.REPORT
    if not isinstance(report, Report):
        raise SystemExit(f"{folder}/report.py: REPORT is not a Report")
    report.folder = folder
    return report


def reports():
    root = tools.ROOT
    return [load(os.path.join(root, d)) for d in sorted(os.listdir(root)) if d != "emreports" and os.path.isfile(os.path.join(root, d, "report.py"))]


def find(name):
    found = [r for r in reports() if r.name == name] or [r for r in reports() if name in r.name]
    if len(found) != 1:
        raise SystemExit(f"no single report matches '{name}': {', '.join(r.name for r in reports())}")
    return found[0]


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return
    if argv[0] == "list":
        for r in reports():
            print(f"{r.name:28} {'published' if r.published else 'draft':10} {r.title}")
        return
    if argv[0] == "site":
        p = argparse.ArgumentParser(prog="report site")
        p.add_argument("--out", default=os.path.join(tools.ROOT, "_site"))
        site.make(reports(), os.path.abspath(p.parse_args(argv[1:]).out))
        return
    report = find(argv[0])
    p = argparse.ArgumentParser(prog=f"report {report.name}")
    p.add_argument("action", choices=["run", "status", "figures", "pdf", "all", "adopt"])
    p.add_argument("runs", nargs="*", help="runs to solve (names or prefixes); default every run but the scans")
    p.add_argument("-j", "--jobs", type=int, default=1, help="runs at a time (mind their memory)")
    p.add_argument("--again", action="store_true", help="solve again runs already done")
    p.add_argument("--scans", action="store_true", help="the design scans too")
    a = p.parse_args(argv[1:])
    print(f"{report.name}:", flush=True)
    if a.action in ("run", "all"):
        build.run(report, a.runs, a.jobs, a.again, a.scans)
    if a.action == "adopt":
        if len(a.runs) != 1:
            raise SystemExit("adopt takes the EMCraft version the runs were solved with")
        build.adopt(report, a.runs[0])
    if a.action == "status":
        build.status(report)
    if a.action in ("figures", "all"):
        build.figures(report)
    if a.action in ("pdf", "all"):
        build.pdf(report)
