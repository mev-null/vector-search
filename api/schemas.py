from pydantic import BaseModel
from typing import Optional, List, Any

class SearchQuery(BaseModel):
  """Request"""
  query: str
  limit: int=10

class SearchResultItem(BaseModel):
  """Response"""
  title: str
  date: str
  url: str
  """SQLAlchemy -> Pydantic"""
  class Config:
    orm_mode = True

class ItemToDelete(BaseModel):
  """Request body for deleting an item"""
  title: str
  date: str
  url: str

class DataSave(BaseModel):
  """データベースに保存するためのスキーマ"""
  title: str
  url: str
  date: str
  embedding: List[float]
