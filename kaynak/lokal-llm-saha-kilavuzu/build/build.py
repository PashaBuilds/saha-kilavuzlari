#!/usr/bin/env python3
"""
build.py — content/*.md + assets/svg + assets/css -> dist/index.html
Tek self-contained HTML üretir. Sadece stdlib.

Markdown sözleşmesi için CLAUDE.md'ye bak.
"""
import html
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONTENT = ROOT / "content"
SVG_DIR = ROOT / "assets" / "svg"
CSS_FILE = ROOT / "assets" / "css" / "kilavuz.css"
OUT = ROOT / "dist" / "index.html"

DOC_TITLE = "Lokal LLM Dünyası — Saha Kılavuzu"
DOC_SUBTITLE = ("Kendi bilgisayarında büyük dil modeli çalıştırmak isteyenler için "
                "kavramlardan donanıma, formatlardan kuruluma uçtan uca yol haritası.")
DOC_META = ("Son güncelleme: 12 Temmuz 2026 · Model manzarası hızla değişir; "
            "kavramsal bölümler kalıcı, model/cihaz tabloları döneme aittir.")

BOX_DEFAULT_TITLES = {
    "saha-notu": "Saha Notu",
    "tuzak": "Tuzak",
    "analoji": "Analoji",
    "hesap": "Hesap Kutusu",
    "derin-dalis": "Derin Dalış",
    "ozet": "Bölüm Özeti",
}

TR_MAP = str.maketrans("çğıöşüÇĞİÖŞÜâÂ", "cgiosuCGIOSUaA")


def slugify(text: str) -> str:
    text = text.translate(TR_MAP).lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


# --------------------------------------------------------------------------
# Inline markdown
# --------------------------------------------------------------------------

def inline(text: str) -> str:
    """Inline md -> HTML. Önce escape, sonra biçimlendirme."""
    # kod span'larını koru
    parts = re.split(r"(`[^`]+`)", text)
    out = []
    for p in parts:
        if p.startswith("`") and p.endswith("`") and len(p) > 2:
            out.append("<code>" + html.escape(p[1:-1]) + "</code>")
        else:
            e = html.escape(p, quote=False)
            e = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", e)
            e = re.sub(r"(?<![\w*])\*([^*\n]+?)\*(?![\w*])", r"<em>\1</em>", e)
            e = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", r'<a href="\2">\1</a>', e)
            out.append(e)
    return "".join(out)


# --------------------------------------------------------------------------
# Blok parser
# --------------------------------------------------------------------------

class Ctx:
    def __init__(self):
        self.fig_no = 0


def parse_table(lines, i):
    rows = []
    while i < len(lines) and lines[i].lstrip().startswith("|"):
        rows.append(lines[i].strip())
        i += 1
    if len(rows) < 2:
        return None, i
    def cells(row):
        return [c.strip() for c in row.strip("|").split("|")]
    header = cells(rows[0])
    aligns = []
    for c in cells(rows[1]):
        if c.startswith(":") and c.endswith(":"):
            aligns.append(' style="text-align:center"')
        elif c.endswith(":"):
            aligns.append(' style="text-align:right"')
        else:
            aligns.append("")
    wide = len(header) >= 5
    h = ['<div class="table-scroll%s"><table>' % (" wide" if wide else "")]
    h.append("<thead><tr>" + "".join(
        f"<th{aligns[j] if j < len(aligns) else ''}>{inline(c)}</th>"
        for j, c in enumerate(header)) + "</tr></thead><tbody>")
    for row in rows[2:]:
        cs = cells(row)
        h.append("<tr>" + "".join(
            f"<td{aligns[j] if j < len(aligns) else ''}>{inline(c)}</td>"
            for j, c in enumerate(cs)) + "</tr>")
    h.append("</tbody></table></div>")
    return "\n".join(h), i


