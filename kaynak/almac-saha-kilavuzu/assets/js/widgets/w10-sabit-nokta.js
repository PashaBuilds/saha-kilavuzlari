/* W-10 — Sabit nokta oyun alanı
   Kontroller: giriş seviyesi (dBFS), kelime genişliği B, yuvarlama modu (round/trunc), taşma modu (sat/wrap)
   Çıktı: zaman (ideal vs kuantize), hata sinyali (LSB), spektrum; ölçülen SNR, DC bias, taşan örnek sayısı
   Hesap: DSP.sabitNokta, DSP.spektrumDbfs, DSP.spektrumMetrik */
WK.kaydet("w10", function (w) {
  var S = w.S, fs = (S.ddc ? S.ddc.cikis_fs_msps : 300) * 1e6;
  WK.kaydirici(w, { ad: "seviye", etiket: "giriş seviyesi (tepe)", min: -80, max: 6, adim: 0.5, deger: -6, birim: "dBFS" });
  WK.kaydirici(w, { ad: "B", etiket: "kelime genişliği B", min: 4, max: 24, adim: 1, deger: 16, birim: "bit", tamsayi: true });
  var kapat = WK.grup(w, "Kesme davranışı");
  WK.secim(w, { ad: "mod", etiket: "yuvarlama", secenekler: [["round", "rounding (yuvarlama)"], ["trunc", "truncation (kesme, floor)"]], deger: "round", metin: true });
  WK.secim(w, { ad: "tasma", etiket: "taşma", secenekler: [["sat", "saturation (doyurma)"], ["wrap", "wrap-around (sarma)"]], deger: "sat", metin: true });
  kapat();

  var pZaman = WK.panel(w, 190), pHata = WK.panel(w, 150), pSpek = WK.panel(w, 240);
  var N = 4096, KBIN = 203;                       // bin ortasında ton (pencere sızıntısı yok)

  function ciz() {
    var p = w.param, B = Math.round(p.B), lsb = Math.pow(2, -(B - 1));
    var A = Math.pow(10, p.seviye / 20);
    var x = new Float64Array(N), k;
    for (k = 0; k < N; k++) x[k] = A * Math.cos(2 * Math.PI * KBIN * k / N);
    var y = DSP.sabitNokta(x, B, p.mod, p.tasma);
    var e = new Float64Array(N), eSum = 0, eMax = 0;
    for (k = 0; k < N; k++) { e[k] = (y[k] - x[k]) / lsb; eSum += e[k]; eMax = Math.max(eMax, Math.abs(e[k])); }
    var dcLsb = eSum / N;
    // spektrum (reel → sağ yarı)
    var sp = DSP.spektrumDbfs(y, null, "blackman-harris", { reel: true });
    var half = sp.subarray(N / 2, N);
    var m = DSP.spektrumMetrik(half, { koruma: 6, dcAtla: false });
    var dcDbfs = DSP.db20(Math.abs(dcLsb * lsb));      // DC bileşeni, tam ölçeğe göre
    var teoriSnr = DSP.snrKuantizasyon(B) + p.seviye;    // sinyale göre SNR = tam ölçek SNR − headroom
    // ---- zaman
    WK.temizle(pZaman);
    var nT = 96;
    var gz = WK.grafik(pZaman, { W: 640, H: 190, xmin: 0, xmax: nT - 1, ymin: -1.6, ymax: 1.6, kenar: { sol: 44, sag: 14, ust: 22, alt: 30 } });
    gz.eksenler({ xAdet: 8, yAdet: 4, xAd: "örnek n", yAd: "genlik (tam ölçek = 1)", baslik: "Zaman: ideal (kesikli) ve kuantize (mavi) — kırmızı: ±tam ölçek", yFmt: function (v) { return v.toFixed(1); } });
    gz.yatay(1, "w-cizgi-kirmizi"); gz.yatay(-1, "w-cizgi-kirmizi");
    var xs = [], yx = [], yy = [];
    for (k = 0; k < nT; k++) { xs.push(k); yx.push(x[k]); yy.push(y[k]); }
    gz.cizgi(xs, yx, "w-cizgi-gri"); gz.cizgi(xs, yy, "w-cizgi-sinyal");
    // ---- hata
    WK.temizle(pHata);
    var eLim = Math.max(1, Math.ceil(eMax * 1.1));
    var gh = WK.grafik(pHata, { W: 640, H: 150, xmin: 0, xmax: nT - 1, ymin: -eLim, ymax: eLim, kenar: { sol: 44, sag: 14, ust: 22, alt: 30 } });
    gh.eksenler({ xAdet: 8, yAdet: 4, xAd: "örnek n", yAd: "hata (LSB)", baslik: "Hata sinyali y − x (LSB cinsinden)", yFmt: function (v) { return v.toFixed(eLim > 4 ? 0 : 1); } });
    var ye = []; for (k = 0; k < nT; k++) ye.push(e[k]);
    gh.yatay(0, "w-cizgi-gri"); gh.yatay(dcLsb, "w-cizgi-altin", "ortalama " + dcLsb.toFixed(2) + " LSB");
    gh.cizgi(xs, ye, "w-cizgi-kirmizi");
    // ---- spektrum
    WK.temizle(pSpek);
    var gs = WK.grafik(pSpek, { W: 640, H: 240, xmin: 0, xmax: fs / 2e6, ymin: -160, ymax: 10, kenar: { sol: 48, sag: 14, ust: 22, alt: 34 } });
    gs.eksenler({ xAdet: 6, yAdet: 6, xAd: "frekans (MHz)", yAd: "dBFS", baslik: "Spektrum (N = 4096, Blackman-Harris, fs = " + (fs / 1e6) + " MSPS)" });
    var fx = [], fy = [];
    for (k = 0; k < N / 2; k++) { fx.push(k * fs / N / 1e6); fy.push(half[k]); }
    gs.alan(fx, fy, -160, "w-dolgu-sinyal"); gs.cizgi(fx, fy, "w-cizgi-sinyal");
    gs.yatay(-70, "w-cizgi-kirmizi", "tespit eşiği (örnek) −70 dBFS");
    var nq = -(6.02 * B + 1.76) - 10 * Math.log10(N / 2 / 2);   // bin başına taban kestirimi (ENBW≈2 bin)
    gs.yatay(nq, "w-cizgi-gri", "kuram tabanı/bin " + nq.toFixed(0) + " dBFS");
    if (m.spurBin > 0) {
      gs.nokta(fx[m.spurBin], m.spurDbfs, 4, "w-nokta");
      var sagda = gs.px(fx[m.spurBin]) > (gs.x0 + gs.x1) / 2;          // sağ yarıda ise etiketi sola yaz (eşik etiketiyle çakışmasın)
      gs.metin(gs.px(fx[m.spurBin]) + (sagda ? -6 : 6), gs.py(m.spurDbfs) - 8, "en büyük istenmeyen " + m.spurDbfs.toFixed(1) + " dBFS", "w-not", sagda ? "end" : "start");
    }
    // ---- sonuçlar
    var tasmaSay = y.tasma || 0;
    var snrMetin = (m.snr < teoriSnr - 6 ? "!" : "+") + m.snr.toFixed(1) + " dB";
    WK.sonucYaz(w, {
      "LSB": lsb.toExponential(2) + " (Q1." + (B - 1) + ")",
      "ölçülen SNR (sinyale göre)": snrMetin,
      "kuram 6.02·B+1.76 − headroom": teoriSnr.toFixed(1) + " dB",
      "DC bias": (Math.abs(dcLsb) > 0.1 ? "!" : "+") + dcLsb.toFixed(3) + " LSB → " + (dcDbfs > -150 ? dcDbfs.toFixed(0) : "< −150") + " dBFS @0 Hz",
      "tepe hata": eMax.toFixed(2) + " LSB",
      "taşan örnek": (tasmaSay > 0 ? "!" : "+") + tasmaSay + " / " + N + (tasmaSay > 0 ? (p.tasma === "wrap" ? " (WRAP!)" : " (doyuruldu)") : ""),
      "SFDR": m.sfdr.toFixed(1) + " dBc"
    });
  }
  return {
    ciz: ciz,
    presetler: [
      { ad: "Referans senaryo", param: { seviye: -6, B: 16, mod: "round", tasma: "sat" } },
      { ad: "Truncation DC'si", param: { seviye: -6, B: 16, mod: "trunc", tasma: "sat" } },
      { ad: "8 bit", param: { seviye: -6, B: 8, mod: "round", tasma: "sat" } },
      { ad: "Saturation (+2 dBFS)", param: { seviye: 2, B: 16, mod: "round", tasma: "sat" } },
      { ad: "Wrap felaketi", param: { seviye: 2, B: 16, mod: "round", tasma: "wrap" } }
    ]
  };
});
