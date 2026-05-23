from fastapi import FastAPI

from app.routers.ai_retention import router as ai_retention_router
from app.routers.auth import router as auth_router
from app.routers.chart import router as chart_router
from app.routers.horoscope import router as horoscope_router

app = FastAPI(title="Monthly Fortune API", version="1.1.0")

app.include_router(chart_router)
app.include_router(horoscope_router)
app.include_router(ai_retention_router)
app.include_router(auth_router)
