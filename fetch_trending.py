import os, datetime as dt
import requests, pandas as pd
from config import API_KEY, REGION_CODE, DATA_DIR

BASE = "https://www.googleapis.com/youtube/v3"
TODAY = dt.date.today().isoformat()
os.makedirs(DATA_DIR, exist_ok=True)

def get_categories():
    r = requests.get(f"{BASE}/videoCategories",
                     params={"part": "snippet", "regionCode": REGION_CODE, "key": API_KEY}).json()
    rows = [dict(category_id=i["id"], category_name=i["snippet"]["title"],
                 assignable=i["snippet"].get("assignable", False))
            for i in r.get("items", [])]
    return pd.DataFrame(rows)

def get_trending(category_id=None, max_pages=4):
    rows, token, rank = [], None, 0
    for _ in range(max_pages):
        params = dict(part="snippet,statistics,contentDetails", chart="mostPopular",
                      regionCode=REGION_CODE, maxResults=50, key=API_KEY)
        if category_id:
            params["videoCategoryId"] = category_id
        if token:
            params["pageToken"] = token
        r = requests.get(f"{BASE}/videos", params=params)
        if not r.ok:   # some categories have no trending chart
            print(f"  skipped category {category_id}: {r.status_code}")
            return rows
        data = r.json()
        for v in data.get("items", []):
            rank += 1
            s, st, cd = v["snippet"], v.get("statistics", {}), v["contentDetails"]
            rows.append(dict(
                snapshot_date=TODAY, category_chart=category_id or "overall", rank=rank,
                video_id=v["id"], title=s["title"], channel_id=s["channelId"],
                channel_title=s["channelTitle"], category_id=s["categoryId"],
                published_at=s["publishedAt"], duration=cd["duration"],
                audio_lang=s.get("defaultAudioLanguage"), default_lang=s.get("defaultLanguage"),
                tags="|".join(s.get("tags", [])),
                views=int(st["viewCount"]) if "viewCount" in st else None,
                likes=int(st["likeCount"]) if "likeCount" in st else None,
                comments=int(st["commentCount"]) if "commentCount" in st else None))
        token = data.get("nextPageToken")
        if not token:
            break
    return rows

if __name__ == "__main__":
    cats = get_categories()
    cats.to_csv(f"{DATA_DIR}/dim_category.csv", index=False)
    print(f"Saved {len(cats)} categories")

    all_rows = get_trending()                      # overall India chart
    for cid in cats[cats.assignable]["category_id"]:
        print(f"Category {cid}")
        all_rows += get_trending(cid)

    df = pd.DataFrame(all_rows)
    df.to_csv(f"{DATA_DIR}/trending_videos_{TODAY}.csv", index=False)
    print(f"Saved {len(df)} rows, {df.video_id.nunique()} unique videos, "
          f"{df.channel_id.nunique()} unique channels")