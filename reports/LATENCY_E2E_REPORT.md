# Uçtan Uca Cevap Süresi Raporu

**Ölçüm tarihi:** 26 Kasım 2026
**Hedef (AGENTS.md):** `p95 < 10 saniye` uçtan uca cevap süresi
**Sonuç:** Sistem hedefin altında (p95 2,1 sn). Groq ücretsiz katmanının hız limitine takılındığında hedef aşılıyor (p95 38,7 sn).

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
- **Kullanıcıya etkisi:** Frontend 30 saniyede zaman aşımına düşer. Ölçüm B'de 30 isteğin 6'sı bu sınırı aştı; kullanıcı bu durumda "Sunucu zamanında cevap vermedi" hatası görür.

## Sınırlar ve öneriler

- Ölçüm yerel makinede yapıldı. Canlı ortamda ağ gecikmesi eklenir. Deploy sonrası aynı araçla tekrar ölçülmelidir ([docs/deploy.md](../docs/deploy.md)).
- Demo sırasında birden fazla kişi aynı anda kullanırsa ücretsiz katman limitine takılınabilir. Demodan hemen önce eval çalıştırılmamalı, çünkü aynı limit paylaşılıyor.
- Kalıcı çözüm seçenekleri: Groq'un ücretli katmanı ya da hız limiti aşıldığında kullanıcıya 24 saniye bekletmek yerine hemen anlaşılır bir "yoğunluk" mesajı dönmek.
