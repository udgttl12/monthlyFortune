from fastapi import FastAPI

from app.routers.horoscope import router as horoscope_router

app = FastAPI(title="Monthly Fortune API", version="1.0.0")

app.include_router(horoscope_router)
