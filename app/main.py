from secrets import token_urlsafe

from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, HttpUrl


app = FastAPI(
    title="URL Shortener API",
    description="A small URL shortener used to demonstrate Docker and CI/CD.",
    version="1.0.0",
)


class URLRequest(BaseModel):
    url: HttpUrl


class URLRecord(BaseModel):
    original_url: str
    clicks: int = 0


url_store: dict[str, URLRecord] = {}


def generate_short_code() -> str:
    return token_urlsafe(6)[:8]


@app.get("/")
def root():
    return {
        "service": "URL Shortener API",
        "version": "1.0.0",
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "url-shortener",
        "version": "1.0.0",
    }


@app.post("/urls", status_code=201)
def create_short_url(request: URLRequest):
    short_code = generate_short_code()

    while short_code in url_store:
        short_code = generate_short_code()

    url_store[short_code] = URLRecord(
        original_url=str(request.url),
    )

    return {
        "short_code": short_code,
        "short_url": f"/{short_code}",
        "original_url": str(request.url),
    }


@app.get("/urls")
def list_urls():
    return url_store


@app.get("/urls/{short_code}")
def get_url_info(short_code: str):
    record = url_store.get(short_code)

    if record is None:
        raise HTTPException(
            status_code=404,
            detail="Short URL not found",
        )

    return {
        "short_code": short_code,
        "original_url": record.original_url,
        "clicks": record.clicks,
    }


@app.delete("/urls/{short_code}")
def delete_short_url(short_code: str):
    if short_code not in url_store:
        raise HTTPException(
            status_code=404,
            detail="Short URL not found",
        )

    del url_store[short_code]

    return {
        "message": "Short URL deleted"
    }


@app.get("/{short_code}")
def redirect_to_url(short_code: str):
    record = url_store.get(short_code)

    if record is None:
        raise HTTPException(
            status_code=404,
            detail="Short URL not found",
        )

    record.clicks += 1

    return RedirectResponse(
        url=record.original_url,
        status_code=307,
    )