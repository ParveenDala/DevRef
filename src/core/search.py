from typing import Optional

from pydantic import BaseModel


class SearchResult(BaseModel):
    title: str
    url: str
    snippet: str = ""
    source: str = "google"
    date: Optional[str] = None
