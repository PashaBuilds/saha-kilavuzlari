/* W-14 — FFT laboratuvarı
   Kontroller: N, ton frekansı (bin merkezine oturt seçeneği), ikinci ton, bant içi gürültü seviyesi,
   pencere (dikdörtgen/Hann), sıfır doldurma, ortalama sayısı
   Çıktı: spektrum (dBFS), teorik/ölçülen FFT tabanı, gerçek SNR vs tepe−taban, bin genişliği, gözlem süresi
   Yerel yardımcı (çekirdekte yok): spektrumZP — sıfır doldurmalı + ortalamalı spektrum */
WK.kaydet("w14", function (w) {
  var S = w.S;
  var fsRef = (S.ddc && S.ddc.cikis_fs_msps ? S.ddc.cikis_fs_msps : 300) * 1e6;
  var nRef = S.fft && S.fft.n ? S.fft.n : 1024;
  var snrRef = S.turetilmis_beklenen && S.turetilmis_beklenen.snr_ideal_14bit_db ? S.turetilmis_beklenen.snr_ideal_14bit_db : 86.04;
  var gRef = S.ddc && S.ddc.islem_kazanci_db ? S.ddc.islem_kazanci_db : 6.02;   // 1200 → 300 MHz decimation kazancı
  var gurRef = -(snrRef + gRef);                                                // DDC çıkışında bant içi gürültü ≈ −92 dBFS

  WK.secim(w, { ad: "N", etiket: "FFT boyu N", secenekler: [[256, "256"], [512, "512"], [1024, "1024"], [2048, "2048"], [4096, "4096"]], deger: nRef });
  WK.secim(w, { ad: "pen", etiket: "pencere", secenekler: [["rect", "dikdörtgen"], ["hann", "Hann"]], deger: "hann", metin: true });
  var kapat = WK.grup(w, "Tonlar");
  WK.kaydirici(w, { ad: "f1", etiket: "ton 1 frekansı", min: -150e6, max: 150e6, adim: 0.01e6, deger: 10e6, olcek: 1e6, birim: "MHz", hane: 3 });
  WK.onay(w, { ad: "binOrta", etiket: "ton 1'i bin merkezine oturt (koherent)", deger: false });
  WK.onay(w, { ad: "ton2", etiket: "ikinci ton açık", deger: false });
  WK.kaydirici(w, { ad: "df2", etiket: "ton 2 uzaklığı", min: 0.1e6, max: 30e6, adim: 0.1e6, deger: 2e6, olcek: 1e6, birim: "MHz" });
  WK.kaydirici(w, { ad: "a2", etiket: "ton 2 seviyesi", min: -100, max: 0, adim: 1, deger: -40, birim: "dBFS" });
  kapat();
  kapat = WK.grup(w, "Gürültü ve işleme");
  WK.kaydirici(w, { ad: "gur", etiket: "bant içi gürültü (toplam)", min: -120, max: -20, adim: 1, deger: gurRef, birim: "dBFS" });
  WK.secim(w, { ad: "zp", etiket: "zero-padding (sıfır doldurma)", secenekler: [[1, "yok (1×)"], [2, "2×"], [4, "4×"], [8, "8×"]], deger: 1 });   // etiket: zero-padding
  WK.secim(w, { ad: "ort", etiket: "ortalama (Welch)", secenekler: [[1, "1 çerçeve"], [4, "4"], [16, "16"], [64, "64"]], deger: 1 });
  kapat();

  var spek = WK.panel(w, 290), yakin = WK.panel(w, 200);

  // Yerel yardımcı: N örneklik kompleks çerçeve → pencere → Z× sıfır doldurma → |X|/Σw (lineer güç).
  function spektrumZP(i, q, N, Z, pen) {
    var win = DSP.pencere(pen, N), s1 = 0, k;
    for (k = 0; k < N; k++) s1 += win[k];
    var M = N * Z, re = new Float64Array(M), im = new Float64Array(M);
    for (k = 0; k < N; k++) { re[k] = i[k] * win[k]; im[k] = q[k] * win[k]; }
    DSP.fft(re, im, false);
    var out = new Float64Array(M);
    for (k = 0; k < M; k++) { var idx = (k + M / 2) % M; out[idx] = (re[k] * re[k] + im[k] * im[k]) / (s1 * s1); }
    return out;
  }

  function ciz() {
    var p = w.param, N = +p.N, Z = +p.zp, K = +p.ort, fs = fsRef;
    var bin = fs / N, T = N / fs;
    var f1 = p.f1;
    if (p.binOrta) f1 = Math.round(f1 / bin) * bin;
    var f2 = f1 + p.df2, a2 = DSP.lin20(p.a2);
    var sigma = DSP.lin20(p.gur);                         // toplam gürültü rms (bant içi güç = sigma²)
    var rnd = DSP.prng(1234);
    var toplam = N * K;
    if (toplam > 65536) { K = Math.max(1, Math.floor(65536 / N)); toplam = N * K; }
    var i = new Float64Array(toplam), q = new Float64Array(toplam), k;
    for (k = 0; k < toplam; k++) {
      var ph = 2 * Math.PI * f1 * k / fs; i[k] = Math.cos(ph); q[k] = Math.sin(ph);
      if (p.ton2) { var ph2 = 2 * Math.PI * f2 * k / fs + 1; i[k] += a2 * Math.cos(ph2); q[k] += a2 * Math.sin(ph2); }
      var g = DSP.gaussKompleks(rnd, sigma); i[k] += g[0]; q[k] += g[1];
    }
    // Welch: K ardışık çerçevenin güç ortalaması
    var M = N * Z, acc = new Float64Array(M), seg;
    for (seg = 0; seg < K; seg++) {
      var sp = spektrumZP(i.subarray(seg * N, (seg + 1) * N), q.subarray(seg * N, (seg + 1) * N), N, Z, p.pen);
      for (k = 0; k < M; k++) acc[k] += sp[k];
    }
    var db = new Float64Array(M), fx = new Float64Array(M);
    for (k = 0; k < M; k++) { db[k] = DSP.db10(acc[k] / K); fx[k] = (k - M / 2) * fs / M / 1e6; }
    // metrikler
    var pm = DSP.pencereMetrik(DSP.pencere(p.pen, N));
    var enbwDb = DSP.db10(pm.enbw);
    var tabanTeori = p.gur - DSP.db10(N) + enbwDb;        // kompleks giriş: gürültü N bin'e yayılır, ENBW kadar toplanır
    var pk = 0; for (k = 1; k < M; k++) if (db[k] > db[pk]) pk = k;
    // ölçülen taban: tepe(ler)den uzak bin'ler (±48 bin koruma; pencere yan lobları ortalamayı yukarı çekmesin),
    // dB medyanı + 1.59 dB (üstel dağılımda ortalama güç / medyan farkı)
    var koruma = 48 * Z, k2 = p.ton2 ? Math.round((f2 / fs) * M) + M / 2 : -1e9, uzak = [];
    for (k = 0; k < M; k++) { if (Math.abs(k - pk) <= koruma || Math.abs(k - k2) <= koruma) continue; uzak.push(db[k]); }
    if (uzak.length < 16) { uzak = []; for (k = 0; k < M; k++) if (Math.abs(k - pk) > 8 * Z) uzak.push(db[k]); }
    uzak.sort(function (a, b) { return a - b; });
    var tabanOlc = uzak[uzak.length >> 1] + 1.59;
    // saçılım (tek çekim vs ortalama): aynı uzak bin'lerin dB standart sapması
    var s2 = 0, ort2 = 0;
    for (k = 0; k < uzak.length; k++) ort2 += uzak[k]; ort2 /= Math.max(1, uzak.length);
    for (k = 0; k < uzak.length; k++) { var d = uzak[k] - ort2; s2 += d * d; }
    var sapma = Math.sqrt(s2 / Math.max(1, uzak.length));
    var gercekSnr = -p.gur;                                 // 0 dBFS ton / bant içi gürültü
    var tepeTaban = db[pk] - tabanOlc;
    var kayma = f1 / bin - Math.round(f1 / bin);           // bin kesri
    // --- geniş spektrum
    WK.temizle(spek);
    var g1 = WK.grafik(spek, { W: 640, H: 290, xmin: -fs / 2e6, xmax: fs / 2e6, ymin: -160, ymax: 10, kenar: { sol: 50, sag: 14, ust: 22, alt: 34 } });
    g1.eksenler({ xAdet: 6, yAdet: 6, xAd: "frekans (MHz) — DDC çıkışı, kompleks", yAd: "dBFS", baslik: "Spektrum: N = " + N + (Z > 1 ? " (+" + Z + "× sıfır doldurma)" : "") + (K > 1 ? ", " + K + " ortalama" : "") + ", " + (p.pen === "hann" ? "Hann" : "dikdörtgen") });
    var xs = [], ys = [], adim = Math.max(1, Math.floor(M / 2048));
    for (k = 0; k < M; k += adim) { var mx = db[k]; for (var j = 1; j < adim && k + j < M; j++) if (db[k + j] > mx) mx = db[k + j]; xs.push(fx[k]); ys.push(mx); }
    g1.alan(xs, ys, -160, "w-dolgu-sinyal"); g1.cizgi(xs, ys, "w-cizgi-sinyal");
    g1.yatay(tabanTeori, "w-cizgi-kirmizi", "teorik taban " + tabanTeori.toFixed(1) + " dBFS/bin");
    g1.yatay(p.gur, "w-cizgi-altin", "bant içi toplam gürültü " + p.gur + " dBFS (= −SNR)");
    g1.nokta(fx[pk], db[pk], 4, "w-nokta");
    // --- yakınlaştırma: tepe ±12 bin
    WK.temizle(yakin);
    var b0 = f1 / 1e6 - 12 * bin / 1e6, b1 = f1 / 1e6 + 12 * bin / 1e6;
    var g2 = WK.grafik(yakin, { W: 640, H: 200, xmin: b0, xmax: b1, ymin: -80, ymax: 5, kenar: { sol: 50, sag: 14, ust: 22, alt: 34 } });
    g2.eksenler({ xAdet: 6, yAdet: 4, xAd: "frekans (MHz) — tepe ±12 bin", yAd: "dBFS", baslik: "Bin ızgarası: nokta = FFT bin'i, çizgi = sıfır doldurmalı örnekleme", xFmt: function (v) { return v.toFixed(2); } });
    var zx = [], zy = [];
    for (k = 0; k < M; k++) { if (fx[k] < b0 || fx[k] > b1) continue; zx.push(fx[k]); zy.push(db[k]); if (k % Z === 0) g2.nokta(fx[k], Math.max(-80, db[k]), 2.5, "w-nokta"); }
    g2.cizgi(zx, zy, "w-cizgi-sinyal");
    for (var bb = Math.ceil(b0 * 1e6 / bin); bb * bin / 1e6 <= b1; bb++) g2.dikey(bb * bin / 1e6, "w-izgara");
    g2.dikey(f1 / 1e6, "w-cizgi-altin", "ton " + (f1 / 1e6).toFixed(3) + " MHz");
    // sonuçlar
    var sonuc = {
      "bin genişliği fs/N": WK.fmtHz(bin),
      "gözlem süresi T = N/fs": WK.fmtS(T),
      "ton 1 bin konumu": (f1 / bin).toFixed(2) + " (kesir " + kayma.toFixed(2) + (Math.abs(kayma) < 0.01 ? ", koherent)" : ", sızıntı)"),
      "tepe": db[pk].toFixed(2) + " dBFS" + (Math.abs(kayma) > 0.01 && !p.ton2 ? " (scalloping kaybı " + (-db[pk]).toFixed(2) + " dB)" : ""),
      "gerçek SNR (bant içi)": gercekSnr.toFixed(1) + " dB",
      "işlem kazancı 10·log10(N)": DSP.db10(N).toFixed(1) + " dB (reel giriş için N/2 → " + DSP.fftIslemKazanci(N).toFixed(1) + ")",
      "ENBW": pm.enbw.toFixed(2) + " bin (+" + enbwDb.toFixed(2) + " dB)",
      "FFT tabanı teori": tabanTeori.toFixed(1) + " dBFS/bin",
      "FFT tabanı ölçülen": tabanOlc.toFixed(1) + " dBFS/bin",
      "tepe − taban": tepeTaban.toFixed(1) + " dB (≠ SNR!)",
      "taban saçılımı σ": (K > 1 ? "+" : "") + sapma.toFixed(1) + " dB" + (K > 1 ? " (ortalama varyansı düşürdü)" : " (tek çekim)")
    };
    if (p.ton2) {
      var gorunur = p.a2 > tabanTeori + 6;
      sonuc["ton 2"] = (gorunur ? "+" : "!") + (f2 / 1e6).toFixed(2) + " MHz, " + p.a2 + " dBFS — " + (p.df2 < 2 * bin * pm.enbw ? "ana lob içinde: ayrılmaz" : (gorunur ? "tabanın üstünde" : "taban altında"));
    }
    WK.sonucYaz(w, sonuc);
  }
  return {
    ciz: ciz,
    presetler: [
      { ad: "Referans senaryo", param: { N: nRef, pen: "hann", f1: 10e6, binOrta: false, ton2: false, df2: 2e6, a2: -40, gur: gurRef, zp: 1, ort: 1 } },
      { ad: "Koherent, dikdörtgen", param: { N: nRef, pen: "rect", f1: 10e6, binOrta: true, ton2: false, df2: 2e6, a2: -40, gur: gurRef, zp: 1, ort: 1 } },
      { ad: "Sızıntı (dikdörtgen)", param: { N: nRef, pen: "rect", f1: 10e6, binOrta: false, ton2: false, df2: 2e6, a2: -40, gur: gurRef, zp: 1, ort: 1 } },
      { ad: "N'i 4 katla", param: { N: 4096, pen: "hann", f1: 10e6, binOrta: false, ton2: false, df2: 2e6, a2: -40, gur: gurRef, zp: 1, ort: 1 } },
      { ad: "Yakın iki ton", param: { N: nRef, pen: "hann", f1: 10e6, binOrta: true, ton2: true, df2: 0.5e6, a2: -6, gur: gurRef, zp: 4, ort: 1 } },
      { ad: "64 ortalama", param: { N: nRef, pen: "hann", f1: 10e6, binOrta: false, ton2: false, df2: 2e6, a2: -40, gur: gurRef, zp: 1, ort: 64 } }
    ]
  };
});
