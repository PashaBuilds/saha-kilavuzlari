/* W-11 — NCO laboratuvarı
   Kontroller: fs, hedef frekans, akümülatör biti N, LUT adres biti P, genlik biti A, dither
   Çıktı: FTW (hex), gerçek frekans ve hata, çözünürlük; zaman çizimi (I/Q), spektrum + en büyük spur */
WK.kaydet("w11", function (w) {
  var S = w.S, fsRef = S.adc ? S.adc.fs_hz : 2400e6, fRef = S.ddc ? S.ddc.nco_hz : 600e6;
  WK.kaydirici(w, { ad: "fs", etiket: "fs (NCO saati)", min: 100e6, max: 4000e6, adim: 1e6, deger: fsRef, olcek: 1e6, birim: "MHz" });
  WK.kaydirici(w, { ad: "f", etiket: "hedef frekans", min: -2000e6, max: 2000e6, adim: 0.1e6, deger: fRef, olcek: 1e6, birim: "MHz" });
  var kapat = WK.grup(w, "Bit genişlikleri");
  WK.kaydirici(w, { ad: "N", etiket: "akümülatör N", min: 8, max: 48, adim: 1, deger: 32, birim: "bit", tamsayi: true });
  WK.kaydirici(w, { ad: "P", etiket: "LUT adres P", min: 4, max: 20, adim: 1, deger: 14, birim: "bit", tamsayi: true });
  WK.kaydirici(w, { ad: "A", etiket: "genlik A", min: 4, max: 20, adim: 1, deger: 16, birim: "bit", tamsayi: true });
  WK.onay(w, { ad: "dither", etiket: "faz dither", deger: true });
  kapat();

  var zaman = WK.panel(w, 200), spek = WK.panel(w, 250);
  var NFFT = 4096;

  function ciz() {
    var p = w.param;
    var N = Math.min(p.N, 48), P = Math.min(p.P, N), A = p.A;
    var ftw = DSP.ftw(p.f, p.fs, N);
    var fGercek = DSP.ncoGercekFrekans(ftw, p.fs, N);
    if (fGercek > p.fs / 2) fGercek -= p.fs;           // işaretli yorum
    var res = DSP.ncoCozunurluk(p.fs, N);
    var out = DSP.nco({ n: NFFT, N: N, P: P, A: A, ftw: ftw, dither: p.dither, rnd: DSP.prng(21) });
    // spektrum
    var sp = DSP.spektrumDbfs(out.i, out.q, "blackman-harris");
    var m = DSP.spektrumMetrik(sp, { koruma: 6 });
    var teoriSpur = DSP.fazKirpmaSpurDbc(P);
    // --- zaman çizimi: ilk 64 örnek
    WK.temizle(zaman);
    var gz = WK.grafik(zaman, { W: 640, H: 200, xmin: 0, xmax: 63, ymin: -1.15, ymax: 1.15, kenar: { sol: 44, sag: 14, ust: 22, alt: 30 } });
    gz.eksenler({ xAdet: 8, yAdet: 4, xAd: "örnek n", yAd: "genlik", baslik: "NCO çıkışı — I (mavi) ve Q (mor)", yFmt: function (v) { return v.toFixed(1); } });
    var xs = [], yi = [], yq = [];
    for (var k = 0; k < 64; k++) { xs.push(k); yi.push(out.i[k]); yq.push(out.q[k]); }
    gz.cizgi(xs, yi, "w-cizgi-sinyal"); gz.cizgi(xs, yq, "w-cizgi-q");
    for (k = 0; k < 64; k += 1) { gz.nokta(k, out.i[k], 2, "w-nokta"); }
    // --- spektrum
    WK.temizle(spek);
    var gs = WK.grafik(spek, { W: 640, H: 250, xmin: -p.fs / 2e6, xmax: p.fs / 2e6, ymin: -140, ymax: 5, kenar: { sol: 48, sag: 14, ust: 22, alt: 34 } });
    gs.eksenler({ xAdet: 6, yAdet: 6, xAd: "frekans (MHz)", yAd: "dBFS", baslik: "Spektrum (N=4096, Blackman-Harris)" });
    var fx = [], fy = [];
    for (k = 0; k < NFFT; k++) { fx.push((k - NFFT / 2) * p.fs / NFFT / 1e6); fy.push(sp[k]); }
    gs.alan(fx, fy, -140, "w-dolgu-sinyal"); gs.cizgi(fx, fy, "w-cizgi-sinyal");
    gs.yatay(teoriSpur, "w-cizgi-kirmizi", "−6.02·P = " + teoriSpur.toFixed(0) + " dBc (faz kırpma kestirimi)");
    if (m.spurBin >= 0) {
      gs.nokta(fx[m.spurBin], m.spurDbfs, 4, "w-nokta");
      // etiket: kestirim çizgisine yakınsa altına, değilse üstüne; sağ yarıda ise sola yazılır (çizgi etiketiyle çakışmasın)
      var sagda = gs.px(fx[m.spurBin]) > (gs.x0 + gs.x1) / 2, yakin = Math.abs(m.spurDbfs - teoriSpur) < 8;
      gs.metin(gs.px(fx[m.spurBin]) + (sagda ? -7 : 7), gs.py(m.spurDbfs) + (yakin ? 14 : -8), "en büyük spur " + m.spurDbfs.toFixed(1) + " dBc", "w-not", sagda ? "end" : "start");
    }
    // sonuçlar
    var hata = fGercek - p.f;
    var altBitSifir = N > P && (ftw % Math.pow(2, N - P)) === 0;
    var sfdrMetin = m.sfdr > 6.02 * A + 30 ? "+> " + (6.02 * A + 30).toFixed(0) + " dBc (faz hatası yok)" : (m.sfdr < 60 ? "!" : "+") + m.sfdr.toFixed(1) + " dBc";
    WK.sonucYaz(w, {
      "FTW": DSP.ftwHex(ftw, N) + " (" + ftw + ")",
      "gerçek f": WK.fmtHz(fGercek),
      "hata": (Math.abs(hata) < 1e-6 ? "+0 Hz (tam)" : (Math.abs(hata) > res ? "!" : "") + hata.toFixed(3) + " Hz"),
      "Δf = fs/2^N": res < 1 ? res.toExponential(2) + " Hz" : WK.fmtHz(res),
      "ölçülen SFDR": sfdrMetin,
      "kırpılan bitler": altBitSifir ? "+hepsi 0 → kırpma hatası yok" : "sıfırdan farklı → periyodik hata",
      "kestirim −6.02·P": teoriSpur.toFixed(1) + " dBc",
      "genlik SNR 6.02·A+1.76": DSP.snrKuantizasyon(A).toFixed(1) + " dB",
      "yön": p.f < 0 ? "ters (e^{+jθ})" : "düz (e^{−jθ})"
    });
  }
  return {
    ciz: ciz,
    presetler: [
      { ad: "Referans senaryo", param: { fs: fsRef, f: fRef, N: 32, P: 14, A: 16, dither: true } },
      { ad: "Kaba tablo (P=8)", param: { fs: fsRef, f: fRef + 1e6, N: 32, P: 8, A: 16, dither: false } },
      { ad: "Dar akümülatör (N=16)", param: { fs: fsRef, f: 601e6, N: 16, P: 12, A: 16, dither: true } },
      { ad: "Ters yön", param: { fs: fsRef, f: -fRef, N: 32, P: 14, A: 16, dither: true } },
      { ad: "Düşük genlik biti", param: { fs: fsRef, f: fRef + 1e6, N: 32, P: 14, A: 6, dither: true } }
    ]
  };
});
