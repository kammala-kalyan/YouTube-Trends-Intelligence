"""Clean raw snapshots in data/ and build the star schema in data/model/ for Power BI.

Safe to rerun any time: it rebuilds every table from all raw files.
"""
import glob, os, re, math
import numpy as np
import pandas as pd
from config import DATA_DIR
from keywords import all_keywords, ANCHOR

OUT = os.path.join(DATA_DIR, "model")
os.makedirs(OUT, exist_ok=True)


def read_all(pattern):
    files = sorted(glob.glob(os.path.join(DATA_DIR, pattern)))
    if not files:
        return pd.DataFrame()
    return pd.concat([pd.read_csv(f) for f in files], ignore_index=True)


def save(df, name):
    df.to_csv(os.path.join(OUT, f"{name}.csv"), index=False, encoding="utf-8-sig")
    print(f"  {name:<24} {len(df):>7,} rows")


# ---------------------------------------------------------------- languages
LANG_NAMES = {
    "hi": "Hindi", "en": "English", "ta": "Tamil", "te": "Telugu", "kn": "Kannada",
    "ml": "Malayalam", "bn": "Bengali", "mr": "Marathi", "pa": "Punjabi", "gu": "Gujarati",
    "or": "Odia", "bh": "Bhojpuri", "ur": "Urdu", "as": "Assamese", "ne": "Nepali",
}
# Unicode block -> (script name, most likely language)
SCRIPTS = [
    (0x0900, 0x097F, "Devanagari", "hi"), (0x0980, 0x09FF, "Bengali", "bn"),
    (0x0A00, 0x0A7F, "Gurmukhi", "pa"), (0x0A80, 0x0AFF, "Gujarati", "gu"),
    (0x0B00, 0x0B7F, "Odia", "or"), (0x0B80, 0x0BFF, "Tamil", "ta"),
    (0x0C00, 0x0C7F, "Telugu", "te"), (0x0C80, 0x0CFF, "Kannada", "kn"),
    (0x0D00, 0x0D7F, "Malayalam", "ml"), (0x0600, 0x06FF, "Arabic", "ur"),
]


def detect_script(text):
    """Dominant non-Latin script in the text, else Latin (or None if no letters)."""
    if not isinstance(text, str):
        return None, None
    counts = {}
    latin = 0
    for ch in text:
        cp = ord(ch)
        if ch.isascii():
            latin += ch.isalpha()
            continue
        for lo, hi, name, lang in SCRIPTS:
            if lo <= cp <= hi:
                counts[(name, lang)] = counts.get((name, lang), 0) + 1
                break
    if counts:
        return max(counts, key=counts.get)
    return ("Latin", "en") if latin else (None, None)


def norm_lang(code):
    if not isinstance(code, str) or code.lower() in ("zxx", "und", ""):
        return None
    return code.split("-")[0].lower()


def resolve_language(row):
    """audio language > non-Latin title script > default language > Latin title."""
    script, script_lang = detect_script(f"{row['title']} ")
    audio = norm_lang(row.get("audio_lang"))
    if audio:
        return audio, "audio track", script
    if script and script != "Latin":
        return script_lang, "title script", script
    default = norm_lang(row.get("default_lang"))
    if default:
        return default, "default language", script
    if script == "Latin":
        return "en", "title script", script
    return "unknown", "unknown", script


# ---------------------------------------------------------------- helpers
DUR_RE = re.compile(r"P(?:(\d+)D)?(?:T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?)?")


def duration_seconds(iso):
    if not isinstance(iso, str):
        return None
    m = DUR_RE.fullmatch(iso)
    if not m:
        return None
    d, h, mi, s = (int(x) if x else 0 for x in m.groups())
    return d * 86400 + h * 3600 + mi * 60 + s


def duration_bucket(sec):
    if sec is None or pd.isna(sec) or sec == 0:
        return "Live / unknown"
    for limit, label in [(60, "1. Under 1 min"), (180, "2. 1-3 min"), (600, "3. 3-10 min"),
                         (1200, "4. 10-20 min"), (3600, "5. 20-60 min")]:
        if sec <= limit:
            return label
    return "6. Over 1 hour"


