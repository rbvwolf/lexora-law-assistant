# lexora: AI Destekli Hukuk Asistanı

lexora, Türk hukuku için RAG tabanlı bir yapay zekâ asistanıdır. Kullanıcının niyetini sınıflandırır, kanun maddesine atıf yaparak soruları yanıtlar ve kullanıma hazır hukuki belgeler (.docx ve .pdf) üretir.

> **Bu sistem bir AI asistanıdır; avukatlık hizmeti vermez.** Üretilen belgeler taslaktır ve kullanılmadan önce bir hukukçu tarafından kontrol edilmelidir.

Mimari, API sözleşmesi, KVKK kuralları ve kodlama standartları için tek kaynak [AGENTS.md](AGENTS.md) dosyasıdır.

## Ne yapar

| Özellik | Durum |
|---|---|
| Niyet sınıflandırma (`question_answering` / `document_generation` / `out_of_scope`) | Groq LLM ile |
| Hukuki soru-cevap | Madde bazlı RAG (ChromaDB), cevapta kanun ve madde atfı |
| Belge üretimi | Fahiş kira artışına itiraz ihtarnamesi (TBK m. 344), kira temerrüt ihtarnamesi (TBK m. 315) |
| Parametre çıkarma | Sohbetten olay bilgileri çıkarılır, eksik alanlar sorulur |
| KVKK | Sohbette PII maskeleme, kişisel veriler LLM'e gitmez, üretilen dosyalar 120 dakika sonra silinir |

Kapsamdaki kanunlar (91 madde): 6098 sayılı TBK (kira ve temerrüt hükümleri), 6502 sayılı TKHK ve 4857 sayılı İş Kanunu'ndan seçili maddeler. Ayıplı mal şablonu henüz örnek dosya üretir.

## Teknoloji

- **Backend:** Python 3.11, FastAPI, Pydantic v2, Groq API, ChromaDB, sentence-transformers, docxtpl (.docx), fpdf2 (.pdf)
- **Frontend:** React + Vite, React Router, Tailwind CSS
- **Gözlemlenebilirlik:** Langfuse (PII maskeli)
- **Deploy:** Backend Docker ile Render veya Railway, frontend Vercel ([docs/deploy.md](docs/deploy.md))

## Yerel kurulum

### Backend

```bash
# Repo kökünde
python -m venv .venv
# Windows (PowerShell): .venv\Scripts\Activate.ps1
# Linux / macOS:        source .venv/bin/activate
pip install -r requirements.txt

cp backend/.env.example backend/.env      # GROQ_API_KEY'i doldurun; boş kalırsa mock cevap döner

cd backend
python scripts/ingest_laws.py --reset     # data/laws -> ChromaDB (ilk kurulumda ve kanun verisi değişince)
uvicorn app.main:app --reload             # http://localhost:8000/docs
```

Backend komutları `backend/` klasöründen çalıştırılır; şablon ve font yolları buna göre ayarlıdır.

### Frontend

```bash
cd frontend
cp .env.example .env                      # VITE_API_BASE_URL=http://localhost:8000
npm ci
npm run dev                               # http://localhost:5173
```

## Test ve değerlendirme

```bash
cd backend && pytest tests                # backend birim testleri
cd frontend && npm test && npm run lint   # frontend testleri ve lint

cd backend
python scripts/run_eval.py                # 30 senaryo: hit@5, MRR, retrieval gecikmesi
python scripts/run_eval.py --include-llm --eval-judge   # + niyet doğruluğu ve LLM-as-judge (Groq anahtarı gerekir)
python scripts/measure_latency.py         # uçtan uca /chat/message cevap süresi (hedef p95 < 10 sn)
```

Sonuç raporları [reports/](reports/) klasöründedir.

## Belge şablonları

Belge metni ve düzeni [backend/app/services/doc_layouts.py](backend/app/services/doc_layouts.py) dosyasında tek yerde tanımlıdır; .docx ve .pdf aynı tanımdan üretilir. Metni değiştirdikten sonra .docx şablonlarını yeniden üretin:

```bash
cd backend && python -m tools.build_doc_templates
```

Testler, commit'lenmiş .docx ile tanımın aynı olduğunu kontrol eder.

## Klasör yapısı

```
backend/   FastAPI uygulaması, servisler, betikler (ingest, eval, latency) ve testler
frontend/  React + Vite arayüzü
data/      Kanun metinleri (laws), belge şablonları (templates), fontlar, eval senaryoları
reports/   Eval, prompt injection ve gecikme raporları
docs/      Proposal, roadmap, durum raporları, deploy rehberi
```
