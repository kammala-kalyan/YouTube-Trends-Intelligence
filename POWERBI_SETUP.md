# Power BI setup

All tables come from `data/model/` (built by `python build_model.py`). Rerun the pipeline, then hit **Refresh** in Power BI.

## 1. Import with a folder parameter (keeps the report portable)

1. **Home → Transform data → Manage Parameters → New**: name `DataFolder`, type Text, value = full path to `data\model\` (end with a backslash).
2. For each CSV: **Get data → Text/CSV**, pick the file, click **Transform Data**. In the formula bar, replace the hard-coded path with `DataFolder & "fact_video_snapshot.csv"` (and so on). Set **File origin = 65001: Unicode (UTF-8)** so Hindi, Tamil, etc. display correctly.
3. Check column types: dates as **Date** (`snapshot_date`, `date`, `published_date`, `week_start`), `published_at`/`created_at` as **Date/Time**, the counts as **Whole number**, rates and indexes as **Decimal number**, `is_*` columns as **True/False**.

Tables: `dim_date`, `dim_video`, `dim_channel`, `dim_category`, `dim_language`, `dim_keyword`, `dim_state`, `fact_video_snapshot`, `fact_channel_snapshot`, `fact_trends_keyword`, `fact_trends_region`, `fact_keyword_opportunity`, `bridge_keyword_video`.

## 2. Relationships (Model view)

All are many-to-one, single direction, unless noted.

| From (many) | To (one) |
|---|---|
| fact_video_snapshot[video_id] | dim_video[video_id] |
| fact_video_snapshot[snapshot_date] | dim_date[date] |
| dim_video[channel_id] | dim_channel[channel_id] |
| dim_video[category_id] | dim_category[category_id] |
| dim_video[language] | dim_language[language] |
| fact_channel_snapshot[channel_id] | dim_channel[channel_id] |
| fact_trends_keyword[keyword] | dim_keyword[keyword] |
| fact_trends_keyword[date] | dim_date[date] |
| fact_trends_region[keyword] | dim_keyword[keyword] |
| fact_trends_region[state] | dim_state[state] |
| fact_keyword_opportunity[keyword] | dim_keyword[keyword] (one-to-one, single direction from dim_keyword) |
| bridge_keyword_video[keyword] | dim_keyword[keyword] |
| bridge_keyword_video[video_id] | dim_video[video_id], **cross-filter: Both** (lets a keyword slicer filter videos) |

Leave `fact_channel_snapshot[snapshot_date] → dim_date[date]` **inactive** to avoid ambiguous paths. Use `USERELATIONSHIP` when you need it.

Mark `dim_date` as a date table: **Table tools → Mark as date table → date**.

## 3. Measures

Create an empty table called `_Measures` (Enter data → OK) and put the measures there.

```DAX
Videos Tracked = DISTINCTCOUNT(fact_video_snapshot[video_id])

Latest Snapshot = MAX(fact_video_snapshot[snapshot_date])

Total Views =
VAR d = [Latest Snapshot]
RETURN CALCULATE(SUM(fact_video_snapshot[views]), fact_video_snapshot[snapshot_date] = d)

Engagement Rate =
DIVIDE(SUM(fact_video_snapshot[likes]) + SUM(fact_video_snapshot[comments]),
       SUM(fact_video_snapshot[views]))

Avg Views per Day = AVERAGE(fact_video_snapshot[views_per_day])

Median Views = MEDIAN(fact_video_snapshot[views])

Shorts Share =
DIVIDE(CALCULATE([Videos Tracked], dim_video[is_short] = TRUE()), [Videos Tracked])

Regional Language Share =
DIVIDE(CALCULATE([Videos Tracked], dim_language[is_indian_regional] = TRUE()), [Videos Tracked])

Trending Videos =
CALCULATE([Videos Tracked], fact_video_snapshot[in_trending] = TRUE())

Top Category =
MAXX(TOPN(1, VALUES(dim_category[category_name]), [Videos Tracked]),
     dim_category[category_name])

Channels = DISTINCTCOUNT(dim_video[channel_id])

-- Google Trends (normalized across batches using the "cricket" anchor)
Interest = AVERAGE(fact_trends_keyword[interest_norm])

Interest MoM % =
VAR cur  = CALCULATE([Interest], DATESINPERIOD(dim_date[date], MAX(dim_date[date]), -1, MONTH))
VAR prev = CALCULATE([Interest], DATEADD(DATESINPERIOD(dim_date[date], MAX(dim_date[date]), -1, MONTH), -1, MONTH))
RETURN DIVIDE(cur - prev, prev)

Interest YoY % =
VAR cur  = CALCULATE([Interest], DATESINPERIOD(dim_date[date], MAX(dim_date[date]), -3, MONTH))
VAR prev = CALCULATE([Interest], SAMEPERIODLASTYEAR(DATESINPERIOD(dim_date[date], MAX(dim_date[date]), -3, MONTH)))
RETURN DIVIDE(cur - prev, prev)

Trend Status =
SWITCH(TRUE(),
    ISBLANK([Interest MoM %]), "Low volume",
    [Interest MoM %] > 0.15, "Rising",
    [Interest MoM %] < -0.15, "Declining",
    "Stable")

-- Regions
State Index = AVERAGE(fact_trends_region[state_index])       -- 0-100 within a keyword
Interest vs Cricket = AVERAGE(fact_trends_region[ratio_to_anchor])

-- Opportunities
Content Gap Score = AVERAGE(fact_keyword_opportunity[content_gap_score])
Demand Index = AVERAGE(fact_keyword_opportunity[demand_index])
Supply (30d videos, est.) = SUM(fact_keyword_opportunity[videos_last_30d_est])
Growth 12w % = AVERAGE(fact_keyword_opportunity[growth_12w])
```

Format: `Engagement Rate`, `Shorts Share`, `Regional Language Share`, and the `%` measures as **Percentage, 1 decimal**. `Total Views` as **Whole number, display units Auto**.

## 4. Notes to show on the dashboard

- **Trending ≠ all of YouTube.** The `mostPopular` chart lists only trending videos (survivorship bias).
- **Trends values are relative.** Google Trends gives a 0–100 index, not search counts. Keywords are made comparable by dividing by the "cricket" anchor, so values mean "interest relative to cricket".
- **Content gap score (0–100)** = 40% demand (Trends interest, last 12 weeks) + 30% growth (vs the previous 12 weeks) + 30% small-channel share (share of the keyword's top recent videos from channels under 100K subscribers), each ranked as a percentile. The search API's video count (`videos_last_30d_est`) is capped at 1,000,000 for most keywords, so it isn't used for ranking. Keywords get a score once the daily rotation has searched them (all within 3 days).
- **Hidden likes** are blank, not zero (`likes_hidden` flag).
- **Language** comes from the video's audio track; if that's missing, the title's script; then the default language.
