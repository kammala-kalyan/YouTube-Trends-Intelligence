import sys, datetime as dt
import requests, pandas as pd
from config import API_KEY, REGION_CODE, DATA_DIR, DAILY_QUOTA_LIMIT
from keywords import all_keywords

BASE = "https://www.googleapis.com/youtube/v3"
TODAY = dt.date.today().isoformat()
since = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%SZ")

# Each search costs 100 units, so we can't search every keyword every day.
# Split keywords into N_GROUPS and run one group per day (rotates by date).
# Run `python fetch_topics.py 2` to force a specific group (0-based).
N_GROUPS = 3
everything = all_keywords()
group = int(sys.argv[1]) if len(sys.argv) > 1 else dt.date.today().toordinal() % N_GROUPS
todays = everything[group::N_GROUPS]   # interleaved, so every group covers every category
print(f"Group {group + 1}/{N_GROUPS}: {len(todays)} of {len(everything)} keywords")

units, hits, supply = 0, [], []
for cat, kw, lang in todays:
    if units + 100 > DAILY_QUOTA_LIMIT:
        print("Quota guard reached, stopping")
        break
    r = requests.get(f"{BASE}/search", params=dict(
        part="snippet", q=kw, type="video", regionCode=REGION_CODE,
        relevanceLanguage=lang, order="viewCount", publishedAfter=since,
        maxResults=50, key=API_KEY))
    units += 100
    if not r.ok:
        print(f"  {kw}: error {r.status_code} {r.text[:150]}")
        if r.status_code == 403:   # quota exhausted - no point continuing
            break
        continue
    d = r.json()
    supply.append(dict(snapshot_date=TODAY, category=cat, keyword=kw, lang=lang,
                       videos_last_30d_est=d["pageInfo"]["totalResults"]))
    hits += [dict(keyword=kw, category=cat, lang=lang, video_id=i["id"]["videoId"])
             for i in d.get("items", []) if "videoId" in i["id"]]
    print(f"{cat} / {kw}: {len(d.get('items', []))} videos")

if not supply:
    raise SystemExit("No searches succeeded - nothing saved.")
pd.DataFrame(supply).to_csv(f"{DATA_DIR}/keyword_supply_{TODAY}.csv", index=False)

# fetch full stats for the videos found (1 unit per 50 videos)
hit_df = pd.DataFrame(hits).drop_duplicates(["keyword", "video_id"])
ids = hit_df["video_id"].unique().tolist()
rows = []
for i in range(0, len(ids), 50):
    r = requests.get(f"{BASE}/videos", params=dict(
        part="snippet,statistics,contentDetails", id=",".join(ids[i:i + 50]), key=API_KEY))
    units += 1
    if not r.ok:
        print(f"  videos.list error {r.status_code}")
        continue
    for v in r.json().get("items", []):
        s, st, cd = v["snippet"], v.get("statistics", {}), v["contentDetails"]
        rows.append(dict(
            video_id=v["id"], title=s["title"], channel_id=s["channelId"],
            channel_title=s["channelTitle"], category_id=s["categoryId"],
            published_at=s["publishedAt"], duration=cd.get("duration"),
            audio_lang=s.get("defaultAudioLanguage"), default_lang=s.get("defaultLanguage"),
            tags="|".join(s.get("tags", [])),
            views=int(st["viewCount"]) if "viewCount" in st else None,
            likes=int(st["likeCount"]) if "likeCount" in st else None,
            comments=int(st["commentCount"]) if "commentCount" in st else None))

stats = pd.DataFrame(rows)
out = hit_df.merge(stats, on="video_id", how="left")
out["snapshot_date"] = TODAY
out.to_csv(f"{DATA_DIR}/topic_videos_{TODAY}.csv", index=False)
print(f"Saved {len(out)} rows, {out.video_id.nunique()} unique videos. Quota used: ~{units}")
