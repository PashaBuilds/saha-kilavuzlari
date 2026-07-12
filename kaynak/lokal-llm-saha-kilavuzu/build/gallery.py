#!/usr/bin/env python3
"""Görsel QA yardımcısı: assets/svg/*.svg -> dist/_semalar-N.html (4'erli sayfalar).
Ana build'in parçası değildir; şemaları scroll'suz tek karede incelemek için."""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SVGS = sorted((ROOT / "assets" / "svg").glob("*.svg"))
CSS = (ROOT / "assets" / "css" / "kilavuz.css").read_text(encoding="utf-8")

DEFS = """<svg width="0" height="0" style="position:absolute" aria-hidden="true"><defs>
<marker id="ar" viewBox="0 0 10 10" refX="8.5" refY="5" markerWidth="6.5" markerHeight="6.5" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" style="fill:var(--muted)"/></marker>
<marker id="ar-a" viewBox="0 0 10 10" refX="8.5" refY="5" markerWidth="6.5" markerHeight="6.5" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" style="fill:var(--accent)"/></marker>
<marker id="ar-g" viewBox="0 0 10 10" refX="8.5" refY="5" markerWidth="6.5" markerHeight="6.5" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" style="fill:var(--gold)"/></marker>
<marker id="ar-t" viewBox="0 0 10 10" refX="8.5" refY="5" markerWidth="6.5" markerHeight="6.5" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" style="fill:var(--teal)"/></marker>
<marker id="ar-r" viewBox="0 0 10 10" refX="8.5" refY="5" markerWidth="6.5" markerHeight="6.5" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" style="fill:var(--red)"/></marker>
</defs></svg>"""

theme = sys.argv[1] if len(sys.argv) > 1 else "dark"
attr = ' data-theme="light"' if theme == "light" else ""
per_page = 4
pages = [SVGS[i:i + per_page] for i in range(0, len(SVGS), per_page)]
for n, group in enumerate(pages, 1):
    figs = []
    for p in group:
        svg = re.sub(r"^<\?xml[^>]*\?>\s*", "", p.read_text(encoding="utf-8"))
        figs.append(f'<figure style="max-width:920px"><p class="small">{p.name}</p>\n{svg}\n</figure>')
    html = (f'<!DOCTYPE html><html lang="tr"{attr}><head><meta charset="utf-8">'
            f"<title>şemalar {n} ({theme})</title><style>{CSS}</style></head>"
            f'<body style="padding:10px">{DEFS}\n' + "\n".join(figs) + "</body></html>")
    out = ROOT / "dist" / f"_semalar-{theme}-{n}.html"
    out.write_text(html, encoding="utf-8")
    print(f"{out.name}: {', '.join(p.name for p in group)}")
