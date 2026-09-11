from pydantic import BaseModel, Field


class CrawledPage(BaseModel):
    url: str
    text: str
    priority: int


class CompanyResearch(BaseModel):
    domain: str
    pages: list[CrawledPage] = Field(
        default_factory=list
    )
    