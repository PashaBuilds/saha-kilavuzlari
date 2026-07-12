# Bölüm 8 — Yazılım Katmanı: Motorlar ve Arayüzler

Donanım ve model kavramları tamam; sıra makineyle model arasındaki yazılıma
geldi. İyi haber: bu katman, ekosistemin en olgun tarafıdır. Birkaç araç var,
hepsi bedava, hepsi birbirine benzer bir arayüz sunar ve bölümün sonunda
birini kurup ilk API isteğini atmış olacaksın.

## Katman haritası

{{svg:16-yazilim-katmanlari.svg|Yazılım yığını: model dosyası, onu çalıştıran motor, motoru saran çalıştırıcı, dışarı açılan OpenAI-uyumlu API ve o API'ye bağlanan istemciler.|wide}}

Katmanları tek tek adlandıralım:

- **llama.cpp** — ekosistemin temeli. C/C++ ile yazılmış, her donanımda
  (NVIDIA, AMD, Apple, Intel, çıplak CPU) çalışan çıkarım motoru; GGUF
  formatının (Bölüm 4) evi. Ollama ve LM Studio dahil pek çok araç altta
  bunu (ya da türevini) kullanır. Doğrudan da kullanılabilir: `llama-server`
  komutu, yerleşik web arayüzü olan hafif bir sunucu açar.
- **Ollama** — kolay başlangıcın standardı. Tek komutla kurulum, tek komutla
  model indirme/çalıştırma, arka planda hep hazır bir API. Docker'ın LLM
  dünyasındaki karşılığı gibidir: modeller imaj gibi çekilir, sürümlenir.
- **LM Studio** — GUI ile keşif. Model arama/indirme, quant seçimi, context
  ayarı, sohbet ve sunucu — hepsi görsel arayüzde. Terminalden ürkenlerin
  ve "hangi quant sığar?" sorusunu görerek çözmek isteyenlerin aracı.
- **MLX** — Apple'ın kendi makine öğrenmesi çatısı. Apple Silicon'da
  llama.cpp'den çoğu zaman %5-15 hızlıdır ve unified memory'yi en iyi o
  kullanır; LM Studio ve güncel Ollama sürümleri Mac'te MLX motorunu
  otomatik seçebiliyor.
- **vLLM / SGLang** — sunucu sınıfı. Çok kullanıcılı, batch'li (Bölüm 7),
  yüksek verimli servis motorları. Ailene/ekibine sunucu kuracaksan
  (Bölüm 12) adres bunlardır; tek kullanıcılı günlük işte fazla gelir.

Hangisi kime? **Yeni başlayan:** Ollama (bu bölümde kuracağız) ya da GUI
istiyorsa LM Studio. **Mac'çi:** LM Studio/Ollama (MLX motorlu). **Kurcalamacı:**
llama.cpp'nin kendisi. **Sunucu kuran:** vLLM/SGLang.

## Ortak payda: OpenAI-uyumlu API

Bu araçların hepsi aynı dili konuşur: **OpenAI-uyumlu HTTP API.** OpenAI'ın
API şeması fiilî standart hâline geldiği için her motor, `/v1/chat/completions`
biçimindeki uçları kendi makinende sunar. Sonuç muazzam bir pratiklik:
OpenAI/ChatGPT API'siyle çalışan **her** kütüphane, editör eklentisi ve
uygulama, iki satır ayarla (adres + model adı) senin lokal modelinle çalışır.
Yerleşik adresler: Ollama `localhost:11434`, LM Studio `localhost:1234`,
llama-server `localhost:8080`.

## Adım adım: ilk modelin

Ollama ile sıfırdan çalışan API'ye gidelim. **1) Kurulum:**

```bash
# macOS
brew install ollama          # ya da ollama.com'dan uygulamayı indir

# Windows (PowerShell)
winget install Ollama.Ollama # ya da ollama.com'dan kurulum dosyası
```

**2) Model indir ve çalıştır** (iki iş tek komutta — model yoksa önce iner):

```bash
ollama run gpt-oss:20b
```

Bu örnek (~13 GB) 16 GB+ belleğe uygun; daha mütevazı makinede
`ollama run phi4-mini` (~2,5 GB) ile aynı akışı yaşayabilirsin. Komut
bittiğinde terminalde sohbet açılır; `/bye` ile çıkılır.

{{svg:17-ollama-akisi.svg|Ollama akışı: pull modeli blob deposuna indirir (bir kez), run belleğe yükler; arka plandaki sunucu localhost:11434'te hem CLI'ya hem API istemcilerine hizmet verir.|wide}}

**3) API'ye ilk istek.** Sohbet penceresi hoş ama asıl güç API'de:

```bash
curl http://localhost:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-oss:20b",
    "messages": [
      {"role": "user", "content": "Merhaba! Tek cümleyle kendini tanıt."}
    ]
  }'
```