STATE_ZONE = {
    "Andhra Pradesh": "South", "Karnataka": "South", "Kerala": "South", "Tamil Nadu": "South",
    "Telangana": "South", "Puducherry": "South", "Lakshadweep": "South",
    "Andaman and Nicobar Islands": "South",
    "Delhi": "North", "Haryana": "North", "Himachal Pradesh": "North",
    "Jammu and Kashmir": "North", "Ladakh": "North", "Punjab": "North", "Chandigarh": "North",
    "Uttarakhand": "North", "Uttar Pradesh": "North", "Rajasthan": "North",
    "Bihar": "East", "Jharkhand": "East", "Odisha": "East", "West Bengal": "East",
    "Assam": "Northeast", "Arunachal Pradesh": "Northeast", "Manipur": "Northeast",
    "Meghalaya": "Northeast", "Mizoram": "Northeast", "Nagaland": "Northeast",
    "Sikkim": "Northeast", "Tripura": "Northeast",
    "Goa": "West", "Gujarat": "West", "Maharashtra": "West",
    "Dadra and Nagar Haveli and Daman and Diu": "West", "Dadra and Nagar Haveli": "West",
    "Daman and Diu": "West",
    "Madhya Pradesh": "Central", "Chhattisgarh": "Central",
}

# ================================================================= load raw
print("Loading raw files...")
trending = read_all("trending_videos_*.csv")
topics = read_all("topic_videos_*.csv")
channels = read_all("channels_*.csv")
supply = read_all("keyword_supply_*.csv")
t_time = read_all("trends_over_time_*.csv")
t_state = read_all("trends_by_state_*.csv")
cats = pd.read_csv(os.path.join(DATA_DIR, "dim_category.csv"))
print(f"  trending {len(trending):,} | topics {len(topics):,} | channels {len(channels):,} | "
      f"supply {len(supply):,} | trends-time {len(t_time):,} | trends-state {len(t_state):,}")

print("Building tables...")
# ================================================================= dim_category
dim_category = (cats.drop_duplicates("category_id")
                [["category_id", "category_name", "assignable"]])
save(dim_category, "dim_category")

# ================================================================= videos
video_cols = ["video_id", "title", "channel_id", "channel_title", "category_id",
              "published_at", "duration", "audio_lang", "default_lang", "tags",
              "views", "likes", "comments", "snapshot_date"]
trending["source"] = "trending"
topics = topics.dropna(subset=["title"]) if not topics.empty else topics
topics["source"] = "topic search"
all_videos = pd.concat([trending[video_cols + ["source"]],
                        topics[video_cols + ["source"]] if not topics.empty else None],
                       ignore_index=True)

# ---- dim_video: latest known metadata per video
latest = (all_videos.sort_values("snapshot_date")
          .drop_duplicates("video_id", keep="last").copy())
lang = latest.apply(resolve_language, axis=1, result_type="expand")
latest[["language", "language_source", "title_script"]] = lang
latest["duration_sec"] = latest["duration"].map(duration_seconds)
latest["duration_bucket"] = latest["duration_sec"].map(duration_bucket)
text = (latest["title"].fillna("") + " " + latest["tags"].fillna("")).str.lower()
latest["is_short"] = (latest["duration_sec"].fillna(9999) <= 60) | text.str.contains("#shorts")
latest["published_at"] = pd.to_datetime(latest["published_at"], utc=True, format="ISO8601").dt.tz_localize(None)
latest["published_date"] = latest["published_at"].dt.date
latest["publish_hour_ist"] = (latest["published_at"] + pd.Timedelta(hours=5, minutes=30)).dt.hour
latest["tag_count"] = latest["tags"].fillna("").map(lambda t: len(t.split("|")) if t else 0)
latest["title_length"] = latest["title"].str.len()
dim_video = latest[["video_id", "title", "channel_id", "category_id", "published_at",
                    "published_date", "publish_hour_ist", "duration_sec", "duration_bucket",
                    "is_short", "language", "language_source", "title_script",
                    "tag_count", "title_length", "tags"]]
save(dim_video, "dim_video")

# ---- fact_video_snapshot: one row per video per snapshot day
trend_ranks = trending.assign(
    rank_overall=np.where(trending["category_chart"].astype(str) == "overall",
                          trending["rank"], np.nan),
    rank_category=np.where(trending["category_chart"].astype(str) != "overall",
                           trending["rank"], np.nan))
trend_ranks = (trend_ranks.groupby(["snapshot_date", "video_id"])
               .agg(trending_rank_overall=("rank_overall", "min"),
                    trending_rank_category=("rank_category", "min"),
                    charts_count=("category_chart", "nunique"))
               .reset_index())