def parse_list(lines, i):
    """Tek ve iki seviyeli listeler."""
    ordered = bool(re.match(r"\s*\d+\.\s", lines[i]))
    tag = "ol" if ordered else "ul"
    items = []  # (level, text)
    pat = re.compile(r"^(\s*)(?:[-*]|\d+\.)\s+(.*)$")
    while i < len(lines):
        m = pat.match(lines[i])
        if not m:
            # devam satırı (girintili, madde işareti yok)
            if items and lines[i].startswith("  ") and lines[i].strip():
                items[-1] = (items[-1][0], items[-1][1] + " " + lines[i].strip())
                i += 1
                continue
            break
        level = 1 if len(m.group(1)) >= 2 else 0
        items.append((level, m.group(2)))
        i += 1
    h = [f"<{tag}>"]
    open_sub = False
    for j, (level, text) in enumerate(items):
        if level == 1 and not open_sub:
            h[-1] = h[-1]  # önceki <li> açık kalsın
            h.append("<ul>")
            open_sub = True
        if level == 0 and open_sub:
            h.append("</ul></li>")
            open_sub = False
        if level == 0:
            nxt_sub = j + 1 < len(items) and items[j + 1][0] == 1
            h.append(f"<li>{inline(text)}" + ("" if nxt_sub else "</li>"))
        else:
            h.append(f"<li>{inline(text)}</li>")
    if open_sub:
        h.append("</ul></li>")
    h.append(f"</{tag}>")
    return "\n".join(h), i


def parse_blocks(lines, ctx, chapter_num=None, chapter_id="", heads=None):
    """Satır listesi -> HTML. heads: h3 başlıkları toplanır (TOC için)."""
    out = []
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        stripped = line.strip()

        if not stripped:
            i += 1
            continue

        # kod bloğu
        if stripped.startswith("```"):
            lang = stripped[3:].strip()
            i += 1
            code = []
            while i < n and not lines[i].strip().startswith("```"):
                code.append(lines[i])
                i += 1
            i += 1  # kapanış
            esc = html.escape("\n".join(code))
            lang_tag = f'<span class="code-lang">{html.escape(lang)}</span>' if lang else ""
            out.append(
                f'<pre>{lang_tag}<button class="copy-btn" type="button">Kopyala</button>'
                f"<code>{esc}</code></pre>")
            continue

        # kutu direktifi
        m = re.match(r"^:::([a-z-]+)(?:\s+(.*))?$", stripped)
        if m and m.group(1) in BOX_DEFAULT_TITLES:
            btype, btitle = m.group(1), (m.group(2) or "").strip()
            i += 1
            inner = []
            depth = 1
            while i < n:
                s = lines[i].strip()
                if s.startswith(":::") and re.match(r"^:::[a-z-]+", s):
                    depth += 1
                elif s == ":::":
                    depth -= 1
                    if depth == 0:
                        break
                inner.append(lines[i])
                i += 1
            i += 1  # kapanış
            default = BOX_DEFAULT_TITLES[btype]
            title = f"{default} — {btitle}" if btitle else default
            body = parse_blocks(inner, ctx, chapter_num, chapter_id)
            if btype == "derin-dalis":
                out.append(
                    f'<details class="box derin-dalis"><summary>{inline(title)}</summary>\n'
                    f"{body}\n</details>")
            else:
                out.append(
                    f'<div class="box {btype}"><span class="box-title">{inline(title)}</span>\n'
                    f"{body}\n</div>")
            continue

        # hesap adımları (kutular içinde kullanılır)
        if stripped.startswith(">> "):
            out.append(f'<span class="adim">{inline(stripped[3:])}</span>')
            i += 1
            continue
        if stripped.startswith("=> "):
            out.append(f'<span class="sonuc">{inline(stripped[3:])}</span>')
            i += 1
            continue

        # SVG figürü
        m = re.match(r"^\{\{svg:([\w.\-]+)(?:\|([^|}]*))?(?:\|(wide))?\}\}$", stripped)
        if m:
            fname, caption, wide = m.group(1), (m.group(2) or "").strip(), m.group(3)
            svg_path = SVG_DIR / fname
            if not svg_path.exists():
                print(f"  UYARI: SVG yok: {fname}", file=sys.stderr)
                svg = f'<svg viewBox="0 0 700 80"><text x="20" y="45" fill="var(--red)">EKSİK SVG: {html.escape(fname)}</text></svg>'
            else:
                svg = svg_path.read_text(encoding="utf-8")
                svg = re.sub(r"^<\?xml[^>]*\?>\s*", "", svg)
            ctx.fig_no += 1
            cap = (f'<figcaption><span class="fig-no">Şema {ctx.fig_no}.</span> '
                   f"{inline(caption)}</figcaption>") if caption else ""
            cls = ' class="wide"' if wide else ""
            out.append(f"<figure{cls}>\n{svg}\n{cap}\n</figure>")
            i += 1
            continue

        # ham HTML bloğu
        if stripped.startswith("<"):
            block = [line]
            i += 1
            while i < n and lines[i].strip():
                block.append(lines[i])
                i += 1
            out.append("\n".join(block))
            continue

        # başlıklar (## -> h3 vb.; # bölüm başlığı ayrıca işlenir)
        m = re.match(r"^(#{2,4})\s+(.*)$", stripped)
        if m:
            level = len(m.group(1)) + 1  # ## -> h3
            text = m.group(2).strip()
            if level == 3 and heads is not None:
                heads.append(text)
                num = f"{chapter_num}.{len(heads)}" if chapter_num is not None else ""
                hid = f"{chapter_id}-{slugify(text)}"
                shown = f"{num} {inline(text)}" if num else inline(text)
                out.append(
                    f'<h3 id="{hid}">{shown}'
                    f'<a class="anchor" href="#{hid}" aria-label="bağlantı">#</a></h3>')
            else:
                out.append(f"<h{level}>{inline(text)}</h{level}>")
            i += 1
            continue

        # yatay çizgi
        if re.match(r"^---+$", stripped):
            out.append("<hr>")
            i += 1
            continue

        # tablo
        if stripped.startswith("|"):
            tbl, ni = parse_table(lines, i)
            if tbl:
                out.append(tbl)
                i = ni
                continue

        # liste
        if re.match(r"^(\s*)([-*]|\d+\.)\s+", line):
            lst, ni = parse_list(lines, i)
            out.append(lst)
            i = ni
            continue

        # alıntı
        if stripped.startswith(">"):
            quote = []
            while i < n and lines[i].strip().startswith(">"):
                quote.append(lines[i].strip().lstrip(">").strip())
                i += 1
            out.append("<blockquote><p>" + inline(" ".join(quote)) + "</p></blockquote>")
            continue

        # paragraf
        para = [stripped]
        i += 1
        while i < n and lines[i].strip() and not re.match(
                r"^(#{1,4}\s|```|:::|\{\{svg:|\||[-*]\s|\d+\.\s|>|<|>> |=> |---)", lines[i].strip()):
            para.append(lines[i].strip())
            i += 1
        out.append("<p>" + inline(" ".join(para)) + "</p>")

    return "\n".join(out)


