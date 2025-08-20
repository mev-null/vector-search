# api/routers/data.py
from fastapi import APIRouter, Depends, HTTPException
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sentence_transformers import SentenceTransformer

import schemas, crud
from database import get_async_db

# 入力データ構造
class NasaApodInput(schemas.BaseModel):
  title: str
  explanation: str
  url: str
  date: str

router = APIRouter()

_model = SentenceTransformer("all-MiniLM-L6-v2")

@router.post("/data", response_model=List[schemas.SearchResultItem], tags=["Data Management"])
async def load_data(items: List[NasaApodInput], db: AsyncSession = Depends(get_async_db)):
  """
  APODデータのリストを受け取り、ベクトル埋め込みを生成してデータベースに保存します。

  - **入力**: `title`, `explanation`, `url`, `date`を持つオブジェクトのJSON配列。
  - **処理**:
    1. 各項目について、`explanation`を'all-MiniLM-L6-v2'モデルでベクトル化します。
    2. 元の`title`, `url`, `date`と新しい`embedding`をCRUD関数に渡します。
    3. CRUD関数がSQLAlchemyを通じてPostgreSQLデータベースにデータを保存します。
  - **出力**: 保存に成功した項目のJSON配列（embeddingを除く）。
  """
  created_items = []
  for item in items:
    # 1. explanationテキストをベクトル化
    embedding = _model.encode(item.explanation).tolist()

    # 2. 保存用のPydanticスキーマインスタンスを作成
    item_to_save = schemas.DataSave(
      title=item.title,
      url=item.url,
      date=item.date,
      embedding=embedding
    )

    # 3. CRUD関数を呼び出してデータベースに保存
    created_item = await crud.create_item(db=db, item=item_to_save)
    created_items.append(created_item)
  
  return created_items


@router.delete("/data", status_code=200, tags=["Data Management"])
async def delete_item(item_to_delete: schemas.ItemToDelete, db: AsyncSession = Depends(get_async_db)):
  """
  Deletes a specific item from the database based on its title, date, and url.
  """
  deleted_item = await crud.delete_item_by_details(db, item_to_delete)
  
  if deleted_item is None:
    raise HTTPException(status_code=404, detail="Item not found")
  
  return {"message": "Item deleted successfully", "deleted_item": {"title": deleted_item.title, "date": deleted_item.date, "url": deleted_item.url}}