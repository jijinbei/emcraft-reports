"""Doing a report's recipe (report.py): its steps, designs, runs and documents."""
import hashlib, json, os, subprocess, sys, time
from concurrent.futures import ThreadPoolExecutor

from . import tools


def step(report, s):
    print(f"  {s.script} {' '.join(s.args)}".rstrip(), flush=True)
    env = {**os.environ, "EMCRAFT_CLI": tools.emcraft()}
    subprocess.run([sys.executable, report.path(s.script), *s.args], cwd=report.folder, env=env, check=True)


STAMPS = os.path.join(tools.ROOT, ".build", "designs.json")


def design(report, d):
    """The design built again when its script changed (the script's hash against the one it was
    last built from, kept in .build/; a design there before any stamp is taken as built)."""
    script, out = report.path(d.script), report.path(d.design)
    stamps = json.load(open(STAMPS)) if os.path.exists(STAMPS) else {}
    key, sha = os.path.relpath(out, tools.ROOT), digest(script)
    if os.path.exists(out) and stamps.get(key, sha) == sha:
        stamps[key] = sha
    else:
        print(f"  SolidCraft: {d.design}", flush=True)
        tools.solidcraft("run", script, "--save", out)
        stamps[key] = sha
    os.makedirs(os.path.dirname(STAMPS), exist_ok=True)
    with open(STAMPS, "w") as f:
        json.dump(stamps, f, indent=1, sort_keys=True)


def digest(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def done(report, r):
    record = report.path(r.record)
    if not os.path.exists(record) or not os.path.exists(report.path(r.out)):
        return False
    rec = json.load(open(record))
    return rec.get("status") == "done" and rec.get("script_sha256") == digest(report.path(r.script))


def solve(report, r, version):
    """emcraft-cli run <script> from the script's folder, its replies into `out` and its record
    beside them."""
    script, out = report.path(r.script), report.path(r.out)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    start = time.time()
    with open(out, "w") as f:
        p = subprocess.Popen([tools.emcraft(), "run", os.path.basename(script)], cwd=os.path.dirname(script),
                             stdout=f, stderr=subprocess.PIPE, text=True)
        err = p.stderr.read()
        # Waited for here, not by Popen, for this child's own peak memory.
        _, wait, usage = os.wait4(p.pid, 0)
        p.returncode = os.waitstatus_to_exitcode(wait)
    record = {
        "run": r.name, "script": r.script, "script_sha256": digest(script), "status": "done" if p.returncode == 0 else "failed",
        "emcraft": version, "started": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(start)), "seconds": round(time.time() - start, 1),
        "peak_memory_mb": round(usage.ru_maxrss / 1024), "summary": tools.summary(tools.replies(open(out).read())),
    }
    if p.returncode:
        record["error"] = err.strip()[-2000:]
    with open(report.path(r.record), "w") as f:
        json.dump(record, f, indent=1)
        f.write("\n")
    print(f"  {r.name}: {record['status']} in {record['seconds']:.0f} s {json.dumps(record['summary'])}", flush=True)
    return record


def run(report, names=(), jobs=1, again=False, scans=False):
    """The steps that write the scripts, the designs, then the runs not done yet — those named
    (a name or a prefix), else every run (and the scans with `scans`) — `jobs` at a time, then the
    analysis."""
    for s in report.prepare:
        step(report, s)
    for d in report.designs:
        design(report, d)
    chosen = [r for r in report.runs if (any(r.name.startswith(n) for n in names) if names else (scans or not r.scan))]
    todo = [r for r in chosen if again or not done(report, r)]
    print(f"  {len(todo)} of {len(chosen)} runs to solve", flush=True)
    if todo:
        version = tools.emcraft_version()
        with ThreadPoolExecutor(max_workers=max(jobs, 1)) as pool:
            failed = [rec for rec in pool.map(lambda r: solve(report, r, version), todo) if rec["status"] != "done"]
        if failed:
            raise SystemExit(f"{len(failed)} runs failed: {', '.join(rec['run'] for rec in failed)}")
    for s in report.analysis:
        step(report, s)


def figures(report):
    for s in report.figures:
        step(report, s)


def pdf(report, only=None):
    """Each document (or `only`) compiled to the PDF beside it."""
    made = []
    for doc in [only] if only else report.documents:
        target = report.path(os.path.splitext(doc)[0] + ".pdf")
        print(f"  {doc} -> {os.path.basename(target)}", flush=True)
        tools.typst(report.path(doc), target)
        made.append(target)
    return made


def status(report):
    """A line a run: done, not run or out of date with its script, and its numbers."""
    for r in report.runs:
        record = report.path(r.record)
        if done(report, r):
            rec = json.load(open(record))
            took = f"{rec['seconds']:>6.0f} s" if "seconds" in rec else "  adopted"
            state = f"done  {took}  {rec['emcraft']}  {json.dumps(rec.get('summary', {}))}"
        elif os.path.exists(record):
            state = "out of date (its script changed)"
        elif os.path.exists(report.path(r.out)):
            state = "solved before records were kept"
        else:
            state = "not run"
        print(f"  {'scan ' if r.scan else ''}{r.name}: {state}")


def adopt(report, version):
    """Records for the runs solved before records were kept (their replies there, no record):
    their script as it is now, the EMCraft `version` they were solved with, no time."""
    for r in report.runs:
        if os.path.exists(report.path(r.out)) and not os.path.exists(report.path(r.record)):
            record = {"run": r.name, "script": r.script, "script_sha256": digest(report.path(r.script)), "status": "done",
                      "emcraft": version, "adopted": True, "summary": tools.summary(tools.replies(open(report.path(r.out)).read()))}
            with open(report.path(r.record), "w") as f:
                json.dump(record, f, indent=1)
                f.write("\n")
            print(f"  {r.name}: adopted")