# --------------------------------------------------------------------------
# Bölüm derleme
# --------------------------------------------------------------------------

def compile_chapter(path: Path, ctx: Ctx):
    lines = path.read_text(encoding="utf-8").splitlines()
    title = None
    body_start = 0
    for j, l in enumerate(lines):
        if l.startswith("# "):
            title = l[2:].strip()
            body_start = j + 1
            break
    if title is None:
        title = path.stem
    m = re.match(r"^Bölüm\s+(\d+)", title)
    chapter_num = int(m.group(1)) if m else None
    chapter_id = slugify(path.stem)
    heads = []
    body = parse_blocks(lines[body_start:], ctx, chapter_num, chapter_id, heads)
    h2 = (f'<h2 id="{chapter_id}">{inline(title)}'
          f'<a class="anchor" href="#{chapter_id}" aria-label="bağlantı">#</a></h2>')
    return {
        "id": chapter_id,
        "title": title,
        "num": chapter_num,
        "heads": heads,
        "html": f'<section aria-labelledby="{chapter_id}">\n{h2}\n{body}\n</section>',
    }


def build_toc(chapters, mobile=False):
    items = []
    for ch in chapters:
        subs = ""
        if not mobile and ch["heads"]:
            sub_items = []
            for k, htext in enumerate(ch["heads"], 1):
                hid = f'{ch["id"]}-{slugify(htext)}'
                num = f'{ch["num"]}.{k} ' if ch["num"] is not None else ""
                sub_items.append(f'<li><a href="#{hid}">{num}{inline(htext)}</a></li>')
            subs = "<ol>" + "".join(sub_items) + "</ol>"
        items.append(f'<li><a href="#{ch["id"]}">{inline(ch["title"])}</a>{subs}</li>')
    return "<ol>" + "\n".join(items) + "</ol>"


