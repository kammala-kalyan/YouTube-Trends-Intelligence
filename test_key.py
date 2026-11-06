import requests
from config import API_KEY

r = requests.get(
    "https://www.googleapis.com/youtube/v3/videos",
    params={"part": "snippet", "chart": "mostPopular", "regionCode": "IN",
            "maxResults": 1, "key": API_KEY},
)
print(r.status_code)
print(r.json()["items"][0]["snippet"]["title"] if r.ok else r.text)