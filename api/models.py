from sqlalchemy import Column, Integer, String
from pgvector.sqlalchemy import Vector

from database import Base
import schemas

VECTOR_DIMENSION = 384
# 'all-MiniLM-L6-v2'model

class Apod(Base):
  __tablename__ = "apod"

  id = Column(Integer, primary_key=True)
  title = Column(String(1024))
  url = Column(String(2048))
  date = Column(String(10))
  embedding = Column(Vector(VECTOR_DIMENSION))

class NasaApodInput(schemas.BaseModel):
  title: str
  explanation: str
  url: str
  date: str