JS = r"""
(function () {
  var root = document.documentElement;
  var saved = null;
  try { saved = localStorage.getItem('tema'); } catch (e) {}
  var prefers = window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark';
  setTheme(saved || prefers);

  function setTheme(t) {
    if (t === 'light') root.setAttribute('data-theme', 'light');
    else root.removeAttribute('data-theme');
    var btn = document.getElementById('theme-toggle');
    if (btn) btn.textContent = t === 'light' ? '◒ Koyu' : '◓ Açık';
    root.dataset.mode = t;
  }
  document.getElementById('theme-toggle').addEventListener('click', function () {
    var next = root.dataset.mode === 'light' ? 'dark' : 'light';
    setTheme(next);
    try { localStorage.setItem('tema', next); } catch (e) {}
  });

  // ilerleme çubuğu
  var bar = document.getElementById('progress');
  function onScroll() {
    var h = document.documentElement;
    var max = h.scrollHeight - h.clientHeight;
    bar.style.width = (max > 0 ? (h.scrollTop / max) * 100 : 0) + '%';
  }
  addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  // kod kopyala
  document.addEventListener('click', function (e) {
    var btn = e.target.closest('.copy-btn');
    if (!btn) return;
    var code = btn.parentElement.querySelector('code');
    var fallback = function (txt) {
      var ta = document.createElement('textarea');
      ta.value = txt; ta.style.position = 'fixed'; ta.style.opacity = '0';
      document.body.appendChild(ta); ta.select();
      try { document.execCommand('copy'); } catch (err) {}
      ta.remove();
    };
    var done = function () {
      btn.textContent = 'Kopyalandı ✓';
      setTimeout(function () { btn.textContent = 'Kopyala'; }, 1600);
    };
    var txt = code.textContent;
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(txt).then(done, function () { fallback(txt); done(); });
    } else {
      fallback(txt); done();
    }
  });

  // TOC scroll-spy
  var tocLinks = Array.prototype.slice.call(document.querySelectorAll('nav.toc a'));
  var byId = {};
  tocLinks.forEach(function (a) { byId[a.getAttribute('href').slice(1)] = a; });
  var targets = Array.prototype.slice.call(document.querySelectorAll('main h2[id], main h3[id]'))
    .filter(function (el) { return byId[el.id]; });
  var active = null;
  function activate(id) {
    if (active) active.classList.remove('active');
    active = byId[id];
    if (active) {
      active.classList.add('active');
      var nav = document.querySelector('nav.toc');
      var r = active.getBoundingClientRect(), nr = nav.getBoundingClientRect();
      if (r.top < nr.top || r.bottom > nr.bottom) active.scrollIntoView({ block: 'center' });
    }
  }
  if ('IntersectionObserver' in window && targets.length) {
    var visible = new Set();
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting) visible.add(en.target.id);
        else visible.delete(en.target.id);
      });
      var first = targets.find(function (t) { return visible.has(t.id); });
      if (first) activate(first.id);
    }, { rootMargin: '-10% 0px -70% 0px' });
    targets.forEach(function (t) { io.observe(t); });
  }

  // ---- hesaplayıcılar ----
  function fmtGB(x) { return (x >= 100 ? x.toFixed(0) : x >= 10 ? x.toFixed(1) : x.toFixed(2)).replace('.', ',') + ' GB'; }

  function bindCalc(el) {
    var type = el.dataset.calc;
    var q = function (s) { return el.querySelector(s); };
    function update() {
      if (type === 'boyut') {
        var b = parseFloat(q('[name=param]').value) || 0;
        var bits = parseFloat(q('[name=quant]').value) || 4.5;
        var dosya = b * bits / 8 * 1.1;
        q('[data-out=dosya]').textContent = fmtGB(dosya);
        q('[data-out=bellek]').textContent = fmtGB(dosya * 1.2 + 1.5);
      } else if (type === 'hiz') {
        var bw = parseFloat(q('[name=bant]').value) || 0;
        var gb = parseFloat(q('[name=aktif]').value) || 1;
        var t = bw / gb * 0.6; // pratik verim ~%50-70
        q('[data-out=hiz]').textContent = (t >= 10 ? t.toFixed(0) : t.toFixed(1)) + ' token/s civarı';
      } else if (type === 'kv') {
        var ctx = parseFloat(q('[name=ctx]').value) || 0;
        var gbk = parseFloat(q('[name=model]').value) || 0; // GB / 8K token
        q('[data-out=kv]').textContent = fmtGB(ctx / 8192 * gbk);
      }
    }
    el.addEventListener('input', update);
    update();
  }
  Array.prototype.forEach.call(document.querySelectorAll('.calc[data-calc]'), bindCalc);
})();
"""


