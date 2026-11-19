# Lexora RAG Sistemi — Resmi Değerlendirme Raporu
**30 Senaryo Benchmark Sonuçları**

> Bu doküman rapor ekibi tarafından doğrudan **Bölüm 3.1 (RAG Retrieval Metrikleri)** ve **Bölüm 3.5 (Mentor Doğrulama)** başlıklarına yapıştırılabilir.

---

## Genel Bilgiler

| Alan | Değer |
|---|---|
| Dataset Sürümü | `2.0.0-phase2` |
| Toplam Senaryo | 30 |
| Hukuk Mentor Onaylı | 30 / 30 (%100) |
| Değerlendirme Tarihi | 2026-11-19 |
| Embedding Modeli | `paraphrase-multilingual-mpnet-base-v2` |
| Top-K | 5 |

---

## Bölüm 3.1 — RAG Retrieval Metrikleri

### Özet Metrik Tablosu

| Metrik | Değer | Hedef | Durum |
|---|---|---|---|
| **Hit@5** (en az 1 makale ilk 5'te) | **%100.0** (27/27) | ≥%80 | ✅ GEÇTI |
| **All-Hit@5** (tüm beklenen maddeler) | **%70.37** (19/27) | ≥%60 | ✅ GEÇTI |
| **Hit@1** (ilk sırada doğruluk) | **%59.26** (16/27) | ≥%50 | ✅ GEÇTI |
| **MRR** (Ortalama Karşılıklı Sıralama) | **0.748** | ≥0.70 | ✅ GEÇTI |
| **Ortalama Gecikme** | 462.2 ms* | — | — |
| **p95 Gecikme** | **74.4 ms** | <100 ms | ✅ GEÇTI |

> *İlk sorgu embedding modelini RAM'e yükler (cold-start ~11 s), sonraki sorgular <75 ms'de yanıt verir. p95 hesabına ilk sorgu dahil edilmemiştir.

### Yorum

- **Hit@5 %100** başarısı, sistemin tüm 27 RAG senaryosunda doğru yasal maddeyi ilk 5 sonuç içinde döndürebildiğini göstermektedir. Bu, hukuki danışmanlık akışı için gereken minimum doğruluk eşiğinin üzerindedir.
- **MRR = 0.748**, doğru maddenin ortalama olarak ~1.3. sırada geldiğini ifade eder; bu oran LLM'e gönderilecek bağlamın kalitesini doğrudan etkiler ve kabul edilebilir bir değerdedir.
- **p95 gecikme 74.4 ms**, AGENTS.md'de tanımlanan `p95 < 10 saniye` SLA hedefinin çok altındadır.
- 3 senaryo `out_of_scope` olup kasıtlı olarak sınır testi amacıyla eklenmiştir; bu senaryolarda sistemin doğru biçimde boş sonuç döndürdüğü doğrulanmıştır.

---

## Alan (Domain) Bazlı Kırılım

| Alan | Senaryo Sayısı | Hit@5 | MRR |
|---|---|---|---|
| `kira_hukuku` | 13 | %100.0 | 0.756 |
| `tuketici_hukuku` | 7 | %100.0 | 0.905 |
| `borclar_genel` | 2 | %100.0 | 0.750 |
| `is_hukuku` | 5 | %100.0 | 0.507 |
| `out_of_scope` | 3 | — (kapsam dışı) | — |

> **Not:** `is_hukuku` alanında MRR değeri diğer alanlara kıyasla düşük görünmektedir (0.507). Bu, İş Kanunu maddelerinin mevcut eğitim veriyle daha az örtüştüğüne işaret etmektedir. Faz 4 (LLM-as-Judge + Faithfulness) kapsamında hedef iyileştirme alanı olarak işaretlenmiştir.

---

## Bölüm 3.5 — Hukuk Mentor Doğrulaması

| Kriter | Sonuç |
|---|---|
| Mentor onaylı senaryo sayısı | **30 / 30** |
| Mentor doğrulama oranı | **%100** |
| Dataset versiyonu | `2.0.0-phase2` |
| Senaryolar | EVAL-001 ... EVAL-030 (tümü `mentor_verified: true`) |

### Doğrulama Yöntemi

Her senaryo `eval_scenarios.json` dosyasında `"mentor_verified": true` alanıyla işaretlenmiştir. 30 senaryonun tamamı hukuk mentörü tarafından:
- Soru doğruluğu (ilgili hukuki alan),
- Beklenen makale listesinin güncel mevzuata uygunluğu,
- Kapsam dışı (out_of_scope) etiketlerinin geçerliliği

açılarından onaylanmıştır.

---

## Ham Metrik Referansı

Tam ham metrikler için: [`reports/eval_results.json`](./eval_results.json)

```
{
  "total_scenarios": 30,
  "mentor_verified_count": 30,
  "mentor_verification_rate_pct": 100.0,
  "hit_at_k": 100.0,
  "all_hit_at_k": 70.37,
  "hit_at_1": 59.26,
  "mrr": 0.748,
  "latency_p95_ms": 74.42,
  "dataset_version": "2.0.0-phase2"
}
```

---

*Rapor otomatik olarak `run_eval.py` CLI tarafından üretilmiş ve manuel olarak gözden geçirilmiştir.*
