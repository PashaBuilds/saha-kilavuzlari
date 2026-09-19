/* W-18 — CFAR laboratuvarı
   Kontroller: CFAR tipi (CA/GO/SO/OS), N, guard, hedef Pfa, gürültü profili (düz/basamak/rampa),
               darbe yoğunluğu, darbe SNR'ı
   Çıktı: güç dizisi + adaptif eşik (üst panel) ve aynı dizi + sabit eşik (alt panel);
          tespit / kaçırma / yanlış alarm sayaçları, α, CFAR kaybı, Monte Carlo Pfa
   Hesap: DSP.cfar, DSP.caCfarAlfa, DSP.osCfarAlfa, DSP.gaussKompleks */
WK.kaydet("w18", function (w) {
  var S = w.S, T = S.tespit || {};
  // Yerel yardımcı (dsp-core'da yok): N üstel örneğin k'ıncı sıra istatistiğinin beklenen değeri / ortalama
  // E[x_(k)] = Σ_{i=0}^{k−1} 1/(N−i)  → OS-CFAR'ın efektif eşik çarpanı α·E[x_(k)] için.
  function osOrtalamaKat(N, k) { var s = 0; for (var i = 0; i < k; i++) s += 1 / (N - i); return s; }
  var nRef = T.n_ref || 16, gRef = T.guard === undefined ? 2 : T.guard, snrRef = T.tespit_snr_db || 15;

  WK.secim(w, { ad: "tip", etiket: "CFAR tipi", secenekler: [["CA", "CA — ortalama"], ["GO", "GO — büyük yarı"], ["SO", "SO — küçük yarı"], ["OS", "OS — sıra istatistiği (k = 3N/4)"]], deger: "CA", metin: true });
  var kapat = WK.grup(w, "Pencere");
  WK.secim(w, { ad: "N", etiket: "referans hücre N", secenekler: [[8, "8"], [16, "16 (referans)"], [32, "32"], [64, "64"]], deger: 16 });
  WK.kaydirici(w, { ad: "G", etiket: "guard (taraf başına)", min: 0, max: 6, adim: 1, deger: gRef, birim: "hücre", tamsayi: true });
  WK.secim(w, { ad: "pfa", etiket: "hedef Pfa (hücre başına)", secenekler: [["1e-3", "10⁻³"], ["1e-4", "10⁻⁴"], ["1e-6", "10⁻⁶ (referans)"], ["1e-9", "10⁻⁹"]], deger: "1e-6", metin: true });
  kapat();
  kapat = WK.grup(w, "Sahne");
  WK.secim(w, { ad: "profil", etiket: "gürültü tabanı profili", secenekler: [["duz", "düz"], ["basamak", "basamak (+6 dB, ortada)"], ["rampa", "rampa (0 → +8 dB)"]], deger: "duz", metin: true });
  WK.secim(w, { ad: "yogunluk", etiket: "darbe yoğunluğu", secenekler: [["seyrek", "seyrek (6 yalnız darbe)"], ["orta", "orta (12 darbe, rastgele)"], ["yogun", "yoğun (8 yakın çift, 5 hücre ara)"]], deger: "seyrek", metin: true });
  WK.kaydirici(w, { ad: "snr", etiket: "darbe SNR'ı (yerel tabana göre)", min: 5, max: 30, adim: 0.5, deger: snrRef, birim: "dB" });
  kapat();

  var pCfar = WK.panel(w, 250), pSabit = WK.panel(w, 250);
  var NC = 1800, PW = 3, MC_N = 20000;   // darbe 3 hücre: G = 2 ile tam örtülür (G < 1 → kendini maskeler)

  function tabanProfili(profil, n) {
    var m = new Float64Array(n);
    for (var k = 0; k < n; k++) {
      if (profil === "basamak") m[k] = k < n / 2 ? 1 : DSP.lin10(6);
      else if (profil === "rampa") m[k] = DSP.lin10(8 * k / n);
      else m[k] = 1;
    }
    return m;
  }
  function darbeler(yogunluk, n, rnd) {
    var d = [], k;
    if (yogunluk === "seyrek") for (k = 0; k < 6; k++) d.push(Math.round(n * (k + 0.5) / 6) + Math.round((rnd() - 0.5) * 40));
    else if (yogunluk === "orta") for (k = 0; k < 12; k++) d.push(60 + Math.floor(rnd() * (n - 120)));
    else for (k = 0; k < 8; k++) { var b = Math.round(n * (k + 0.5) / 8); d.push(b); d.push(b + PW + 5); }
    return d;
  }
  // güç dizisi: kompleks Gauss gürültü (hücre başına ortalama güç m[k]) + darbeler (yerel SNR)
  function sahne(m, dList, snrDb, rnd) {
    var n = m.length, guc = new Float64Array(n), darbeMi = new Uint8Array(n), k, j;
    var A = new Float64Array(n);
    for (j = 0; j < dList.length; j++) for (k = 0; k < PW; k++) { var c = dList[j] + k; if (c >= 0 && c < n) { A[c] = Math.sqrt(DSP.lin10(snrDb) * m[dList[j]]); darbeMi[c] = 1; } }
    for (k = 0; k < n; k++) {
      var g = DSP.gaussKompleks(rnd, Math.sqrt(m[k]));
      var i = g[0] + A[k] * Math.cos(0.7 * k), q = g[1] + A[k] * Math.sin(0.7 * k);
      guc[k] = i * i + q * q;
    }
    return { guc: guc, darbeMi: darbeMi };
  }
  function say(tespit, darbeMi) {
    var det = 0, kac = 0, fa = 0, top = 0;
    for (var k = 0; k < tespit.length; k++) {
      if (darbeMi[k]) { top++; if (tespit[k]) det++; else kac++; } else if (tespit[k]) fa++;
    }
    return { det: det, kac: kac, fa: fa, top: top };
  }
  function panelCiz(svg, baslik, guc, esik, tespit, darbeMi, m) {
    WK.temizle(svg);
    var g = WK.grafik(svg, { W: 640, H: 250, xmin: 0, xmax: NC, ymin: -12, ymax: 32, kenar: { sol: 48, sag: 14, ust: 22, alt: 34 } });
    g.eksenler({ xAd: "hücre (örnek ya da FFT bin'i)", yAd: "dB (başlangıç gürültüsü = 0)", baslik: baslik, xAdet: 6, yAdet: 5, yFmt: function (v) { return v.toFixed(0); } });
    var xs = [], ys = [], es = [], k;
    for (k = 0; k < NC; k++) { xs.push(k); ys.push(DSP.db10(guc[k])); es.push(DSP.db10(esik[k])); }
    g.alan(xs, ys, -12, "w-dolgu-gurultu");
    g.cizgi(xs, ys, "w-cizgi-gri");
    g.cizgi(xs, es, "w-cizgi-altin");
    for (k = 0; k < NC; k++) if (tespit[k]) { if (darbeMi[k]) g.nokta(k, ys[k], 2.6, "w-nokta"); else g.ekle("circle", { cx: g.px(k), cy: g.py(ys[k]), r: 2.6, style: "fill:var(--red)" }); }
    return g;
  }

  function ciz() {
    var p = w.param;
    var N = +p.N, G = p.G, pfa = +p.pfa, tip = p.tip, kOs = Math.round(0.75 * N);
    var alfa = tip === "OS" ? DSP.osCfarAlfa(N, kOs, pfa) : DSP.caCfarAlfa(N, pfa);
    var sabitKat = -Math.log(pfa);                        // sabit eşik: başlangıç gürültüsüne göre kurulmuş
    var kayipDb = 10 * Math.log10(alfa / sabitKat);
    if (tip === "OS") kayipDb = 10 * Math.log10(alfa * osOrtalamaKat(N, kOs) / sabitKat);
    var rnd = DSP.prng(18);
    var m = tabanProfili(p.profil, NC);
    var dl = darbeler(p.yogunluk, NC, rnd);
    var sc = sahne(m, dl, p.snr, rnd);
    var cf = DSP.cfar(sc.guc, tip, N, G, alfa, kOs);
    var esikSabit = new Float64Array(NC), tespitSabit = new Uint8Array(NC), k;
    for (k = 0; k < NC; k++) { esikSabit[k] = sabitKat * 1.0; tespitSabit[k] = sc.guc[k] > esikSabit[k] ? 1 : 0; }
    var sC = say(cf.tespit, sc.darbeMi), sS = say(tespitSabit, sc.darbeMi);
    panelCiz(pCfar, tip + "-CFAR (N = " + N + ", G = " + G + ", α = " + alfa.toFixed(1) + ") — eşik altın, tespit mavi, yanlış alarm kırmızı", sc.guc, cf.esik, cf.tespit, sc.darbeMi, m);
    panelCiz(pSabit, "Sabit eşik: başlangıç gürültüsünün " + sabitKat.toFixed(1) + " katı (" + (10 * Math.log10(sabitKat)).toFixed(1) + " dB) — aynı sahne", sc.guc, esikSabit, tespitSabit, sc.darbeMi, m);
    // Monte Carlo Pfa: yalnız gürültü, düz taban
    var rnd2 = DSP.prng(1818), mDuz = tabanProfili("duz", MC_N);
    var scN = sahne(mDuz, [], 0, rnd2);
    var cfN = DSP.cfar(scN.guc, tip, N, G, alfa, kOs);
    var faN = 0; for (k = N / 2 + G; k < MC_N - N / 2 - G; k++) faN += cfN.tespit[k];
    var bek = pfa * (MC_N - N - 2 * G);
    WK.sonucYaz(w, {
      "α": alfa.toFixed(2) + (tip === "OS" ? " (k = " + kOs + ")" : "") + "  · Q6.10 = 0x" + Math.round(alfa * 1024).toString(16).toUpperCase(),
      "CFAR kaybı (sabit eşiğe göre)": (kayipDb > 3 ? "!" : "") + kayipDb.toFixed(2) + " dB",
      "CFAR — tespit": (sC.det === sC.top ? "+" : "") + sC.det + " / " + sC.top + " darbe hücresi",
      "CFAR — kaçırma": (sC.kac > 0 ? "!" : "+") + sC.kac,
      "CFAR — yanlış alarm": (sC.fa > 0 ? "!" : "+") + sC.fa,
      "sabit eşik — tespit / kaçırma / y.alarm": sS.det + " / " + sS.kac + " / " + (sS.fa > 3 ? "!" : "") + sS.fa,
      "Monte Carlo Pfa (yalnız gürültü)": faN + " alarm / " + MC_N.toLocaleString("tr-TR") + " hücre → " + (faN / (MC_N - N - 2 * G)).toExponential(1) + " (hedef " + pfa.toExponential(0) + ", beklenen " + (bek < 10 ? bek.toFixed(2) : bek.toFixed(0)) + ")"
    });
  }
  return {
    ciz: ciz,
    presetler: [
      { ad: "Referans senaryo", param: { tip: "CA", N: nRef, G: gRef, pfa: "1e-6", profil: "duz", yogunluk: "seyrek", snr: snrRef } },
      { ad: "Basamak (+6 dB)", param: { tip: "CA", N: nRef, G: gRef, pfa: "1e-6", profil: "basamak", yogunluk: "seyrek", snr: snrRef } },
      { ad: "Rampa", param: { tip: "CA", N: nRef, G: gRef, pfa: "1e-6", profil: "rampa", yogunluk: "seyrek", snr: snrRef } },
      { ad: "Yoğun ortam — CA maskeler", param: { tip: "CA", N: nRef, G: gRef, pfa: "1e-6", profil: "duz", yogunluk: "yogun", snr: 20 } },
      { ad: "Yoğun ortam — OS çözer", param: { tip: "OS", N: nRef, G: gRef, pfa: "1e-6", profil: "basamak", yogunluk: "yogun", snr: 20 } },
      { ad: "SO basamakta", param: { tip: "SO", N: nRef, G: gRef, pfa: "1e-6", profil: "basamak", yogunluk: "yogun", snr: 20 } },
      { ad: "Pfa 10⁻³ — Monte Carlo", param: { tip: "CA", N: nRef, G: gRef, pfa: "1e-3", profil: "duz", yogunluk: "seyrek", snr: snrRef } },
      { ad: "N = 64 (kayıp 0.5 dB)", param: { tip: "CA", N: 64, G: gRef, pfa: "1e-6", profil: "duz", yogunluk: "seyrek", snr: snrRef } }
    ]
  };
});
