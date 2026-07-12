// build.mjs — src/*.md + diagrams/* → dist/index.html (tek, self-contained dosya)
//
// Boru hattı:
//   1. src/*.md dosyalarını numara sırasıyla oku
//   2. ```wavedrom / ```mermaid çitli blokları ve ![](../diagrams/...) referanslarını
//      inline SVG'ye çevir (mermaid hash ile .cache/ altında saklanır)
//   3. templates/page.html içine göm
//
// Şekil sistemi:
//   - ![Altyazı](../diagrams/svg/d01.svg)  → <figure id="fig-d01"> "Şekil N.M — Altyazı"
//   - {{fig:d01}}  → <a href="#fig-d01">Şekil N.M</a>   (ileri referans desteklenir)
//   - {{sec:9}}    → <a href="#bolum-9">§9</a>

import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import MarkdownIt from 'markdown-it';
import anchor from 'markdown-it-anchor';
import container from 'markdown-it-container';
import JSON5 from 'json5';
import wavedrom from 'wavedrom';
import onml from 'onml';
import { createHighlighter } from 'shiki';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const SRC = path.join(ROOT, 'src');
const DIA = path.join(ROOT, 'diagrams');
const CACHE = path.join(ROOT, '.cache', 'mermaid');
const DIST = path.join(ROOT, 'dist');
const MMDC = path.join(ROOT, 'node_modules', '.bin', 'mmdc');

fs.mkdirSync(CACHE, { recursive: true });
fs.mkdirSync(DIST, { recursive: true });

// ---------------------------------------------------------------- yardımcılar

const TR_MAP = { ç: 'c', Ç: 'c', ğ: 'g', Ğ: 'g', ı: 'i', İ: 'i', ö: 'o', Ö: 'o', ş: 's', Ş: 's', ü: 'u', Ü: 'u', â: 'a', î: 'i', û: 'u' };
function slugify(s) {
  return s
    .replace(/[çÇğĞıİöÖşŞüÜâîû]/g, (c) => TR_MAP[c] ?? c)
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '');
}

const sha1 = (s) => crypto.createHash('sha1').update(s).digest('hex').slice(0, 16);

function warn(msg) {
  warnings.push(msg);
  console.warn('  ⚠ ' + msg);
}
const warnings = [];

// SVG'yi inline'a hazırla: prolog/doctype/yorum temizle
function cleanSvg(svg) {
  return svg
    .replace(/<\?xml[^>]*\?>/g, '')
    .replace(/<!DOCTYPE[^>]*>/g, '')
    .replace(/<!--[\s\S]*?-->/g, '')
    .trim();
}

// ------------------------------------------------------------ wavedrom render

let wavedromIndex = 0;

// Skin <style>'ını inline style attribute'larına düzleştir.
// Neden: inline HTML'de <use> shadow klonları document CSS'ten sınıf eşleşmesi
// almıyor (Chromium); presentation/inline stiller ise klonlara taşınır.
function flattenWavedromStyles(svg) {
  const m = svg.match(/<style[^>]*>([\s\S]*?)<\/style>/);
  if (!m) return svg;
  const rules = {};
  let textRule = '';
  for (const part of m[1].split('}')) {
    const [sel, decl] = part.split('{');
    if (!sel || !decl) continue;
    const s = sel.trim();
    if (s === 'text') textRule = decl.trim();
    else if (s.startsWith('.')) rules[s.slice(1)] = decl.trim();
  }
  textRule = textRule.replace(/font-family:[^;]+/, "font-family:-apple-system,system-ui,'Segoe UI',sans-serif");
  let out = svg.replace(m[0], '');
  out = out.replace(/<(\w+)((?:\s+[\w:-]+="[^"]*")*)\s*(\/?)>/g, (full, tag, attrs, selfClose) => {
    const decls = [];
    if (tag === 'text') decls.push(textRule);
    const cm = attrs.match(/class="([^"]*)"/);
    if (cm) for (const c of cm[1].split(/\s+/)) if (rules[c]) decls.push(rules[c]);
    if (!decls.length) return full;
    if (/style="/.test(attrs)) {
      return `<${tag}${attrs.replace(/style="([^"]*)"/, (_, ex) => `style="${decls.join(';')};${ex}"`)}${selfClose ? ' /' : ''}>`;
    }
    return `<${tag}${attrs} style="${decls.join(';')}"${selfClose ? ' /' : ''}>`;
  });
  return out;
}

