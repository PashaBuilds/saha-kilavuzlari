/* kilavuz.js — theme, TOC highlighting, copy, reading bar, task tracking,
   scroll-reveal, confetti and celebration. No framework.
   localStorage keys: "go-tema", "go-gorevler". */
(function () {
  "use strict";

  var kok = document.documentElement;
  kok.classList.add("js-hazir"); // enable reveal's hidden states

  var azHareket = false;
  try { azHareket = window.matchMedia("(prefers-reduced-motion: reduce)").matches; }
  catch (e) {}

  /* Scroll to target — via window.scrollTo. NOTE: the scroll-behavior:smooth
     in the html renders element.scrollIntoView() ineffective on this page;
     window.scrollTo with an absolute position works reliably. */
  function hedefeKaydir(el, yumusak) {
    if (!el) { return; }
    var y = el.getBoundingClientRect().top + window.scrollY - 60;
    // "instant" (overrides the CSS scroll-behavior:smooth). If it were "auto"
    // it would follow the CSS, start a 40,000px smooth scroll and miss.
    window.scrollTo({ top: y, behavior: (yumusak && !azHareket) ? "smooth" : "instant" });
  }

  /* If there is a hash on load (bookmark / deep link), scroll to the target.
     On a heavy page (25 SVGs) the browser's initial anchor jump misses before
     the layout settles; with load + a short delay we reliably reach the target. */
  function hashaKaydir() {
    if (!location.hash || location.hash.length < 2) { return; }
    try {
      hedefeKaydir(document.getElementById(
        decodeURIComponent(location.hash.slice(1))), false);
    } catch (e) {}
  }
  if (location.hash && location.hash.length > 1) {
    window.addEventListener("load", function () { setTimeout(hashaKaydir, 80); });
    setTimeout(hashaKaydir, 350); // fallback in case load already fired early
  }

  /* ---------- Theme ---------- */
  function temaUygula(tema) {
    if (tema === "acik") { kok.setAttribute("data-tema", "acik"); }
    else { kok.removeAttribute("data-tema"); }
    var g = document.getElementById("tema-gunes");
    var a = document.getElementById("tema-ay");
    if (g && a) {
      g.style.display = tema === "acik" ? "none" : "";
      a.style.display = tema === "acik" ? "" : "none";
    }
  }

  var kayitliTema = null;
  try { kayitliTema = localStorage.getItem("go-tema"); } catch (e) {}
  temaUygula(kayitliTema === "acik" ? "acik" : "koyu");

  var temaDugme = document.getElementById("tema-dugme");
  if (temaDugme) {
    temaDugme.addEventListener("click", function () {
      var yeni = kok.hasAttribute("data-tema") ? "koyu" : "acik";
      temaUygula(yeni);
      try { localStorage.setItem("go-tema", yeni); } catch (e) {}
    });
  }

  /* ---------- Reading progress bar ---------- */
  var okumaBar = document.getElementById("okuma-bar");
  if (okumaBar) {
    var barGuncelle = function () {
      var h = document.documentElement.scrollHeight - window.innerHeight;
      var oran = h > 0 ? (window.scrollY / h) * 100 : 0;
      okumaBar.style.width = oran + "%";
    };
    window.addEventListener("scroll", barGuncelle, { passive: true });
    barGuncelle();
  }

  /* ---------- Code copy ---------- */
  document.addEventListener("click", function (ev) {
    var dugme = ev.target.closest(".kopyala-dugme");
    if (!dugme) { return; }
    var kutu = dugme.closest(".kod-kutu");
    var kod = kutu ? kutu.querySelector("pre code") : null;
    if (!kod) { return; }
    var yaz = function () {
      dugme.classList.add("kopyalandi");
      dugme.textContent = "kopyalandı";
      setTimeout(function () {
        dugme.classList.remove("kopyalandi");
        dugme.textContent = "kopyala";
      }, 1600);
    };
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(kod.textContent).then(yaz, yaz);
    } else {
      var secim = document.createRange();
      secim.selectNodeContents(kod);
      var sec = window.getSelection();
      sec.removeAllRanges(); sec.addRange(secim);
      try { document.execCommand("copy"); } catch (e) {}
      sec.removeAllRanges();
      yaz();
    }
  });

  /* ---------- Scroll-reveal (bulletproof) ----------
     Content must NEVER stay hidden. Hence three safeguards:
     1) With a wide rootMargin the element is revealed ~320px BEFORE it enters
        the viewport, so no opacity:0 content is ever seen during normal scrolling.
     2) A scroll fallback throttled with rAF reveals every element in view if the
        observer skips one for any reason.
     3) After 4 s, whatever is still not revealed is revealed unconditionally (last resort). */
  (function () {
    var secim = "figure.sema, .gorev-karti, .kutu, details.derin-dalis, " +
                ".kod-kutu, .ilerleme-panosu, .tablo-sar, main > section.bolum > h2";
    var ogeler = Array.prototype.slice.call(document.querySelectorAll(secim));
    if (!ogeler.length) { return; }
    ogeler.forEach(function (o) { o.classList.add("reveal"); });
    var kalan = ogeler.slice();

    function ac(o) { o.classList.add("gorunur"); }
    function yakinlariAc() {
      var h = window.innerHeight, pay = 320;
      for (var i = kalan.length - 1; i >= 0; i--) {
        var r = kalan[i].getBoundingClientRect();
        if (r.top < h + pay && r.bottom > -pay) {
          ac(kalan[i]); kalan.splice(i, 1);
        }
      }
    }

    if ("IntersectionObserver" in window) {
      var gozlemci = new IntersectionObserver(function (girdiler, gozc) {
        girdiler.forEach(function (g) {
          if (g.isIntersecting) {
            ac(g.target); gozc.unobserve(g.target);
            var k = kalan.indexOf(g.target); if (k >= 0) { kalan.splice(k, 1); }
          }
        });
      }, { rootMargin: "320px 0px 320px 0px", threshold: 0 });
      ogeler.forEach(function (o) { gozlemci.observe(o); });
    } else {
      // if there is no IO, reveal them all immediately (no animation but visible)
      ogeler.forEach(ac); return;
    }

    // scroll fallback (throttled with rAF)
    var bekliyor = false;
    function scrollTetik() {
      if (bekliyor || !kalan.length) { return; }
      bekliyor = true;
      requestAnimationFrame(function () { bekliyor = false; yakinlariAc(); });
    }
    window.addEventListener("scroll", scrollTetik, { passive: true });
    window.addEventListener("resize", scrollTetik, { passive: true });
    // also trigger on hash/anchor jumps
    window.addEventListener("hashchange", function () {
      setTimeout(yakinlariAc, 30);
    });
    requestAnimationFrame(yakinlariAc);   // first screen
    // last resort: after 4 s reveal whatever remains
    setTimeout(function () { kalan.slice().forEach(ac); kalan.length = 0; }, 4000);
  })();

  /* ---------- TOC active heading highlight ---------- */
  var tocLinkler = Array.prototype.slice.call(
    document.querySelectorAll("nav.toc a[href^='#']"));
  if (tocLinkler.length && "IntersectionObserver" in window) {
    var linkHaritasi = {};
    tocLinkler.forEach(function (a) {
      linkHaritasi[a.getAttribute("href").slice(1)] = a;
    });
    var aktifId = null;
    var gozlemci2 = new IntersectionObserver(function (girdiler) {
      girdiler.forEach(function (g) {
        if (g.isIntersecting) { aktifId = g.target.id; }
      });
      if (aktifId && linkHaritasi[aktifId]) {
        tocLinkler.forEach(function (a) { a.classList.remove("aktif"); });
        linkHaritasi[aktifId].classList.add("aktif");
        var l = linkHaritasi[aktifId];
        var nav = l.closest("nav.toc");
        if (nav) {
          // IMPORTANT: l.scrollIntoView() is NOT USED HERE — to make the element
          // visible it would scroll every scrollable ancestor including the window
          // and pull the page back up. By adjusting only the TOC box's own scrollTop
          // we center the active link within the panel; the window is never affected.
          var ust = l.getBoundingClientRect().top - nav.getBoundingClientRect().top;
          if (ust < 60 || ust > nav.clientHeight - 60) {
            nav.scrollTop += ust - nav.clientHeight / 2;
          }
        }
      }
    }, { rootMargin: "-15% 0px -75% 0px" });
    Object.keys(linkHaritasi).forEach(function (id) {
      var hedef = document.getElementById(id);
      if (hedef) { gozlemci2.observe(hedef); }
    });
  }

  /* ---------- Confetti ---------- */
  var konfetiParcalari = [];
  var konfetiTuval = null, konfetiCtx = null, konfetiAktif = false;

  function konfetiRenkleri() {
    var stil = getComputedStyle(kok);
    return ["--vurgu", "--altin", "--yesil", "--mor", "--kirmizi"]
      .map(function (v) { return (stil.getPropertyValue(v) || "#4DA3FF").trim(); });
  }

  function konfetiTuvalHazirla() {
    if (konfetiTuval) { return; }
    konfetiTuval = document.createElement("canvas");
    konfetiTuval.id = "konfeti-tuval";
    document.body.appendChild(konfetiTuval);
    konfetiCtx = konfetiTuval.getContext("2d");
    var boyutla = function () {
      var dpr = Math.min(window.devicePixelRatio || 1, 2);
      konfetiTuval.width = window.innerWidth * dpr;
      konfetiTuval.height = window.innerHeight * dpr;
      konfetiCtx.setTransform(dpr, 0, 0, dpr, 0, 0);
    };
    boyutla();
    window.addEventListener("resize", boyutla);
  }

  function konfetiPatlat(x, y, adet) {
    if (azHareket) { return; }
    konfetiTuvalHazirla();
    var renkler = konfetiRenkleri();
    adet = adet || 26;
    for (var i = 0; i < adet; i++) {
      var aci = Math.PI * 2 * (i / adet) + (i % 3) * 0.3;
      var hiz = 4 + (i % 5) * 1.6;
      konfetiParcalari.push({
        x: x, y: y,
        vx: Math.cos(aci) * hiz * (0.6 + (i % 4) * 0.18),
        vy: Math.sin(aci) * hiz - 3,
        g: 0.16 + (i % 3) * 0.03,
        boy: 5 + (i % 4) * 2,
        renk: renkler[i % renkler.length],
        donme: (i % 6) * 0.5, dHiz: (i % 5 - 2) * 0.2,
        omur: 1
      });
    }
    if (!konfetiAktif) { konfetiAktif = true; requestAnimationFrame(konfetiDon); }
  }

  function konfetiDon() {
    konfetiCtx.clearRect(0, 0, konfetiTuval.width, konfetiTuval.height);
    for (var i = konfetiParcalari.length - 1; i >= 0; i--) {
      var p = konfetiParcalari[i];
      p.vy += p.g; p.x += p.vx; p.y += p.vy;
      p.vx *= 0.99; p.donme += p.dHiz; p.omur -= 0.008;
      if (p.omur <= 0 || p.y > window.innerHeight + 30) {
        konfetiParcalari.splice(i, 1); continue;
      }
      konfetiCtx.save();
      konfetiCtx.globalAlpha = Math.max(0, Math.min(1, p.omur));
      konfetiCtx.translate(p.x, p.y);
      konfetiCtx.rotate(p.donme);
      konfetiCtx.fillStyle = p.renk;
      konfetiCtx.fillRect(-p.boy / 2, -p.boy / 2, p.boy, p.boy * 0.62);
      konfetiCtx.restore();
    }
    if (konfetiParcalari.length) { requestAnimationFrame(konfetiDon); }
    else { konfetiAktif = false; konfetiCtx.clearRect(0, 0, konfetiTuval.width, konfetiTuval.height); }
  }

  /* ---------- Celebration banner (when all tasks are done) ---------- */
  var kutlamaAfis = null;
  function kutlamaGoster() {
    if (!kutlamaAfis) {
      kutlamaAfis = document.createElement("div");
      kutlamaAfis.className = "kutlama-afis";
      kutlamaAfis.innerHTML =
        '<span class="kutlama-ikon" aria-hidden="true"><svg viewBox="0 0 24 24" ' +
        'fill="none" stroke="currentColor" stroke-width="2.4"><path d="M4 12.5l5 5L20 6"/></svg></span>' +
        '<div class="kutlama-metin"><strong>Yolculuk tamamlandı</strong>' +
        '<span>Bütün görevler tamamlandı. Artık gerçek gömülü işleri üstlenecek donanıma sahipsin. Tebrikler.</span></div>' +
        '<button type="button" class="kutlama-kapat" aria-label="Kapat">&times;</button>';
      document.body.appendChild(kutlamaAfis);
      kutlamaAfis.querySelector(".kutlama-kapat").addEventListener("click", function () {
        kutlamaAfis.classList.remove("gorunur");
      });
    }
    requestAnimationFrame(function () { kutlamaAfis.classList.add("gorunur"); });
    // large confetti from multiple sources
    if (!azHareket) {
      var W = window.innerWidth;
      [0.2, 0.5, 0.8].forEach(function (fx, k) {
        setTimeout(function () { konfetiPatlat(W * fx, window.innerHeight * 0.35, 34); }, k * 180);
      });
    }
  }

  /* ---------- Task tracking (checkbox + panel + counters) ---------- */
  function gorevleriOku() {
    try { return JSON.parse(localStorage.getItem("go-gorevler") || "{}"); }
    catch (e) { return {}; }
  }
  function gorevleriYaz(d) {
    try { localStorage.setItem("go-gorevler", JSON.stringify(d)); } catch (e) {}
  }

  var kutucuklar = Array.prototype.slice.call(
    document.querySelectorAll("input.gorev-kutucuk"));
  var toplamGorev = kutucuklar.length;
  var oncekiTamam = -1;

  function arayuzuGuncelle() {
    var durum = gorevleriOku();
    var tamam = 0;
    var ilkEksikDurak = null;
    kutucuklar.forEach(function (k) {
      var id = k.getAttribute("data-gorev");
      var isaretli = !!durum[id];
      if (isaretli) { tamam += 1; }
      k.checked = isaretli;
      var kart = k.closest(".gorev-karti");
      if (kart) { kart.classList.toggle("tamamlandi", isaretli); }
      var etiket = k.closest(".gorev-tamam");
      if (etiket) {
        var yazi = etiket.querySelector(".gorev-tamam-yazi");
        if (yazi) { yazi.textContent = isaretli ? "Tamamlandı" : "Tamamlandı işaretle"; }
      }
      var tocOge = document.querySelector("nav.toc li[data-gorev='" + id + "']");
      if (tocOge) { tocOge.classList.toggle("tamam", isaretli); }
      var durak = document.querySelector(".durak[data-gorev='" + id + "']");
      if (durak) {
        durak.classList.toggle("tamam", isaretli);
        durak.classList.remove("sirada");
        if (!isaretli && !ilkEksikDurak) { ilkEksikDurak = durak; }
      }
      var parca = document.querySelector(".patika-parca[data-gorev='" + id + "']");
      if (parca) { parca.style.opacity = isaretli ? "1" : "0"; }
    });
    // mark the next (first incomplete) stop
    if (ilkEksikDurak) { ilkEksikDurak.classList.add("sirada"); }

    var sayac = document.getElementById("gorev-sayac");
    if (sayac) { sayac.textContent = tamam + " / " + toplamGorev + " görev"; }
    var oran = toplamGorev ? Math.round((tamam / toplamGorev) * 100) : 0;
    var panoDurum = document.getElementById("pano-durum");
    if (panoDurum) {
      panoDurum.innerHTML = "<span class='oran'>" + tamam + " / " + toplamGorev +
        "</span> görev tamamlandı (%" + oran + ")";
    }
    var panoDolu = document.getElementById("pano-ilerleme-dolu");
    if (panoDolu) { panoDolu.style.width = oran + "%"; }

    // if all tasks have just been completed, celebrate
    if (oncekiTamam !== -1 && tamam === toplamGorev && oncekiTamam < toplamGorev
        && toplamGorev > 0) {
      kutlamaGoster();
    }
    oncekiTamam = tamam;
  }

  kutucuklar.forEach(function (k) {
    k.addEventListener("change", function (ev) {
      var durum = gorevleriOku();
      var id = k.getAttribute("data-gorev");
      if (k.checked) {
        durum[id] = true;
        // confetti from the checkbox position
        var r = k.closest(".gorev-tamam");
        if (r) {
          var b = r.getBoundingClientRect();
          konfetiPatlat(b.left + b.width / 2, b.top + b.height / 2, 24);
        }
      } else { delete durum[id]; }
      gorevleriYaz(durum);
      arayuzuGuncelle();
    });
  });

  Array.prototype.slice.call(document.querySelectorAll(".durak")).forEach(function (d) {
    d.addEventListener("click", function () {
      hedefeKaydir(document.getElementById(d.getAttribute("data-gorev")), true);
    });
  });

  arayuzuGuncelle();
})();
