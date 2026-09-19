/* W-07 — Katlanma ve spur haritası
   Kontroller: fs, f_in (bant merkezi), sinyal BW, interleave yolu M, gösterilecek harmonik derecesi
   Çıktı: Nyquist bölgesi, alias konumu, evrik mi; HD2…HD5 bantlarının ve interleaving spur'larının
   1. bölgeye katlandığı yerler; "temiz bant" göstergesi (sinyal bandına spur düşüyor mu?)
   Hesap: DSP.katla, DSP.spurHaritasi */
WK.kaydet("w07", function (w) {
  var S = w.S;
  var fsRef = S.adc ? S.adc.fs_hz : 2400e6, fRef = S.on_uc ? S.on_uc.if_hz : 1800e6;
  var bwRef = S.ddc ? 2 * S.ddc.cikis_bant_mhz * 1e6 : 300e6;
  WK.kaydirici(w, { ad: "fs", etiket: "fs (örnekleme)", min: 200e6, max: 6000e6, adim: 10e6, deger: fsRef, olcek: 1e6, birim: "MHz" });
  WK.kaydirici(w, { ad: "f", etiket: "f_in (bant merkezi)", min: 10e6, max: 12000e6, adim: 10e6, deger: fRef, olcek: 1e6, birim: "MHz" });
  WK.kaydirici(w, { ad: "bw", etiket: "sinyal bandı (toplam)", min: 0, max: 1000e6, adim: 10e6, deger: bwRef, olcek: 1e6, birim: "MHz" });
  var kapat = WK.grup(w, "Bozulma kaynakları");
  WK.secim(w, { ad: "M", etiket: "interleave yolu M", secenekler: [[1, "yok (tek çekirdek)"], [2, "2"], [4, "4"], [8, "8"]], deger: 2 });
  WK.secim(w, { ad: "hmax", etiket: "harmonik derecesi", secenekler: [[3, "HD2–HD3"], [5, "HD2–HD5"]], deger: 3 });
  kapat();

  var ust = WK.panel(w, 170), alt = WK.panel(w, 250);

  // Bir bandın 1. bölgeye katlanmış aralığı: bant boyunca örnekleyip min/max alias.
  // (Bant bir bölge sınırını aşarsa aralık sınıra kadar genişler — bu da doğru davranıştır.)
  function bantKatla(fa, fb, fs) {
    var n = 96, lo = Infinity, hi = -Infinity;
    for (var k = 0; k <= n; k++) {
      var a = DSP.katla(fa + (fb - fa) * k / n, fs).alias;
      if (a < lo) lo = a;
      if (a > hi) hi = a;
    }
    return [lo, hi];
  }
  function kesisir(a, b) { return a[0] <= b[1] && b[0] <= a[1]; }

  function ciz() {
    var p = w.param, fs = p.fs, f = p.f, bw = p.bw, M = +p.M, hmax = +p.hmax;
    var nyq = fs / 2;
    var fa = Math.max(0, f - bw / 2), fb = f + bw / 2;
    var kat = DSP.katla(f, fs);
    var sinyal = bantKatla(fa, fb, fs);
    // spur listeleri
    var bantlar = []; // {ad, gercek:[a,b], kat:[a,b], tur}
    for (var h = 2; h <= hmax; h++) bantlar.push({ ad: "HD" + h, gercek: [h * fa, h * fb], kat: bantKatla(h * fa, h * fb, fs), tur: "harmonik" });
    var cizgiler = []; // {ad, f}
    if (M > 1) {
      for (var k = 1; k < M; k++) {
        cizgiler.push({ ad: "ofset k·fs/M (k=" + k + ")", f: DSP.katla(k * fs / M, fs).alias, tur: "offset" });
        var b1 = bantKatla(Math.abs(k * fs / M - fb), Math.abs(k * fs / M - fa), fs);
        var b2 = bantKatla(k * fs / M + fa, k * fs / M + fb, fs);
        bantlar.push({ ad: "IL image k·fs/M − f (k=" + k + ")", kat: b1, tur: "il" });
        bantlar.push({ ad: "IL image k·fs/M + f (k=" + k + ")", kat: b2, tur: "il" });
      }
    }
    // temiz bant kararı
    var kirleten = [];
    bantlar.forEach(function (b) { if (bw > 0 ? kesisir(b.kat, sinyal) : (b.kat[0] <= sinyal[1] && b.kat[1] >= sinyal[0])) kirleten.push(b.ad); });
    cizgiler.forEach(function (c) { if (c.f >= sinyal[0] - 1e3 && c.f <= sinyal[1] + 1e3) kirleten.push(c.ad); });
    // ---- üst panel: gerçek frekans ekseni, bölgeler
    WK.temizle(ust);
    var fmaxU = Math.max(hmax * fb, fs) * 1.05;
    var gu = WK.grafik(ust, { W: 640, H: 170, xmin: 0, xmax: fmaxU / 1e6, ymin: 0, ymax: 1, kenar: { sol: 30, sag: 14, ust: 22, alt: 34 } });
    gu.eksenler({ xAdet: 8, yTik: [], xAd: "gerçek frekans (MHz) — Nyquist bölgeleri ve bozulma kaynakları", baslik: "AAF girişi (ADC öncesi)" });
    var zn = Math.ceil(fmaxU / nyq);
    for (var z = 0; z < zn; z++) {
      var xa = z * nyq / 1e6, xb = Math.min((z + 1) * nyq, fmaxU) / 1e6;
      if (z % 2 === 1) gu.bant(xa, xb, "w-dolgu-gurultu");
      if ((xb - xa) / (fmaxU / 1e6) > 0.06) gu.metin(gu.px((xa + xb) / 2), gu.y1 + 12, (z + 1) + (z % 2 ? " evrik" : ""), "w-not", "middle");
    }
    bantlar.forEach(function (b) { if (b.gercek) gu.bant(b.gercek[0] / 1e6, b.gercek[1] / 1e6, "w-dolgu-kirmizi"); });
    gu.bant(fa / 1e6, fb / 1e6, "w-dolgu-sinyal");
    gu.dikey(f / 1e6, "w-cizgi-sinyal");
    gu.etiket(gu.px(f / 1e6) + 3, gu.y1 + 24, "f_in", "start");   // bölge etiketlerinin (üst satır) altına
    bantlar.forEach(function (b, i) { if (b.gercek) gu.metin(gu.px((b.gercek[0] + b.gercek[1]) / 2e6), gu.y0 - 6 - (i % 2) * 11, b.ad, "w-not", "middle"); });
    // ---- alt panel: 1. bölgeye katlanmış
    WK.temizle(alt);
    var ga = WK.grafik(alt, { W: 640, H: 250, xmin: 0, xmax: nyq / 1e6, ymin: 0, ymax: 1, kenar: { sol: 30, sag: 14, ust: 22, alt: 34 } });
    ga.eksenler({ xAdet: 8, yTik: [], xAd: "ADC çıkışı: 0 … fs/2 (MHz)", baslik: "1. bölgeye katlanmış harita — sinyal mavi, spur kırmızı" });
    // satır düzeni: her kaynak ayrı yükseklik şeridi
    var satirlar = [{ ad: "sinyal" + (kat.evrik ? " (evrik)" : " (düz)"), aralik: sinyal, kls: "w-dolgu-sinyal" }];
    bantlar.forEach(function (b) { satirlar.push({ ad: b.ad, aralik: b.kat, kls: "w-dolgu-kirmizi" }); });
    var n = satirlar.length, hS = (ga.y0 - ga.y1) / Math.max(n, 4);
    satirlar.forEach(function (s, i) {
      var y = ga.y1 + i * hS;
      ga.ekle("rect", { x: ga.px(Math.max(0, s.aralik[0] / 1e6)), y: y + 3, width: Math.max(2, ga.px(Math.min(nyq, s.aralik[1]) / 1e6) - ga.px(Math.max(0, s.aralik[0]) / 1e6)), height: Math.max(4, hS - 6), "class": s.kls });
      ga.etiket(ga.x0 + 4, y + hS / 2 + 4, s.ad + " → " + WK.kisaSayi(s.aralik[0] / 1e6) + "–" + WK.kisaSayi(s.aralik[1] / 1e6), "start");
    });
    // sağ kenara yakın çizgilerin etiketi sola (kırpılmasın)
    cizgiler.forEach(function (c) { ga.dikey(c.f / 1e6, "w-cizgi-kirmizi", c.ad.replace("ofset ", ""), c.f > 0.72 * nyq ? "sol" : "sag"); });
    ga.dikey(kat.alias / 1e6, "w-cizgi-sinyal", "");
    // sonuç
    var evrikDuzelt = kat.evrik ? "!evrik → NCO işareti ters ya da I/Q swap" : "+düz";
    var sonuc = {
      "Nyquist bölgesi": kat.bolge + ". bölge",
      "alias (katlanmış merkez)": WK.fmtHz(kat.alias),
      "katlanmış bant": WK.fmtHz(sinyal[0]) + " – " + WK.fmtHz(sinyal[1]),
      "spektrum": evrikDuzelt,
      "bant tek bölgede mi": (Math.floor(fa / nyq) === Math.floor((fb - 1) / nyq)) ? "+evet" : "!hayır — bant bölge sınırını aşıyor, kendi üstüne katlanır",
      "temiz bant": kirleten.length ? "!hayır: " + kirleten.join(", ") + " sinyal bandına düşüyor" : "+evet — HD" + hmax + "'e kadar ve M=" + M + " için temiz"
    };
    if (M > 1) sonuc["fs/M"] = WK.fmtHz(fs / M);
    WK.sonucYaz(w, sonuc);
  }
  return {
    ciz: ciz,
    presetler: [
      { ad: "Referans senaryo", param: { fs: fsRef, f: fRef, bw: bwRef, M: 2, hmax: 3 } },
      { ad: "Dar bant, M=4", param: { fs: fsRef, f: fRef, bw: 20e6, M: 4, hmax: 3 } },
      { ad: "fs/4'ten kaydır (IF 1700)", param: { fs: fsRef, f: 1700e6, bw: 300e6, M: 4, hmax: 3 } },
      { ad: "Bölge sınırında bant", param: { fs: fsRef, f: 1250e6, bw: 300e6, M: 2, hmax: 3 } },
      { ad: "Direct RF 9.4 GHz, 5 GSPS", param: { fs: 5000e6, f: 9400e6, bw: 300e6, M: 4, hmax: 3 } }
    ]
  };
});
