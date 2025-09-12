from typing import Optional, List

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from pgvector.sqlalchemy import Vector

import schemas, models

async def create_item(db: AsyncSession, item: schemas.DataSave) -> models.Apod:
  """
    save to database
  """
  # schemasのデータをmodelのインスタンスに
  db_item = models.Apod(
    title=item.title,
    url=item.url,
    date=item.date,
    embedding=item.embedding
  )
  db.add(db_item)
  await db.commit()
  await db.refresh(db_item)
  return db_item

async def search_vector(db: AsyncSession, query_embedding: List[float], limit: int) -> List[models.Apod]:
  """
    search items based on "cosine similarity"
  """
  # pgvectorのコサイン類似度演算子 `<=>` を使用
  # ORDER BYで昇順に並べ替える
  stmt = select(models.Apod).order_by(
    models.Apod.embedding.l2_distance(query_embedding)
  ).limit(limit)
    
  # データベースでクエリを実行，データを取得
  result = await db.execute(stmt)
  items = result.scalars().all()

  return items

async def delete_item_by_details(db: AsyncSession, item_details: schemas.ItemToDelete) -> Optional[models.Apod]:
  """
  Find an item by title, date, and url, then delete it.
  """
  
  # 削除対象のアイテムを検索
  stmt = select(models.Apod).where(
    and_(
      models.Apod.title == item_details.title,
      models.Apod.date == item_details.date,
      models.Apod.url == item_details.url
    )
  )
  result = await db.execute(stmt)
  item_to_delete = result.scalars().one_or_none()
  
  # アイテムが見つかった場合のみ削除処理を実行
  if item_to_delete:
    await db.delete(item_to_delete)
    await db.commit()
    return item_to_delete
  
  # 見つからなかった場合はNoneを返す
  return None