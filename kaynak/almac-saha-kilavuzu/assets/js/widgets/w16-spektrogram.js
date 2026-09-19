/* W-16 — Spektrogram / zaman–frekans takası
   Kontroller: FFT boyu N, overlap, pencere, darbe tipi (sabit / LFM), PW, chirp BW, örnek başına SNR, darbe başlangıcı
   Çıktı: <canvas> spektrogram (renkler CSS değişkenlerinden okunur; tema değişince site.js w._ciz çağırır),
          SVG zaman paneli (zarf + çerçeve ızgarası), sayılar: bin, çerçeve süresi, darbedeki çerçeve sayısı,
          pencere–darbe uyumsuzluğundan SNR kaybı 10·log10(N/L), en iyi çerçevede ölçülen tepe−taban */
WK.kaydet("w16", function (w) {
  var S = w.S;
  var fs = (S.ddc && S.ddc.cikis_fs_msps ? S.ddc.cikis_fs_msps : 300) * 1e6;
  var pwRef = S.sinyal && S.sinyal.pw_s ? S.sinyal.pw_s : 1e-6;
  var bwRef = S.sinyal && S.sinyal.varyant_b ? S.sinyal.varyant_b.chirp_bw_hz : 10e6;
  var nRef = S.fft && S.fft.n ? S.fft.n : 1024;
  var SURE = 4e-6, M = Math.round(SURE * fs);          // 4 µs = 1200 örnek
  var F0 = 10e6;                                        // baseband ton (emiter bant merkezinin 10 MHz üstünde)
  WK.secim(w, { ad: "N", etiket: "FFT boyu N", secenekler: [[32, "32"], [64, "64"], [128, "128"], [256, "256"], [512, "512"], [1024, "1024"]], deger: 128 });
  WK.secim(w, { ad: "ov", etiket: "overlap", secenekler: [[0, "%0"], [0.5, "%50"], [0.75, "%75"], [0.875, "%87.5"]], deger: 0.75 });
  WK.secim(w, { ad: "pen", etiket: "pencere", secenekler: [["rect", "dikdörtgen"], ["hann", "Hann"], ["blackman-harris", "Blackman-Harris"]], deger: "hann", metin: true });
  var kapat = WK.grup(w, "Darbe");
  WK.secim(w, { ad: "mop", etiket: "darbe tipi", secenekler: [["yok", "sabit frekans (CW)"], ["lfm", "LFM (chirp)"]], deger: "yok", metin: true });
  WK.kaydirici(w, { ad: "pw", etiket: "PW", min: 0.1e-6, max: 3e-6, adim: 0.05e-6, deger: pwRef, olcek: 1e-6, birim: "µs" });
  WK.kaydirici(w, { ad: "bw", etiket: "chirp BW", min: 1e6, max: 40e6, adim: 1e6, deger: bwRef, olcek: 1e6, birim: "MHz" });
  WK.kaydirici(w, { ad: "snr", etiket: "örnek başına SNR", min: -20, max: 30, adim: 1, deger: 10, birim: "dB" });
  WK.kaydirici(w, { ad: "t0", etiket: "darbe başlangıcı", min: 0, max: 2e-6, adim: 0.05e-6, deger: 1e-6, olcek: 1e-6, birim: "µs" });
  kapat();

  var zaman = WK.panel(w, 130);
  var cv = document.createElement("canvas");
  cv.width = 640; cv.height = 300; cv.setAttribute("role", "img"); cv.setAttribute("aria-label", "spektrogram");
  w.cizim.appendChild(cv);
  var ctx = cv.getContext("2d");

  function cssRenk(ad, yedek) { var v = getComputedStyle(document.documentElement).getPropertyValue(ad).trim(); return v || yedek; }

  function ciz() {
    var p = w.param, N = +p.N, ov = +p.ov, hop = Math.max(1, Math.round(N * (1 - ov)));
    var bin = fs / N, Tcer = N / fs, L = Math.round(p.pw * fs);
    var sigma = DSP.lin20(-p.snr);
    var sig = DSP.darbeKompleks({ n: M, fs: fs, pw: p.pw, pri: 0, f0: F0, mop: p.mop, chirpBw: p.bw, gecikme: p.t0 });
    DSP.gurultuEkle(sig, sigma, DSP.prng(31));
    var win = DSP.pencere(p.pen, N), s1 = 0, k;
    for (k = 0; k < N; k++) s1 += win[k];
    var pm = DSP.pencereMetrik(win);
    // STFT
    var baslar = [];
    for (var b = 0; b + N <= M; b += hop) baslar.push(b);
    var nf = baslar.length, fmin = -40e6, fmax = 40e6;
    var kmin = Math.ceil(fmin / fs * N), kmax = Math.floor(fmax / fs * N), nb = kmax - kmin + 1;
    var db = new Float64Array(nf * nb), enIyi = -1e9, enIyiCer = 0, re = new Float64Array(N), im = new Float64Array(N);
    var tabanTop = 0, tabanSay = 0;
    for (var j = 0; j < nf; j++) {
      for (k = 0; k < N; k++) { re[k] = sig.i[baslar[j] + k] * win[k]; im[k] = sig.q[baslar[j] + k] * win[k]; }
      DSP.fft(re, im, false);
      var mx = -1e9;
      for (k = kmin; k <= kmax; k++) { var kk = (k + N) % N, v = DSP.db10((re[kk] * re[kk] + im[kk] * im[kk]) / (s1 * s1)); db[j * nb + (k - kmin)] = v; if (v > mx) mx = v; }
      if (mx > enIyi) { enIyi = mx; enIyiCer = j; }
      // taban: darbeden tamamen önceki çerçeveler
      if (baslar[j] + N < p.t0 * fs) { for (k = 0; k < nb; k++) { tabanTop += DSP.lin10(db[j * nb + k]); tabanSay++; } }
    }
    var taban = tabanSay ? DSP.db10(tabanTop / tabanSay) : -p.snr - DSP.db10(N) + DSP.db10(pm.enbw);
    // --- canvas spektrogram
    var W = cv.width, H = cv.height, mL = 50, mR = 14, mT = 22, mB = 34;
    var panel = cssRenk("--dia-panel", "white"), accent = cssRenk("--accent", "royalblue"), ink = cssRenk("--ink-2", "gray"), line = cssRenk("--line-2", "silver"), gold = cssRenk("--gold", "goldenrod");
    ctx.clearRect(0, 0, W, H);
    ctx.fillStyle = panel; ctx.fillRect(0, 0, W, H);
    var pw_ = (W - mL - mR) / nf, ph_ = (H - mT - mB) / nb;
    var ust = 0, alt = -50;                                // dB → opaklık aralığı (tam ölçek CW = 0)
    ctx.fillStyle = accent;
    for (j = 0; j < nf; j++) for (k = 0; k < nb; k++) {
      var a = (db[j * nb + k] - alt) / (ust - alt);
      if (a <= 0.02) continue;
      ctx.globalAlpha = Math.min(1, a);
      ctx.fillRect(mL + j * pw_, H - mB - (k + 1) * ph_, pw_ + 0.5, ph_ + 0.5);
    }
    ctx.globalAlpha = 1;
    // en iyi çerçeve vurgusu
    ctx.strokeStyle = gold; ctx.lineWidth = 1.5; ctx.strokeRect(mL + enIyiCer * pw_, mT, pw_, H - mT - mB);
    // eksenler
    ctx.strokeStyle = line; ctx.lineWidth = 1; ctx.strokeRect(mL, mT, W - mL - mR, H - mT - mB);
    ctx.fillStyle = ink; ctx.font = "11px system-ui, sans-serif"; ctx.textAlign = "right"; ctx.textBaseline = "middle";
    for (var f = fmin; f <= fmax; f += 10e6) { var y = H - mB - ((f / fs * N) - kmin + 0.5) * ph_; ctx.fillText((f / 1e6).toFixed(0), mL - 6, y); ctx.beginPath(); ctx.moveTo(mL - 3, y); ctx.lineTo(mL, y); ctx.stroke(); }
    ctx.textAlign = "center"; ctx.textBaseline = "top";
    for (var t = 0; t <= SURE + 1e-12; t += 1e-6) { var x = mL + ((t * fs - N / 2) / hop + 0.5) * pw_; x = Math.max(mL, Math.min(W - mR, x)); ctx.fillText((t * 1e6).toFixed(0) + " µs", x, H - mB + 6); }
    ctx.textAlign = "left"; ctx.font = "bold 12px system-ui, sans-serif";
    ctx.fillText("Spektrogram — N = " + N + ", adım " + hop + " (" + (hop / fs * 1e9).toFixed(0) + " ns), " + (p.pen === "hann" ? "Hann" : p.pen) + " · −50…0 dB · altın = en güçlü çerçeve", mL, 5);
    ctx.save(); ctx.translate(12, (mT + H - mB) / 2); ctx.rotate(-Math.PI / 2); ctx.textAlign = "center"; ctx.font = "11px system-ui, sans-serif"; ctx.fillText("frekans (MHz)", 0, 0); ctx.restore();
    ctx.textAlign = "center"; ctx.font = "11px system-ui, sans-serif"; ctx.fillText("çerçeve merkezi zamanı", (mL + W - mR) / 2, H - 14);
    // --- zaman paneli (SVG): zarf + çerçeve ızgarası
    WK.temizle(zaman);
    var g = WK.grafik(zaman, { W: 640, H: 130, xmin: 0, xmax: SURE * 1e6, ymin: -0.1, ymax: 1.3, kenar: { sol: 50, sag: 14, ust: 22, alt: 30 } });
    g.eksenler({ xAdet: 8, yAdet: 2, xAd: "zaman (µs)", yAd: "zarf", baslik: "Darbe zarfı ve FFT çerçeveleri (her " + hop + ". örnekte yeni çerçeve, çerçeve = " + WK.fmtS(Tcer) + ")", yFmt: function (v) { return v.toFixed(0); } });
    var xs = [], ys = [];
    for (k = 0; k < M; k += 2) { xs.push(k / fs * 1e6); ys.push(sig.zarf[k]); }
    g.alan(xs, ys, 0, "w-dolgu-sinyal"); g.cizgi(xs, ys, "w-cizgi-sinyal");
    var gost = Math.max(1, Math.ceil(nf / 24));
    for (j = 0; j < nf; j += gost) { var t0 = baslar[j] / fs * 1e6, t1 = (baslar[j] + N) / fs * 1e6; g.ekle("rect", { x: g.px(t0), y: g.py(1.25) + (j / gost % 2) * 6, width: g.px(t1) - g.px(t0), height: 5, "class": j === enIyiCer ? "w-dolgu-altin" : "w-dolgu-gurultu" }); }
    // --- sayılar
    var doluluk = Math.min(1, L / N), kayip = L < N ? DSP.db10(N / L) : 0, cerDarbe = L > N ? Math.floor((L - N) / hop) + 1 : 0;
    // teori: darbe çerçevenin ortasında — pencere ağırlıklı koherent toplam² / gürültü Σw²
    var s2 = 0, sp = 0, a0 = L >= N ? 0 : Math.floor((N - L) / 2), a1 = L >= N ? N : a0 + L;
    for (k = 0; k < N; k++) { s2 += win[k] * win[k]; if (k >= a0 && k < a1) sp += win[k]; }
    var teoriTepeTaban = p.snr + DSP.db10(sp * sp / s2) - (p.mop === "lfm" ? DSP.db10(Math.max(1, p.bw / bin * Math.min(L, N) / L)) : 0);
    WK.sonucYaz(w, {
      "bin genişliği": WK.fmtHz(bin),
      "çerçeve süresi N/fs": WK.fmtS(Tcer) + " (" + N + " örnek)",
      "darbe örnek sayısı L": L + " (" + WK.fmtS(p.pw) + ")",
      "çerçeve / darbe": L >= N ? "+" + cerDarbe + " çerçeve tamamen darbe içinde" : "!darbe çerçeveden kısa: doluluk %" + (doluluk * 100).toFixed(0),
      "SNR kaybı 10·log10(N/L)": (kayip > 3 ? "!" : (kayip > 0 ? "" : "+")) + kayip.toFixed(1) + " dB (dikdörtgen çerçeve; pencere ortadaki darbeyi kayırır)",
      "en iyi çerçeve tepe − taban": (enIyi - taban).toFixed(1) + " dB (teori, darbe ortalanmış: " + teoriTepeTaban.toFixed(1) + ")",
      "LFM'de bin başına yayılma": p.mop === "lfm" ? (p.bw / bin * Math.min(L, N) / L).toFixed(1) + " bin (çerçeve içi süpürme / bin)" : "—",
      "frekans çözünürlüğü ↔ zaman çözünürlüğü": WK.fmtHz(bin) + " ↔ " + WK.fmtS(Tcer) + " (çarpım = 1)"
    });
  }
  return {
    ciz: ciz,
    presetler: [
      { ad: "Referans senaryo", param: { N: 128, ov: 0.75, pen: "hann", mop: "yok", pw: pwRef, bw: bwRef, snr: 10, t0: 1e-6 } },
      { ad: "LFM varyantı", param: { N: 128, ov: 0.75, pen: "hann", mop: "lfm", pw: pwRef, bw: bwRef, snr: 10, t0: 1e-6 } },
      { ad: "N = 1024: darbe kaybolur", param: { N: nRef, ov: 0.5, pen: "hann", mop: "yok", pw: pwRef, bw: bwRef, snr: 0, t0: 1e-6 } },
      { ad: "N = 32: frekans kaybolur", param: { N: 32, ov: 0.5, pen: "hann", mop: "lfm", pw: pwRef, bw: bwRef, snr: 10, t0: 1e-6 } },
      { ad: "Overlap'siz sınır", param: { N: 256, ov: 0, pen: "hann", mop: "yok", pw: 0.5e-6, bw: bwRef, snr: 5, t0: 0.75e-6 } },
      { ad: "Zayıf darbe (SNR −5 dB)", param: { N: 256, ov: 0.75, pen: "hann", mop: "yok", pw: pwRef, bw: bwRef, snr: -5, t0: 1e-6 } }
    ]
  };
});
