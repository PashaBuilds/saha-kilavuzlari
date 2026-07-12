// verify.mjs — Definition of Done denetçisi (KICKOFF §10 + final geçiş şartları)
// Kontroller:
//  (a) dist/index.html'de dış istek yok (http/https src|href taraması)
//  (b) şema sayısı = envanter (18 inline figür, kimlikleriyle)
//  (c) kalan [DOĞRULA] etiketi = 0
//  (d) src/ altında 20 bölüm dosyası
//  (e) sözlük maddeleri: bölüm linkleri kırık değil + her terim metinde geçiyor
//  (+) çözülmemiş {{...}} / KIRIK-REF kalıntısı yok; şekil numaraları ardışık

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const dist = fs.readFileSync(path.join(ROOT, 'dist', 'index.html'), 'utf8');
const srcDir = path.join(ROOT, 'src');

let fail = 0;
const ok = (name, cond, detail = '') => {
  console.log(`${cond ? '✔' : '✘'} ${name}${detail ? ' — ' + detail : ''}`);
  if (!cond) fail++;
};

// (a) dış istek
const ext = dist.match(/(?:src|href)\s*=\s*"(https?:)?\/\/[^"]+"/gi) || [];
ok('(a) dış istek yok', ext.length === 0, ext.length ? `${ext.length} bulundu: ${ext.slice(0, 3).join(', ')}` : 'src/href taraması temiz');

// (b) şema envanteri
const ENVANTER = [
  'd01', 'd02', 'd03', 'd04', 'd05', 'd06', 'd07', 'd08', 'd09', 'd10',
  'w01', 'w02', 'w03', 'w04', 'w05',
  'm01b', 'm01c', 'm02',
];
const figIds = [...dist.matchAll(/<figure class="dia [^"]*" id="fig-([a-z0-9-]+)"/g)].map((m) => m[1]);
const eksik = ENVANTER.filter((id) => !figIds.includes(id));
const fazla = figIds.filter((id) => !ENVANTER.includes(id));
ok('(b) şema sayısı = envanter', figIds.length === ENVANTER.length && !eksik.length && !fazla.length,
  `${figIds.length}/${ENVANTER.length}` + (eksik.length ? ` eksik: ${eksik}` : '') + (fazla.length ? ` fazla: ${fazla}` : ''));

// (c) [DOĞRULA]
const srcFiles = fs.readdirSync(srcDir).filter((f) => /^\d{2}-.*\.md$/.test(f)).sort();
let dogrula = 0;
for (const f of srcFiles) dogrula += (fs.readFileSync(path.join(srcDir, f), 'utf8').match(/\[DOĞRULA/g) || []).length;
ok('(c) [DOĞRULA] etiketi = 0', dogrula === 0, dogrula ? `${dogrula} kaldı` : 'temiz');

// (d) 20 bölüm dosyası
ok('(d) 20 bölüm dosyası', srcFiles.length === 20, `${srcFiles.length} dosya`);

// (e) sözlük
const sozluk = fs.readFileSync(path.join(srcDir, '18-sozluk.md'), 'utf8');
const maddeler = [...sozluk.matchAll(/^- \*\*(.+?)\*\* — [\s\S]*?\{\{sec:(\d+)\}\}/gm)];
ok('(e1) sözlükte madde var', maddeler.length >= 60, `${maddeler.length} madde`);

// bölüm linkleri: hedef id'ler dist'te mevcut mu
const bolumIds = new Set([...dist.matchAll(/<h1[^>]*id="(bolum-\d+)"/g)].map((m) => m[1]));
const kirikLink = maddeler.filter(([, , n]) => !bolumIds.has(`bolum-${n}`));
ok('(e2) sözlük bölüm linkleri sağlam', kirikLink.length === 0,
  kirikLink.length ? `kırık: ${kirikLink.map((m) => m[1]).join(', ')}` : `${maddeler.length} link doğrulandı`);

// her terim metinde geçiyor mu (sözlük dışındaki bölümlerde)
const digerMetin = srcFiles
  .filter((f) => !f.startsWith('18-'))
  .map((f) => fs.readFileSync(path.join(srcDir, f), 'utf8'))
  .join('\n')
  .toLowerCase();
const gecmeyen = [];
for (const [, terim] of maddeler) {
  const adaylar = terim
    .split('/')
    .map((t) => t.replace(/\(.*?\)/g, '').trim().toLowerCase())
    .filter(Boolean);
  if (!adaylar.some((a) => digerMetin.includes(a))) gecmeyen.push(terim);
}
ok('(e3) her sözlük terimi metinde geçiyor', gecmeyen.length === 0,
  gecmeyen.length ? `geçmeyen: ${gecmeyen.join(', ')}` : 'tümü bulundu');

// (+) çözülmemiş referans kalıntıları
const kalinti = dist.match(/\{\{[a-z]+:[^}]*\}\}|KIRIK-REF/g) || [];
ok('(+) çözülmemiş referans yok', kalinti.length === 0, kalinti.length ? kalinti.slice(0, 5).join(', ') : 'temiz');

// (+) şekil numaraları bölüm içinde ardışık
const etiketler = [...dist.matchAll(/<span class="fig-label">Şekil (\d+)\.(\d+)<\/span>/g)].map((m) => [+m[1], +m[2]]);
let sirali = true;
const sayac = {};
for (const [s, n] of etiketler) {
  sayac[s] = (sayac[s] || 0) + 1;
  if (n !== sayac[s]) sirali = false;
}
ok('(+) şekil numaraları ardışık', sirali, etiketler.map(([s, n]) => `${s}.${n}`).join(' '));

console.log(fail ? `\n✘ ${fail} kontrol BAŞARISIZ` : '\n✔ tüm kontroller geçti');
process.exit(fail ? 1 : 0);
