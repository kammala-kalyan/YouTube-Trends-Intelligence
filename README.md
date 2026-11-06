# India YouTube Trends & Content Intelligence

A Power BI dashboard about what India watches and searches on YouTube. It uses public YouTube Data API v3 data and Google Trends (YouTube Search), so you don't need to own a channel.

## Pipeline

| Script | What it does | Quota | How often |
|---|---|---|---|
| `fetch_trending.py` | India trending chart, overall and per category | ~60 units | daily |
| `fetch_topics.py` | Top videos from the last 30 days for one-third of the keywords (rotates daily), plus supply estimate | ~3,600 units | daily |
| `fetch_channels.py` | Stats for every channel seen in the latest trending and topic files | ~55 units | daily |
| `fetch_trends.py` | Google Trends 5-year weekly interest and state breakdown for every keyword | none (rate-limited) | weekly |
| `build_model.py` | Cleans everything and writes the star schema to `data/model/` | none | after each run |
| `run_daily.py` | Runs all of the above in order; Trends only when the last run is 7+ days old | | daily |

Keywords live in `keywords.py`: 105 keywords across 13 topic groups, including regional terms in Hindi, Tamil, Telugu, Kannada, Malayalam, Bengali, Marathi and Punjabi. The anchor term `cricket` is added to every Trends batch so values can be compared across batches.

### Setup

```
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env      # then paste your YouTube API key
python run_daily.py
```

### Schedule it (Windows Task Scheduler)

Create Basic Task → Daily (for example, 9:00 AM) → Start a program → `run_daily.bat` (full path). Under Conditions, untick "Start only if on AC power". Logs go to `logs/`.

History is the main asset, since the YouTube API only shows current numbers. Keep the daily run going.

## Star schema (`data/model/`)

- **Facts:** `fact_video_snapshot` (video × day: views, likes, comments, ranks, engagement), `fact_channel_snapshot`, `fact_trends_keyword` (keyword × week, raw and anchor-normalized interest), `fact_trends_region` (keyword × state), `fact_keyword_opportunity` (demand, growth, supply, content gap score)
- **Dimensions:** `dim_video` (with detected language, duration bucket, Shorts flag), `dim_channel`, `dim_category`, `dim_keyword`, `dim_language`, `dim_state`, `dim_date`
- **Bridge:** `bridge_keyword_video` (which keyword search returned which video)

See [POWERBI_SETUP.md](POWERBI_SETUP.md) for import steps, relationships and DAX.

## Data caveats

- The trending chart covers only trending videos, not all of YouTube.
- Google Trends values are relative indexes and sampled, so they vary slightly between runs.
- The search API's `totalResults` is capped at 1,000,000, so the content gap score uses demand, growth and small-channel share instead.
- Like counts can be hidden by creators.
- About 22% of channels have no country set; these are labelled "Unknown".