// id'leri namespace'le: wavedrom defs id'leri (pclk, 000, 111...) her SVG'de
// aynı; aynı sayfada çakışırlarsa <use> yanlış (ilk) tanıma bağlanır.
function namespaceSvgIds(svg, ns) {
  return svg
    .replace(/id="([^"]+)"/g, (_, id) => `id="${id}__${ns}"`)
    .replace(/(xlink:href|href)="#([^"]+)"/g, (_, attr, id) => `${attr}="#${id}__${ns}"`)
    .replace(/url\(#([^)]+)\)/g, (_, id) => `url(#${id}__${ns})`);
}

// Koyu tema renk haritası (inline stiller CSS ile ezilemediği için ikinci kopya)
const WD_DARK_MAP = [
  [/#ffffb4/gi, '#4a4423'], // data sarısı (3/x34x)
  [/#ffe0b9/gi, '#4a3a26'], // data turuncusu (4)
  [/#b9e0ff/gi, '#26394a'], // data mavisi (5)
  [/#ccfdfe/gi, '#254245'],
  [/#cdfdc5/gi, '#2a4527'],
  [/#f0c1fb/gi, '#432a47'],
  [/#f5c2c0/gi, '#472a29'],
  [/#0041c4/gi, '#4fc3dd'], // node/ok mavisi → sysref camgöbeği
  [/#aaa\b/gi, '#7d7c76'],
  [/#000\b/gi, '#e6e4dd'],  // mürekkep
  [/#fff\b/gi, '#1b1e26'],  // lane zemini / etiket kutusu → koyu panel
  [/fill:\s*white/g, 'fill:#1b1e26'],
  [/stroke:\s*white/g, 'stroke:#1b1e26'],
  [/fill:\s*black/g, 'fill:#e6e4dd'],
  [/stroke:\s*black/g, 'stroke:#e6e4dd'],
];

function renderWavedrom(source) {
  const obj = JSON5.parse(source);
  const idx = wavedromIndex++;
  const raw = onml.stringify(wavedrom.renderAny(idx, obj, wavedrom.waveSkin));
  const flat = cleanSvg(flattenWavedromStyles(raw));
  const light = namespaceSvgIds(flat, `wl${idx}`);
  let dark = flat;
  for (const [re, renk] of WD_DARK_MAP) dark = dark.replace(re, renk);
  dark = namespaceSvgIds(dark, `wd${idx}`);
  return `<div class="only-light">${light}</div><div class="only-dark">${dark}</div>`;
}

// ------------------------------------------------------------- mermaid render

const MERMAID_FONT = "-apple-system, system-ui, 'Segoe UI', sans-serif";

function renderMermaid(source, figId) {
  const out = {};
  for (const theme of ['light', 'dark']) {
    const key = sha1(source + '::' + theme + '::v3');
    const cached = path.join(CACHE, `${key}.svg`);
    if (fs.existsSync(cached)) {
      out[theme] = fs.readFileSync(cached, 'utf8');
      continue;
    }
    const tmpIn = path.join(CACHE, `${key}.mmd`);
    const tmpCfg = path.join(CACHE, `${key}.json`);
    fs.writeFileSync(tmpIn, source);
    fs.writeFileSync(
      tmpCfg,
      JSON.stringify({
        theme: theme === 'dark' ? 'dark' : 'neutral',
        themeVariables: { fontFamily: MERMAID_FONT, fontSize: '15px' },
      })
    );
    console.log(`  … mermaid render (${figId}, ${theme})`);
    execFileSync(MMDC, ['-i', tmpIn, '-o', cached, '-b', 'transparent', '-c', tmpCfg, '--svgId', `${figId}-${theme}`], {
      stdio: ['ignore', 'ignore', 'inherit'],
    });
    fs.unlinkSync(tmpIn);
    fs.unlinkSync(tmpCfg);
    out[theme] = fs.readFileSync(cached, 'utf8');
  }
  return `<div class="only-light">${cleanSvg(out.light)}</div><div class="only-dark">${cleanSvg(out.dark)}</div>`;
}

// --------------------------------------------------------------- şekil kaydı

const figures = new Map(); // id → { label: 'Şekil 3.1', sec }

function registerFigure(env, figId) {
  if (figures.has(figId)) throw new Error(`Şekil ID çakışması: ${figId}`);
  env.figCount += 1;
  const label = `Şekil ${env.secNum}.${env.figCount}`;
  figures.set(figId, { label, sec: env.secNum });
  return label;
}

function figureHtml(kind, figId, label, captionHtml, inner) {
  return (
    `<figure class="dia dia-${kind}" id="fig-${figId}">` +
    `<div class="dia-body">${inner}</div>` +
    `<figcaption><span class="fig-label">${label}</span> — ${captionHtml}</figcaption>` +
    `</figure>`
  );
}

// Diyagram dosyası → inline SVG figure
function renderDiagramFile(env, src, captionHtml) {
  const abs = path.resolve(SRC, src);
  if (!fs.existsSync(abs)) throw new Error(`Diyagram dosyası yok: ${src}`);
  const figId = path.basename(abs).replace(/\.[^.]+$/, '');
  const label = registerFigure(env, figId);
  const raw = fs.readFileSync(abs, 'utf8');
  const ext = path.extname(abs);
  if (ext === '.svg') {
    // data-wide="1" işaretli SVG'ler doğal boyutta kalır (yatay kaydırma)
    const kind = /data-wide="1"/.test(raw) ? 'svg dia-wide' : 'svg';
    return figureHtml(kind, figId, label, captionHtml, cleanSvg(raw));
  }
  if (ext === '.json5') return figureHtml('wavedrom', figId, label, captionHtml, renderWavedrom(raw));
  if (ext === '.mmd') return figureHtml('mermaid', figId, label, captionHtml, renderMermaid(raw, figId));
  throw new Error(`Bilinmeyen diyagram türü: ${src}`);
}

// ------------------------------------------------------------------- markdown

const highlighter = await createHighlighter({
  themes: ['github-light', 'github-dark'],
  langs: ['c', 'bash', 'tcl', 'verilog', 'system-verilog', 'json', 'python', 'text'],
});

const md = new MarkdownIt({
  html: true,
  linkify: false,
  typographer: false,
  highlight(code, lang) {
    const use = highlighter.getLoadedLanguages().includes(lang) ? lang : 'text';
    return highlighter.codeToHtml(code, {
      lang: use,
      themes: { light: 'github-light', dark: 'github-dark' },
      defaultColor: 'light',
    });
  },
});

md.use(anchor, { level: [2, 3, 4], slugify, tabIndex: false });

// Callout kutuları: ::: not / dikkat / saha / pasa / ogren
const CALLOUTS = {
  not: { cls: 'co-not', title: 'NOT' },
  dikkat: { cls: 'co-dikkat', title: 'DİKKAT' },
  saha: { cls: 'co-saha', title: 'SAHA NOTU' },
  pasa: { cls: 'co-pasa', title: 'PAŞA NOTU' },
  ogren: { cls: 'co-ogren', title: 'Bu bölümde ne öğreneceksin' },
};
for (const [name, cfg] of Object.entries(CALLOUTS)) {
  md.use(container, name, {
    render(tokens, i) {
      if (tokens[i].nesting === 1) {
        const custom = tokens[i].info.trim().slice(name.length).trim();
        const title = custom || cfg.title;
        return `<aside class="callout ${cfg.cls}"><p class="co-title">${md.utils.escapeHtml(title)}</p>\n`;
      }
      return '</aside>\n';
    },
  });
}

// Çitli wavedrom/mermaid blokları (dosyasız, yerinde tanım): ```wavedrom id | altyazı
const defaultFence = md.renderer.rules.fence;
md.renderer.rules.fence = function (tokens, idx, options, env, self) {
  const info = tokens[idx].info.trim();
  const m = info.match(/^(wavedrom|mermaid)\s+([a-z0-9-]+)\s*\|\s*(.+)$/i);
  if (m) {
    const [, kind, figId, caption] = m;
    const label = registerFigure(env, figId);
    const captionHtml = md.renderInline(caption, env);
    const inner = kind === 'wavedrom' ? renderWavedrom(tokens[idx].content) : renderMermaid(tokens[idx].content, figId);
    return figureHtml(kind, figId, label, captionHtml, inner);
  }
  return defaultFence(tokens, idx, options, env, self);
};

// Tek başına duran görsel paragraflarını <figure>'a çevir; başlıkları TOC'a topla
const toc = []; // { level, id, text, sec }

md.core.ruler.push('kilavuz', (state) => {
  const env = state.env;
  const tokens = state.tokens;
  let h2Count = 0;
  for (let i = 0; i < tokens.length; i++) {
    const t = tokens[i];

    // paragraf = [tek görsel] → figure
    if (
      t.type === 'paragraph_open' &&
      tokens[i + 1]?.type === 'inline' &&
      tokens[i + 2]?.type === 'paragraph_close' &&
      tokens[i + 1].children?.length === 1 &&
      tokens[i + 1].children[0].type === 'image'
    ) {
      const img = tokens[i + 1].children[0];
      const src = img.attrGet('src') || '';
      if (src.includes('/diagrams/')) {
        const captionHtml = md.renderInline(img.content || '', env);
        const html = new state.Token('html_block', '', 0);
        html.content = renderDiagramFile(env, src, captionHtml) + '\n';
        html.block = true;
        tokens.splice(i, 3, html);
        continue;
      }
    }

    // başlıklar: h1 → bolum-N kimliği; h2 → N.M numarası; TOC kaydı
    if (t.type === 'heading_open') {
      const inline = tokens[i + 1];
      const text = inline.children
        .filter((c) => c.type === 'text' || c.type === 'code_inline')
        .map((c) => c.content)
        .join('')
        .replace(/\{\{sec:(\d+)\}\}/g, '§$1') // TOC'ta düz metin (iç içe <a> olmaz)
        .replace(/\{\{fig:[a-z0-9-]+\}\}/g, '');
      if (t.tag === 'h1') {
        t.attrSet('id', `bolum-${env.secNum}`);
        t.attrSet('class', 'sec-title');
        toc.push({ level: 1, id: `bolum-${env.secNum}`, text, sec: env.secNum });
      } else if (t.tag === 'h2') {
        h2Count += 1;
        const num = `${env.secNum}.${h2Count}`;
        const numTok = new state.Token('html_inline', '', 0);
        numTok.content = `<span class="h2-num">${num}</span> `;
        inline.children.unshift(numTok);
        toc.push({ level: 2, id: t.attrGet('id'), text: `${num} ${text}`, sec: env.secNum });
      }
    }
  }
});

// ---------------------------------------------------------------------- build

const t0 = Date.now();
console.log('▶ build başladı');

const files = fs
  .readdirSync(SRC)
  .filter((f) => /^\d{2}-.*\.md$/.test(f))
  .sort();

if (files.length === 0) throw new Error('src/ altında bölüm dosyası yok');

const sections = [];
const stats = [];
for (const f of files) {
  const secNum = parseInt(f.slice(0, 2), 10);
  const raw = fs.readFileSync(path.join(SRC, f), 'utf8');
  const env = { secNum, figCount: 0 };
  const html = md.render(raw, env);
  sections.push(`<section class="bolum" data-sec="${secNum}">\n${html}\n</section>`);
  const words = raw.replace(/```[\s\S]*?```/g, ' ').split(/\s+/).filter(Boolean).length;
  stats.push({ file: f, secNum, words, figs: env.figCount });
}

let content = sections.join('\n');

// "- [ ]" görev maddeleri → şık onay kutusu
content = content.replace(/<li>\[ \]\s*/g, '<li class="gorev">');

// h1 "Bölüm N — Ad" → kicker + ad (tipografi için)
content = content.replace(
  /(<h1[^>]*class="sec-title"[^>]*>)Bölüm (\d+) — ([^<]+)(<\/h1>)/g,
  '$1<span class="sec-kicker">Bölüm $2</span><span class="sec-name">$3</span>$4'
);

// {{fig:id}} ve {{sec:N}} çapraz referansları
content = content.replace(/\{\{fig:([a-z0-9-]+)\}\}/g, (_, id) => {
  const fig = figures.get(id);
  if (!fig) {
    warn(`Kırık şekil referansı: {{fig:${id}}}`);
    return `<span class="brokenref">[KIRIK-REF fig:${id}]</span>`;
  }
  return `<a class="figref" href="#fig-${id}">${fig.label}</a>`;
});
content = content.replace(/\{\{sec:(\d+)\}\}/g, (_, n) => {
  const num = parseInt(n, 10);
  if (!stats.some((s) => s.secNum === num)) {
    warn(`Kırık bölüm referansı: {{sec:${n}}}`);
    return `<span class="brokenref">[KIRIK-REF sec:${n}]</span>`;
  }
  return `<a class="secref" href="#bolum-${num}">§${num}</a>`;
});
const leftover = content.match(/\{\{[a-z]+:[^}]*\}\}/g);
if (leftover) leftover.forEach((l) => warn(`Çözülmemiş referans: ${l}`));

// ------------------------------------------------------------------------ TOC

const KISIMLAR = [
  { label: null, range: [0, 0] },
  { label: 'KISIM I — Temeller', range: [1, 3] },
  { label: 'KISIM II — SERDES ve JESD204', range: [4, 7] },
  { label: 'KISIM III — Clocking ve SYSREF', range: [8, 10] },
  { label: 'KISIM IV — Donanım Zincirleri', range: [11, 13] },
  { label: 'KISIM V — Versal Entegrasyonu', range: [14, 16] },
  { label: 'KISIM VI — Kapanış', range: [17, 19] },
];

function buildToc() {
  let html = '<nav class="toc" id="toc" aria-label="İçindekiler">\n';
  for (const k of KISIMLAR) {
    const items = toc.filter((t) => t.sec >= k.range[0] && t.sec <= k.range[1]);
    if (items.length === 0) continue;
    if (k.label) html += `<p class="toc-kisim">${k.label}</p>\n`;
    html += '<ul>\n';
    for (const item of items) {
      if (item.level === 1) {
        html += `<li class="toc-h1" data-sec="${item.sec}"><a href="#${item.id}">${md.utils.escapeHtml(item.text)}</a>`;
        const subs = toc.filter((s) => s.level === 2 && s.sec === item.sec);
        if (subs.length) {
          html += '<ul class="toc-sub">';
          for (const s of subs) html += `<li><a href="#${s.id}">${md.utils.escapeHtml(s.text)}</a></li>`;
          html += '</ul>';
        }
        html += '</li>\n';
      }
    }
    html += '</ul>\n';
  }
  html += '</nav>';
  return html;
}

// -------------------------------------------------------------------- şablon

const template = fs.readFileSync(path.join(ROOT, 'templates', 'page.html'), 'utf8');
const totalWords = stats.reduce((a, s) => a + s.words, 0);
const kelimeStr = totalWords >= 1000 ? `~${Math.round(totalWords / 1000)}k` : `${totalWords}`;
const buildInfo = `${new Date().toISOString().slice(0, 10)} · ${stats.length} bölüm · ${figures.size} şekil · ${kelimeStr} kelime`;

const out = template
  .replace('<!--{TOC}-->', buildToc())
  .replace('<!--{CONTENT}-->', content)
  .replace('<!--{BUILD_INFO}-->', buildInfo);

fs.writeFileSync(path.join(DIST, 'index.html'), out);

// ----------------------------------------------------------------------- özet

const dogrula = files
  .map((f) => {
    const c = fs.readFileSync(path.join(SRC, f), 'utf8');
    return { f, n: (c.match(/\[DOĞRULA/g) || []).length };
  })
  .filter((x) => x.n > 0);

console.log('\n  bölüm                              kelime  şekil');
for (const s of stats) {
  console.log(`  ${s.file.padEnd(36)} ${String(s.words).padStart(5)}  ${String(s.figs).padStart(4)}`);
}
console.log(`  ${'TOPLAM'.padEnd(36)} ${String(totalWords).padStart(5)}  ${String(figures.size).padStart(4)}`);
if (dogrula.length) {
  console.log('\n  [DOĞRULA] etiketleri:');
  dogrula.forEach((x) => console.log(`    ${x.f}: ${x.n}`));
}
if (warnings.length) console.log(`\n  ⚠ ${warnings.length} uyarı`);
const kb = (fs.statSync(path.join(DIST, 'index.html')).size / 1024).toFixed(0);
console.log(`\n✔ dist/index.html yazıldı (${kb} KB, ${((Date.now() - t0) / 1000).toFixed(1)} sn)`);
if (warnings.length) process.exitCode = 0; // uyarılar build'i düşürmez; verify.mjs sıkı kontrol yapar
