# How to use this repo

Technical guide for **India YouTube Trends**: how to open the dashboard, how the daily data pipeline works, how to run it yourself, and what's in the data. For what the project is and why it exists, see the [README](../README.md).

---

## 1. Open the dashboard (2 minutes)

You need **Power BI Desktop** (free, Windows).

1. Clone this repo, or download it as a ZIP and unzip it.
2. Open **`Dashboards/India YouTube Trends.pbip`** in Power BI Desktop. (Don't use the `.pbix`: it's an older copy.)
3. Click **Home → Refresh**. The first time, Power BI asks how to connect to `raw.githubusercontent.com`: choose **Anonymous** → **Connect**.

The dashboard reads its data straight from [`data/model/`](../data/model) in this repo, so it always shows the latest daily data. There are no local paths or setup to change. It opens empty until you click Refresh, because the data cache isn't stored in git.

---

## 2. How the data updates every day

[`.github/workflows/daily.yml`](../.github/workflows/daily.yml) runs on GitHub's servers every day at **9:00 AM IST**:

1. Runs [`run_daily.py`](../run_daily.py), which calls the scripts below in order.
2. Commits **only the `data/` folder** (as `data: YYYY-MM-DD`, by `github-actions[bot]`). Code and dashboard files are never changed by the job.
3. If a step fails (for example, Google Trends blocks the GitHub server), the data that did arrive is still committed, **previous data is kept**, and the run is marked failed, so GitHub sends an email. The run page says which step failed.

| Script | What it does | YouTube quota | How often |
|---|---|---|---|
| `fetch_trending.py` | India's trending chart, overall and per category | ~60 units | daily |
| `fetch_topics.py` | Top videos from the last 30 days for a third of the keywords (rotates daily) | ~6,200 units | daily |
| `fetch_channels.py` | Stats for every channel seen in the latest trending and topic files | ~55 units | daily |
| `fetch_trends.py` | Google Trends (YouTube Search, India): 5-year weekly interest and state breakdown, for a seventh of the keywords each day plus any new keyword, and cricket's state profile | none (rate-limited) | daily |
| `build_model.py` | Cleans everything and writes the star schema to `data/model/` | none | every run |

The free YouTube Data API quota is 10,000 units a day; the scripts stop at 9,000.

**History is the main asset**: the YouTube API only shows current numbers, so old data files are never deleted.

### Keywords

[`keywords.py`](../keywords.py) holds **184 keywords in 26 topic groups**.
- Regional keywords follow how people actually search: **topic + language in English letters** ("UPSC Telugu", "share market Tamil"), for Telugu, Tamil, Kannada, Malayalam, Bengali, Marathi and Gujarati, plus older native-script terms.
- Five optional niche groups sit behind `INCLUDE_TIER2`.
- Before relying on new keywords, run `python test_keywords.py`: it checks keywords without Trends data against Google Trends and lists any that return nothing.

### Making Google Trends comparable

Google Trends scores every request 0–100 against the biggest term in that request (max 5 terms). To put all 184 keywords on one scale:
- Every batch includes a **reference term**: `cricket` for most keywords.
- Small keywords round to 0 next to cricket, so they use a **chain of smaller references**, `Excel` and then `bike review`. Each reference is measured one level up, so everything converts back to the cricket scale. References must be searched nationwide, because state results are chained through them too.
- A keyword that comes back all zero moves to a smaller reference automatically the next day. `python fetch_trends.py --dry` shows the day's plan without contacting Google.
- State scores are **popularity within the state**: a keyword's ratio to cricket in that state × cricket's own popularity there, scaled 0–100 per keyword.

---

## 3. Set up the daily job on your own fork (once)

1. Get a free **YouTube Data API v3** key (Google Cloud Console → APIs & Services).
2. Push the repo to GitHub, including `data/`.
3. Add a repository secret named **`YOUTUBE_API_KEY`** (Settings → Secrets and variables → Actions → New repository secret).
4. Actions tab → **Daily data pipeline** → **Run workflow** to test it once.
5. Turn on failure emails: GitHub → Settings → Notifications → Actions.

Always `git pull` before you push: the daily job commits to `data/` every morning.

---

## 4. Run the pipeline on your computer (optional)

```
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env      # then paste your YouTube API key into .env
python test_key.py          # checks the key works
python run_daily.py         # add --trends to pull Google Trends for every keyword at once
python test_keywords.py     # checks new keywords return Google Trends data
```

Don't schedule it on your PC as well: GitHub Actions is the only scheduler.

---

## 5. What's in the data (`data/model/`)

A star schema:
- **Facts:** `fact_video_snapshot` (video × day: views, likes, comments, ranks, engagement), `fact_channel_snapshot`, `fact_trends_keyword` (keyword × week, raw and normalized interest), `fact_trends_region` (keyword × state), `fact_keyword_opportunity` (demand, 12-week growth, small-channel share).
- **Dimensions:** `dim_video` (detected language, duration bucket, Shorts flag), `dim_channel`, `dim_category`, `dim_keyword`, `dim_language`, `dim_state`, `dim_date`.
- **Bridge:** `bridge_keyword_video` (which keyword search found which video). It lets one Topic filter drive both search trends and video stats.

**Video language** is decided in this order: Indian-language audio track → native script in the title → one Indian language named in the title/tags ("Telugu", "Hindi dubbed") → English audio track → default language → English letters; then the channel's main language relabels weak cases.

---

## 6. Changing the dashboard

The dashboard was generated by [`build_report.py`](../build_report.py) and then finished by hand in Power BI. **Don't run `build_report.py` again**: it rebuilds every page from scratch and would overwrite the hand-made changes. Make further changes directly in Power BI Desktop.

---

## 7. Data limits

- **The map shows searches, not views.** YouTube doesn't share viewer location for public videos, so Google Trends search popularity by state is used as the audience signal.
- States/UTs **under 2 million people** are hidden on the audience page: a handful of searches swings their scores.
- The trending chart covers trending videos, not all of YouTube; topic searches add the top recent videos for every keyword.
- Google Trends values are relative and sampled, so they vary slightly between runs.
- The YouTube search API caps result counts at 1,000,000, so competition is measured as the **share of top videos from channels under 100K subscribers**, not a raw count.
- Some regional keywords are too small for Google Trends even with the reference chain; they're still used for YouTube video search.
- Like counts can be hidden by creators; about 20% of channels have no country set.
- Video patterns (format, length, title length) describe popular videos. They're not proof of cause.
