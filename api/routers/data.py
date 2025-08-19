from fastapi import APIRouter

router = APIRouter()

@router.post("/data/load")
async def load_data():
  pass