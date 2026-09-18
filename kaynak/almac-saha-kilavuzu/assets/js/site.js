/* site.js — tema, ilerleme çubuğu, TOC scroll-spy, rota filtresi, kopyala,
   üç-göz sekmeleri, baskı öncesi açılır kutular, widget başlatma. */
(function () {
  "use strict";
  var kok = document.documentElement;

  // tema
  var td = document.getElementById("tema-dugme");
  if (td) td.addEventListener("click", function () {
    var t = kok.getAttribute("data-theme") === "dark" ? "light" : "dark";
    kok.setAttribute("data-theme", t);
    try { localStorage.setItem("tema", t); } catch (e) {}
    // Canvas tabanlı widget'lar tema değişince yeniden çizsin
    if (window.WK) WK.ornekler.forEach(function (w) { if (w._ciz) w._ciz(); });
  });

  // ilerleme
  var bar = document.getElementById("progress");
  function ilerleme() { var h = kok; bar.style.width = (h.scrollTop / (h.scrollHeight - h.clientHeight) * 100) + "%"; }
  addEventListener("scroll", ilerleme, { passive: true }); ilerleme();

  // kopyala
  document.querySelectorAll(".komut").forEach(function (kutu) {
    var b = document.createElement("button");
    b.className = "kopyala"; b.type = "button"; b.textContent = "Kopyala";
    b.addEventListener("click", function () {
      var metin = kutu.querySelector("code").innerText;
      (navigator.clipboard ? navigator.clipboard.writeText(metin) : Promise.reject()).then(function () {
        b.textContent = "Kopyalandı"; b.classList.add("ok");
        setTimeout(function () { b.textContent = "Kopyala"; b.classList.remove("ok"); }, 1600);
      }).catch(function () { b.textContent = "Olmadı"; });
    });
    kutu.appendChild(b);
  });

  // başlık anchor'ı → tam URL panoya
  document.querySelectorAll("a.baglanti").forEach(function (a) {
    a.addEventListener("click", function () {
      var url = location.origin + location.pathname + a.getAttribute("href");
      if (navigator.clipboard) navigator.clipboard.writeText(url).catch(function () {});
    });
  });

  // üç göz sekmeleri
  document.querySelectorAll(".uc-goz").forEach(function (kutu) {
    var sek = kutu.querySelectorAll('[role="tab"]'), pan = kutu.querySelectorAll('[role="tabpanel"]');
    sek.forEach(function (b, i) {
      b.addEventListener("click", function () {
        sek.forEach(function (x, j) { x.setAttribute("aria-selected", i === j ? "true" : "false"); pan[j].hidden = i !== j; });
      });
      b.addEventListener("keydown", function (e) {
        if (e.key === "ArrowRight" || e.key === "ArrowLeft") { var n = (i + (e.key === "ArrowRight" ? 1 : sek.length - 1)) % sek.length; sek[n].focus(); sek[n].click(); }
      });
    });
  });

  // rota filtresi
  var toclar = document.querySelectorAll("nav.toc");
  var rf = document.querySelectorAll(".rota-filtre");
  function rotaUygula(r) {
    toclar.forEach(function (n) { n.setAttribute("data-rota", r); });
    rf.forEach(function (g) { g.querySelectorAll("button").forEach(function (b) { b.setAttribute("aria-pressed", b.getAttribute("data-rota") === r ? "true" : "false"); }); });
    try { localStorage.setItem("almac-rota", r); } catch (e) {}
  }
  rf.forEach(function (g) { g.querySelectorAll("button").forEach(function (b) { b.addEventListener("click", function () { rotaUygula(b.getAttribute("data-rota")); }); }); });
  try { var kr = localStorage.getItem("almac-rota"); if (kr) rotaUygula(kr); } catch (e) {}

  // TOC scroll-spy (iki seviye)
  var basliklar = Array.prototype.slice.call(document.querySelectorAll("section.bolum > h2[id], section.bolum h3[id]"));
  var linkler = {};
  document.querySelectorAll('nav.toc a[href^="#"]').forEach(function (a) { var id = a.getAttribute("href").slice(1); (linkler[id] = linkler[id] || []).push(a); });
  var aktifBolum = null, aktifAlt = null;
  function vurgula(id) {
    var h = document.getElementById(id); if (!h) return;
    var bolumId = id, altId = null;
    if (h.tagName === "H3") { altId = id; var sec = h.closest("section.bolum"); bolumId = sec ? sec.id : id; }
    else { bolumId = h.closest("section.bolum").id; }
    if (bolumId === aktifBolum && altId === aktifAlt) return;
    aktifBolum = bolumId; aktifAlt = altId;
    document.querySelectorAll("nav.toc a.aktif").forEach(function (a) { a.classList.remove("aktif"); });
    document.querySelectorAll("nav.toc li.acik").forEach(function (li) { li.classList.remove("acik"); });
    (linkler[bolumId] || []).forEach(function (a) { a.classList.add("aktif"); var li = a.closest("li.toc-bolum"); if (li) li.classList.add("acik"); });
    if (altId) (linkler[altId] || []).forEach(function (a) { a.classList.add("aktif"); });
    var ilk = (linkler[altId || bolumId] || [])[0];
    if (ilk && ilk.scrollIntoView && innerWidth > 960) ilk.scrollIntoView({ block: "nearest" });
  }
  var sonToc = 0;
  function tocGuncelle() {
    var esik = innerHeight * 0.35, aday = null;
    for (var i = 0; i < basliklar.length; i++) { if (basliklar[i].getBoundingClientRect().top <= esik) aday = basliklar[i].id; else break; }
    if (!aday && basliklar.length) aday = basliklar[0].id;
    if (aday) vurgula(aday);
  }
  addEventListener("scroll", function () {
    var t = Date.now();
    if (t - sonToc > 80) { sonToc = t; tocGuncelle(); }
    else { clearTimeout(tocGuncelle._z); tocGuncelle._z = setTimeout(tocGuncelle, 100); }
  }, { passive: true });
  addEventListener("resize", tocGuncelle);

  // baskı: tüm <details> açılsın
  var acilanlar = [];
  addEventListener("beforeprint", function () { acilanlar = []; document.querySelectorAll("details:not([open])").forEach(function (d) { d.open = true; acilanlar.push(d); }); });
  addEventListener("afterprint", function () { acilanlar.forEach(function (d) { d.open = false; }); });

  // widget'lar
  if (window.WK) WK.baslat();
  tocGuncelle();
})();
