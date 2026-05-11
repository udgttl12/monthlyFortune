# Monthly Fortune

Monthly Fortune is a full-stack astrology project built with Next.js on the frontend and FastAPI on the backend.

## Stack

- Frontend: Next.js 14, React 18, TypeScript
- Backend: FastAPI, Uvicorn, Pydantic
- Astrology: Swiss Ephemeris via `pysweph`

## App structure

- `/` home page with birth input form
- `/chart` natal chart result page
- `/horoscope` personalized yearly overview + monthly detail page
- `/calendar` AI 30-day action calendar page
- `/today` AI daily briefing page
- `/coach` AI decision timing coach page
- `/api/chart/natal` natal chart API
- `/api/horoscope/yearly` personalized yearly horoscope API
- `/api/horoscope/monthly` monthly horoscope API
- `/api/ai-retention/action-calendar` AI action calendar API
- `/api/ai-retention/daily-brief` AI daily briefing API
- `/api/ai-retention/coach` AI timing coach API

## Local development

### Frontend

```bash
npm install
npm run dev
```

### Backend

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Optional AI enhancement:

```bash
export XAI_API_KEY=your_xai_key
export XAI_MODEL=grok-4.20-reasoning
export XAI_TIMEOUT_SECONDS=45
```

AI retention loop provider settings:

```bash
export LLM_RETENTION_PROVIDER=xai
export LLM_RETENTION_API_KEY=your_provider_key
export LLM_RETENTION_MODEL=grok-4.20-reasoning
export LLM_RETENTION_TIMEOUT_SECONDS=45
```

The `/coach` page submits from the browser, so set `NEXT_PUBLIC_MONTHLY_FORTUNE_API_URL` to the same backend origin used by `MONTHLY_FORTUNE_API_URL`.

To switch the retention loop to DeepSeek:

```bash
export LLM_RETENTION_PROVIDER=deepseek
export LLM_RETENTION_MODEL=deepseek-v4-pro
```

If `LLM_RETENTION_API_KEY` is empty, `/calendar`, `/today`, and `/coach` fall back to deterministic timing guidance from the transit engine. MariaDB is intentionally not used in v1; add it only when server-side history or cross-device storage is required.

## Production deployment

The recommended production target is direct deployment on a Linux server with:

- `nginx`
- `systemd`
- Next.js on `127.0.0.1:3000`
- FastAPI on `127.0.0.1:8000`

Server deployment assets are included here:

- [docs/rockyos-deployment.md](/C:/Users/lKira/Project/monthlyFortune/docs/rockyos-deployment.md)
- [.github/workflows/deploy-rockyos.yml](/C:/Users/lKira/Project/monthlyFortune/.github/workflows/deploy-rockyos.yml)
- [deploy/rockyos/monthly-fortune-api.service](/C:/Users/lKira/Project/monthlyFortune/deploy/rockyos/monthly-fortune-api.service)
- [deploy/rockyos/monthly-fortune-web.service](/C:/Users/lKira/Project/monthlyFortune/deploy/rockyos/monthly-fortune-web.service)
- [deploy/rockyos/monthly-fortune.nginx.conf](/C:/Users/lKira/Project/monthlyFortune/deploy/rockyos/monthly-fortune.nginx.conf)
- [scripts/deploy-rockyos.sh](/C:/Users/lKira/Project/monthlyFortune/scripts/deploy-rockyos.sh)

## Verification

```bash
npm run lint
npm run build
npm run test:frontend
.venv-root/Scripts/python.exe -m unittest discover -s tests -v
```