(Windows PowerShell'de `curl.exe` yaz ve tek satırda kullan; ya da isteği
birazdan gelen Python örneğiyle at.)

**4) Aynı istek Python'dan** — resmî `openai` istemcisiyle
(`pip install openai`):

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:11434/v1",  # lokal Ollama
    api_key="ollama",                      # zorunlu alan; içeriği önemsiz
)

cevap = client.chat.completions.create(
    model="gpt-oss:20b",
    messages=[
        {"role": "system", "content": "Kısa ve net cevap ver."},
        {"role": "user", "content": "Quantization'ı tek cümleyle anlat."},
    ],
)
print(cevap.choices[0].message.content)
```

Bu dört adım, kılavuzun kalan her şeyinin zeminidir: Bölüm 12'deki bütün
senaryolar bu API'nin üzerine kurulur.

:::saha-notu Ollama etiketlerinde quant seçimi
`ollama pull qwen3.6` gibi çıplak bir isim, deponun **varsayılan** etiketini
çeker — bu genellikle Q4 civarı bir quant'tır ama hangisi olduğu modele göre
değişir. Model sayfasındaki "tags" listesinde aynı modelin `:27b-q8_0`,
`:27b-q4_K_M` gibi varyantları bulunur; Bölüm 4'teki bilinçle etiketi kendin
seç. `ollama show <model>` komutu yüklü modelin parametre sayısını, quant'ını
ve context'ini gösterir — "elimde tam olarak ne var?" sorusunun cevabı.
:::

:::tuzak
Bölüm 7'nin uyarısını kurulum gününde hatırla: motorun varsayılan context'i
modelinkinden küçüktür. Ollama'da küçük VRAM'li makinede varsayılan 4K'dır;
uzun doküman işleri için `OLLAMA_CONTEXT_LENGTH=32768` gibi bir ayar
(ya da LM Studio'da yükleme ekranındaki context alanı) gerekir. "Model
unutkan çıktı" şikâyetlerinin yarısı bu tek ayardır.
:::

## Sohbet arayüzleri: kendi ChatGPT ekranın

API'nin üstüne bir sohbet arayüzü koymak istersen iki isim öne çıkar.
**Open WebUI:** tarayıcıda çalışan, çok kullanıcılı, doküman yükleme ve
basit RAG yetenekli arayüz; Ollama'yı otomatik bulur, ev sunucusu
senaryosunun (Bölüm 12) standart ön yüzüdür. **Jan:** tek tıkla kurulan
masaüstü uygulaması; motor + arayüz bir arada, "hiç terminal görmeden
lokal LLM" isteyenlere uygun. İkisi de açık kaynaklıdır ve OpenAI-uyumlu
her motorla konuşur.

:::derin-dalis 2026 motor hızlandırıcıları: MTP ve spekülatif decoding
Bölüm 5'in formülü bir tavan çizer: her token, aktif ağırlıkların bir kez
okunmasına mal olur. Ama işlemci o okuma sırasında boş oturuyorsa, aynı
okumayla birden fazla token denenemez mi? **Spekülatif decoding** küçük bir
"taslak model"e birkaç token önerdirir, büyük model tek geçişte hepsini
doğrular; **MTP (multi-token prediction)** ise modelin kendisinin tek adımda
birden çok token üretmesini sağlar — 2026'da llama.cpp'ye giren native MTP
desteği, uyumlu modellerde üretimi 1,4-2 kat hızlandırıyor. Motorlar bunları
giderek otomatik açıyor; senin için pratik sonuç, formül tahminini aşan
token/s değerleri görebileceğindir. Diğer güncel motor lüksleri: llama.cpp
WebUI'nin MCP araç desteği ve dinamik model yükle/boşalt; LM Studio'nun
uzun ajan oturumları için KV checkpointing'i. Ekosistem, aynı donanımdan
her yıl daha çok token sıkıyor.
:::

:::ozet
- Yığın dört katmandır: model dosyası → motor (llama.cpp/MLX/vLLM) →
  çalıştırıcı (Ollama/LM Studio) → OpenAI-uyumlu API → istemciler.
- Seçim rehberi: başlangıç = Ollama; GUI = LM Studio; Mac'te MLX motoru;
  çok kullanıcılı sunucu = vLLM/SGLang.
- Her şey OpenAI-uyumlu API'de buluşur: OpenAI ile çalışan her araç, iki
  satır ayarla lokal modelinle çalışır (`localhost:11434/v1`).
- İlk kurulum dört adımdır: kur → `ollama run` → curl testi → Python istemcisi.
- Etiketle quant'ını bilinçli seç (`ollama show` ile doğrula) ve context
  varsayılanını elle yükselt.
:::
