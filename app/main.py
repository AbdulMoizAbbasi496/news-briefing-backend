from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.scraper import get_briefing

app = FastAPI(title=settings.APP_NAME)

origins = [o.strip() for o in settings.ALLOWED_ORIGINS.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"message": "Geo News Briefing API is running", "docs": "/docs"}


@app.get("/api/briefing")
def briefing(today_only: bool = Query(default=True)):
    return get_briefing(today_only=today_only)