fact = (all_videos.groupby(["snapshot_date", "video_id"])
        .agg(views=("views", "max"), likes=("likes", "max"), comments=("comments", "max"),
             in_trending=("source", lambda s: (s == "trending").any()),
             in_topic_search=("source", lambda s: (s == "topic search").any()))
        .reset_index()
        .merge(trend_ranks, on=["snapshot_date", "video_id"], how="left"))
fact["snapshot_date"] = pd.to_datetime(fact["snapshot_date"]).dt.date
pub = dim_video.set_index("video_id")["published_at"]
age_days = (pd.to_datetime(fact["snapshot_date"]) - fact["video_id"].map(pub)).dt.total_seconds() / 86400
fact["days_since_publish"] = age_days.clip(lower=0).round(2)
fact["views_per_day"] = (fact["views"] / (fact["days_since_publish"] + 1)).round(0)
fact["likes_hidden"] = fact["likes"].isna()
fact["engagement_rate"] = ((fact["likes"].fillna(0) + fact["comments"].fillna(0))
                           / fact["views"].where(fact["views"] > 0))
fact["charts_count"] = fact["charts_count"].fillna(0).astype(int)
save(fact, "fact_video_snapshot")

# ---- bridge_keyword_video: which keyword search returned which video
if not topics.empty:
    bridge = topics[["snapshot_date", "keyword", "video_id"]].drop_duplicates()
    bridge["snapshot_date"] = pd.to_datetime(bridge["snapshot_date"]).dt.date
    save(bridge, "bridge_keyword_video")

# ================================================================= channels
ch = channels.sort_values("snapshot_date")
dim_channel = ch.drop_duplicates("channel_id", keep="last").copy()
# channels seen on videos but never fetched: keep them so relationships don't break
missing = (latest[~latest["channel_id"].isin(dim_channel["channel_id"])]
           [["channel_id", "channel_title"]].drop_duplicates("channel_id")
           .rename(columns={"channel_title": "channel_name"}))
dim_channel = pd.concat([dim_channel, missing], ignore_index=True)
dim_channel["country"] = dim_channel["country"].fillna("Unknown")
dim_channel["channel_origin"] = np.select(
    [dim_channel["country"] == "IN", dim_channel["country"] == "Unknown"],
    ["India", "Unknown"], "Outside India")
created = pd.to_datetime(dim_channel["created_at"], utc=True, format="ISO8601").dt.tz_localize(None)
dim_channel["created_at"] = created
dim_channel["channel_age_years"] = ((pd.Timestamp.now() - created).dt.days / 365.25).round(1)
dim_channel["subscriber_tier"] = pd.cut(
    dim_channel["subscribers"], [-1, 1e4, 1e5, 1e6, 1e7, float("inf")],
    labels=["1. <10K", "2. 10K-100K", "3. 100K-1M", "4. 1M-10M", "5. 10M+"]
).astype(str).replace("nan", "Hidden / unknown")
save(dim_channel[["channel_id", "channel_name", "country", "channel_origin", "created_at",
                  "channel_age_years", "subscribers", "subscribers_hidden", "subscriber_tier",
                  "total_views", "video_count"]], "dim_channel")

fact_channel = ch[["snapshot_date", "channel_id", "subscribers", "total_views", "video_count"]].copy()
fact_channel["snapshot_date"] = pd.to_datetime(fact_channel["snapshot_date"]).dt.date
save(fact_channel.drop_duplicates(["snapshot_date", "channel_id"]), "fact_channel_snapshot")

# ================================================================= keywords
kw_rows = [dict(keyword=kw, topic_group=cat, keyword_lang=lg) for cat, kw, lg in all_keywords()]
kw_rows.append(dict(keyword=ANCHOR, topic_group="Anchor", keyword_lang="en"))
dim_keyword = pd.DataFrame(kw_rows)
dim_keyword["keyword_language"] = dim_keyword["keyword_lang"].map(LANG_NAMES)
dim_keyword["keyword_script"] = dim_keyword["keyword"].map(lambda k: detect_script(k)[0])
dim_keyword["is_regional"] = dim_keyword["keyword_script"] != "Latin"
dim_keyword["is_anchor"] = dim_keyword["keyword"] == ANCHOR

