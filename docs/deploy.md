# Deploy rehberi

Backend Docker imajı olarak Render veya Railway'e, frontend Vercel'e gider. Hiçbir gizli anahtar repoda tutulmaz; hepsi platformun ortam değişkeni ekranından girilir.

## 1. Backend (Docker)

İmaj repo kökünden build edilir:

```bash
docker build -f backend/Dockerfile -t lexora-backend .
docker run --rm -p 8000:8000 -e ENVIRONMENT=production \
  -e GROQ_API_KEY=... -e GROQ_MODEL_NAME=... -e 'CORS_ORIGINS=["http://localhost:5173"]' lexora-backend
# http://localhost:8000/api/v1/health
```

`--env-file backend/.env` kullanmayın. O dosyadaki `TEMPLATES_DIR`, `FONTS_DIR` ve `CHROMA_PERSIST_DIR` göreli yolları yerel geliştirme içindir ve imajın içindeki yolları ezer. Konteynere yalnızca anahtarları ve modeli verin.

İmaj build sırasında şunları yapar:

- Yalnızca CPU'lu torch kurar. Varsayılan Linux paketi, sunucunun kullanmadığı birkaç GB'lık CUDA kütüphanesi indirir.
- `data/laws` altındaki kanun maddelerini ChromaDB'ye yükler, yani indeks imajın içinde gelir. Embedding modeli de bu sırada indirilir; ilk istek modeli internetten çekmez.
- Uygulamayı root olmayan `lexora` kullanıcısıyla çalıştırır ve platformun verdiği `$PORT` değişkenini dinler.

Kanun verisi (`data/laws`) değiştiğinde imajı yeniden build etmek yeterlidir.

**Boyut ve bellek (26 Kasım, yerel ölçüm):** İmaj yaklaşık 5 GB (1.9 GB Python paketleri, 1.1 GB embedding modeli). Konteyner açılışta 437 MB, ilk sohbet isteğinden sonra 817 MB RAM kullanıyor. Bu yüzden en az **1 GB, tercihen 2 GB RAM** gerekir:

- Render free ve starter planları (512 MB) yetmez, konteyner bellek yetersizliğinden kapanır. [render.yaml](../render.yaml) `standard` (2 GB) planını seçer.
- Railway'de servis ayarındaki bellek sınırı 1 GB'ın üzerinde olmalı.

### Render

1. Render'da **New > Blueprint** seçin ve bu repoyu bağlayın. [render.yaml](../render.yaml) otomatik okunur.
2. `sync: false` olarak işaretli değişkenler sorulur:
   - `GROQ_API_KEY`
   - `GROQ_MODEL_NAME` (yerelde kullandığınız modelle aynı olmalı)
   - `CORS_ORIGINS`: Vercel adresi JSON liste olarak, örn. `["https://lexora.vercel.app"]`. Sonda `/` olmamalı.
   - `LANGFUSE_SECRET_KEY`, `LANGFUSE_PUBLIC_KEY`: boş bırakılırsa izleme kapalı kalır.
3. `autoDeploy: false` ayarlı; her deploy elle başlatılır. Dondurma sonrası beklenmedik bir sürümün canlıya çıkmasını önler.

### Railway

1. **New Project > Deploy from GitHub repo** ile repoyu seçin. [railway.json](../railway.json) Dockerfile'ı ve health check yolunu tanımlar.
2. **Variables** sekmesine Render listesindeki değişkenleri ve `ENVIRONMENT=production` girin.
3. **Settings > Networking** altından bir public domain açın.

## 2. Frontend (Vercel)

1. Vercel'de **Add New > Project** ile repoyu içe aktarın ve **Root Directory** olarak `frontend` seçin. [frontend/vercel.json](../frontend/vercel.json) build ayarlarını ve React Router için gereken yönlendirmeyi içerir.
2. **Environment Variables** ekranına `VITE_API_BASE_URL` girin: backend'in public adresi, sonda `/` olmadan. Vite bu değeri build sırasında koda gömer; değiştirirseniz yeniden deploy etmeniz gerekir.
3. Deploy edin ve çıkan adresi backend'in `CORS_ORIGINS` listesine ekleyin. Bu yapılmazsa tarayıcı backend'e giden her isteği engeller.

## 3. Deploy sonrası kontrol

```bash
curl https://<backend>/api/v1/health
cd backend && python scripts/measure_latency.py --base-url https://<backend> --delay 5
```

- Health cevabında `chromadb: initialized` ve `groq: configured` görünmeli. Supabase kullanılmadığı için `status` alanı production'da `degraded` döner. Bu beklenen bir durumdur: endpoint yine 200 döndüğü için platformun health check'i geçer.
- Arayüzde bir soru sorun ve bir belge üretip .docx ile .pdf'i indirin.
- Cevap süresi ölçümü `reports/latency_e2e.json` dosyasına yazılır. Ölçümden önce servisi yeniden başlatın: sunucu LLM cevaplarını bellekte önbellekler ve aynı senaryolar ikinci kez sorulursa cevaplar önbellekten gelir, ölçüm anlamsızlaşır.

## Notlar

- Üretilen belgeler konteynerin geçici diskinde tutulur ve 120 dakika sonra silinir (KVKK). Yeniden başlatmada da silinirler; kalıcı disk bağlanmamalıdır.
- `ENVIRONMENT=production` iken bir şablonun .docx dosyası ya da PDF fontu eksikse belge üretimi hata verir. Development ortamındaki gibi sessizce örnek dosya üretmez.
- Supabase şu an hiçbir yerde kullanılmıyor; değişkenleri boş kalabilir.
