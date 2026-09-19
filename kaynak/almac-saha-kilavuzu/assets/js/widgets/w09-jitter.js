/* W-09 — Jitter–SNR hesaplayıcı
   Kontroller: f_in, σ_jitter (saat + aperture birleşik), bit sayısı, termal (ADC iç) SNR, ilgilenilen bant B
   Çıktı: bileşen bileşen SNR (kuantizasyon, jitter, termal) ve güç domeninde toplam (DSP.snrBirlestir);
   baskın terim vurgusu; f_in ekseninde eğri ailesi ve çalışma noktası; işlem kazancıyla bant içi SNR
   Hesap: DSP.snrKuantizasyon, DSP.snrJitter, DSP.snrBirlestir, DSP.islemKazanci, DSP.enob, DSP.nsd */
WK.kaydet("w09", function (w) {
  var S = w.S, fsRef = S.adc ? S.adc.fs_hz : 2400e6, bitRef = S.adc ? S.adc.bit : 14;
  var fRef = S.on_uc ? S.on_uc.if_hz : 1800e6, jRef = S.adc ? S.adc.jitter_s : 100e-15;
  var bwRef = S.ddc ? 2 * S.ddc.cikis_bant_mhz * 1e6 : 300e6;
  WK.kaydirici(w, { ad: "f", etiket: "giriş frekansı f_in", min: 10e6, max: 12000e6, deger: fRef, log: true, olcek: 1e6, birim: "MHz", hane: 0 });
  WK.kaydirici(w, { ad: "j", etiket: "toplam jitter σ_j (rms)", min: 5e-15, max: 5e-12, deger: jRef, log: true, olcek: 1e-15, birim: "fs", hane: 0 });
  WK.kaydirici(w, { ad: "bit", etiket: "çözünürlük N", min: 6, max: 16, adim: 1, deger: bitRef, birim: "bit", tamsayi: true });
  WK.kaydirici(w, { ad: "termal", etiket: "termal SNR (ADC, düşük f_in)", min: 40, max: 90, adim: 0.5, deger: 62, birim: "dB" });
  var kapat = WK.grup(w, "Bant");
  WK.kaydirici(w, { ad: "fs", etiket: "fs", min: 100e6, max: 6000e6, adim: 10e6, deger: fsRef, olcek: 1e6, birim: "MHz" });
  WK.kaydirici(w, { ad: "bw", etiket: "ilgilenilen bant B", min: 1e6, max: 3000e6, deger: bwRef, log: true, olcek: 1e6, birim: "MHz", hane: 0 });
  kapat();

  var cub = WK.panel(w, 150), egri = WK.panel(w, 260);

  function ciz() {
    var p = w.param;
    var q = DSP.snrKuantizasyon(p.bit), j = DSP.snrJitter(p.f, p.j), t = p.termal;
    var toplam = DSP.snrBirlestir([q, j, t]);
    var pg = DSP.islemKazanci(p.fs, p.bw);
    var bantIci = toplam + pg;
    var bilesen = [["kuantizasyon 6.02N+1.76", q], ["jitter −20log(2πfσ)", j], ["termal (datasheet)", t]];
    var baskin = bilesen.reduce(function (a, b) { return b[1] < a[1] ? b : a; });
    // ---- çubuklar
    WK.temizle(cub);
    var gc = WK.grafik(cub, { W: 640, H: 150, xmin: 20, xmax: 110, ymin: 0, ymax: 4, kenar: { sol: 190, sag: 14, ust: 22, alt: 34 } });
    gc.eksenler({ xAdet: 9, yTik: [], xAd: "SNR (dB) — kısa çubuk = daha çok gürültü = baskın terim", baslik: "Bileşenler ve toplam (güç domeninde birleşik)" });
    var satir = bilesen.concat([["TOPLAM (Nyquist bandı)", toplam]]);
    satir.forEach(function (s, i) {
      var y = gc.y1 + 6 + i * (gc.y0 - gc.y1 - 12) / 4, h = (gc.y0 - gc.y1 - 12) / 4 - 6;
      var kls = i === 3 ? "w-dolgu-sinyal" : (s === baskin ? "w-dolgu-kirmizi" : "w-dolgu-altin");
      gc.ekle("rect", { x: gc.x0, y: y, width: Math.max(0, gc.px(Math.min(110, Math.max(20, s[1]))) - gc.x0), height: h, "class": kls });
      gc.metin(gc.x0 - 6, y + h / 2 + 4, s[0], "w-not", "end");
      gc.metin(gc.px(Math.min(110, Math.max(20, s[1]))) + 4, y + h / 2 + 4, s[1].toFixed(1) + " dB" + (s === baskin ? " ← baskın" : ""), "w-not");
    });
    // ---- eğri: SNR vs f_in
    WK.temizle(egri);
    var ge = WK.grafik(egri, { W: 640, H: 260, xmin: 10, xmax: 12000, ymin: 20, ymax: 110, xlog: true, kenar: { sol: 48, sag: 14, ust: 22, alt: 34 } });
    ge.eksenler({ xTik: [10, 30, 100, 300, 1000, 3000, 10000], yAdet: 9, xAd: "giriş frekansı f_in (MHz, log) — fs değil", yAd: "SNR (dB)", baslik: "Toplam SNR'ın f_in ile düşüşü: jitter köşesi", xFmt: function (v) { return v >= 1000 ? (v / 1000) + " GHz" : v + ""; } });
    var xs = [], yj = [], yt = [], yq = [], yb = [];
    for (var k = 0; k <= 120; k++) {
      var f = 10 * Math.pow(1200, k / 120);
      var sj = DSP.snrJitter(f * 1e6, p.j);
      xs.push(f); yj.push(sj); yq.push(q); yt.push(t); yb.push(DSP.snrBirlestir([q, sj, t]));
    }
    ge.cizgi(xs, yq, "w-cizgi-altin"); ge.metin(ge.x0 + 6, ge.py(q) - 4, "kuantizasyon " + q.toFixed(1), "w-not");
    ge.cizgi(xs, yt, "w-cizgi-yesil"); ge.metin(ge.x0 + 6, ge.py(t) - 4, "termal " + t.toFixed(1), "w-not");
    ge.cizgi(xs, yj, "w-cizgi-kirmizi");
    ge.cizgi(xs, yb, "w-cizgi-sinyal");
    ge.etiket(ge.px(300), ge.py(DSP.snrJitter(3e8, p.j)) - 8, "jitter σ = " + WK.kisaSayi(p.j * 1e15) + " fs", "middle");
    ge.nokta(p.f / 1e6, toplam, 5, "w-nokta");
    var cx = ge.px(p.f / 1e6), cSag = cx > ge.x0 + 0.7 * (ge.x1 - ge.x0);   // sağ kenarda etiket sola (kırpılmasın)
    ge.etiket(cx + (cSag ? -8 : 8), ge.py(toplam) + 16, "çalışma noktası " + toplam.toFixed(1) + " dB", cSag ? "end" : "start");
    // jitter köşesi: jitter SNR'ın termal+kuantizasyon toplamına eşitlendiği f
    var tabanTQ = DSP.snrBirlestir([q, t]);
    var fKose = DSP.lin20(-tabanTQ) / (2 * Math.PI * p.j);
    if (fKose / 1e6 > 10 && fKose / 1e6 < 12000) ge.dikey(fKose / 1e6, "w-cizgi-gri", "köşe " + WK.fmtHz(fKose));
    // ---- sonuç
    var sigmaGerek = DSP.lin20(-tabanTQ) / (2 * Math.PI * p.f);
    WK.sonucYaz(w, {
      "kuantizasyon": q.toFixed(1) + " dB",
      "jitter": (j < tabanTQ - 3 ? "!" : "") + j.toFixed(1) + " dB (f_in = " + WK.fmtHz(p.f) + ", σ = " + WK.kisaSayi(p.j * 1e15) + " fs)",
      "termal": t.toFixed(1) + " dB",
      "toplam (Nyquist bandı)": toplam.toFixed(1) + " dB → ENOB " + DSP.enob(toplam).toFixed(1) + " bit",
      "baskın terim": (baskin[1] === j ? "!" : "") + baskin[0],
      "NSD": DSP.nsd(toplam, p.fs).toFixed(1) + " dBFS/Hz",
      "işlem kazancı 10log(fs/2B)": "+" + pg.toFixed(1) + " dB → bant içi SNR " + bantIci.toFixed(1) + " dB",
      "jitter köşesi": WK.fmtHz(fKose) + " (bu f_in'in üstünde jitter baskın)",
      "bu f_in'de jitter'ın görünmez kalması için": "σ ≤ " + (sigmaGerek * 1e15).toFixed(0) + " fs"
    });
  }
  return {
    ciz: ciz,
    presetler: [
      { ad: "Referans senaryo", param: { f: fRef, j: jRef, bit: bitRef, termal: 62, fs: fsRef, bw: bwRef } },
      { ad: "Direct RF 9.4 GHz", param: { f: 9400e6, j: jRef, bit: bitRef, termal: 62, fs: 5000e6, bw: bwRef } },
      { ad: "Kötü saat (1 ps)", param: { f: fRef, j: 1e-12, bit: bitRef, termal: 62, fs: fsRef, bw: bwRef } },
      { ad: "Düşük IF (100 MHz)", param: { f: 100e6, j: jRef, bit: bitRef, termal: 62, fs: fsRef, bw: bwRef } },
      { ad: "Mükemmel saat (10 fs)", param: { f: fRef, j: 10e-15, bit: bitRef, termal: 62, fs: fsRef, bw: bwRef } }
    ]
  };
});