# ---- fact_trends_keyword: weekly interest, normalized across batches via the anchor
fact_trends = pd.DataFrame()
if not t_time.empty:
    t = t_time.copy()
    t["date"] = pd.to_datetime(t["date"]).dt.date
    # scale factor per (snapshot, batch) = reference anchor mean / this batch's anchor mean
    anc = (t[t["keyword"] == ANCHOR].groupby(["snapshot_date", "batch_id"])["interest"]
           .mean().rename("anchor_mean").reset_index())
    anc["ref"] = anc.groupby("snapshot_date")["anchor_mean"].transform("median")
    anc["scale"] = anc["ref"] / anc["anchor_mean"].replace(0, np.nan)
    t = t.merge(anc[["snapshot_date", "batch_id", "scale"]], on=["snapshot_date", "batch_id"])
    t["interest_norm"] = (t["interest"] * t["scale"]).round(3)
    # each run returns the full 5-year history, so per keyword keep only its latest snapshot.
    # the anchor appears in every batch: average its normalized copies into one series.
    is_latest = t["snapshot_date"] == t.groupby("keyword")["snapshot_date"].transform("max")
    kw_part = t[(t["keyword"] != ANCHOR) & is_latest]
    anchor_part = (t[(t["keyword"] == ANCHOR) & (t["snapshot_date"] == t["snapshot_date"].max())]
                   .groupby(["date", "keyword", "snapshot_date"], as_index=False)
                   .agg(interest=("interest", "mean"), interest_norm=("interest_norm", "mean")))
    fact_trends = pd.concat([kw_part, anchor_part], ignore_index=True)
    fact_trends = fact_trends.rename(columns={"interest": "interest_raw"})
    fact_trends = fact_trends[["date", "keyword", "interest_raw", "interest_norm", "snapshot_date"]]
    save(fact_trends, "fact_trends_keyword")

# ---- fact_trends_region: state-level interest, comparable via ratio to the anchor
if not t_state.empty:
    s = t_state.copy()
    s = s[s["snapshot_date"] == s.groupby("keyword")["snapshot_date"].transform("max")]
    anc = (s[s["keyword"] == ANCHOR][["snapshot_date", "batch_id", "state", "interest"]]
           .rename(columns={"interest": "anchor_interest"}))
    s = s.merge(anc, on=["snapshot_date", "batch_id", "state"], how="left")
    s["ratio_to_anchor"] = s["interest"] / s["anchor_interest"].where(s["anchor_interest"] > 0)
    # anchor: one row per state (identical across batches up to sampling noise)
    s_kw = s[s["keyword"] != ANCHOR]
    s_anchor = (s[s["keyword"] == ANCHOR].groupby(["state", "keyword", "snapshot_date"], as_index=False)
                .agg(interest=("interest", "mean")))
    s_anchor["ratio_to_anchor"] = 1.0
    s = pd.concat([s_kw, s_anchor], ignore_index=True)
    # 0-100 per keyword: 100 = state where the keyword is strongest relative to cricket
    s["state_index"] = (100 * s["ratio_to_anchor"]
                        / s.groupby("keyword")["ratio_to_anchor"].transform("max")).round(1)
    s["zone"] = s["state"].map(STATE_ZONE).fillna("Other")
    s["state_map_name"] = s["state"] + ", India"   # helps Power BI's map geocode correctly
    s = s.rename(columns={"interest": "interest_share"})
    save(s[["keyword", "state", "state_map_name", "zone", "interest_share", "ratio_to_anchor",
            "state_index", "snapshot_date"]], "fact_trends_region")
    dim_state = (s[["state", "state_map_name", "zone"]].drop_duplicates("state")
                 .sort_values("state"))
    save(dim_state, "dim_state")

# ---- fact_keyword_opportunity: demand vs supply per keyword (content gap)
opp = dim_keyword[~dim_keyword["is_anchor"]][["keyword"]].copy()
if not fact_trends.empty:
    ft = fact_trends.copy()
    ft["date"] = pd.to_datetime(ft["date"])
    end = ft["date"].max()
    recent = ft[ft["date"] > end - pd.Timedelta(weeks=12)].groupby("keyword")["interest_norm"].mean()
    prior = ft[(ft["date"] <= end - pd.Timedelta(weeks=12)) &
               (ft["date"] > end - pd.Timedelta(weeks=24))].groupby("keyword")["interest_norm"].mean()
    last_year = ft[(ft["date"] > end - pd.Timedelta(weeks=64)) &
                   (ft["date"] <= end - pd.Timedelta(weeks=52))].groupby("keyword")["interest_norm"].mean()
    opp["demand_index"] = opp["keyword"].map(recent).round(2)
    opp["growth_12w"] = ((opp["demand_index"] - opp["keyword"].map(prior))
                         / opp["keyword"].map(prior).replace(0, np.nan)).round(3)
    opp["growth_yoy"] = ((opp["demand_index"] - opp["keyword"].map(last_year))
                         / opp["keyword"].map(last_year).replace(0, np.nan)).round(3)
    opp["trend_status"] = np.select([opp["growth_12w"] > 0.15, opp["growth_12w"] < -0.15],
                                    ["Rising", "Declining"], "Stable")
    # interest rounds to 0 for low-volume terms, so growth can't be computed
    opp.loc[opp["growth_12w"].isna(), "trend_status"] = "Low volume"
