/* W-08 — Kuantizasyon laboratuvarı
   Kontroller: bit sayısı N, giriş seviyesi (dBFS), dither, ek termal gürültü, ton frekansı
   Çıktı: zaman dalga şekli (sürekli + kuantalanmış), hata sinyali, spektrum (dBFS);
   ölçülen SNR / SINAD / SFDR / ENOB ile teorik 6.02·N + 1.76 karşılaştırması, clipping/overrange sayacı
   Hesap: DSP.ton, DSP.kuantize, DSP.spektrumDbfs, DSP.spektrumMetrik, DSP.snrKuantizasyon, DSP.enob */
WK.kaydet("w08", function (w) {
  var S = w.S, fsRef = S.adc ? S.adc.fs_hz : 2400e6, bitRef = S.adc ? S.adc.bit : 14;
  var NFFT = 4096;
  WK.kaydirici(w, { ad: "bit", etiket: "çözünürlük N", min: 2, max: 16, adim: 1, deger: bitRef, birim: "bit", tamsayi: true });
  WK.kaydirici(w, { ad: "seviye", etiket: "giriş seviyesi", min: -60, max: 6, adim: 0.5, deger: -1, birim: "dBFS" });
  WK.kaydirici(w, { ad: "f", etiket: "ton frekansı", min: 10e6, max: 1190e6, adim: 1e6, deger: 601e6, olcek: 1e6, birim: "MHz" });
  var kapat = WK.grup(w, "Gürültü ve dither");
  WK.onay(w, { ad: "dither", etiket: "dither (±½ LSB tekdüze)", deger: false });
  WK.kaydirici(w, { ad: "termal", etiket: "ek analog gürültü", min: -140, max: -40, adim: 1, deger: -140, birim: "dBFS (tüm bant)" });
  kapat();

  var zaman = WK.panel(w, 190), hata = WK.panel(w, 120), spek = WK.panel(w, 250);

  function ciz() {
    var p = w.param, N = p.bit, fs = fsRef;
    // tam bin: ölçüm penceresiz de temiz olsun (bin sayısı tek → örüntü kırılır)
    var bin = Math.round(p.f / fs * NFFT); if (bin % 2 === 0) bin += 1;
    var f = bin * fs / NFFT;
    var A = DSP.lin20(p.seviye);
    var x = DSP.ton(NFFT, fs, f, A, 0.3);
    // dBFS: tam ölçek sinüs gücü 0.5 → gürültü gücü 0.5·10^(dBFS/10) → σ = lin20/√2
    if (p.termal > -139) DSP.gurultuEkleReel(x, DSP.lin20(p.termal) / Math.SQRT2, DSP.prng(17));
    var y = DSP.kuantize(x, N, { dither: p.dither, rnd: DSP.prng(3) });
    var e = new Float64Array(NFFT);
    for (var k = 0; k < NFFT; k++) e[k] = y[k] - x[k];
    var lsb = Math.pow(2, 1 - N);
    // spektrum: reel giriş, tek taraflı
    var sp = DSP.spektrumDbfs(y, null, "blackman-harris", { reel: true, shift: false });
    var yarim = sp.subarray(0, NFFT / 2);
    var m = DSP.spektrumMetrik(yarim, { koruma: 8, dcAtla: false });
    // DC bölgesini (pencere sızıntısı) gürültüden say: ilk 6 bin'i atlamak için metrik yeniden — basit düzeltme
    var teori = DSP.snrKuantizasyon(N) + Math.min(0, p.seviye);
    var kirpildi = y.tasma;
    // ---- zaman
    WK.temizle(zaman);
    var L = 48;
    var gz = WK.grafik(zaman, { W: 640, H: 190, xmin: 0, xmax: L - 1, ymin: -1.15, ymax: 1.15, kenar: { sol: 44, sag: 14, ust: 22, alt: 28 } });
    gz.eksenler({ xAdet: 8, yAdet: 4, xAd: "örnek n", yAd: "genlik (FS = 1)", baslik: "Giriş (altın) ve " + N + "-bit kuantalanmış çıkış (mavi merdiven)", yFmt: function (v) { return v.toFixed(1); } });
    gz.yatay(1, "w-cizgi-kirmizi", "+FS"); gz.yatay(-1, "w-cizgi-kirmizi", "−FS");
    var xs = [], yx = [];
    for (k = 0; k < L; k++) { xs.push(k); yx.push(x[k]); }
    // merdiven
    var xm = [], ym = [];
    for (k = 0; k < L; k++) { xm.push(k - 0.5, k + 0.5); ym.push(y[k], y[k]); }
    gz.cizgi(xs, yx, "w-cizgi-altin");
    gz.cizgi(xm, ym, "w-cizgi-sinyal");
    if (N <= 6) for (k = 0; k < Math.pow(2, N); k++) { var lv = -1 + k * lsb; gz.ekle("line", { x1: gz.x0, y1: gz.py(lv), x2: gz.x1, y2: gz.py(lv), "class": "w-izgara" }); }
    // ---- hata
    WK.temizle(hata);
    var eMax = Math.max(lsb, 1e-6);
    var gh = WK.grafik(hata, { W: 640, H: 120, xmin: 0, xmax: L - 1, ymin: -eMax, ymax: eMax, kenar: { sol: 44, sag: 14, ust: 20, alt: 24 } });
    gh.eksenler({ xAdet: 8, yTik: [-lsb / 2, 0, lsb / 2], xAd: "", baslik: "hata e[n] = y − x (±½ LSB çizgileri kırmızı; taşmada dışına çıkar)", yFmt: function (v) { return v === 0 ? "0" : (v > 0 ? "+½ LSB" : "−½ LSB"); } });
    gh.yatay(lsb / 2, "w-cizgi-kirmizi"); gh.yatay(-lsb / 2, "w-cizgi-kirmizi");
    var ye = [];
    for (k = 0; k < L; k++) ye.push(Math.max(-eMax, Math.min(eMax, e[k])));
    gh.cizgi(xs, ye, "w-cizgi-kirmizi");
    for (k = 0; k < L; k++) gh.nokta(k, ye[k], 2, "w-nokta");
    // ---- spektrum
    WK.temizle(spek);
    var gs = WK.grafik(spek, { W: 640, H: 250, xmin: 0, xmax: fs / 2e6, ymin: -160, ymax: 5, kenar: { sol: 48, sag: 14, ust: 22, alt: 34 } });
    gs.eksenler({ xAdet: 6, yAdet: 6, xAd: "frekans (MHz)", yAd: "dBFS", baslik: "Spektrum (N = 4096, Blackman-Harris, reel giriş → 0…fs/2)" });
    var fx = [], fy = [];
    for (k = 0; k < NFFT / 2; k++) { fx.push(k * fs / NFFT / 1e6); fy.push(Math.max(-160, yarim[k])); }
    gs.alan(fx, fy, -160, "w-dolgu-sinyal"); gs.cizgi(fx, fy, "w-cizgi-sinyal");
    // teorik gürültü tabanı (bin başına): −SNR_q − 10log(N/2) + ENBW(BH ≈ 2 bin → +3 dB)
    var tabanTeori = -DSP.snrKuantizasyon(N) - DSP.fftIslemKazanci(NFFT) + 3.0 + (p.dither ? 3.0 : 0);
    gs.yatay(tabanTeori, "w-cizgi-altin", "teorik kuantizasyon tabanı (bin başına) " + tabanTeori.toFixed(0) + " dBFS", "sol");
    if (m.spurBin >= 0) {
      var sx = gs.px(fx[m.spurBin]), sagda = sx > gs.x0 + 0.6 * (gs.x1 - gs.x0);   // sağ yarıda etiket sola (kırpılmasın)
      gs.nokta(fx[m.spurBin], m.spurDbfs, 4, "w-nokta");
      gs.etiket(sx + (sagda ? -6 : 6), gs.py(m.spurDbfs) - 8, "en büyük spur " + m.spurDbfs.toFixed(1) + " dBFS", sagda ? "end" : "start");
    }
    // ---- sonuç
    var snrOlc = m.snr, sinad = m.sinad, enob = m.enob;
    var fark = snrOlc - teori;
    WK.sonucYaz(w, {
      "LSB": lsb.toExponential(2) + " · FS (" + (lsb * 1e6 / 2).toFixed(1) + " µV @ 1 Vpp)",
      "teori 6.02N+1.76 (+seviye)": teori.toFixed(1) + " dB",
      "ölçülen SNR": (Math.abs(fark) > 3 && !kirpildi ? "!" : "") + snrOlc.toFixed(1) + " dB",
      "SINAD / ENOB": sinad.toFixed(1) + " dB / " + enob.toFixed(2) + " bit",
      "SFDR": (m.sfdr < 6.02 * N ? "!" : "+") + m.sfdr.toFixed(1) + " dBc",
      "clipping": kirpildi ? "!" + kirpildi + " örnek doydu → overrange bayrağı; harmonikler patlar" : "+yok",
      "dither etkisi": p.dither ? "taban ≈ +3 dB, spur'lar dağılır" : "kapalı",
      "hata RMS / LSB": (DSP.rms(e) / lsb).toFixed(3) + " (ideal 1/√12 = 0.289)"
    });
  }
  return {
    ciz: ciz,
    presetler: [
      { ad: "Referans senaryo", param: { bit: bitRef, seviye: -1, f: 601e6, dither: false, termal: -140 } },
      { ad: "Kaba kuantizör (4 bit)", param: { bit: 4, seviye: -3, f: 601e6, dither: false, termal: -140 } },
      { ad: "4 bit + dither", param: { bit: 4, seviye: -3, f: 601e6, dither: true, termal: -140 } },
      { ad: "Zayıf sinyal (−40 dBFS)", param: { bit: bitRef, seviye: -40, f: 601e6, dither: false, termal: -140 } },
      { ad: "Aşırı sürme (+3 dBFS)", param: { bit: bitRef, seviye: 3, f: 601e6, dither: false, termal: -140 } },
      { ad: "Analog gürültü baskın", param: { bit: bitRef, seviye: -1, f: 601e6, dither: false, termal: -60 } }
    ]
  };
});
