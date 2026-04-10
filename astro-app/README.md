# Astrology SaaS Monolith

A monorepo full-stack astrology app with FastAPI + Next.js.

## Features
- `GET /api/chart` for planets, houses, and aspects.
- `GET /api/horoscope/monthly` for monthly events plus cards (Career, Money, Love, Risk).
- Frontend pages: Home, Chart, Horoscope.
- Loading states: **Calculating chart...** and **Analyzing planets...**.

## Run with Docker
```bash
cd astro-app
docker compose up --build
```

- Frontend: http://localhost:3000
- Backend docs: http://localhost:8000/docs

## Run locally
### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```
