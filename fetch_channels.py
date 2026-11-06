import glob, datetime as dt
import requests, pandas as pd
from config import API_KEY, DATA_DIR

BASE = "https://www.googleapis.com/youtube/v3"
TODAY = dt.date.today().isoformat()

# Channels from the latest trending file and the latest topic-search file.
ids = set()
for pattern in ("trending_videos_*.csv", "topic_videos_*.csv"):
    files = sorted(glob.glob(f"{DATA_DIR}/{pattern}"))
    if files:
        print("Reading", files[-1])
        ids |= set(pd.read_csv(files[-1])["channel_id"].dropna())
ids = sorted(ids)

rows = []
for i in range(0, len(ids), 50):
    batch = ids[i:i + 50]
    r = requests.get(f"{BASE}/channels",
                     params={"part": "snippet,statistics", "id": ",".join(batch),
                             "maxResults": 50, "key": API_KEY})
    if not r.ok:
        print("Error", r.status_code, r.text[:200])
        continue
    for c in r.json().get("items", []):
        s, st = c["snippet"], c.get("statistics", {})
        hidden = st.get("hiddenSubscriberCount", False)
        rows.append(dict(
            snapshot_date=TODAY, channel_id=c["id"], channel_name=s["title"],
            country=s.get("country"), created_at=s["publishedAt"],
            subscribers=None if hidden else int(st.get("subscriberCount", 0)),
            subscribers_hidden=hidden,
            total_views=int(st.get("viewCount", 0)),
            video_count=int(st.get("videoCount", 0))))
    print(f"{min(i + 50, len(ids))}/{len(ids)} channels")

df = pd.DataFrame(rows)
df.to_csv(f"{DATA_DIR}/channels_{TODAY}.csv", index=False)
print(f"Saved {len(df)} channels; country filled for {df.country.notna().sum()}")
