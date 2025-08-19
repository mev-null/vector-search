from fastapi import APIRouter

router = APIRouter()

@router.post("/search")
async def search():
  pass