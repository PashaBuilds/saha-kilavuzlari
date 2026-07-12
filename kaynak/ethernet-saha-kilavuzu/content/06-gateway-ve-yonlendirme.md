# Bölüm 6 — Gateway ve Yönlendirme

Bölüm 5'in kararını hatırla: hedef uzaksa paket **default gateway**'e
gider. Peki gateway tam olarak ne yapar, stack onu nereden bilir ve paket
oradan sonra dünyayı nasıl dolaşır? Bu bölümde routing table (yönlendirme
tablosu) okumayı, kılavuzun en kritik cümlelerinden birini ("IP hedefi
uzak, MAC hedefi gateway") ve TTL/traceroute ikilisini öğreneceksin.

## Default gateway: ağın çıkış kapısı

**Default gateway**, senin subnet'inde oturan ve "benim bilmediğim her
yeri bilen" router'ın adresidir — tipik olarak `192.168.1.1` gibi ağın ilk
adresi (gelenek; zorunluluk değil). "Default" (varsayılan) kelimesi
anlamlıdır: daha spesifik bir kural yoksa *her şey* oraya gider.

{{svg:sema-09-topoloji.svg|Tipik lab/ev topolojisi: cihazlar switch üzerinden aynı L2 ağını paylaşır; subnet dışına çıkan her paket router'ın LAN bacağına (default gateway) teslim edilir. Router'ın WAN bacağı başka bir ağdır — internet oradan başlar.}}

Topolojide iki şeye dikkat et. Birincisi, switch'in IP'si yok: o L2'de
frame taşır, IP dünyasının oyuncusu değil. İkincisi, router'ın *iki* adresi
var: LAN bacağı (`192.168.1.1`) senin subnet'inde bir komşu; WAN bacağı ise
bambaşka bir ağın üyesi. Router tam da bu yüzden yönlendirebilir: birden
çok ağda aynı anda oturur.

## Kritik kavrayış: IP hedefi uzak, MAC hedefi gateway

Uzak bir hedefe — diyelim `172.217.17.14` (bir Google sunucusu) — paket
gönderirken oluşan frame'i inceleyelim:

| Alan | Değer | Not |
|---|---|---|
| Hedef IP | `172.217.17.14` | **uçtan uca hedef — hiç değişmez** |
| Kaynak IP | `192.168.1.20` | senin adresin (NAT'a kadar — Bölüm 12) |
| Hedef MAC | `router'ın LAN MAC'i` | **yalnızca bu segmentteki ilk durak** |
| Kaynak MAC | `senin kartının MAC'i` | |

Zarf metaforuyla: IP adresi zarfın üstündeki nihai adres, MAC ise zarfı
şu an elden ele verdiğin kişidir. Router paketi alır, IP header'ına bakar,
kendi routing table'ından sonraki adımı (next hop) bulur ve paketi **yeni
bir frame'e** sarar: bu kez kaynak MAC router'ın çıkış bacağı, hedef MAC
bir sonraki router'dır. Yol boyunca her atlamada (hop) frame yeniden
doğar, IP paketi aynı kalır. Bölüm 1'de söz verdiğimiz cümle böylece
yerine oturdu.

Bunun pratikteki izdüşümü: Wireshark'ta internete giden trafiğine bak —
*bütün* uzak hedeflerin frame'lerinde hedef MAC aynıdır: gateway'in MAC'i.
Farklı IP'ler, tek MAC. Şaşırtıcı değil; tanımın kendisi.

## Routing table okumak

Stack'in "yerel mi, gateway'e mi, hangi arabirimden mi" kararlarının tümü
**routing table**'da yazılıdır. Görmek için:

```text
Windows:  route print          (IPv4 Route Table bölümüne bak)
Linux:    ip route
```

Tipik bir Linux çıktısı ve okunuşu:

```text
default via 192.168.1.1 dev eth0            ← bilinmeyen her şey gateway'e
192.168.1.0/24 dev eth0 src 192.168.1.20    ← kendi subnet'im: doğrudan gönder
```

Kural seçimi **longest prefix match** iledir: hedefe uyan en *spesifik*
(prefix'i en uzun) satır kazanır. `192.168.1.55` hem `default`'a (/0) hem
`192.168.1.0/24`'e uyar; /24 daha uzun olduğu için doğrudan gönderilir.
Windows'ta aynı mantık, tablo biraz daha kalabalıktır (`0.0.0.0` satırı =
default).

İki klasik hata mesajını ayırt et: **"Network unreachable"** — routing
table'da hedefe uyan *hiçbir* satır yok (gateway tanımsız); paket kabloya
hiç çıkmadı. **"Request timed out"** — rota var, paket gitti, ama cevap
gelmedi; sorun yolda ya da karşıda. İlki senin konfigürasyonun, ikincisi
ağın veya hedefin derdidir.

:::tuzak Gömülü kartta gateway'i boş bırakmak
Lab'da kart yalnız PC'yle konuşuyorsa gateway'siz yaşar — ikisi aynı
subnet'te olduğu sürece kimse gateway'i sormaz. Sonra kart kurumsal ağa
taşınır, NTP/log sunucusu başka subnet'tedir ve "kart interneti olan ağda
ama sunucuya ulaşamıyor" arızası doğar: stack, uzak hedefe giden paketi
teslim edecek kapı bulamaz. lwIP'te `netif` yapısına gateway'i vermeyi
unutmak bu arızanın gömülü versiyonudur. Kural: kart subnet dışına tek
paket bile gönderecekse gateway tanımlı olmalı.
:::

## TTL ve traceroute: yolun röntgeni

IP header'ında **TTL** (Time To Live) alanı vardır: pakete başlangıçta bir
sayı yazılır (tipik 64 ya da 128), her router paketi iletirken **1
azaltır**. Sıfıra düşerse router paketi atar ve göndericiye ICMP ile
"Time Exceeded" (süre doldu) haber verir. Amaç, yönlendirme halkaya
girerse (A→B→A→B...) paketin sonsuza dek dönmesini engellemektir.

**traceroute** bu mekanizmayı zekice suistimal eder: hedefe önce TTL=1
ile paket yollar — ilk router düşürür ve kimliğini açık eder; sonra TTL=2 —
ikinci router görünür; böyle böyle hedefe kadar tüm yol haritalanır:

```text
Windows:  tracert 8.8.8.8
Linux:    traceroute 8.8.8.8

  1    <1 ms   192.168.1.1        ← kendi gateway'in
  2    12 ms   85.102.0.1         ← ISS'in ilk router'ı
  3    ...
  8    12 ms   8.8.8.8            ← hedef
```

İlk satır her zaman gateway'indir — değilse routing'inde bir tuhaflık var
demektir. Bir de yan bilgi: ping çıktısındaki TTL değerinden karşı tarafın
kaç hop uzakta olduğunu kestirebilirsin (128 - görülen TTL ≈ hop sayısı;
Linux kökenliler 64'ten, Windows 128'den başlar).

:::saha-notu Teşhisin altın sırası
Bağlantı derdinde ping sırası şudur: önce `127.0.0.1` (stack ayakta mı) →
kendi IP'n (arabirim ayakta mı) → **gateway** (yerel ağ + switch + kablo
tamam mı) → uzak bir IP, mesela `8.8.8.8` (yönlendirme/internet tamam mı) →
son olarak isimle `ping google.com` (DNS tamam mı — Bölüm 10). Hangi
adımda kırıldıysa arıza o katmandadır. Bölüm 16'daki karar ağacının
omurgası bu sıradır.
:::

:::analoji Gateway: sitenin güvenlik kulübesi
Site içi zarfları kapı kapı kendin dağıtırsın (yerel, ARP). Şehir dışına
gidecek her zarfı kulübeye bırakırsın; oradaki görevli hangi kargo
şirketine, hangi aktarma merkezine vereceğini bilir (routing table).
Zarfın üstündeki alıcı adresi hiç değişmez ama zarfı elinde tutan kişi
her aktarmada değişir — IP sabit, MAC her hop'ta yeni.
:::

:::ozet
- Default gateway, subnet'inin çıkış kapısıdır; uzak hedefe giden her
  paket ona teslim edilir.
- Frame'de: hedef IP uçtan uca sabit, hedef MAC yalnızca bu segmentteki
  ilk durak (gateway). Her hop'ta frame yenilenir.
- Routing table `route print` / `ip route` ile okunur; en uzun prefix
  kazanır; `default` satırı gateway'i gösterir.
- "Network unreachable" = rota yok (senin ayarın); "timeout" = rota var,
  cevap yok (yol/hedef).
- TTL her hop'ta 1 azalır; traceroute bunu kullanarak yolu haritalar;
  ilk hop daima gateway'in olmalı.
:::
