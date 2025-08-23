#api/routers/search.py
from fastapi import APIRouter, Depends
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sentence_transformers import SentenceTransformer

import schemas, crud
from database import get_async_db
from models import VECTOR_DIMENSION

router = APIRouter()
_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

@router.post("/search", response_model=List[schemas.SearchResultItem])
async def search(request_body: schemas.SearchQuery ,db: AsyncSession=Depends(get_async_db)):
  """
  入力: ユーザーからのJSONデータ（{"query": "..."}）。
  処理:
    queryをsentence-transformersでベクトル化。
    embeddingとlimitをcrud.pyの検索関数に渡す。
    crud.pyがSQLAlchemy経由でpgvectorに検索クエリを送信。
    データベースが類似データ（title, url, date, embeddingなど）を返す。
    SQLAlchemyがmodelsオブジェクトに変換し、Pydanticのschemasがtitle, url, dateをJSONに整形。
  出力: JSON形式の検索結果（{"results": [...]}）。
  """
  query_embedding = _model.encode(request_body.query).tolist()
  results = await crud.search_vector(db, query_embedding, request_body.limit)

  return results
