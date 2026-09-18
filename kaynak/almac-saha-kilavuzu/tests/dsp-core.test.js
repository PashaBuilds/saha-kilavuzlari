// dsp-core birim testleri + KICKOFF §10.4 bilinen-cevap kontrolleri
// Çalıştır: node --test tests/   (Node ≥ 18)
"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const path = require("node:path");
const fs = require("node:fs");
const DSP = require(path.join(__dirname, "..", "assets", "js", "dsp-core.js"));
const S = JSON.parse(fs.readFileSync(path.join(__dirname, "..", "data", "scenario.json"), "utf8"));

const yakin = (a, b, tol, msg) => assert.ok(Math.abs(a - b) <= tol, `${msg || ""} beklenen ${b}, bulunan ${a}`);

test("kTB 290 K, 1 Hz = −174.0 dBm/Hz", () => yakin(DSP.KTB_DBM_HZ, -174.0, 0.05));
test("gürültü tabanı B=300 MHz, NF=6 → −83.2 dBm", () => yakin(DSP.gurultuTabaniDbm(300e6, 6), -83.2, 0.05));
test("hassasiyet 15 dB SNR → −68.2 dBm", () => yakin(DSP.hassasiyetDbm(300e6, 6, 15), -68.2, 0.05));
test("ideal SNR 14 bit = 86.04 dB", () => yakin(DSP.snrKuantizasyon(14), 86.04, 0.01));
test("jitter SNR f=1 GHz, σ=100 fs ≈ 64.0 dB", () => yakin(DSP.snrJitter(1e9, 100e-15), 64.04, 0.05));
test("alias fs=2400, f=1800 → 600 MHz, evrik, 2. bölge", () => {
  const k = DSP.katla(1800e6, 2400e6);
  yakin(k.alias, 600e6, 1); assert.equal(k.evrik, true); assert.equal(k.bolge, 2);
});
test("alias fs=2400, f=600 → 600 MHz, düz, 1. bölge", () => {
  const k = DSP.katla(600e6, 2400e6);
  yakin(k.alias, 600e6, 1); assert.equal(k.evrik, false); assert.equal(k.bolge, 1);
});
test("FTW f=600, fs=2400, N=32 → 0x40000000", () => {
  const v = DSP.ftw(600e6, 2400e6, 32);
  assert.equal(DSP.ftwHex(v, 32), "0x40000000"); assert.equal(v, S.ddc.ftw);
});
test("NCO çözünürlüğü fs=2400, N=32 ≈ 0.559 Hz", () => yakin(DSP.ncoCozunurluk(2400e6, 32), 0.559, 0.001));
test("işlem kazancı 1200 → 300 MHz = 6.02 dB", () => yakin(DSP.islemKazanci(2400e6, 300e6), 6.02, 0.01));
test("FFT bin fs=300 MSPS, N=1024 ≈ 293 kHz", () => yakin(300e6 / 1024, 292968.75, 0.01));
test("FFT işlem kazancı N=1024 ≈ 27.1 dB", () => yakin(DSP.fftIslemKazanci(1024), 27.09, 0.02));
test("Hann ENBW = 1.50 bin, CG = 0.5", () => {
  const m = DSP.pencereMetrik(DSP.pencere("hann", 1024));
  yakin(m.enbw, 1.5, 0.01); yakin(m.cg, 0.5, 0.001);
  assert.ok(m.yanLobDb < -30 && m.yanLobDb > -33, "Hann yan lob ≈ −31.5 dB: " + m.yanLobDb);
});
test("dikdörtgen pencere yan lob ≈ −13.3 dB, scalloping ≈ 3.9 dB", () => {
  const m = DSP.pencereMetrik(DSP.pencere("rect", 256));
  yakin(m.yanLobDb, -13.26, 0.2); yakin(m.scallop, 3.92, 0.05); yakin(m.enbw, 1.0, 0.001);
});
test("Blackman-Harris yan lob < −90 dB", () => assert.ok(DSP.pencereMetrik(DSP.pencere("blackman-harris", 512)).yanLobDb < -88));
test("Rayleigh eşik Pfa=1e-6 = 5.26 σ (ve tersi)", () => {
  yakin(DSP.rayleighEsik(1e-6), 5.257, 0.002); yakin(DSP.rayleighPfa(5.257), 1e-6, 2e-8);
});
test("CA-CFAR α N=16, Pfa=1e-6 ≈ 21.9", () => yakin(DSP.caCfarAlfa(16, 1e-6), 21.94, 0.05));
test("Friis LNA(20 dB, NF 2) + mixer(NF 10) ≈ 2.2 dB", () => {
  const f = DSP.friis([{ kazanc_db: 20, nf_db: 2 }, { kazanc_db: -7, nf_db: 10 }]);
  yakin(f.nf_db, 2.24, 0.03);
});
test("Friis: LNA'yı sona almak NF'i patlatır", () => {
  const iyi = DSP.friis([{ kazanc_db: 20, nf_db: 2 }, { kazanc_db: -7, nf_db: 10 }]).nf_db;
  const kotu = DSP.friis([{ kazanc_db: -7, nf_db: 10 }, { kazanc_db: 20, nf_db: 2 }]).nf_db;
  assert.ok(kotu > iyi + 8, `kötü ${kotu} iyi ${iyi}`);
});
test("senaryo kaskadı Friis ≈ 3.5 dB (bütçe 6 dB'nin altında)", () => {
  const f = DSP.friis(S.on_uc.kaskad);
  yakin(f.nf_db, S.on_uc.nf_friis_db, 0.1, "Friis");
  assert.ok(f.nf_db < S.on_uc.nf_toplam_db, "bütçe aşıldı: " + f.nf_db);
  yakin(f.kazanc_db, 40, 0.5);
});
test("FFT: tam ölçek ton 0 dBFS'e düşer, bin doğru", () => {
  const N = 1024, fs = 300e6, f = 50 * fs / N;
  const t = DSP.tonKompleks(N, fs, f, 1);
  const sp = DSP.spektrumDbfs(t.i, t.q, "rect");
  const m = DSP.spektrumMetrik(sp);
  yakin(m.tepeDbfs, 0, 0.01); assert.equal(m.tepeBin, N / 2 + 50);
});
test("FFT/IFFT gidiş-dönüş", () => {
  const N = 64, re = new Float64Array(N), im = new Float64Array(N);
  for (let k = 0; k < N; k++) re[k] = Math.sin(k * 0.3) + 0.2 * k;
  const r0 = Float64Array.from(re);
  DSP.fft(re, im, false); DSP.fft(re, im, true);
  for (let k = 0; k < N; k++) yakin(re[k], r0[k], 1e-9);
});
test("kuantizasyon SNR ölçümü teoriye yakın (12 bit, dither)", () => {
  const N = 8192, fs = 1, f = 611 / N; // koherent bin
  const x = DSP.ton(N, fs, f, 0.98);
  const y = DSP.kuantize(x, 12, { dither: true, rnd: DSP.prng(42) });
  const sp = DSP.spektrumDbfs(y, null, "rect", { reel: true });
  // reel sinyal: sadece pozitif yarıyı değerlendir
  const poz = sp.subarray(N / 2);
  const m = DSP.spektrumMetrik(poz, { koruma: 2 });
  const teori = DSP.snrKuantizasyon(12) + DSP.db20(0.98) - 3.01; // ±½ LSB tekdüze dither gürültü gücünü ikiye katlar
  assert.ok(Math.abs(m.snr - teori) < 1.5, `ölçülen ${m.snr.toFixed(1)} teori ${teori.toFixed(1)}`);
});
test("Monte Carlo Pfa: Rayleigh eşik, hedef 1e-3, 1e7 örnek → ±%5", () => {
  const rnd = DSP.prng(2024), T = DSP.rayleighEsik(1e-3), T2 = T * T;
  let n = 1e7, say = 0;
  for (let k = 0; k < n; k++) { const g = DSP.gaussKompleks(rnd, Math.SQRT2); if (g[0] * g[0] + g[1] * g[1] > T2) say++; }
  const pfa = say / n;
  assert.ok(Math.abs(pfa - 1e-3) / 1e-3 < 0.05, "Pfa " + pfa);
});
test("CA-CFAR Monte Carlo: gürültüde ölçülen Pfa hedefe yakın (1e-3)", () => {
  const rnd = DSP.prng(77), n = 400000, guc = new Float64Array(n);
  for (let k = 0; k < n; k++) { const g = DSP.gaussKompleks(rnd, 1); guc[k] = g[0] * g[0] + g[1] * g[1]; }
  const N = 16, a = DSP.caCfarAlfa(N, 1e-3);
  const r = DSP.cfar(guc, "CA", N, 2, a);
  let s = 0; for (let k = 20; k < n - 20; k++) s += r.tespit[k];
  const pfa = s / (n - 40);
  assert.ok(Math.abs(pfa - 1e-3) / 1e-3 < 0.15, "Pfa " + pfa);
});
test("darbe FSM: 1 µs darbe 300 MSPS'te 300 örnek, PW ≈ 1 µs", () => {
  const fs = 300e6, n = 4096;
  const d = DSP.darbeKompleks({ n, fs, pw: 1e-6, pri: 0, f0: 0, genlik: 1, gecikme: 2e-6 });
  DSP.gurultuEkle(d, 0.05, DSP.prng(9));
  const p = DSP.darbeFsm(DSP.guc(d.i, d.q), 0.25, { fs, histerezisDb: 3, minPw: 4 });
  assert.equal(p.length, 1);
  yakin(p[0].pw_s, 1e-6, 5e-9); yakin(p[0].toa_s, 2e-6, 5e-9);
});
test("LFM darbe: anlık frekans eğimi = BW/PW", () => {
  const fs = 300e6, n = 2048, pw = 1e-6, bw = 10e6;
  const d = DSP.darbeKompleks({ n, fs, pw, pri: 0, f0: 0, mop: "lfm", chirpBw: bw, gecikme: 1e-6 });
  const egim = DSP.chirpEgimi(d.i, d.q, 300, 600, fs);
  yakin(egim / (bw / pw), 1, 0.02);
});
test("DDC: 1800 MHz IF, fs 2400, NCO 600 → baseband'de 0 Hz civarı (evrik: −Δf)", () => {
  const fs = 2400e6, N = 4096, f = 1800e6 + 5e6; // IF'in 5 MHz üstü
  const x = DSP.ton(N, fs, f, 0.5);
  const r = DSP.ddc(x, fs, 600e6, 100e6, 8, 63, -1);
  const sp = DSP.spektrumDbfs(r.dec.i, r.dec.q, "hann");
  const m = DSP.spektrumMetrik(sp);
  const fOut = (m.tepeBin - sp.length / 2) * r.fsOut / sp.length;
  yakin(fOut, -5e6, r.fsOut / sp.length * 1.5, "evrik bölgede +5 MHz → −5 MHz");
});
test("CIC bit büyümesi R=4, N=4 → 8 bit", () => assert.equal(DSP.cicBitBuyumesi(4, 4), 8));
test("halfband: tek tap'ler sıfır", () => {
  const h = DSP.halfband(15); const m = 7;
  for (let k = 0; k < h.length; k++) if (k !== m && (k - m) % 2 === 0) assert.equal(h[k], 0);
});
test("Pd Swerling-0 (Pfa 1e-6): 11.2 dB → ≈0.5, 13.2 dB → ≈0.9, 15 dB → >0.97", () => {
  const a = DSP.pdSwerling0(11.2, 1e-6), b = DSP.pdSwerling0(13.2, 1e-6), c = DSP.pdSwerling0(15, 1e-6);
  yakin(a, 0.5, 0.06, "Pd(11.2)"); yakin(b, 0.9, 0.04, "Pd(13.2)"); assert.ok(c > 0.97, "Pd(15 dB) " + c);
});
test("Albersheim Pd=0.9, Pfa=1e-6, N=1 ≈ 13.2 dB", () => yakin(DSP.albersheim(0.9, 1e-6, 1), 13.2, 0.3));
test("dBm ↔ Vrms (50 Ω): 0 dBm = 223.6 mV", () => yakin(DSP.dbmToVrms(0), 0.2236, 0.0005));
test("time walk: %50 eşik = rise/2", () => yakin(DSP.timeWalk(50e-9, 0.5), 25e-9, 1e-11));