def main():
    ctx = Ctx()
    files = sorted(p for p in CONTENT.glob("*.md") if not p.name.startswith("_"))
    if not files:
        print("content/ boş — derlenecek bölüm yok", file=sys.stderr)
        sys.exit(1)
    chapters = [compile_chapter(p, ctx) for p in files]
    css = CSS_FILE.read_text(encoding="utf-8")
    toc = build_toc(chapters)
    toc_mobile = build_toc(chapters, mobile=True)
    body = "\n\n".join(ch["html"] for ch in chapters)

    # Çapraz linkler: "Bölüm N" geçişlerini o bölüme bağla.
    # Bölüm başlıklarındaki "Bölüm N — ..." kalıbı (ve TOC) lookahead ile dışarıda kalır.
    num_to_id = {ch["num"]: ch["id"] for ch in chapters if ch["num"] is not None}

    def link_ref(m):
        n = int(m.group(1))
        if n in num_to_id:
            return f'<a href="#{num_to_id[n]}">Bölüm {n}</a>'
        return m.group(0)

    body = re.sub(r"Bölüm (\d+)(?!\s*—|\d)", link_ref, body)

    doc = f"""<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{DOC_TITLE}</title>
<meta name="description" content="{html.escape(DOC_SUBTITLE)}">
<style>
{css}
</style>
</head>
<body>
<svg width="0" height="0" style="position:absolute" aria-hidden="true">
<defs>
<marker id="ar" viewBox="0 0 10 10" refX="8.5" refY="5" markerWidth="6.5" markerHeight="6.5" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" style="fill:var(--muted)"/></marker>
<marker id="ar-a" viewBox="0 0 10 10" refX="8.5" refY="5" markerWidth="6.5" markerHeight="6.5" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" style="fill:var(--accent)"/></marker>
<marker id="ar-g" viewBox="0 0 10 10" refX="8.5" refY="5" markerWidth="6.5" markerHeight="6.5" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" style="fill:var(--gold)"/></marker>
<marker id="ar-t" viewBox="0 0 10 10" refX="8.5" refY="5" markerWidth="6.5" markerHeight="6.5" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" style="fill:var(--teal)"/></marker>
<marker id="ar-r" viewBox="0 0 10 10" refX="8.5" refY="5" markerWidth="6.5" markerHeight="6.5" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" style="fill:var(--red)"/></marker>
</defs>
</svg>
<div id="progress" role="presentation"></div>
<header class="topbar">
  <a class="brand" href="#top">Lokal LLM Dünyası <span>— Saha Kılavuzu</span></a>
  <button id="theme-toggle" type="button" aria-label="Tema değiştir">Tema</button>
</header>
<div class="layout" id="top">
  <nav class="toc" aria-label="İçindekiler">
    <p class="toc-title">İçindekiler</p>
    {toc}
  </nav>
  <main>
    <h1 class="doc-title">{DOC_TITLE}</h1>
    <p class="doc-subtitle">{DOC_SUBTITLE}</p>
    <p class="doc-meta">{DOC_META}</p>
    <details class="toc-mobile">
      <summary>İçindekiler</summary>
      {toc_mobile}
    </details>
{body}
    <footer>
      <hr>
      <p class="small">Lokal LLM Dünyası — Saha Kılavuzu · Saha Kılavuzu serisinin parçası.
      Tek dosya, çevrimdışı çalışır; kaynak: <code>content/*.md</code>.</p>
    </footer>
  </main>
</div>
<script>
{JS}
</script>
</body>
</html>
"""
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(doc, encoding="utf-8")
    kb = OUT.stat().st_size / 1024
    n_svg = doc.count("<figure")
    print(f"OK: {OUT.relative_to(ROOT)}  ({kb:.0f} KB, {len(chapters)} bölüm, {n_svg} figür)")
    if kb > 2048:
        print("UYARI: 2 MB hedefi aşıldı!", file=sys.stderr)


if __name__ == "__main__":
    main()
