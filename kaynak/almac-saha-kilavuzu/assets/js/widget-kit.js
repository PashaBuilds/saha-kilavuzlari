/* ============================================================================
   widget-kit.js — ortak widget kabı, kontroller ve SVG çizim yardımcıları
   Bir widget şu sözleşmeyle kayıt olur:
     WK.kaydet("w11", function (w) { ... return { ciz: fn, presetler: [...] } })
   w: { kok, kontrol, cizim, sonuc, param, S (senaryo), ... }
   Tüm çizimler inline SVG'ye yapılır; renkler CSS sınıfları / değişkenleri ile
   gelir, tema değişince tarayıcı kendisi yeniden boyar.
   ========================================================================== */
(function (kok) {
  "use strict";
  var WK = { fabrikalar: {}, ornekler: [] };
  var NS = "http://www.w3.org/2000/svg";

  WK.kaydet = function (id, fabrika) { WK.fabrikalar[id] = fabrika; };

  /* ------------------------------------------------------------- DOM yardımcıları */
  function el(tag, attrs, cocuklar) {
    var e = document.createElement(tag);
    if (attrs) for (var k in attrs) { if (k === "text") e.textContent = attrs[k]; else if (k === "html") e.innerHTML = attrs[k]; else e.setAttribute(k, attrs[k]); }
    if (cocuklar) cocuklar.forEach(function (c) { if (c) e.appendChild(typeof c === "string" ? document.createTextNode(c) : c); });
    return e;
  }
  WK.el = el;
  function svgEl(tag, attrs) {
    var e = document.createElementNS(NS, tag);
    if (attrs) for (var k in attrs) { if (k === "text") e.textContent = attrs[k]; else e.setAttribute(k, attrs[k]); }
    return e;
  }
  WK.svgEl = svgEl;

  /* ------------------------------------------------------------------ sayı biçimi */
  WK.fmt = function (v, hane) { if (!isFinite(v)) return "—"; return (+v).toFixed(hane === undefined ? 2 : hane); };
  WK.fmtHz = function (hz) { return kok.DSP.birimFormat(hz); };
  WK.fmtS = function (s) { return kok.DSP.sureFormat(s); };
  WK.fmtDb = function (v, hane) { return WK.fmt(v, hane === undefined ? 1 : hane) + " dB"; };

  /* --------------------------------------------------------------- kontrol üretimi */
  // Kaydırıcı + sayısal giriş birlikte. spec: {ad, etiket, min, max, adim, deger, birim, log?, hane?}
  // spec.olcek: param Hz'de tutulurken kutuda MHz göstermek gibi (görünen = param / olcek); spec.birim görünen birim.
  WK.kaydirici = function (w, spec) {
    var deger = spec.deger, olcek = spec.olcek || 1;
    var out = el("span", { "class": "w-deger" });
    var range = el("input", { type: "range", min: spec.log ? 0 : spec.min / olcek, max: spec.log ? 1000 : spec.max / olcek, step: spec.log ? 1 : ((spec.adim || 1) / olcek), "aria-label": spec.etiket });
    var num = el("input", { type: "number", min: spec.min / olcek, max: spec.max / olcek, step: (spec.adim ? spec.adim / olcek : "any"), "aria-label": spec.etiket + " (sayı)" });
    var lab = el("label", { "class": "w-alan" }, [
      el("span", {}, [el("span", { "class": "w-etk", text: spec.etiket }), out]),
      el("div", { "class": "w-satir" }, [range, num])
    ]);
    function toRange(v) { return spec.log ? Math.round(1000 * Math.log(v / spec.min) / Math.log(spec.max / spec.min)) : v / olcek; }
    function fromRange(r) { return spec.log ? spec.min * Math.pow(spec.max / spec.min, r / 1000) : (+r) * olcek; }
    function hane() { if (spec.hane !== undefined) return spec.hane; var a = (spec.adim || 1) / olcek; return a >= 1 ? 0 : a >= 0.1 ? 1 : a >= 0.01 ? 2 : 3; }
    function goster() {
      var v = w.param[spec.ad];
      out.textContent = (spec.goster ? spec.goster(v) : (WK.fmt(v / olcek, hane()) + (spec.birim ? " " + spec.birim : "")));
      range.value = toRange(v); num.value = +((v / olcek).toFixed(Math.max(hane(), spec.log ? 3 : 0)));
    }
    range.addEventListener("input", function () { w.param[spec.ad] = fromRange(range.value); if (spec.tamsayi) w.param[spec.ad] = Math.round(w.param[spec.ad]); goster(); w.degisti(spec.ad); });
    num.addEventListener("change", function () { var v = (+num.value) * olcek; if (!isFinite(v)) return; v = Math.max(spec.min, Math.min(spec.max, v)); if (spec.tamsayi) v = Math.round(v); w.param[spec.ad] = v; goster(); w.degisti(spec.ad); });
    w.param[spec.ad] = deger;
    w.kontrol.appendChild(lab);
    w._gosterenler.push(goster);
    goster();
    return lab;
  };
  // Seçim kutusu: spec {ad, etiket, secenekler:[[deger, metin],...], deger}
  WK.secim = function (w, spec) {
    var sel = el("select", { "aria-label": spec.etiket });
    spec.secenekler.forEach(function (s) { sel.appendChild(el("option", { value: s[0], text: s[1] })); });
    var lab = el("label", { "class": "w-alan" }, [el("span", {}, [el("span", { "class": "w-etk", text: spec.etiket })]), sel]);
    w.param[spec.ad] = spec.deger;
    function goster() { sel.value = w.param[spec.ad]; }
    sel.addEventListener("change", function () { w.param[spec.ad] = isNaN(+sel.value) || spec.metin ? sel.value : +sel.value; w.degisti(spec.ad); });
    w.kontrol.appendChild(lab); w._gosterenler.push(goster); goster();
    return lab;
  };
  WK.onay = function (w, spec) {
    var cb = el("input", { type: "checkbox" });
    var lab = el("label", { "class": "w-onay" }, [cb, el("span", { text: spec.etiket })]);
    w.param[spec.ad] = !!spec.deger;
    function goster() { cb.checked = !!w.param[spec.ad]; }
    cb.addEventListener("change", function () { w.param[spec.ad] = cb.checked; w.degisti(spec.ad); });
    w.kontrol.appendChild(lab); w._gosterenler.push(goster); goster();
    return lab;
  };
  WK.dugme = function (w, etiket, tikla) {
    var b = el("button", { type: "button", "class": "w-dugme", text: etiket });
    b.addEventListener("click", tikla);
    w.kontrol.appendChild(b);
    return b;
  };
  WK.grup = function (w, baslik) {
    var g = el("div", { "class": "w-grup" }, [el("b", { text: baslik })]);
    w.kontrol.appendChild(g);
    var eskiKontrol = w.kontrol;
    w.kontrol = g;
    return function () { w.kontrol = eskiKontrol; };
  };
  // Sonuç şeridi: {etiket: değer} nesnesi; değer string; "!" ile başlarsa uyarı, "+" ile başlarsa iyi.
  WK.sonucYaz = function (w, obj) {
    w.sonuc.innerHTML = "";
    for (var k in obj) {
      var v = String(obj[k]), kls = "";
      if (v.charAt(0) === "!") { kls = "uyar"; v = v.slice(1); } else if (v.charAt(0) === "+") { kls = "iyi"; v = v.slice(1); }
      w.sonuc.appendChild(el("span", { "class": kls }, [k + ": ", el("b", { text: v })]));
    }
  };

  /* ------------------------------------------------------------- çizim: koordinat */
  // Grafik alanı: svg (viewBox W×H), kenar boşlukları; x/y ölçekleri.
  WK.grafik = function (svg, opts) {
    var W = opts.W || 640, H = opts.H || 260, m = opts.kenar || { sol: 48, sag: 14, ust: 22, alt: 34 };
    svg.setAttribute("viewBox", "0 0 " + W + " " + H);
    svg.setAttribute("role", "img");
    var g = { svg: svg, W: W, H: H, m: m, x0: m.sol, x1: W - m.sag, y0: H - m.alt, y1: m.ust,
              xmin: opts.xmin, xmax: opts.xmax, ymin: opts.ymin, ymax: opts.ymax, xlog: !!opts.xlog };
    g.px = function (x) { if (g.xlog) return g.x0 + (Math.log10(x) - Math.log10(g.xmin)) / (Math.log10(g.xmax) - Math.log10(g.xmin)) * (g.x1 - g.x0); return g.x0 + (x - g.xmin) / (g.xmax - g.xmin) * (g.x1 - g.x0); };
    g.py = function (y) { return g.y0 - (y - g.ymin) / (g.ymax - g.ymin) * (g.y0 - g.y1); };
    g.ekle = function (tag, attrs) { var e = svgEl(tag, attrs); svg.appendChild(e); return e; };
    g.metin = function (x, y, t, kls, anchor) { return g.ekle("text", { x: x, y: y, "class": kls || "w-etiket", "text-anchor": anchor || "start", text: t }); };
    // eksenler + ızgara + etiketler
    g.eksenler = function (ax) {
      ax = ax || {};
      var xt = ax.xTik || WK.tikler(g.xmin, g.xmax, ax.xAdet || 6, g.xlog), yt = ax.yTik || WK.tikler(g.ymin, g.ymax, ax.yAdet || 5);
      var k;
      var xf = ax.xFmt || WK.tikFmt(xt), yf = ax.yFmt || WK.tikFmt(yt);
      for (k = 0; k < xt.length; k++) { var px = g.px(xt[k]); g.ekle("line", { x1: px, y1: g.y1, x2: px, y2: g.y0, "class": "w-izgara" }); g.metin(px, g.y0 + 14, xf(xt[k]), "w-etiket", "middle"); }
      for (k = 0; k < yt.length; k++) { var py = g.py(yt[k]); g.ekle("line", { x1: g.x0, y1: py, x2: g.x1, y2: py, "class": "w-izgara" }); g.metin(g.x0 - 6, py + 3.5, yf(yt[k]), "w-etiket", "end"); }
      g.ekle("rect", { x: g.x0, y: g.y1, width: g.x1 - g.x0, height: g.y0 - g.y1, "class": "w-eksen" });
      if (ax.xAd) g.metin((g.x0 + g.x1) / 2, g.H - 6, ax.xAd, "w-eksen-ad", "middle");
      if (ax.yAd) { var t = g.metin(12, (g.y0 + g.y1) / 2, ax.yAd, "w-eksen-ad", "middle"); t.setAttribute("transform", "rotate(-90 12 " + (g.y0 + g.y1) / 2 + ")"); }
      if (ax.baslik) g.metin(g.x0, 13, ax.baslik, "w-baslik");
      return g;
    };
    // çizgi: xs, ys dizileri (kırpmalı)
    g.cizgi = function (xs, ys, kls, kapalı) {
      var d = "", ilk = true;
      for (var k = 0; k < xs.length; k++) {
        var y = ys[k];
        if (!isFinite(y)) { ilk = true; continue; }
        var px = g.px(xs[k]), py = g.py(Math.max(g.ymin - (g.ymax - g.ymin), Math.min(g.ymax + (g.ymax - g.ymin) * 0.1, y)));
        d += (ilk ? "M" : "L") + px.toFixed(1) + " " + py.toFixed(1); ilk = false;
      }
      var p = g.ekle("path", { d: d, "class": kls || "w-cizgi-sinyal" });
      p.setAttribute("clip-path", g.klip());
      return p;
    };
    // alan dolgusu: ys'nin altından taban değere
    g.alan = function (xs, ys, taban, kls) {
      if (!xs.length) return null;
      var d = "M" + g.px(xs[0]).toFixed(1) + " " + g.py(taban).toFixed(1);
      for (var k = 0; k < xs.length; k++) d += "L" + g.px(xs[k]).toFixed(1) + " " + g.py(Math.max(g.ymin, Math.min(g.ymax, ys[k]))).toFixed(1);
      d += "L" + g.px(xs[xs.length - 1]).toFixed(1) + " " + g.py(taban).toFixed(1) + "Z";
      var p = g.ekle("path", { d: d, "class": kls || "w-dolgu-sinyal" });
      p.setAttribute("clip-path", g.klip());
      return p;
    };
    // etiketli metin: arka plan kutusu ile (çizgilerle çakışmayı azaltır)
    g.etiket = function (x, y, t, anchor, kls) {
      var w = 6.2 * String(t).length + 8, h = 14, x0 = anchor === "end" ? x - w : (anchor === "middle" ? x - w / 2 : x - 4);
      g.ekle("rect", { x: x0, y: y - 11, width: w, height: h, rx: 3, fill: "var(--dia-panel)", opacity: ".85" });
      return g.metin(x, y, t, kls || "w-not", anchor);
    };
    // konum: "ust" | "alt" (yatay için) — "sag" | "sol" (dikey için); varsayılan eski davranış
    g.dikey = function (x, kls, etiket, konum) {
      var e = g.ekle("line", { x1: g.px(x), y1: g.y1, x2: g.px(x), y2: g.y0, "class": kls || "w-cizgi-gri" });
      if (etiket) { if (konum === "sol") g.etiket(g.px(x) - 3, g.y1 + 11, etiket, "end"); else g.etiket(g.px(x) + 3, g.y1 + 11, etiket, "start"); }
      return e;
    };
    g.yatay = function (y, kls, etiket, konum) {
      var e = g.ekle("line", { x1: g.x0, y1: g.py(y), x2: g.x1, y2: g.py(y), "class": kls || "w-cizgi-gri" });
      if (etiket) { var yy = konum === "alt" ? g.py(y) + 12 : g.py(y) - 4; var xx = konum === "sol" ? g.x0 + 3 : g.x1 - 3; g.etiket(xx, yy, etiket, konum === "sol" ? "start" : "end"); }
      return e;
    };
    g.nokta = function (x, y, r, kls) { return g.ekle("circle", { cx: g.px(x), cy: g.py(y), r: r || 4, "class": kls || "w-nokta" }); };
    g.bant = function (xa, xb, kls) { var e = g.ekle("rect", { x: g.px(Math.max(xa, g.xmin)), y: g.y1, width: Math.max(0, g.px(Math.min(xb, g.xmax)) - g.px(Math.max(xa, g.xmin))), height: g.y0 - g.y1, "class": kls || "w-dolgu-altin" }); return e; };
    g._klipId = null;
    g.klip = function () {
      if (!g._klipId) {
        g._klipId = "klip-" + Math.random().toString(36).slice(2, 8);
        var cp = svgEl("clipPath", { id: g._klipId });
        cp.appendChild(svgEl("rect", { x: g.x0, y: g.y1, width: g.x1 - g.x0, height: g.y0 - g.y1 }));
        svg.insertBefore(cp, svg.firstChild);
      }
      return "url(#" + g._klipId + ")";
    };
    return g;
  };
  WK.tikler = function (a, b, adet, log) {
    if (log) { var out = [], p = Math.ceil(Math.log10(a)); for (; Math.pow(10, p) <= b * 1.0001; p++) out.push(Math.pow(10, p)); return out; }
    var ham = (b - a) / adet, mag = Math.pow(10, Math.floor(Math.log10(ham))), n = ham / mag;
    var adim = (n < 1.5 ? 1 : n < 3 ? 2 : n < 7 ? 5 : 10) * mag;
    var t = [], v = Math.ceil(a / adim) * adim;
    for (; v <= b + adim * 1e-6; v += adim) t.push(Math.abs(v) < adim * 1e-6 ? 0 : v);
    return t;
  };
  // Tik biçimleyici: eksen değerleri makul aralıktaysa (|v| < 1e5, ≥ 1e-3) SI öneksiz, adıma göre ondalıklı yazar;
  // aksi halde kisaSayi (SI önekli). "5m"/"1.2k" gibi yanıltıcı etiketleri önler.
  WK.tikFmt = function (tikler) {
    var maks = 0, adim = Infinity, k;
    for (k = 0; k < tikler.length; k++) { maks = Math.max(maks, Math.abs(tikler[k])); if (k > 0) adim = Math.min(adim, Math.abs(tikler[k] - tikler[k - 1])); }
    if (maks === 0 || maks >= 1e5 || (maks < 1e-3)) return WK.kisaSayi;
    var hane = adim >= 1 ? 0 : adim >= 0.1 ? 1 : adim >= 0.01 ? 2 : 3;
    return function (v) { return (Math.abs(v) < 1e-12 ? 0 : v).toFixed(hane); };
  };
  WK.kisaSayi = function (v) {
    var a = Math.abs(v);
    if (a >= 1e9) return (v / 1e9).toPrecision(3).replace(/\.?0+$/, "") + "G";
    if (a >= 1e6) return (v / 1e6).toPrecision(3).replace(/\.?0+$/, "") + "M";
    if (a >= 1e3) return (v / 1e3).toPrecision(3).replace(/\.?0+$/, "") + "k";
    if (a >= 1) return (+v.toPrecision(3)).toString();
    if (a === 0) return "0";
    if (a >= 1e-3) return (v * 1e3).toPrecision(3).replace(/\.?0+$/, "") + "m";
    if (a >= 1e-6) return (v * 1e6).toPrecision(3).replace(/\.?0+$/, "") + "µ";
    if (a >= 1e-9) return (v * 1e9).toPrecision(3).replace(/\.?0+$/, "") + "n";
    return (v * 1e12).toPrecision(3).replace(/\.?0+$/, "") + "p";
  };
  // Yeni boş SVG paneli oluşturup çizim alanına ekler
  WK.panel = function (w, yukseklik) {
    var s = svgEl("svg", { viewBox: "0 0 640 " + (yukseklik || 260) });
    w.cizim.appendChild(s);
    return s;
  };
  WK.temizle = function (svg) { while (svg.firstChild) svg.removeChild(svg.firstChild); };

  /* ------------------------------------------------------------------- yaşam döngüsü */
  function kur(kokEl) {
    var id = kokEl.getAttribute("data-widget"), fab = WK.fabrikalar[id];
    if (!fab) { kokEl.querySelector(".w-cizim").innerHTML = '<p class="w-jsyok">Widget kodu bulunamadı: ' + id + '</p>'; return; }
    var w = {
      id: id, kok: kokEl, kontrol: kokEl.querySelector(".w-kontrol"), cizim: kokEl.querySelector(".w-cizim"),
      sonuc: kokEl.querySelector(".w-sonuc"), param: {}, S: kok.SENARYO || {}, _gosterenler: [], _zaman: null, gorunur: true
    };
    w.cizim.innerHTML = "";
    w.tazele = function () { w._gosterenler.forEach(function (f) { f(); }); };
    w.degisti = function () {
      // debounce + rAF
      if (w._zaman) return;
      w._zaman = kok.requestAnimationFrame(function () { w._zaman = null; if (w.gorunur) w._ciz(); else w._kirli = true; });
      var pb = w.kok.querySelectorAll(".w-presetler button"); for (var k = 0; k < pb.length; k++) pb[k].setAttribute("aria-pressed", "false");
    };
    var api;
    try { api = fab(w); } catch (e) { w.cizim.innerHTML = '<p class="w-jsyok">Widget hatası: ' + (e && e.message) + '</p>'; if (kok.console) console.error(id, e); return; }
    w._ciz = function () { try { api.ciz(); } catch (e) { if (kok.console) console.error(id, e); } };
    // presetler
    if (api.presetler && api.presetler.length) {
      var pk = el("div", { "class": "w-presetler" });
      api.presetler.forEach(function (p, i) {
        var b = el("button", { type: "button", text: p.ad, "aria-pressed": i === 0 ? "true" : "false" });
        b.addEventListener("click", function () {
          for (var k in p.param) w.param[k] = p.param[k];
          w.tazele(); w._ciz();
          var pb = pk.querySelectorAll("button"); for (var j = 0; j < pb.length; j++) pb[j].setAttribute("aria-pressed", "false");
          b.setAttribute("aria-pressed", "true");
        });
        pk.appendChild(b);
      });
      var sifirla = el("button", { type: "button", text: "sıfırla" });
      sifirla.addEventListener("click", function () { for (var k in api.presetler[0].param) w.param[k] = api.presetler[0].param[k]; w.tazele(); w._ciz(); });
      pk.appendChild(sifirla);
      w.kok.querySelector(".w-alt").insertBefore(pk, w.sonuc);
      for (var k in api.presetler[0].param) w.param[k] = api.presetler[0].param[k];
      w.tazele();
    }
    // görünürlük: görünmüyorken hesap yapma
    if (kok.IntersectionObserver) {
      var io = new IntersectionObserver(function (g) {
        g.forEach(function (e) { w.gorunur = e.isIntersecting; if (w.gorunur && w._kirli) { w._kirli = false; w._ciz(); } });
      }, { rootMargin: "200px 0px" });
      io.observe(kokEl);
    }
    w._ciz();
    WK.ornekler.push(w);
  }

  WK.baslat = function () {
    var koklar = document.querySelectorAll(".widget[data-widget]");
    for (var k = 0; k < koklar.length; k++) kur(koklar[k]);
  };
  kok.WK = WK;
})(window);
