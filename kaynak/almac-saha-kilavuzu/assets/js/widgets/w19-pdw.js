/* W-19 — PDW üreteci (Bölüm 25–26)
   Kontroller: SNR, PW, PRI (gösterim için ölçekli), MOP, eşik (gürültü üstü dB), histerezis,
   min PW, video filtre uzunluğu, gürültü tohumu
   Çıktı: güç zarfı + eşikler + FSM durum bandı; darbe içi anlık frekans; canlı PDW tablosu
   (TOA, PW, PA, f, MOP, bayraklar) ve her ölçümün gerçek değere göre hatası.
   Hesap: DSP.darbeKompleks, gurultuEkle, guc, kayanOrtalama, darbeFsm, darbeFrekansi,
   chirpEgimi, toaHatasi, crlbFrekans. Yerel yardımcılar: kenarları dışlayan ortalama güç,
   pencere içi faz atlaması sayacı (çekirdeğe taşınabilir). */
WK.kaydet("w19", function (w) {
  var S = w.S;
  var fs = (S.ddc && S.ddc.cikis_fs_msps ? S.ddc.cikis_fs_msps : 300) * 1e6;
  var pwRef = S.sinyal && S.sinyal.pw_s ? S.sinyal.pw_s : 1e-6;
  var riseRef = S.sinyal && S.sinyal.rise_time_ns ? S.sinyal.rise_time_ns * 1e-9 : 50e-9;
  var bwRef = S.sinyal && S.sinyal.varyant_b ? S.sinyal.varyant_b.chirp_bw_hz : 10e6;
  var T = S.tespit || {};
  var snrRef = T.tespit_snr_db || 15, hystRef = T.histerezis_db || 3, minPwRef = T.min_pw_ornek || 4, maRef = T.video_filtre_uzunluk || 4;
  var pfaRef = T.pfa || 1e-6;
  // Rayleigh eşiği güç biriminde, ortalama gürültü gücüne göre: T/P_n = −ln Pfa → dB
  var esikRefDb = 10 * Math.log10(-Math.log(pfaRef));      // 1e-6 → 11.4 dB
  var F0 = 5e6;                                             // baseband ofseti (sabit): f_bb = +5 MHz
  var N = 6144;                                             // 20.5 µs pencere
  var PRI_GOSTERIM = 6e-6;                                  // 1 ms PRI ekrana sığmaz; gösterim için ölçekli

  WK.kaydirici(w, { ad: "snr", etiket: "SNR (örnek başına)", min: 0, max: 40, adim: 0.5, deger: snrRef, birim: "dB" });
  WK.kaydirici(w, { ad: "pw", etiket: "PW (%50 noktaları)", min: 0.05e-6, max: 4e-6, adim: 0.05e-6, deger: pwRef, olcek: 1e-6, birim: "µs", hane: 2 });
  WK.kaydirici(w, { ad: "pri", etiket: "PRI (gösterim ölçeği)", min: 1e-6, max: 10e-6, adim: 0.5e-6, deger: PRI_GOSTERIM, olcek: 1e-6, birim: "µs", hane: 1 });
  WK.secim(w, { ad: "mop", etiket: "MOP", secenekler: [["yok", "yok (sabit taşıyıcı)"], ["lfm", "LFM 10 MHz"], ["barker13", "Barker-13 faz kodu"]], deger: "yok", metin: true });
  var kapat = WK.grup(w, "Tespit / FSM");
  WK.kaydirici(w, { ad: "esik", etiket: "eşik (gürültü ortalaması üstü)", min: 3, max: 25, adim: 0.2, deger: esikRefDb, birim: "dB", hane: 1 });
  WK.kaydirici(w, { ad: "hyst", etiket: "histerezis", min: 0, max: 10, adim: 0.5, deger: hystRef, birim: "dB", hane: 1 });
  WK.kaydirici(w, { ad: "minpw", etiket: "min PW", min: 1, max: 40, adim: 1, deger: minPwRef, birim: "örnek", tamsayi: true });
  WK.kaydirici(w, { ad: "ma", etiket: "video filtre (kayan ort.)", min: 1, max: 32, adim: 1, deger: maRef, birim: "örnek", tamsayi: true });
  WK.kaydirici(w, { ad: "tohum", etiket: "gürültü tohumu", min: 1, max: 99, adim: 1, deger: 7, birim: "", tamsayi: true });
  kapat();

  var pZarf = WK.panel(w, 250), pFrek = WK.panel(w, 190);
  var tabloKap = WK.el("div", { "class": "w-tablo-kap" });
  w.cizim.appendChild(tabloKap);

  // --- yerel yardımcılar (küçük) -------------------------------------------------
  function ortaOrtalama(x, bas, son) {            // kenarların %10'u dışlanmış ortalama
    var kes = Math.max(1, Math.floor((son - bas) * 0.1)), s = 0, n = 0;
    for (var k = bas + kes; k < son - kes; k++) { s += x[k]; n++; }
    return n ? s / n : 0;
  }
  function fazAtlamaSay(i, q, bas, son, esikHz) {  // anlık frekansta |f| > esik olan örnekler (faz atlaması adayı)
    var af = DSP.anlikFrekans(i.subarray(bas, son), q.subarray(bas, son), fs), n = 0;
    var kes = Math.max(1, Math.floor((son - bas) * 0.1));
    for (var k = kes; k < af.length - kes; k++) if (Math.abs(af[k] - F0) > esikHz) n++;
    return n;
  }
  function f3(v, h) { return isFinite(v) ? v.toFixed(h === undefined ? 1 : h) : "—"; }
  function td(t, kls) { return WK.el("td", { text: t, "class": kls || "" }); }

  function ciz() {
    var p = w.param;
    var pw = p.pw, pri = p.pri, rise = Math.min(riseRef, pw / 2);
    var t0 = 1.0e-6;
    var sig = DSP.darbeKompleks({ n: N, fs: fs, pw: pw + rise, pri: pri, f0: F0, genlik: 1, mop: p.mop, chirpBw: bwRef, rise: rise, gecikme: t0 });
    var sigma = Math.pow(10, -p.snr / 20);       // gürültü rms (toplam), sinyal tepe genliği 1
    DSP.gurultuEkle(sig, sigma, DSP.prng(1000 + p.tohum));
    var guc = DSP.guc(sig.i, sig.q);
    var gucF = p.ma > 1 ? DSP.kayanOrtalama(guc, p.ma) : guc;
    var Pn = sigma * sigma;                        // ortalama gürültü gücü
    var esik = Pn * Math.pow(10, p.esik / 10);
    var maxPw = Math.round(3.0e-6 * fs);           // DET_MAX_PW: 3 µs → uzun darbe parçalanır
    var ham = DSP.darbeFsm(gucF, esik, { fs: fs, histerezisDb: p.hyst, minPw: 1, maxPw: maxPw });
    // gerçek darbeler (%50 noktaları)
    var gercek = [];
    for (var t = t0; t < N / fs; t += pri) gercek.push({ toa: t + rise / 2, pw: pw });
    // eşleştir + ölç
    var pdwler = [], atilan = [];
    var oncekiSeg = null;
    ham.forEach(function (d, idx) {
      if (d.ornek < p.minpw) { atilan.push(d); return; }
      var devam = !!(oncekiSeg && d.bas - oncekiSeg.son <= 2);   // SEG parçasının devamı
      oncekiSeg = d.kirpildi ? d : null;
      var bas = d.bas, son = d.son;
      var f = DSP.darbeFrekansi(sig.i, sig.q, bas, son, fs);
      var egim = DSP.chirpEgimi(sig.i, sig.q, bas, son, fs);
      var paOrt = DSP.db10(ortaOrtalama(guc, bas, son));
      var atlama = fazAtlamaSay(sig.i, sig.q, bas, son, 30e6);
      var mopTahmin = Math.abs(egim) > 2e12 ? "LFM" : (atlama >= 2 ? "faz kodu" : "yok");
      // en yakın gerçek darbe
      var enIyi = null, enKucuk = Infinity;
      gercek.forEach(function (g) { var e = Math.abs(g.toa - d.toa_s); if (e < enKucuk) { enKucuk = e; enIyi = g; } });
      var sahte = !devam && (!enIyi || enKucuk > pw + 0.5e-6);
      var bayrak = [];
      if (d.kirpildi) bayrak.push("SEG");
      if (devam) bayrak.push("SEG→");
      if (sahte) bayrak.push("SAHTE");
      if (atlama >= 2) bayrak.push("FAZ↕");
      if (mopTahmin === "LFM") bayrak.push("LFM");
      pdwler.push({ kirpildi: d.kirpildi, toa: d.toa_s, pw: d.pw_s, paTepe: d.pa_dbfs, paOrt: paOrt, f: f, egim: egim, mop: mopTahmin, bayrak: bayrak, sahte: sahte, devam: devam, g: enIyi, bas: bas, son: son });
    });
    // --- zarf paneli
    WK.temizle(pZarf);
    var tmaxUs = N / fs * 1e6;
    var gz = WK.grafik(pZarf, { W: 640, H: 250, xmin: 0, xmax: tmaxUs, ymin: -45, ymax: 8, kenar: { sol: 48, sag: 14, ust: 22, alt: 34 } });
    gz.eksenler({ xAdet: 8, yAdet: 5, xAd: "zaman (µs)", yAd: "güç (dB, tepe = 0)", baslik: "Güç zarfı, eşikler ve FSM durum bandı (yeşil: PDW, kırmızı: min PW altı → atıldı)" });
    var xs = [], ys = [], adim = Math.max(1, Math.floor(N / 2000));
    for (var k = 0; k < N; k += adim) { xs.push(k / fs * 1e6); ys.push(DSP.db10(gucF[k])); }
    gz.alan(xs, ys, -45, "w-dolgu-gurultu");
    gz.cizgi(xs, ys, "w-cizgi-sinyal");
    var esikDb = DSP.db10(esik);
    gz.yatay(esikDb, "w-cizgi-altin", "T_on = gürültü + " + f3(p.esik) + " dB");
    if (p.hyst > 0) gz.yatay(esikDb - p.hyst, "w-cizgi-kirmizi", "T_off (−" + f3(p.hyst) + " dB)");
    pdwler.forEach(function (d) { gz.bant(d.bas / fs * 1e6, d.son / fs * 1e6, d.sahte ? "w-dolgu-kirmizi" : "w-dolgu-yesil"); });
    atilan.forEach(function (d) { gz.bant(d.bas / fs * 1e6, (d.son + 1) / fs * 1e6, "w-dolgu-kirmizi"); });
    gercek.forEach(function (g) { gz.dikey(g.toa * 1e6, "w-cizgi-gri", ""); });
    gz.metin(gz.x0 + 6, gz.y1 + 14, "gri dikey: gerçek TOA (%50 noktası)", "w-not");
    // --- anlık frekans paneli
    WK.temizle(pFrek);
    var gf = WK.grafik(pFrek, { W: 640, H: 190, xmin: 0, xmax: tmaxUs, ymin: -20, ymax: 30, kenar: { sol: 48, sag: 14, ust: 22, alt: 34 } });
    gf.eksenler({ xAdet: 8, yAdet: 5, xAd: "zaman (µs)", yAd: "MHz", baslik: "Darbe içi anlık frekans (yalnız tespit edilen darbelerde; gerçek f_bb = +5 MHz)" });
    gf.yatay(F0 / 1e6, "w-cizgi-gri", "");
    var af = DSP.anlikFrekans(sig.i, sig.q, fs);
    pdwler.forEach(function (d) {
      var fx = [], fy = [];
      for (var k = d.bas; k < d.son; k++) { fx.push(k / fs * 1e6); fy.push(af[k] / 1e6); }
      gf.cizgi(fx, fy, d.sahte ? "w-cizgi-kirmizi" : "w-cizgi-sinyal");
      gf.yatay(d.f / 1e6, "w-cizgi-altin", "");
    });
    // --- tablo
    tabloKap.innerHTML = "";
    var tbl = WK.el("table", { "class": "w-mono" });
    var thead = WK.el("thead"), tr = WK.el("tr");
    ["#", "TOA (µs)", "ΔTOA (ns)", "PW (ns)", "ΔPW (ns)", "PA tepe / ort (dB)", "ΔPA (dB)", "f (MHz)", "Δf (kHz)", "MOP / eğim", "bayrak"].forEach(function (h) { tr.appendChild(WK.el("th", { text: h })); });
    thead.appendChild(tr); tbl.appendChild(thead);
    var tb = WK.el("tbody");
    var eToa = [], ePw = [], eF = [], ePa = [], sahteSay = 0, kacan = 0;
    pdwler.forEach(function (d, i) {
      var r = WK.el("tr");
      r.appendChild(td(String(i + 1)));
      r.appendChild(td(f3(d.toa * 1e6, 3)));
      var dt = (d.sahte || d.devam) ? NaN : (d.toa - d.g.toa) * 1e9;
      var dpw = (d.sahte || d.devam || d.kirpildi) ? NaN : (d.pw - d.g.pw) * 1e9;
      var dpa = d.paOrt - 0;                              // gerçek: 0 dB (tepe genliği 1)
      var df = (d.f - F0) / 1e3;
      if (!d.sahte && !d.bayrak.length) { eToa.push(dt); ePw.push(dpw); eF.push(df); ePa.push(dpa); }
      r.appendChild(td(f3(dt, 1), Math.abs(dt) > 10 ? "uyar" : ""));
      r.appendChild(td(f3(d.pw * 1e9, 0)));
      r.appendChild(td(f3(dpw, 1), Math.abs(dpw) > 20 ? "uyar" : ""));
      r.appendChild(td(f3(d.paTepe, 1) + " / " + f3(d.paOrt, 1)));
      r.appendChild(td(f3(dpa, 2)));
      r.appendChild(td(f3(d.f / 1e6, 3)));
      r.appendChild(td(f3(df, 1), Math.abs(df) > 50 ? "uyar" : ""));
      r.appendChild(td(d.mop + (d.mop === "LFM" ? " " + f3(d.egim / 1e12, 1) + " MHz/µs" : "")));
      r.appendChild(td(d.bayrak.join(" ") || "—", d.sahte ? "uyar" : ""));
      if (d.sahte) sahteSay++;
      tb.appendChild(r);
    });
    tbl.appendChild(tb);
    tabloKap.appendChild(tbl);
    // kaçan darbeler
    gercek.forEach(function (g) { var var_ = pdwler.some(function (d) { return !d.sahte && d.g === g; }); if (!var_) kacan++; });
    // --- sonuçlar
    var rms = function (a) { if (!a.length) return NaN; var s = 0; a.forEach(function (v) { s += v * v; }); return Math.sqrt(s / a.length); };
    var ort = function (a) { if (!a.length) return NaN; var s = 0; a.forEach(function (v) { s += v; }); return s / a.length; };
    var std = function (a) { var m = ort(a); return isFinite(m) ? rms(a.map(function (v) { return v - m; })) : NaN; };
    var twBias = (DSP.timeWalk(rise, Math.pow(10, (p.esik - p.snr) / 20)) - rise / 2 + (p.ma - 1) / 2 / fs) * 1e9;
    var nPw = Math.round(pw * fs);
    var toaTeori = DSP.toaHatasi(rise, p.snr) * 1e9;
    var fTeori = DSP.crlbFrekans(p.snr, nPw, fs) / 1e3;
    var pfaTeori = Math.exp(-Math.pow(10, p.esik / 10));   // MA'sız kare-yasa; MA gürültüyü daraltır, Pfa düşer
    var beklenenPw = pw * 1e9 + rise * 1e9 - 2 * DSP.timeWalk(rise, Math.pow(10, (p.esik - p.snr) / 20)) * 1e9;
    WK.sonucYaz(w, {
      "PDW": pdwler.length + " (gerçek darbe " + gercek.length + ")",
      "sahte / kaçan": (sahteSay ? "!" : "+") + sahteSay + " / " + kacan,
      "min PW altı atılan": String(atilan.length),
      "TOA sapması (ort.)": (eToa.length ? f3(ort(eToa), 1) : "—") + " ns  (time walk + filtre gecikmesi ≈ " + f3(twBias, 1) + " ns)",
      "TOA rms (sapma çıkarılmış)": (eToa.length ? f3(std(eToa), 1) : "—") + " ns  (teori t_r/√(2·SNR) = " + f3(toaTeori, 1) + " ns; 1 örnek = 3.33 ns)",
      "PW ortalama sapması": (ePw.length ? f3(ort(ePw), 1) : "—") + " ns  (eşik tanımından beklenen ≈ " + f3(beklenenPw - pw * 1e9, 1) + " ns)",
      "f rms hatası": (eF.length ? f3(rms(eF), 1) : "—") + " kHz  (CRLB = " + f3(fTeori, 1) + " kHz, N = " + nPw + ")",
      "PA sapması (ort.)": (ePa.length ? f3(ort(ePa), 2) : "—") + " dB (gürültü gücü eklenir: +" + f3(10 * Math.log10(1 + Pn), 2) + " dB beklenir)",
      "Pfa (kare-yasa, MA'sız)": pfaTeori.toExponential(1) + (p.esik < 9 ? " !yüksek" : ""),
      "not": "PRI gösterim için " + f3(pri * 1e6, 1) + " µs'e ölçeklendi; referans senaryoda 1 ms"
    });
  }

  return {
    ciz: ciz,
    presetler: [
      { ad: "Referans senaryo", param: { snr: snrRef, pw: pwRef, pri: PRI_GOSTERIM, mop: "yok", esik: esikRefDb, hyst: hystRef, minpw: minPwRef, ma: maRef, tohum: 7 } },
      { ad: "Varyant B: LFM", param: { snr: snrRef, pw: pwRef, pri: PRI_GOSTERIM, mop: "lfm", esik: esikRefDb, hyst: hystRef, minpw: minPwRef, ma: maRef, tohum: 7 } },
      { ad: "Düşük SNR (10 dB), eşik indirilmiş", param: { snr: 10, pw: pwRef, pri: PRI_GOSTERIM, mop: "yok", esik: 8.5, hyst: hystRef, minpw: minPwRef, ma: maRef, tohum: 7 } },
      { ad: "Histerezis yok, eşik düşük", param: { snr: 12, pw: pwRef, pri: PRI_GOSTERIM, mop: "yok", esik: 7, hyst: 0, minpw: 1, ma: 1, tohum: 7 } },
      { ad: "Uzun darbe (SEG)", param: { snr: 20, pw: 4e-6, pri: 10e-6, mop: "yok", esik: esikRefDb, hyst: hystRef, minpw: minPwRef, ma: maRef, tohum: 7 } }
    ]
  };
});
