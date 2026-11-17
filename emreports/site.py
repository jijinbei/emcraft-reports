"""The reports' site: an index page listing each published report (its question, status and
PDF) with the PDFs beside it."""
import html, os, shutil, subprocess

from . import build, tools

PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>EMCraft reports</title>
<style>
:root {{ --fg: #1d2127; --muted: #5b6370; --line: #dde1e6; --bg: #ffffff; --card: #f6f7f9; --link: #2b5bc8; }}
@media (prefers-color-scheme: dark) {{
  :root {{ --fg: #e6e8eb; --muted: #a2a9b4; --line: #343a42; --bg: #16191d; --card: #1e2227; --link: #7aa2f7; }}
}}
* {{ box-sizing: border-box; }}
body {{ margin: 0; background: var(--bg); color: var(--fg); font: 16px/1.55 system-ui, -apple-system, "Segoe UI", sans-serif; }}
main {{ max-width: 860px; margin: 0 auto; padding: 48px 16px 64px; }}
h1 {{ font-size: 2rem; margin: 0 0 8px; }}
.lead {{ color: var(--muted); margin: 0 0 32px; }}
a {{ color: var(--link); }}
.report {{ background: var(--card); border: 1px solid var(--line); border-radius: 10px; padding: 20px 22px; margin: 0 0 16px; }}
.report h2 {{ font-size: 1.25rem; margin: 0 0 6px; }}
.report p {{ margin: 0 0 10px; }}
.meta {{ color: var(--muted); font-size: 0.9rem; }}
.links a {{ margin-right: 18px; font-weight: 600; }}
footer {{ color: var(--muted); font-size: 0.9rem; margin-top: 40px; }}
</style>
</head>
<body>
<main>
<h1>EMCraft reports</h1>
<p class="lead">Engineering analysis reports made with <a href="https://site.jijinbei.jp/emcraft/">EMCraft</a>,
the open-source electromagnetic field simulator. Each one can be run again from its
<a href="https://github.com/jijinbei/emcraft-reports">sources</a>.</p>
{reports}
<footer>These are simulation studies: they show how a design behaves and why, not certification tests.</footer>
</main>
</body>
</html>
"""

CARD = """<section class="report">
<h2>{title}</h2>
<p>{question}</p>
<p class="meta">{status}{updated}</p>
<p class="links"><a href="{pdf}">PDF</a><a href="https://github.com/jijinbei/emcraft-reports/tree/main/{name}">Sources</a></p>
</section>"""


def updated(report):
    """The date of the folder's last commit, when the history is there."""
    try:
        date = subprocess.run(["git", "log", "-1", "--format=%cs", "--", report.folder], cwd=tools.ROOT,
                              capture_output=True, text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return ""
    return f" · updated {date}" if date else ""


def make(reports, out):
    """The published reports' PDFs compiled into `out` and the index page listing them."""
    os.makedirs(out, exist_ok=True)
    cards = []
    for report in reports:
        if not report.published:
            continue
        print(f"{report.name}:", flush=True)
        (made,) = build.pdf(report, report.published)
        pdf = f"{report.name}.pdf"
        shutil.copyfile(made, os.path.join(out, pdf))
        cards.append(CARD.format(title=html.escape(report.title), question=html.escape(report.question),
                                 status=html.escape(report.status), updated=updated(report), pdf=pdf, name=report.name))
    with open(os.path.join(out, "index.html"), "w") as f:
        f.write(PAGE.format(reports="\n".join(cards)))
    print(f"{len(cards)} reports in {out}/index.html")