if not supply.empty:
    sup = supply.sort_values("snapshot_date").drop_duplicates("keyword", keep="last")
    opp = opp.merge(sup[["keyword", "videos_last_30d_est", "snapshot_date"]]
                    .rename(columns={"snapshot_date": "supply_snapshot_date"}),
                    on="keyword", how="left")
if not topics.empty:
    tv = topics.sort_values("snapshot_date")
    tv = tv[tv["snapshot_date"] == tv.groupby("keyword")["snapshot_date"].transform("max")]
    subs = dim_channel.set_index("channel_id")["subscribers"]
    tv = tv.assign(small_channel=tv["channel_id"].map(subs) < 100_000)
    agg = tv.groupby("keyword").agg(top_videos_median_views=("views", "median"),
                                    top_videos_avg_views=("views", "mean"),
                                    small_channel_share=("small_channel", "mean"))
    agg[["top_videos_median_views", "top_videos_avg_views"]] = \
        agg[["top_videos_median_views", "top_videos_avg_views"]].round(0)
    opp = opp.merge(agg.round(3), left_on="keyword", right_index=True, how="left")
if "videos_last_30d_est" in opp.columns:
    opp["supply_capped"] = opp["videos_last_30d_est"] >= 1_000_000
if {"demand_index", "growth_12w", "small_channel_share"} <= set(opp.columns):
    # totalResults is capped at 1M for most keywords, so it can't rank supply.
    # Instead: high demand + growing + small channels reach the top = open opportunity.
    # Percentile ranks keep the three signals on the same 0-1 scale. Blank until searched.
    scored = opp["small_channel_share"].notna()
    pct = lambda c: opp.loc[scored, c].rank(pct=True).fillna(0)
    opp.loc[scored, "content_gap_score"] = (100 * (0.4 * pct("demand_index")
                                                   + 0.3 * pct("growth_12w")
                                                   + 0.3 * pct("small_channel_share"))).round(1)
save(opp, "fact_keyword_opportunity")
save(dim_keyword, "dim_keyword")

# ================================================================= dim_language
langs = set(dim_video["language"].dropna()) | set(dim_keyword["keyword_lang"])
dim_language = pd.DataFrame({"language": sorted(langs)})
dim_language["language_name"] = dim_language["language"].map(LANG_NAMES).fillna(
    dim_language["language"].str.upper())
dim_language["is_indian_regional"] = ~dim_language["language"].isin(["en", "unknown"]) & \
    dim_language["language"].isin(LANG_NAMES)
save(dim_language, "dim_language")

# ================================================================= dim_date
dates = list(pd.to_datetime(fact["snapshot_date"]))
dates += list(pd.to_datetime(dim_video["published_date"].dropna()))
if not fact_trends.empty:
    dates += list(pd.to_datetime(fact_trends["date"]))
start = max(min(dates), pd.Timestamp("2015-01-01"))
rng = pd.date_range(start.normalize(), max(dates).normalize(), freq="D")
dim_date = pd.DataFrame({"date": rng.date})
d = pd.Series(rng)
dim_date["year"] = d.dt.year
dim_date["quarter"] = "Q" + d.dt.quarter.astype(str)
dim_date["month_num"] = d.dt.month
dim_date["month_name"] = d.dt.strftime("%b")
dim_date["year_month"] = d.dt.strftime("%Y-%m")
dim_date["week_start"] = (d - pd.to_timedelta(d.dt.day_of_week, unit="D")).dt.date
dim_date["weekday"] = d.dt.strftime("%a")
dim_date["weekday_num"] = d.dt.day_of_week + 1
save(dim_date, "dim_date")

print(f"Done. Tables written to {OUT}")
