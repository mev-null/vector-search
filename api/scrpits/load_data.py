import httpx
import os
from datetime import date, timedelta
from dotenv import load_dotenv
import time

load_dotenv()

NASA_API_KEY = os.getenv("NASA_API_KEY", "DEMO_KEY")
NASA_APOD_URL = "https://api.nasa.gov/planetary/apod"
FASTAPI_DATA_URL = "http://127.0.0.1:8000/data"

def get_apod_data_for_range(start_date: date, end_date: date) -> list:
  all_data = []
  current_date = start_date

  with httpx.Client() as client:
    while current_date <= end_date:
      params = {
        "api_key": NASA_API_KEY,
        "date": current_date.strftime("%Y-%m-%d"),
      }
      try:
        response = client.get(NASA_APOD_URL, params=params)
        response.raise_for_status()

        data = response.json()
        if data.get("media_type") == "image":
          all_data.append(data)

      except httpx.HTTPStatusError as e:
        print(f"Could not fetch data for {current_date}: {e}")
      except Exception as e:
        print(f"An unexpected error occurred for {current_date}: {e}")

      current_date += timedelta(days=1)
      time.sleep(1)

  return all_data

def format_for_api(nasa_data: list) -> list:
  formatted_data = []
  for item in nasa_data:
    if all(k in item for k in ["title", "explanation", "url", "date"]):
      formatted_data.append({
        "title": item["title"],
        "explanation": item["explanation"],
        "url": item["url"],
        "date": item["date"]
      })
  return formatted_data

def post_data_to_api(data_to_post: list):
  if not data_to_post:
    return
  
  with httpx.Client(timeout=30.0) as client:
    try:
      response = client.post(FASTAPI_DATA_URL, json=data_to_post)
      response.raise_for_status()

    except httpx.HTTPStatusError as e:
      print(f"Error posting data to your API: {e}")
      print("Response body:", e.response.text)
    except httpx.RequestError as e:
      print(f"Could not connect to your FastAPI application at {FASTAPI_DATA_URL}.")

if __name__ == "__main__":
    # 過去100日分のデータを取得
  end_date = date.today()
  start_date = end_date - timedelta(days=100)
    
  # 1. NASAからデータを取得
  nasa_data = get_apod_data_for_range(start_date, end_date)
    
  # 2. データを自作APIの形式に整形
  formatted_data = format_for_api(nasa_data)
    
  # 3. 自作APIにデータを投入
  post_data_to_api(formatted_data)