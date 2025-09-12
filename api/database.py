import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base

# データベース接続URLを環境変数から取得
# 非同期ドライバ（asyncpg）を使用するため，URLスキームを変換
ASYNC_DB_URL = os.getenv("DATABASE_URL").replace("postgresql://", "postgresql+asyncpg://")

async_engine = create_async_engine(ASYNC_DB_URL, echo=True)
async_session = sessionmaker(
  autocommit=False, 
  autoflush=False, 
  bind=async_engine, 
  class_=AsyncSession,
  expire_on_commit=False # トランザクションコミット後もオブジェクトが使用できるようにする
)

# SQLAlchemyのORMモデルのベースクラス
Base = declarative_base()

# 依存性注入のための関数
async def get_async_db():
  async with async_session() as session:
    yield session