from fastapi import FastAPI

from app.routers.chart import router as chart_router
from app.routers.horoscope import router as horoscope_router

app = FastAPI(title="Monthly Fortune API", version="1.1.0")

app.include_router(chart_router)
app.include_router(horoscope_router)
