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

To switch the retention loop to the OpenAI-compatible Gemma endpoint:

```bash
export LLM_RETENTION_PROVIDER=gemma
export GEMMA_API_KEY=your_gemma_bearer_token
export LLM_RETENTION_MODEL=unsloth/gemma-4-E2B-it-GGUF:UD-Q4_K_XL
export GEMMA_API_BASE_URL=https://gemma.donggyu.link
```

To switch the retention loop to Upstage Solar:

```bash
export LLM_RETENTION_PROVIDER=upstage
export UPSTAGE_API_KEY=your_upstage_key
export LLM_RETENTION_MODEL=solar-pro3
```

The monthly horoscope report uses a separate client with its own provider switch. It defaults to `xai` and reads the legacy `XAI_*` variables when `MONTHLY_LLM_*` is unset:

```bash
export MONTHLY_LLM_PROVIDER=upstage
export UPSTAGE_API_KEY=your_upstage_key
export UPSTAGE_MODEL=solar-pro3
```

Optional Upstage tuning (applies to both clients, omitted from the request when empty):

```bash
export UPSTAGE_REASONING_EFFORT=minimal
export UPSTAGE_API_BASE_URL=https://api.upstage.ai/v1
```

Note the asymmetry: the retention loop picks its model from `LLM_RETENTION_MODEL`, while the monthly report reads `MONTHLY_LLM_MODEL` or the provider-scoped `UPSTAGE_MODEL` / `XAI_MODEL`.

If the selected provider has no usable API key, `/calendar`, `/today`, `/coach`, and the monthly `/horoscope` report fall back to deterministic timing guidance from the transit engine and return `llmEnhanced: false`. MariaDB is optional, but recommended for persistent result caching and account features.

MariaDB-backed cache and account settings:

```bash
export MONTHLY_FORTUNE_MARIADB_HOST=localhost
export MONTHLY_FORTUNE_MARIADB_PORT=3306
export MONTHLY_FORTUNE_MARIADB_USER=monthly_fortune
export MONTHLY_FORTUNE_MARIADB_PASSWORD=change_me
export MONTHLY_FORTUNE_MARIADB_DATABASE=monthly_fortune
export MONTHLY_FORTUNE_CACHE_TTL_DAYS=365
export MONTHLY_FORTUNE_SESSION_DAYS=30
```

When these MariaDB settings are present, horoscope yearly/monthly responses are saved in `fortune_result_cache` and reused by cache key before recomputing or calling an LLM. The account API uses `fortune_users` and `fortune_user_sessions`; without MariaDB settings the account endpoints return `503` and the core horoscope flow still works.

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

## Codex commit helper

On Windows, use the repository wrapper so Codex can stage the intended files,
generate a concise commit message, commit, and push the current branch with one
stable command:

```bat
codex-commit-push.bat
```

Useful options:

```bat
codex-commit-push.bat -DryRun
codex-commit-push.bat -Message "Improve navigation menu"
codex-commit-push.bat -PushBranch main
codex-commit-push.bat -NoPush
```
