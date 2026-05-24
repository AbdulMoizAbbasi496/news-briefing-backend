from pydantic import BaseModel, HttpUrl


class NewsItem(BaseModel):
    category: str
    title: str
    link: HttpUrl | str
    summary: str
    why_it_matters: str
    source: str = "Geo News"
    published: str | None = None


class BriefingResponse(BaseModel):
    date: str
    total: int
    categories: dict[str, list[NewsItem]]
