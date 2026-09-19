/* W-02 — Fazör laboratuvarı
   Kontroller: frekans (±, DDC çıkış hızına göre), başlangıç fazı, I/Q kazanç hatası (dB), I/Q faz hatası (°), I/Q swap
   Çıktı: dönen vektör (birim çember üzerinde örnekler), I(t)/Q(t), kompleks spektrum (ton + image), IRR
   Yerel yardımcı: iqImageDbc (dsp-core'da yok — rapora yazıldı) */
WK.kaydet("w02", function (w) {
  var S = w.S;
  var fsRef = S.ddc ? S.ddc.cikis_fs_msps * 1e6 : 300e6;

  // I/Q dengesizliğinde image/sinyal oranı (dB): x = cos θ + j·g·sin(θ+φ)
  // → x = ½[e^{jθ}(1 + g e^{jφ}) + e^{−jθ}(1 − g e^{−jφ})]; IRR = 20log|1+g e^{jφ}| − 20log|1−g e^{−jφ}|
  function iqImageDbc(kazancDb, fazDeg) {
    var g = Math.pow(10, kazancDb / 20), f = fazDeg * Math.PI / 180;
    var aRe = 1 + g * Math.cos(f), aIm = g * Math.sin(f);
    var bRe = 1 - g * Math.cos(f), bIm = g * Math.sin(f);
    var a = Math.sqrt(aRe * aRe + aIm * aIm), b = Math.sqrt(bRe * bRe + bIm * bIm);
    return -(20 * Math.log10(a) - 20 * Math.log10(Math.max(b, 1e-12)));   // negatif dBc (image seviyesi)
  }

  WK.kaydirici(w, { ad: "f", etiket: "frekans (fs = " + (fsRef / 1e6) + " MSPS)", min: -fsRef / 2 * 0.98, max: fsRef / 2 * 0.98, adim: 0.5e6, deger: 20e6, olcek: 1e6, birim: "MHz", hane: 1 });
  WK.kaydirici(w, { ad: "faz", etiket: "başlangıç fazı φ", min: -180, max: 180, adim: 5, deger: 0, birim: "°", tamsayi: true });
  var kapat = WK.grup(w, "I/Q kusurları");
  WK.kaydirici(w, { ad: "gHata", etiket: "kazanç hatası (Q/I)", min: -3, max: 3, adim: 0.1, deger: 0, birim: "dB", hane: 1 });
  WK.kaydirici(w, { ad: "fHata", etiket: "faz hatası (Q'nun 90°'den sapması)", min: -30, max: 30, adim: 1, deger: 0, birim: "°", tamsayi: true });
  WK.onay(w, { ad: "swap", etiket: "I ↔ Q yer değiştir", deger: false });
  kapat();

  var cember = WK.panel(w, 260), zaman = WK.panel(w, 200), spek = WK.panel(w, 240);
  var NFFT = 2048;

  function ciz() {
    var p = w.param;
    var g = Math.pow(10, p.gHata / 20), fh = p.fHata * Math.PI / 180, f0 = p.faz * Math.PI / 180;
    // örnekler (fs'te)
    var n = NFFT, I = new Float64Array(n), Q = new Float64Array(n);
    for (var k = 0; k < n; k++) {
      var th = 2 * Math.PI * p.f * k / fsRef + f0;
      var i_ = Math.cos(th), q_ = g * Math.sin(th + fh);
      if (p.swap) { var t = i_; i_ = q_; q_ = t; }
      I[k] = i_; Q[k] = q_;
    }
    // --- birim çember: ilk 16 örnek ve vektör
    WK.temizle(cember);
    var W = 640, H = 260, cx = 150, cy = 130, R = 100;
    cember.setAttribute("viewBox", "0 0 " + W + " " + H);
    var e = function (tag, a) { var el = WK.svgEl(tag, a); cember.appendChild(el); return el; };
    e("circle", { cx: cx, cy: cy, r: R, "class": "w-eksen" });
    e("line", { x1: cx - R - 14, y1: cy, x2: cx + R + 14, y2: cy, "class": "w-izgara" });
    e("line", { x1: cx, y1: cy - R - 14, x2: cx, y2: cy + R + 14, "class": "w-izgara" });
    e("text", { x: cx + R + 4, y: cy + 14, "class": "w-not", text: "I" });
    e("text", { x: cx + 6, y: cy - R - 4, "class": "w-not", text: "Q" });
    // gerçek yörünge (elips) 120 nokta
    var d = "";
    for (k = 0; k <= 120; k++) {
      var thh = 2 * Math.PI * k / 120;
      var ii = Math.cos(thh), qq = g * Math.sin(thh + fh);
      if (p.swap) { var tt = ii; ii = qq; qq = tt; }
      d += (k ? "L" : "M") + (cx + R * ii).toFixed(1) + " " + (cy - R * qq).toFixed(1);
    }
    e("path", { d: d, "class": (Math.abs(p.gHata) > 0.05 || Math.abs(p.fHata) > 0.5) ? "w-cizgi-kirmizi" : "w-cizgi-gri" });
    var adet = 16;
    for (k = 0; k < adet; k++) {
      e("circle", { cx: cx + R * I[k], cy: cy - R * Q[k], r: 3.5, "class": "w-nokta", opacity: (0.3 + 0.7 * (k + 1) / adet).toFixed(2) });
    }
    e("line", { x1: cx, y1: cy, x2: cx + R * I[0], y2: cy - R * Q[0], "class": "w-cizgi-sinyal", "stroke-width": 2.5 });
    e("line", { x1: cx + R * I[0], y1: cy - R * Q[0], x2: cx + R * I[0], y2: cy, "class": "w-cizgi-yesil", "stroke-dasharray": "3 3" });
    e("line", { x1: cx + R * I[0], y1: cy - R * Q[0], x2: cx, y2: cy - R * Q[0], "class": "w-cizgi-q", "stroke-dasharray": "3 3" });
    var yon = (p.f > 0) !== !!p.swap;
    e("text", { x: 300, y: 40, "class": "w-baslik", text: "Dönen vektör — ilk " + adet + " örnek" });
    e("text", { x: 300, y: 62, "class": "w-not", text: "örnek başına dönüş: " + (360 * p.f / fsRef).toFixed(1) + "° (= 360°·f/fs)" });
    e("text", { x: 300, y: 82, "class": "w-not", text: "yön: " + (p.f === 0 ? "durağan (DC)" : yon ? "saat yönünün tersi → pozitif frekans" : "saat yönü → negatif frekans") });
    e("text", { x: 300, y: 102, "class": "w-not", text: "genlik = √(I²+Q²), faz = atan2(Q, I)" });
    e("text", { x: 300, y: 122, "class": "w-not", text: "|x| örnek 0: " + Math.sqrt(I[0] * I[0] + Q[0] * Q[0]).toFixed(3) + ", faz: " + (Math.atan2(Q[0], I[0]) * 180 / Math.PI).toFixed(1) + "°" });
    e("text", { x: 300, y: 150, "class": "w-not", text: (Math.abs(p.gHata) > 0.05 || Math.abs(p.fHata) > 0.5) ? "kusurlu I/Q: yörünge elips, |x| örnekten örneğe dalgalanır" : "ideal I/Q: yörünge tam çember, |x| sabit" });
    // anlık frekans
    var af = DSP.anlikFrekans(I, Q, fsRef), afOrt = 0; for (k = 1; k < 64; k++) afOrt += af[k]; afOrt /= 63;
    e("text", { x: 300, y: 170, "class": "w-not", text: "anlık frekans (faz farkından, ilk 64 örnek ort.): " + WK.fmtHz(afOrt) });
    // --- zaman
    WK.temizle(zaman);
    var gz = WK.grafik(zaman, { W: 640, H: 200, xmin: 0, xmax: 63, ymin: -1.5, ymax: 1.5, kenar: { sol: 44, sag: 14, ust: 22, alt: 30 } });
    gz.eksenler({ xAdet: 8, yAdet: 4, xAd: "örnek n (fs = " + fsRef / 1e6 + " MSPS)", yAd: "genlik", baslik: "I(t) mavi, Q(t) mor", yFmt: function (v) { return v.toFixed(1); } });
    var xs = [], yi = [], yq = [];
    for (k = 0; k < 64; k++) { xs.push(k); yi.push(I[k]); yq.push(Q[k]); }
    gz.cizgi(xs, yi, "w-cizgi-sinyal"); gz.cizgi(xs, yq, "w-cizgi-q");
    for (k = 0; k < 64; k += 2) { gz.nokta(k, I[k], 2, "w-nokta"); }
    // --- spektrum
    WK.temizle(spek);
    var sp = DSP.spektrumDbfs(I, Q, "blackman-harris");
    var gs = WK.grafik(spek, { W: 640, H: 240, xmin: -fsRef / 2e6, xmax: fsRef / 2e6, ymin: -100, ymax: 5, kenar: { sol: 48, sag: 14, ust: 22, alt: 34 } });
    gs.eksenler({ xAdet: 6, yAdet: 5, xAd: "frekans (MHz)", yAd: "dBFS", baslik: "Kompleks spektrum (N = 2048, Blackman-Harris) — negatif frekanslar solda" });
    var fx = [], fy = [];
    for (k = 0; k < NFFT; k++) { fx.push((k - NFFT / 2) * fsRef / NFFT / 1e6); fy.push(sp[k]); }
    gs.alan(fx, fy, -100, "w-dolgu-sinyal"); gs.cizgi(fx, fy, "w-cizgi-sinyal");
    gs.dikey(0, "w-cizgi-gri", "0 (DC)");
    var irr = iqImageDbc(p.gHata, p.fHata);
    var fTon = p.swap ? -p.f : p.f;
    if (Math.abs(p.f) > 0.5e6) {
      gs.metin(gs.px(fTon / 1e6) + 6, gs.py(0) + 12, "ton " + (fTon / 1e6).toFixed(1) + " MHz", "w-not");
      if (irr > -95) {
        gs.nokta(-fTon / 1e6, irr, 4);
        gs.metin(gs.px(-fTon / 1e6) + 6, gs.py(irr) - 6, "image " + irr.toFixed(1) + " dBc", "w-not");
      }
    }
    // metrik: image bin gücü
    var m = DSP.spektrumMetrik(sp, { koruma: 8 });
    WK.sonucYaz(w, {
      "örnek başına faz adımı": (360 * p.f / fsRef).toFixed(2) + "°",
      "periyot": p.f === 0 ? "∞" : (fsRef / Math.abs(p.f)).toFixed(1) + " örnek",
      "tonun konumu": (fTon / 1e6).toFixed(1) + " MHz" + (p.swap ? " (swap: aynalandı)" : ""),
      "image (teori)": irr < -95 ? "+yok (ideal I/Q)" : (irr > -30 ? "!" : "") + irr.toFixed(1) + " dBc",
      "image (spektrumdan)": m.sfdr > 95 ? "+< −95 dBc" : (-m.sfdr).toFixed(1) + " dBc",
      "kazanç / faz hatası": p.gHata.toFixed(1) + " dB / " + p.fHata + "°"
    });
  }
  return {
    ciz: ciz,
    presetler: [
      { ad: "Referans senaryo", param: { f: 20e6, faz: 0, gHata: 0, fHata: 0, swap: false } },
      { ad: "Negatif frekans", param: { f: -20e6, faz: 0, gHata: 0, fHata: 0, swap: false } },
      { ad: "I/Q dengesizliği", param: { f: 20e6, faz: 0, gHata: 1, fHata: 10, swap: false } },
      { ad: "Küçük hata (0.1 dB, 1°)", param: { f: 20e6, faz: 0, gHata: 0.1, fHata: 1, swap: false } },
      { ad: "I/Q swap", param: { f: 20e6, faz: 0, gHata: 0, fHata: 0, swap: true } }
    ]
  };
});
