# main.py
import uvicorn
from fastapi import FastAPI

from routers import search, data

openapi_tags = [
  {
    "name": "APOD",
    "description": "NASA APOD への参考リンク",
    "externalDocs": {
      "description": "APOD Archive",
      "url": "https://apod.nasa.gov/apod/archivepix.html",
    },
  }
]

app = FastAPI(
    title="Astronomy Picture of the Day Vector Search",
    description="APOD(Astronomy Picture of the Day)の画像検索エンジン",
    openapi_tags=openapi_tags,
)


@app.get("/")
def read_root():
  return {"message": "Welcome to the NASA Vector Search API!"}

app.include_router(search.router)
app.include_router(data.router)