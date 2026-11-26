# lexora frontend

React + Vite + Tailwind CSS arayüzü. Kurulum, test ve deploy adımları için kök dizindeki [README.md](../README.md) ve [docs/deploy.md](../docs/deploy.md) dosyalarına bakın.

```bash
npm ci
npm run dev      # http://localhost:5173
npm test         # src/lib/*.test.js (node --test)
npm run lint
npm run build    # dist/
```

Backend adresi `VITE_API_BASE_URL` ile verilir ve build sırasında koda gömülür (bkz. `.env.example`).
