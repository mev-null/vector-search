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
  ユーザーからの検索クエリを元に、データベースから類似画像を検索

  Args:
    -request_body (schemas.SearchQuery): `query` (検索テキスト) と `limit`(取得件数) を含むリクエストボディ。
    -db (AsyncSession): データベースへの非同期セッション。

  Returns:
    List[schemas.SearchResultItem]: 検索結果のリスト。各項目は`title`,`date`, `url`を含むJSONオブジェクトに整形

"""
  query_embedding = _model.encode(request_body.query).tolist()
  results = await crud.search_vector(db, query_embedding, request_body.limit)

  return results
