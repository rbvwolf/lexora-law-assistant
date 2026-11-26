# Uçtan Uca Cevap Süresi Raporu

**Ölçüm tarihi:** 26 Kasım 2026
**Hedef (AGENTS.md):** `p95 < 10 saniye` uçtan uca cevap süresi
**Sonuç:** Sistem hedefin altında (p95 2,1 sn). Groq ücretsiz katmanının hız limitine takılındığında hedef aşılıyordu (p95 38,7 sn); 26 Kasım düzeltmesinden sonra aynı yükte en uzun bekleme 5,7 sn. Kapasitenin asıl sınırı Groq'un günlük token limiti (günde yaklaşık 70-90 soru-cevap).

> Bu rapor Bölüm 3.5 (Değerlendirme ve test) içindir. [EVAL_SUMMARY_30_SCENARIOS.md](EVAL_SUMMARY_30_SCENARIOS.md) içindeki 74 ms'lik p95 değeri **yalnızca retrieval** süresidir; kullanıcının beklediği süre değildir ve "cevap süresi" olarak raporlanmamalıdır.

## Ne ölçüldü

Kullanıcının `POST /api/v1/chat/message` isteğinden cevabı alana kadar geçen süre ölçüldü. Bu süre tüm hattı kapsar: girdi temizleme, PII maskeleme, ChromaDB retrieval, Groq ile niyet sınıflandırma ve Groq ile cevap üretimi veya parametre çıkarma.

| Ayar | Değer |
|---|---|
| Ortam | Production Docker imajı (`backend/Dockerfile`), yerel makinede, `ENVIRONMENT=production` |
| Senaryolar | 30 eval senaryosu (`data/eval/eval_scenarios.json`): 23 soru-cevap, 4 belge üretimi, 3 kapsam dışı |
| LLM | Groq, ücretsiz katman, `GROQ_MODEL_NAME` = `qwen/qwen3.8-27b` |
| Embedding | `intfloat/multilingual-e5-base`, imaja gömülü, 91 madde |
| Araç | `backend/scripts/measure_latency.py --base-url ...` |
| Önbellek | Her ölçüm yeni başlatılmış konteynerde yapıldı, hiçbir cevap önbellekten gelmedi |

İlk istek (cold start) ayrı raporlandı ve yüzdeliklere katılmadı.

## Sonuçlar

| Ölçüm | İstek aralığı | p50 | p95 | Maks. | 10 sn üstü | 30 sn üstü | Groq 429 | Hedef |
|---|---|---|---|---|---|---|---|---|
| A: Limit altında | 20 sn | 1,3 sn | **2,1 sn** | 2,4 sn | 0 / 30 | 0 / 30 | 0 | ✅ Geçti |
| B: Yoğun kullanım | 4 sn | 9,3 sn | **38,7 sn** | 40,7 sn | 15 / 30 | 6 / 30 | 31 / 92 çağrı | ❌ Kaldı |

Niyet bazında p95 (Ölçüm A): soru-cevap 2,1 sn, belge üretimi 1,2 sn, kapsam dışı 0,5 sn. Cold start, yani konteyner açıldıktan sonraki ilk istek: 1,4 sn ile 4,0 sn arası.

Ham veriler: [latency_e2e_delay20s.json](latency_e2e_delay20s.json) (A), [latency_e2e_delay4s.json](latency_e2e_delay4s.json) (B).

## Yorum

- **Sistemin kendi süresi hedefin çok altında.** Hız limitine takılmayan bir kullanımda en yavaş cevap 2,4 saniye sürdü.
- **Ölçüm B'deki gecikmenin tamamı Groq hız limitinden geliyor.** Her sohbet mesajı iki Groq çağrısı yapar (niyet sınıflandırma ve cevap). Mesajlar 4 saniye arayla gelince 92 çağrının 31'i `429 Too Many Requests` aldı ve Groq istemcisi her seferinde yaklaşık 24 saniye bekleyip yeniden denedi. Ölçüm B'deki en hızlı istekler (1-2 sn) Ölçüm A ile aynı aralıkta; aradaki fark yeniden deneme beklemelerinden geliyor.
- **Kullanıcıya etkisi:** Ölçüm B'de 30 isteğin 6'sında kullanıcı 30-41 saniye boyunca hiçbir geri bildirim almadan bekledi. Sohbet ekranının zaman aşımı 60 saniye olduğu için hata görmedi, ama bu bekleme kabul edilebilir değil. Aşağıdaki düzeltme bunu gideriyor.

