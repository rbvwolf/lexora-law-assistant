# W1-W2 Backend Görev Dağılımı (G1 ve G2)

- **G1:** AI, RAG ve Değerlendirme (Yiğit)
- **G2:** FastAPI, Güvenlik ve Belge Üretimi (Eren)

> **Ortak başlangıç iskeleti notu:** Repo kurulumunda açılan `main.py`, `schemas/`, `api/v1/`, `security.py` ve `doc_service.py` dosyaları, sunucunun ayağa kalkması ve herkesin birbirini beklemeden paralel çalışabilmesi için oluşturulmuş başlangıç şablonlarıdır (template / mock stub). Bu dosyaların asıl kurgusu, kontrolleri ve işleyişi G2 tarafından yazılıp doldurulacaktır.

## Ana odak

| | G1 | G2 |
|---|---|---|
| Odak | Kanun metinlerinin hazırlanması, madde bazlı parçalama (chunking), ChromaDB vektör arama, Groq API/LLM entegrasyonu ve değerlendirme (eval) kurgusu | FastAPI uç noktaları, API veri şemaları, girdi güvenliği ve PII maskeleme, şablonlardan Word/PDF (`.docx` ve `.pdf`) belge üretimi |

## Sorumlu olunan dosyalar

**G1**
- `data/laws/` ve `data/laws/raw_txts/` (kanun metinleri ve JSON çıktıları)
- `backend/scripts/parse_raw_laws.py` ve `ingest_laws.py`
- `backend/app/services/rag_service.py` (şu an boş template)
- `backend/app/services/llm_service.py` (şu an boş template)
- `data/eval/` (15 başlangıç test senaryosu)

**G2**
- `backend/app/main.py` ve `Dockerfile` (başlangıç şablonu hazır)
- `backend/app/core/config.py` ve `security.py` (başlangıç şablonu hazır)
- `backend/app/schemas/` (taslak Pydantic modelleri, detaylandırılacak)
- `backend/app/api/v1/` (health, chat, documents; şu an mock veri dönen şablon)
- `backend/app/services/doc_service.py` (şu an boş template) ve `data/templates/`

## Hazır olan başlangıç kurulumu

- **G1:** 4 temel kanun metni (`tbk_kira`, `tkhk_tuketici`, `tbk_temerrut`, `ik_is`) toplandı ve `parse_raw_laws.py` ile madde bazlı JSON formatına çevrildi.
- **G2:** Repo klasör ağacı, `requirements.txt`, `.env.example` ve `Dockerfile` oluşturuldu. `schemas/` ve `api/v1/` altında örnek (mock) dönüş yapan şablonlar açıldı.

## W1 görevleri (bu hafta)

**G1**
1. `ingest_laws.py` dosyasını kodlayarak `data/laws/` altındaki JSON kanun maddelerini embedding modeliyle vektörleştirip lokal ChromaDB'ye kaydetmek.
2. `llm_service.py` şablonunu doldurarak Groq API bağlantısını ve yanıt önbellekleme (caching) yapısını kurmak.

**G2**
1. `app/schemas/` altındaki taslak Pydantic v2 modellerini belge ve sohbet ihtiyaçlarına göre kontrol edip geliştirmek.
2. `api/v1/` altındaki üç uç noktanın (`health`, `chat`, `documents`) yönlendirme, hata yönetimi ve doğrulama yapısını kurmak.
3. `security.py` içindeki girdi temizleme (input sanitization) ve PII (TC, IBAN, telefon vb.) maskeleme fonksiyonlarını geliştirmek ve test etmek.

## W2 görevleri (gelecek hafta)

**G1**
1. `rag_service.py` şablonunu doldurarak sorulan soruya en yakın 5 kanun maddesini (`top_k=5`) getiren arama fonksiyonunu yazmak.
2. `llm_service.py` içinde niyet sınıflandırma (durum yönlendirme) ve RAG soru-cevap promptlarını bağlamak.
3. `data/eval/` altında ilk 15 değerlendirme senaryosunu hazırlamak.

**G2**
1. `data/templates/` altına 1. belge şablonunu (`.docx` ve `.html`) değişken alanlarıyla (`{{...}}`) eklemek.
2. `doc_service.py` şablonunu doldurarak `docxtpl` ve `WeasyPrint` ile paralel `.docx` ve `.pdf` üreten yapıyı kodlamak.
3. `/documents/generate` ve `/documents/download/{file_id}` uçlarını `doc_service.py` ve geçici dosya yapısına bağlamak.

## Güncel durum (20 Ekim) ve açık noktalar

> Bu bölüm koda bakılarak eklendi, takım onayı bekliyor.

- `main`'de `security.py`, `config.py`, `langfuse.py` ve `backend/tests/test_api_v1.py` taslak değil, yazılmış durumda. G2'nin işi bunları gözden geçirip düzeltmek.
- Kanun verisi ve parser (`feat/law-data-and-rag`) henüz `main`'e merge edilmedi.
- `core/langfuse.py` kimsenin listesinde yok. **Öneri:** G2 üstlensin, çünkü PII maskeleme ile bağlantılı.
- `ik_is` (İş Kanunu) kapsamdaki alanlarda (tüketici, kira) yok. Hukukçu mentorlarla teyit edilmeli.