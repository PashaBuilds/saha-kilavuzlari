/* W-04 — Kaskad NF / kazanç / hassasiyet hesaplayıcı
   Kontroller: blok listesi (ekle / çıkar / yukarı-aşağı / kazanç / NF), LNA öncesi kayıp, ek sistem payı,
               bant genişliği, gereken SNR, giriş seviyesi; "LNA'yı sona al" düğmesi
   Çıktı: Friis toplam NF, sistem NF (bütçe), gürültü tabanı, MDS, SNR giriş/çıkış, ADC tepe payı; canlı seviye diyagramı
   Hesap: DSP.friis, DSP.gurultuTabaniDbm, DSP.hassasiyetDbm. Blok listesi w.param.bloklar'da JSON metni olarak tutulur
   (preset'ler değişmez kalsın diye). */
WK.kaydet("w04", function (w) {
  var S = w.S;
  var kaskRef = S.on_uc && S.on_uc.kaskad ? S.on_uc.kaskad : [
    { ad: "Limiter", kazanc_db: -0.5, nf_db: 0.5 }, { ad: "LNA", kazanc_db: 20, nf_db: 2 }, { ad: "Preselector", kazanc_db: -2, nf_db: 2 },
    { ad: "Mixer", kazanc_db: -7, nf_db: 7 }, { ad: "IF filtre", kazanc_db: -3, nf_db: 3 }, { ad: "IF yükselteç", kazanc_db: 32, nf_db: 4 }, { ad: "AAF + sürücü", kazanc_db: 0.5, nf_db: 6 }];
  var bwRef = S.ddc ? S.ddc.cikis_bant_mhz * 2e6 : 300e6;
  var snrRef = S.tespit ? S.tespit.tespit_snr_db : 15;
  var girisRef = S.sinyal ? S.sinyal.seviye_dbm_giris : -60;
  var fsDbm = S.adc ? S.adc.tam_olcek_dbm : 4;
  var nfButce = S.on_uc ? S.on_uc.nf_toplam_db : 6;
  var refJson = JSON.stringify(kaskRef);

  function lnaSona(liste) {
    var l = liste.slice(), i = -1;
    for (var k = 0; k < l.length; k++) if (/LNA/i.test(l[k].ad)) { i = k; break; }
    if (i >= 0) { var b = l.splice(i, 1)[0]; l.push(b); }
    return l;
  }
  function lnasiz(liste) { return liste.filter(function (b) { return !/LNA/i.test(b.ad); }); }

  WK.kaydirici(w, { ad: "bw", etiket: "gürültü bant genişliği B", min: 1e5, max: 4e9, deger: bwRef, log: true, olcek: 1e6, birim: "MHz", hane: 2 });
  WK.kaydirici(w, { ad: "snr", etiket: "gereken tespit SNR'ı", min: 0, max: 30, adim: 0.5, deger: snrRef, birim: "dB", hane: 1 });
  WK.kaydirici(w, { ad: "giris", etiket: "giriş sinyali (anten)", min: -130, max: 0, adim: 1, deger: girisRef, birim: "dBm", hane: 0 });
  var kapat = WK.grup(w, "Bütçe kalemleri (Friis dışı)");
  WK.kaydirici(w, { ad: "onKayip", etiket: "LNA öncesi kablo/konektör kaybı", min: 0, max: 4, adim: 0.1, deger: 0, birim: "dB", hane: 1 });
  WK.kaydirici(w, { ad: "pay", etiket: "ADC eşdeğer gürültüsü + sıcaklık/üretim payı", min: 0, max: 4, adim: 0.1, deger: 0, birim: "dB", hane: 1 });
  kapat();

  // ---- blok düzenleyici (özel kontrol)
  var kapat2 = WK.grup(w, "Kaskad blokları (sıra = sinyal yönü)");
  var tablo = WK.el("div", { "class": "w-satir", style: "display:block" });
  w.kontrol.appendChild(tablo);
  WK.dugme(w, "+ blok ekle", function () { var l = oku(); l.push({ ad: "Yeni blok", kazanc_db: 0, nf_db: 3 }); yazParam(l); });
  WK.dugme(w, "LNA'yı sona al", function () { yazParam(lnaSona(oku())); });
  WK.dugme(w, "LNA'yı çıkar", function () { yazParam(lnasiz(oku())); });
  kapat2();
  w.param.bloklar = refJson;

  function oku() { try { return JSON.parse(w.param.bloklar || "[]"); } catch (e) { return []; } }
  function yazParam(l) { w.param.bloklar = JSON.stringify(l); kurTablo(); w.degisti("bloklar"); }
  function kurTablo() {
    tablo.innerHTML = "";
    var l = oku();
    var bas = WK.el("div", { style: "display:grid;grid-template-columns:1.6fr 1fr 1fr auto auto auto;gap:4px;align-items:center;font-size:11px" }, [
      WK.el("span", { "class": "w-etk", text: "blok" }), WK.el("span", { "class": "w-etk", text: "G (dB)" }), WK.el("span", { "class": "w-etk", text: "NF (dB)" }),
      WK.el("span", { text: "" }), WK.el("span", { text: "" }), WK.el("span", { text: "" })]);
    tablo.appendChild(bas);
    l.forEach(function (b, i) {
      var ad = WK.el("input", { type: "text", value: b.ad, "aria-label": "blok adı " + (i + 1), style: "min-width:0" });
      var g = WK.el("input", { type: "number", step: "0.5", value: b.kazanc_db, "aria-label": "kazanç " + b.ad, style: "min-width:0" });
      var nf = WK.el("input", { type: "number", step: "0.5", min: "0", value: b.nf_db, "aria-label": "gürültü şekli " + b.ad, style: "min-width:0" });
      var yukari = WK.el("button", { type: "button", "class": "w-dugme", text: "↑", title: "öne al", "aria-label": b.ad + " öne al" });
      var asagi = WK.el("button", { type: "button", "class": "w-dugme", text: "↓", title: "arkaya al", "aria-label": b.ad + " arkaya al" });
      var sil = WK.el("button", { type: "button", "class": "w-dugme", text: "✕", title: "çıkar", "aria-label": b.ad + " çıkar" });
      ad.addEventListener("change", function () { var l2 = oku(); l2[i].ad = ad.value; w.param.bloklar = JSON.stringify(l2); w.degisti("bloklar"); });
      g.addEventListener("change", function () { var l2 = oku(); l2[i].kazanc_db = +g.value || 0; w.param.bloklar = JSON.stringify(l2); w.degisti("bloklar"); });
      nf.addEventListener("change", function () { var l2 = oku(); l2[i].nf_db = Math.max(0, +nf.value || 0); w.param.bloklar = JSON.stringify(l2); w.degisti("bloklar"); });
      yukari.addEventListener("click", function () { if (i === 0) return; var l2 = oku(); var t = l2[i - 1]; l2[i - 1] = l2[i]; l2[i] = t; yazParam(l2); });
      asagi.addEventListener("click", function () { var l2 = oku(); if (i >= l2.length - 1) return; var t = l2[i + 1]; l2[i + 1] = l2[i]; l2[i] = t; yazParam(l2); });
      sil.addEventListener("click", function () { var l2 = oku(); l2.splice(i, 1); yazParam(l2); });
      var satir = WK.el("div", { style: "display:grid;grid-template-columns:1.6fr 1fr 1fr auto auto auto;gap:4px;align-items:center" }, [ad, g, nf, yukari, asagi, sil]);
      tablo.appendChild(satir);
    });
  }
  var sonJson = null;
  w._gosterenler.push(function () { if (w.param.bloklar !== sonJson) { sonJson = w.param.bloklar; kurTablo(); } });
  kurTablo(); sonJson = w.param.bloklar;

  var seviye = WK.panel(w, 300), katki = WK.panel(w, 150);

  function ciz() {
    var p = w.param;
    var bloklar = oku();
    var zincir = bloklar.slice();
    if (p.onKayip > 0) zincir.unshift({ ad: "Kablo/konektör", kazanc_db: -p.onKayip, nf_db: p.onKayip });
    var fr = zincir.length ? DSP.friis(zincir) : { nf_db: 0, kazanc_db: 0, adimlar: [] };
    var frBlok = bloklar.length ? DSP.friis(bloklar) : { nf_db: 0, kazanc_db: 0, adimlar: [] };
    var nfSistem = fr.nf_db + p.pay;
    var taban = DSP.gurultuTabaniDbm(p.bw, nfSistem);
    var mds = DSP.hassasiyetDbm(p.bw, nfSistem, p.snr);
    var n0 = DSP.gurultuTabaniDbm(p.bw, 0);
    var sev = DSP.seviyeDiyagrami(zincir, p.giris, p.bw);
    var cikis = sev[sev.length - 1];
    // her bloğun Friis katkısı (lineer, giriş-referanslı)
    var katkilar = [], G = 1, F = 0;
    for (var i = 0; i < zincir.length; i++) {
      var f = DSP.lin10(zincir[i].nf_db), g = DSP.lin10(zincir[i].kazanc_db);
      var k = i === 0 ? f : (f - 1) / G;
      katkilar.push(k); F += k; G *= g;
    }
    // --- seviye diyagramı
    WK.temizle(seviye);
    var n = sev.length;
    var ymin = Math.min(-120, Math.floor((n0 - 5) / 10) * 10), ymax = Math.max(10, Math.ceil((Math.max(cikis.sinyal, fsDbm) + 8) / 10) * 10);
    var gs = WK.grafik(seviye, { W: 640, H: 300, xmin: -0.5, xmax: n - 0.5, ymin: ymin, ymax: ymax, kenar: { sol: 52, sag: 14, ust: 22, alt: 46 } });
    var xt = []; for (i = 0; i < n; i++) xt.push(i);
    gs.eksenler({ xTik: xt, yAdet: 7, yAd: "dBm", baslik: "Seviye diyagramı — sinyal (mavi) ve gürültü (gri), B = " + WK.fmtHz(p.bw),
                  xFmt: function (v) { var a = sev[v] ? sev[v].ad : ""; return a.length > 9 ? a.slice(0, 8) + "…" : a; } });
    // gürültü dolgusu
    var d = "M" + gs.px(-0.5) + " " + gs.y0;
    for (i = 0; i < n; i++) d += "L" + gs.px(i - 0.5) + " " + gs.py(sev[i].gurultu) + "L" + gs.px(i + 0.5) + " " + gs.py(sev[i].gurultu);
    d += "L" + gs.px(n - 0.5) + " " + gs.y0 + "Z";
    gs.ekle("path", { d: d, "class": "w-dolgu-gurultu" });
    var ds = "";
    for (i = 0; i < n; i++) ds += (i ? "L" : "M") + gs.px(i - 0.5) + " " + gs.py(sev[i].sinyal) + "L" + gs.px(i + 0.5) + " " + gs.py(sev[i].sinyal);
    gs.ekle("path", { d: ds, "class": "w-cizgi-sinyal", "stroke-width": 2.2 });
    for (i = 0; i < n; i++) {
      gs.metin(gs.px(i), gs.py(sev[i].sinyal) - 6, sev[i].sinyal.toFixed(1), "w-mono", "middle");
      gs.metin(gs.px(i), gs.py(sev[i].gurultu) + 12, sev[i].gurultu.toFixed(1), "w-etiket", "middle");
    }
    gs.yatay(fsDbm, "w-cizgi-altin", "ADC tam ölçek " + fsDbm + " dBm");
    var snrIn = sev[0].sinyal - sev[0].gurultu, snrOut = cikis.sinyal - cikis.gurultu;
    gs.metin(gs.px(0) - 4, gs.y1 + 14, "SNR giriş " + snrIn.toFixed(1) + " dB", "w-not");
    gs.metin(gs.x1 - 4, gs.y1 + 28, "SNR çıkış " + snrOut.toFixed(1) + " dB → kayıp = NF = " + (snrIn - snrOut).toFixed(2) + " dB", "w-not", "end");
    // --- katkı çubukları
    WK.temizle(katki);
    var gk = WK.grafik(katki, { W: 640, H: 150, xmin: -0.5, xmax: Math.max(1, zincir.length) - 0.5, ymin: 0, ymax: 1, kenar: { sol: 52, sag: 14, ust: 22, alt: 30 } });
    var xt2 = []; for (i = 0; i < zincir.length; i++) xt2.push(i);
    gk.eksenler({ xTik: xt2, yAdet: 2, yAd: "pay", baslik: "Her bloğun toplam gürültü faktörüne katkısı (Friis terimleri, pay olarak)",
                  xFmt: function (v) { var a = zincir[v] ? zincir[v].ad : ""; return a.length > 9 ? a.slice(0, 8) + "…" : a; }, yFmt: function (v) { return (v * 100).toFixed(0) + "%"; } });
    var enB = -1, enBv = 0;
    for (i = 0; i < zincir.length; i++) {
      var pay = katkilar[i] / Math.max(F, 1e-12);
      if (i > 0 && katkilar[i] > enBv) { enBv = katkilar[i]; enB = i; }
      gk.ekle("rect", { x: gk.px(i - 0.35), y: gk.py(pay), width: gk.px(i + 0.35) - gk.px(i - 0.35), height: gk.py(0) - gk.py(pay), "class": /LNA/i.test(zincir[i].ad) ? "w-dolgu-yesil" : "w-dolgu-kirmizi" });
      gk.metin(gk.px(i), gk.py(pay) - 4, (pay * 100).toFixed(0) + "%", "w-etiket", "middle");
    }
    // sonuçlar
    var lnaIdx = -1; for (i = 0; i < bloklar.length; i++) if (/LNA/i.test(bloklar[i].ad)) { lnaIdx = i; break; }
    var sonuc = {
      "Friis NF (bloklar)": frBlok.nf_db.toFixed(2) + " dB",
      "+ LNA öncesi kayıp": p.onKayip > 0 ? fr.nf_db.toFixed(2) + " dB (kayıp doğrudan eklenir: +" + (fr.nf_db - frBlok.nf_db).toFixed(2) + ")" : "0 → " + fr.nf_db.toFixed(2) + " dB",
      "sistem NF (+pay)": (nfSistem > nfButce + 0.05 ? "!" : "") + nfSistem.toFixed(2) + " dB (bütçe " + nfButce + " dB)",
      "toplam kazanç": fr.kazanc_db.toFixed(1) + " dB",
      "gürültü tabanı": taban.toFixed(1) + " dBm = −174 + " + DSP.db10(p.bw).toFixed(1) + " + " + nfSistem.toFixed(2),
      "MDS (taban + SNR)": mds.toFixed(1) + " dBm",
      "giriş sinyali": p.giris + " dBm → " + (p.giris >= mds ? "+tespit edilir (" + (p.giris - mds).toFixed(1) + " dB pay)" : "!MDS'in " + (mds - p.giris).toFixed(1) + " dB altında"),
      "ADC tepe payı": (cikis.sinyal > fsDbm ? "!" : "") + (fsDbm - cikis.sinyal).toFixed(1) + " dB (çıkış " + cikis.sinyal.toFixed(1) + " dBm)"
    };
    if (enB >= 0) sonuc["LNA sonrası en büyük katkı"] = zincir[enB].ad + " (%" + (100 * katkilar[enB] / F).toFixed(0) + ")";
    if (lnaIdx > 0 && bloklar.slice(0, lnaIdx).some(function (b) { return b.kazanc_db < -1; })) sonuc["uyarı"] = "!LNA'nın önünde kayıp var — her dB doğrudan NF'e eklenir";
    if (lnaIdx < 0) sonuc["uyarı"] = "!zincirde LNA yok — mixer/kayıplar NF'i belirler";
    WK.sonucYaz(w, sonuc);
  }
  return {
    ciz: ciz,
    presetler: [
      { ad: "Referans senaryo", param: { bloklar: refJson, bw: bwRef, snr: snrRef, giris: girisRef, onKayip: 0, pay: 0 } },
      { ad: "Sistem bütçesi (6 dB)", param: { bloklar: refJson, bw: bwRef, snr: snrRef, giris: girisRef, onKayip: 1.0, pay: 1.55 } },
      { ad: "LNA sonda", param: { bloklar: JSON.stringify(lnaSona(kaskRef)), bw: bwRef, snr: snrRef, giris: girisRef, onKayip: 0, pay: 0 } },
      { ad: "LNA yok", param: { bloklar: JSON.stringify(lnasiz(kaskRef)), bw: bwRef, snr: snrRef, giris: girisRef, onKayip: 0, pay: 0 } },
      { ad: "Dar bant (2 MHz)", param: { bloklar: refJson, bw: 2e6, snr: snrRef, giris: girisRef, onKayip: 0, pay: 0 } },
      { ad: "Zayıf sinyal (−75 dBm)", param: { bloklar: refJson, bw: bwRef, snr: snrRef, giris: -75, onKayip: 0, pay: 0 } }
    ]
  };
});