## Groq ücretsiz katman kapasitesi

Limitler Groq'un cevap başlıklarından ve 429 mesajından okundu (model `qwen/qwen3.8-27b`, 26 Kasım):

| Limit | Değer | Lexora için anlamı |
|---|---|---|
| Dakikada token (TPM) | 8.000 | Dakikada yaklaşık 3 soru-cevap |
| Günde token (TPD) | 200.000 | **Günde yaklaşık 70-90 soru-cevap.** Asıl darboğaz bu. |
| Günde istek (RPD) | 1.000 | Günde yaklaşık 500 mesaj (her mesaj 2 çağrı) |

Mesaj başına ölçülen token kullanımı: soru-cevap 2.200-2.900 (prompt'a giren 5 kanun maddesi bunun büyük kısmı), belge talebi yaklaşık 1.200, niyet sınıflandırma yaklaşık 280.

**Değerlendirilip uygulanmayan seçenek:** LLM'e 5 yerine 3 madde göndermek token kullanımını yaklaşık üçte bir azaltırdı. Ama eval sonuçlarına göre 27 senaryonun 3'ünde doğru madde ilk 3'te değil (ilk 3'te isabet 24/27, ilk 5'te 27/27). Bu senaryolarda model doğru maddeyi hiç görmezdi; kalite kaybı kabul edilmedi.

## Hız limiti yönetimi (26 Kasım düzeltmesi)

Önceden Groq SDK'sı her 429'da Retry-After süresi kadar (yaklaşık 24 sn) istek içinde bekliyordu. Artık:

- 4 saniyeye kadar olan beklemeler istek içinde yapılıyor; kullanıcı fark etmiyor.
- Daha uzun beklemelerde backend hemen `503 LLM_RATE_LIMITED` ve gerçek bekleme süresini dönüyor. Dakika limitinde mesaj saniye cinsinden, günlük limitte dakika cinsinden.
- Sohbet ekranı 30 saniyeye kadar olan beklemeyi geri sayımla gösterip soruyu bir kez otomatik tekrar gönderiyor. Daha uzun beklemede kullanıcıya mesaj gösteriliyor.
- Eval betiği (`run_eval.py`) eskisi gibi sabırla bekliyor.

Aynı yoğun yükte (4 sn arayla 30 mesaj) yeni davranış:

| | Önce | Sonra |
|---|---|---|
| En uzun bekleme | 40,7 sn | 5,7 sn |
| 30 sn'den uzun bekleyen | 6 / 30 | 0 / 30 |
| Hemen "yoğunluk" cevabı alan | 0 | 20 / 30 (6-15 sn sonra tekrar deneme önerisiyle) |
| Başarılı cevapların p95'i | 38,7 sn | 5,7 sn |

Ham veri: [latency_e2e_delay4s_failfast.json](latency_e2e_delay4s_failfast.json). Bu ölçüm, dakika limitinin kapasitenin çok üstünde zorlandığı bir stres testidir; kapasite aynı kaldığı için başarılı cevap sayısı artmaz, yalnızca kimse askıda kalmaz.

## Sınırlar ve öneriler

- Ölçüm yerel makinede yapıldı. Canlı ortamda ağ gecikmesi eklenir. Deploy sonrası aynı araçla tekrar ölçülmelidir ([docs/deploy.md](../docs/deploy.md)).
- **Günlük token limiti eval turlarıyla paylaşılıyor.** 30 senaryoluk bir LLM eval turu ya da bu rapordaki bir ölçüm günlük kotanın üçte biri kadarını harcayabilir. Demo gününde eval ve ölçüm çalıştırılmamalı.
- Gerçek kapasite artışı için seçenekler: Groq Dev Tier (ücretli, limitler çok daha yüksek) ya da Groq konsolunda daha yüksek ücretsiz limitli bir model (eval ile karşılaştırılarak).
