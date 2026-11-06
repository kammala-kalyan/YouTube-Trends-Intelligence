# Power BI technical reference

Everything technical behind the **India YouTube Trends** dashboard: the tools, how the data is loaded, the data model, every DAX formula, and the design strategies used in Power BI. For what the project is, see the [README](../README.md); for the data pipeline, see [ARCHITECTURE.md](ARCHITECTURE.md); for setup, see [HOW_TO_USE.md](HOW_TO_USE.md).

**Contents:** [1. Tools and technologies](#1-tools-and-technologies) · [2. Loading the data (Power Query)](#2-loading-the-data-power-query) · [3. The data model](#3-the-data-model) · [4. DAX strategies](#4-dax-strategies-explained) · [5. Report design strategies](#5-report-design-strategies) · [6. Report as code](#6-report-as-code-pbip--pbir--tmdl) · [7. Full DAX reference](#7-full-dax-reference)

---

## 1. Tools and technologies

| Area | Technology | Used for |
|---|---|---|
| Dashboard | **Power BI Desktop** | The 4-page report, the data model and all DAX |
| Report format | **PBIP project** (`.pbip`) with **PBIR** (report as JSON files) and **TMDL** (model as text files) | Keeping the whole report and model in git as readable text; every change is reviewable |
| Data loading | **Power Query (M)**: `Web.Contents`, `Csv.Document`, a `DataFolder` parameter | Reading the 13 CSV tables straight from the public GitHub repo |
| Calculations | **DAX**: 88 measures, 13 calculated columns | KPIs, time intelligence, dynamic headlines, conditional colours, filters |
| Maps | Power BI **Filled map** (Bing) | State-level heat map of India |
| Look and feel | Custom **JSON theme** (`youtube_light_theme.json`), **SVG icons** as image-URL measures | A clean, YouTube-style look; icons that render the same on every computer |
| Data pipeline | **Python 3.14**: pandas, NumPy, requests, pytrends, python-dotenv | Collecting, cleaning and modelling the data |
| Data sources | **YouTube Data API v3**, **Google Trends** (YouTube Search, India) via pytrends | Videos, channels and categories; 5-year search interest and state breakdown |
| Automation | **GitHub Actions** (daily cron, 9:00 AM IST), repository secrets | Running the pipeline daily and committing only the data |
| Hosting | **GitHub** (public repo; raw file URLs) | Storing the data and serving it to Power BI |
| Report generation | `build_report.py` (Python writing PBIR JSON + TMDL) | Building the pages, helper measures and calculated columns as code, then polished by hand |

---

## 2. Loading the data (Power Query)

- **Storage mode: Import.** The 13 tables are small CSVs (a few MB), so import gives the fastest visuals.
- **One parameter for the source:** `DataFolder` = `https://raw.githubusercontent.com/kammala-kalyan/YouTube-Trends-Intelligence/main/data/model/`. Every table builds its URL from it, so the source can be switched in one place (Transform data → Manage parameters).
- **Same three steps for every table:** download and parse the CSV, promote headers, set column types with a fixed culture (`en-US`) so dates and decimals parse the same on any computer.

```m
let
    Source = Csv.Document(Web.Contents(DataFolder & "fact_trends_keyword.csv"),
                          [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    Promoted = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    Typed = Table.TransformColumnTypes(Promoted,
              {{"date", type date}, {"keyword", type text}, {"interest_raw", type number},
               {"interest_norm", type number}, {"snapshot_date", type date}}, "en-US")
in
    Typed
```

- **Encoding 65001 (UTF-8)** keeps Hindi, Telugu, Tamil and other scripts intact.
- **Authentication:** Anonymous (public repo). Anyone who clones the repo just clicks Refresh.
- **Why load from GitHub, not a local folder:** the daily pipeline commits fresh data to the repo, so the dashboard always reads the latest version, with no local paths to fix on another computer.
- Heavy transformations happen **before** Power BI, in Python (`build_model.py`). Power Query only loads and types the data, which keeps refreshes fast and simple.

---

## 3. The data model

A **star schema**: fact tables hold the numbers, dimension tables describe them, plus one bridge table.

| Table | Type | Grain (one row per…) |
|---|---|---|
| `fact_video_snapshot` | Fact | video × day: views, likes, comments, trending rank, engagement |
| `fact_channel_snapshot` | Fact | channel × day: subscribers, total views, video count |
| `fact_trends_keyword` | Fact | search term × week: raw and normalised search interest (5 years) |
| `fact_trends_region` | Fact | search term × state: share, ratio to cricket, state score |
| `fact_keyword_opportunity` | Fact | search term: demand, 12-week growth, small-channel share |
| `dim_video` | Dimension | video: title, length, Shorts flag, language, publish time |
| `dim_channel` | Dimension | channel: subscribers, size tier, age, country |
| `dim_category` | Dimension | YouTube category |
| `dim_keyword` | Dimension | search term: topic group, language, script |
| `dim_language` | Dimension | language code and name |
| `dim_state` | Dimension | state: map name, zone |
| `dim_date` | Dimension | day (calendar table, Oct 2021 → latest snapshot) |
| `bridge_keyword_video` | Bridge | which search term found which video |
| `_Measures` | Measures only | all 88 measures, grouped in display folders |

### Relationships

| From (many) | To (one) | Notes |
|---|---|---|
| `fact_video_snapshot[video_id]` | `dim_video[video_id]` | |
| `fact_video_snapshot[snapshot_date]` | `dim_date[date]` | |
| `dim_video[channel_id]` | `dim_channel[channel_id]` | snowflake step: video → channel |
| `dim_video[category_id]` | `dim_category[category_id]` | |
| `dim_video[language]` | `dim_language[language]` | |
| `fact_channel_snapshot[channel_id]` | `dim_channel[channel_id]` | |
| `fact_channel_snapshot[snapshot_date]` | `dim_date[date]` | |
| `fact_trends_keyword[keyword]` | `dim_keyword[keyword]` | |
| `fact_trends_keyword[date]` | `dim_date[date]` | |
| `fact_trends_region[keyword]` | `dim_keyword[keyword]` | |
| `fact_trends_region[state]` | `dim_state[state]` | |
| `fact_keyword_opportunity[keyword]` | `dim_keyword[keyword]` | |
| `bridge_keyword_video[keyword]` | `dim_keyword[keyword]` | |
| `bridge_keyword_video[video_id]` | `dim_video[video_id]` | **both directions**: lets a keyword/topic filter reach videos |
| `dim_video[published_date]` | `dim_date[date]` | **inactive**: used only through `USERELATIONSHIP` in `Videos Published` |

**Two deliberate choices:**
- **The two-way bridge** is what lets one **Topic** slicer drive both search data and video data: Topic filters `dim_keyword` → bridge → `dim_video` → `fact_video_snapshot`. It's limited to the bridge, so no other relationship is ambiguous.
- **The inactive publish-date relationship** avoids two active paths between dates and videos (snapshot date and publish date). The measure that needs publish dates switches it on with `USERELATIONSHIP`.

**Display folders** in `_Measures`: Videos, Channels, Trends, Regions, Opportunities, Labels (text/headlines), Colors (conditional formatting), Icons (SVG images).

**Auto date/time** is best turned off (File → Options → Current file → Data load). The model has its own `dim_date`, and the hidden auto date tables only add size.

---

## 4. DAX strategies explained

**1. Counting each video once across daily snapshots.** Every video can appear on many days, so plain `SUM(views)` would double-count. Measures iterate the distinct videos and take each one's latest value:

```dax
Total Views = SUMX(VALUES(fact_video_snapshot[video_id]), CALCULATE(MAX(fact_video_snapshot[views])))
```

**2. Median instead of average.** One viral video (330M views) skews any average. `MEDIANX` over distinct videos gives what a *typical* popular video gets (`Median Views`).

**3. Honest engagement.** `Engagement Rate = (likes + comments) / views`, computed only over videos whose likes are public (`likes_hidden = FALSE`), so hidden likes don't drag the rate down.

**4. Time intelligence on weekly search data.** Month-on-month uses `DATESINPERIOD` and `DATEADD`; year-on-year uses `SAMEPERIODLASTYEAR`:

```dax
Interest MoM % =
VAR cur  = CALCULATE([Interest], DATESINPERIOD(dim_date[date], MAX(dim_date[date]), -1, MONTH))
VAR prev = CALCULATE([Interest], DATEADD(DATESINPERIOD(dim_date[date], MAX(dim_date[date]), -1, MONTH), -1, MONTH))
RETURN DIVIDE(cur - prev, prev)
```

**5. A low-volume guard.** Tiny search terms jump between 0 and 1 on Google's scale (= ±100%). `Trend Status` returns **"Low volume"** when last month's score (`Recent Interest`) is under 0.5, so Rising/Falling lists and counts only show reliable moves (±15% thresholds).

**6. Context-aware classification (quadrants, not weights).** `Niche Quadrant` compares each keyword with the **average of the keywords currently selected**, using `ALLSELECTED`, so "above average" adapts to whatever topic or language is filtered. `Hot Niche Flag` and `Hot Niches` build on it.

**7. Dynamic headlines.** Each page has a one-line headline measure that recalculates with the filters. They use `TOPN` to find the leader, and an **ordered table constructor + `CONCATENATEX`** to join only the non-blank parts in a fixed order:

```dax
VAR parts = FILTER({(1, part1), (2, part2), (3, part3)}, NOT ISBLANK([Value2]))
RETURN CONCATENATEX(parts, [Value2], "  ·  ", [Value1], ASC)
```

**8. Finding one row: the most-viewed video.** `TOPN(1, …)` with a **tie-breaker** column gives one deterministic video, then `LOOKUPVALUE` fetches its title, channel and views (`Top Video Title`, `Top Video Detail`).

**9. Colour from measures (conditional formatting).** Bar colours come from `HL …` measures that return a hex colour: the value divided by the biggest value **in the current visual** (`ISINSCOPE` picks the axis, `MAXX(ALLSELECTED(axis), …)` finds the biggest), mapped to a 6-step light-to-dark red scale. The biggest bar is always darkest, and colours update as filters change.
- **Lesson learned (the map):** the filled map groups by `dim_state[state_map_name]`, so `Map Color` must find the maximum over **that** column with the map's own filter removed (`CALCULATETABLE(VALUES(dim_state[state_map_name]), ALLSELECTED(dim_state), …)`). Iterating a different column kept the map's filter, compared each state only with itself, and painted the whole map one colour.

**10. Measures as visual filters.** Measures are used as visual-level filters to keep visuals honest and avoid blank pages:

| Filter | Where | Why |
|---|---|---|
| `Videos Tracked > 0` | Topic, language and category slicers | Only list choices that have data (no blank pages) |
| `Hot Niche Flag = 1` | Hot niches table | Show only Hot keywords |
| `Map Strength ≥ 0.1` | India map | Hide states with almost no interest, so auto-zoom fits the real audience |
| `Recent Interest ≥ 0.5` | Rising / Falling tables | Leave out low-volume noise |
| `Demand Index > 0` | Opportunity map | Required for the log-scale axis |
| `Interest MoM % > 0` / `< 0` + Top N 5 | Rising / Falling tables | Top 5 risers and fallers only |

**11. Scaling within a group.** `Demand Within Language` divides each topic's demand by the **top topic in the same language** (`MAXX(ALLSELECTED(dim_keyword[topic_group]), …)` keeps the language in context), so small regional languages are readable: "within Telugu, which topic leads?"

**12. Counting across a relationship chain.** `Small Channels in Top Results` counts channels behind videos (`SUMMARIZE` over the fact table through video → channel), filtered with `KEEPFILTERS(subscribers < 100000)` so slicers still apply. `Median Uploads per Month (Small)` takes a `MEDIANX` over the same set.

**13. Filter-proof labels.** `Data As Of` uses `REMOVEFILTERS()` so the "Data as of" date never goes blank when a slicer excludes everything.

**14. Calculated columns for grouping.** Buckets that visuals group by are calculated columns (row by row, at refresh):
- **video length**, **title length**, **Shorts / Long-form**, **upload weekday in India time** (`published_at` is UTC, so `+ 5.5 / 24`)
- channel **age**, **uploads per month** and **upload pace**
- **"has videos"** flags for slicers, readable **language labels**, and a **small-region** flag for tiny states

**15. Images from measures.** Icon measures return `data:image/svg+xml` text with **Data category = Image URL**, so cards and tables show crisp icons that look the same on every computer (unlike emoji).

---

## 5. Report design strategies

- **One question per page**, in the order a creator decides: *What's happening → Where should I start → How should I make it and grow → Who and where.* The page title is the question, and a live headline gives the answer.
- **Same layout on every page** (1280 × 720): title + headline, page navigator, filter row, KPI cards with icons, charts, footnote with data caveats.
- **Page navigator** buttons styled as tabs; helper pages are hidden from it.
- **Slicer interactions:** filters that describe videos (video language, content type) are set to **not filter** the search-trend visuals, because they don't apply to searches (Edit interactions → None).
- **Top N visual filters** keep bar charts to the top 5–10 items.
- **Tooltip page** ("Keyword tooltip", 320 × 240): hovering a keyword shows its trend status, month-on-month change and 5-year line.
- **Drill-through page** ("State detail"): right-click a state → its top keywords, topics and languages, with a back button.
- **Colour rules:** one hue (light → dark red) for "more vs less", because two-colour scales read as good vs bad. Opportunity-map points are coloured by quadrant (dark red = Hot).
- **Log scale** on the opportunity map's demand axis, because one huge keyword would otherwise squash all others into a corner.
- **Small regions hidden** on the audience page (states/UTs under 2 million people), because their search scores are noisy.
- **Plain-language titles and footnotes** written for a non-technical viewer; every caveat is on the page that it affects.

---

## 6. Report as code (PBIP / PBIR / TMDL)

- The report is saved as a **Power BI Project**: `Dashboards/India YouTube Trends.Report/` (pages and visuals as JSON) and `Dashboards/India YouTube Trends.SemanticModel/` (tables, measures and relationships as TMDL text). Every change shows up as a readable diff in git.
- The 4 pages, the helper measures and calculated columns were **generated by `build_report.py`**, a Python script that writes the PBIR JSON and TMDL, so the layout was consistent and reproducible. The dashboard was then **finished by hand in Power BI**; the script is no longer run on the pages, because it would overwrite those hand edits.
- Power BI's local cache and settings (`.pbi/cache.abf`, `localSettings.json`) are kept out of git, so the repo holds only the definition, never a copy of the data.

---

## 7. Full DAX reference

Every measure and calculated column in the model, taken directly from the model files. *"On a page"* = used in a visual; *"helper"* = used by another measure that's on a page; *"available"* = in the model for analysis, not on the current pages.

## Measures (88)

### Video measures (14)

**Videos Tracked** · _on a page · format `#,0`_  
Distinct videos in the current filter.

```dax
Videos Tracked =
DISTINCTCOUNT(fact_video_snapshot[video_id])
```

**Latest Snapshot** · _available, not on the current pages · format `yyyy-mm-dd`_  
Most recent snapshot date in the current filter.

```dax
Latest Snapshot =
MAX(fact_video_snapshot[snapshot_date])
```

**Total Views** · _available, not on the current pages · format `#,0`_  
Sum of each video's latest public view count (counted once per video, not once per snapshot).

```dax
Total Views =
SUMX(
    VALUES(fact_video_snapshot[video_id]),
    CALCULATE(MAX(fact_video_snapshot[views]))
)
```

**Total Likes** · _available, not on the current pages · format `#,0`_  
Sum of each video's latest like count. Hidden likes are blank, not zero.

```dax
Total Likes =
SUMX(
    VALUES(fact_video_snapshot[video_id]),
    CALCULATE(MAX(fact_video_snapshot[likes]))
)
```

**Total Comments** · _available, not on the current pages · format `#,0`_  
Sum of each video's latest comment count.

```dax
Total Comments =
SUMX(
    VALUES(fact_video_snapshot[video_id]),
    CALCULATE(MAX(fact_video_snapshot[comments]))
)
```

**Engagement Rate** · _on a page · format `0.0%`_  
(Likes + comments) / views, using only videos whose likes are public, so hidden likes don't drag the rate down.

```dax
Engagement Rate =
VAR vids = CALCULATETABLE(VALUES(fact_video_snapshot[video_id]), fact_video_snapshot[likes_hidden] = FALSE())
VAR likes = SUMX(vids, CALCULATE(MAX(fact_video_snapshot[likes])))
VAR comments = SUMX(vids, CALCULATE(MAX(fact_video_snapshot[comments])))
VAR views = SUMX(vids, CALCULATE(MAX(fact_video_snapshot[views])))
RETURN DIVIDE(likes + comments, views)
```

**Avg Views per Day** · _available, not on the current pages · format `#,0`_  
Average of views / days since publish, using each video's latest snapshot.

```dax
Avg Views per Day =
AVERAGEX(
    VALUES(fact_video_snapshot[video_id]),
    VAR d = CALCULATE(MAX(fact_video_snapshot[snapshot_date]))
    RETURN CALCULATE(AVERAGE(fact_video_snapshot[views_per_day]), fact_video_snapshot[snapshot_date] = d)
)
```

**Median Views** · _on a page · format `#,0`_  
Median latest view count per video. Less skewed by viral outliers than the average.

```dax
Median Views =
MEDIANX(
    VALUES(fact_video_snapshot[video_id]),
    CALCULATE(MAX(fact_video_snapshot[views]))
)
```

**Shorts Share** · _on a page · format `0.0%`_  
Share of videos that are Shorts.

```dax
Shorts Share =
DIVIDE(CALCULATE([Videos Tracked], dim_video[is_short] = TRUE()), [Videos Tracked])
```

**Regional Language Share** · _on a page · format `0.0%`_  
Share of videos in an Indian language other than English (includes Hindi, Tamil, Telugu, etc., per dim_language[is_indian_regional]).

```dax
Regional Language Share =
DIVIDE(CALCULATE([Videos Tracked], dim_language[is_indian_regional] = TRUE()), [Videos Tracked])
```

**Trending Videos** · _available, not on the current pages · format `#,0`_  
Videos that appeared in an India mostPopular chart (overall or per category).

```dax
Trending Videos =
CALCULATE([Videos Tracked], fact_video_snapshot[in_trending] = TRUE())
```

**Top Category** · _helper for another measure_  
Category with the most videos in the current filter.

```dax
Top Category =
MAXX(
    TOPN(1, FILTER(VALUES(dim_category[category_name]), [Videos Tracked] > 0), [Videos Tracked]),
    dim_category[category_name]
)
```

**Avg Views per Video** · _available, not on the current pages · format `#,0`_  
Total Views / Videos Tracked. Skewed by viral videos; compare with Median Views.

```dax
Avg Views per Video =
DIVIDE([Total Views], [Videos Tracked])
```

**Videos Published** · _available, not on the current pages · format `#,0`_  
Tracked videos by their publish date (uses the inactive dim_video[published_date] relationship). For upload-volume-over-time charts.

```dax
Videos Published =
CALCULATE(COUNTROWS(dim_video), USERELATIONSHIP(dim_video[published_date], dim_date[date]))
```

### Channel measures (6)

**Channels** · _helper for another measure · format `#,0`_  
Distinct channels behind the videos in the current filter.

```dax
Channels =
COUNTROWS(SUMMARIZE(fact_video_snapshot, dim_video[channel_id]))
```

**Total Subscribers** · _available, not on the current pages · format `#,0`_  
Subscribers summed over the channels behind the videos in view (each channel once). Hidden subscriber counts are blank.

```dax
Total Subscribers =
SUMX(
    SUMMARIZE(fact_video_snapshot, dim_channel[channel_id], dim_channel[subscribers]),
    dim_channel[subscribers]
)
```

**Avg Subscribers per Channel** · _available, not on the current pages · format `#,0`_  
Total Subscribers / Channels.

```dax
Avg Subscribers per Channel =
DIVIDE([Total Subscribers], [Channels])
```

**Channels Outside India Share** · _available, not on the current pages · format `0.0%`_  
Share of channels in view whose country is set to somewhere other than India (Unknown counts as not outside).

```dax
Channels Outside India Share =
DIVIDE(
    COUNTROWS(FILTER(SUMMARIZE(fact_video_snapshot, dim_channel[channel_id], dim_channel[channel_origin]), dim_channel[channel_origin] = "Outside India")),
    [Channels]
)
```

**Small Channels in Top Results** · _on a page_  
Channels under 100K subscribers behind videos in the top search results for the tracked keywords.

```dax
Small Channels in Top Results =
CALCULATE([Channels], KEEPFILTERS(dim_channel[subscribers] < 100000), dim_channel[subscribers_hidden] = FALSE(), fact_video_snapshot[in_topic_search] = TRUE())
```

**Median Uploads per Month (Small)** · _on a page_  
Median uploads per month (lifetime average) of small channels in top search results.

```dax
Median Uploads per Month (Small) =
MEDIANX(CALCULATETABLE(SUMMARIZE(fact_video_snapshot, dim_channel[channel_id], dim_channel[uploads_per_month]), KEEPFILTERS(dim_channel[subscribers] < 100000), dim_channel[subscribers_hidden] = FALSE(), fact_video_snapshot[in_topic_search] = TRUE()), dim_channel[uploads_per_month])
```

### Search trend measures (9)

**Interest** · _on a page · format `0.0`_  
Google Trends interest, normalised to the 'cricket' anchor so keywords are comparable across batches. Relative index, not search counts.

```dax
Interest =
AVERAGE(fact_trends_keyword[interest_norm])
```

**Interest MoM %** · _on a page · format `0.0%`_  
Average interest in the last month vs the month before (ending at the latest date in context).

```dax
Interest MoM % =
VAR cur  = CALCULATE([Interest], DATESINPERIOD(dim_date[date], MAX(dim_date[date]), -1, MONTH))
VAR prev = CALCULATE([Interest], DATEADD(DATESINPERIOD(dim_date[date], MAX(dim_date[date]), -1, MONTH), -1, MONTH))
RETURN DIVIDE(cur - prev, prev)
```

**Interest YoY % (3M)** · _available, not on the current pages · format `0.0%`_  
Average interest over the last 3 months vs the same 3 months a year earlier.

```dax
Interest YoY % (3M) =
VAR cur  = CALCULATE([Interest], DATESINPERIOD(dim_date[date], MAX(dim_date[date]), -3, MONTH))
VAR prev = CALCULATE([Interest], SAMEPERIODLASTYEAR(DATESINPERIOD(dim_date[date], MAX(dim_date[date]), -3, MONTH)))
RETURN DIVIDE(cur - prev, prev)
```

**Trend Status** · _helper for another measure_  
Rising / Declining = more than +/-15% vs the previous month. Low volume = too few searches for a reliable change (last-month score under 0.5).

```dax
Trend Status =
SWITCH(TRUE(),
    ISBLANK([Interest MoM %]) || [Recent Interest] < 0.5, "Low volume",
    [Interest MoM %] > 0.15, "Rising",
    [Interest MoM %] < -0.15, "Declining",
    "Stable")
```

**Rising Keywords** · _on a page · format `#,0`_  
Keywords (excluding the anchor) whose interest rose more than 15% month on month.

```dax
Rising Keywords =
COUNTROWS(FILTER(CALCULATETABLE(VALUES(dim_keyword[keyword]), dim_keyword[is_anchor] = FALSE()), [Trend Status] = "Rising"))
```

**Declining Keywords** · _available, not on the current pages · format `#,0`_  
Keywords (excluding the anchor) whose interest fell more than 15% month on month.

```dax
Declining Keywords =
COUNTROWS(FILTER(CALCULATETABLE(VALUES(dim_keyword[keyword]), dim_keyword[is_anchor] = FALSE()), [Trend Status] = "Declining"))
```

**Trend Status Color** · _on a page_  
Hex colour for Trend Status (works on both YouTube light and dark themes). Rising green, Declining orange (red is reserved for the brand accent), Stable grey.

```dax
Trend Status Color =
SWITCH([Trend Status], "Rising", "#1f9142", "Declining", "#c4630b", "Stable", "#909090", "#717171")
```

**Trend Label** · _on a page_  
Trend Status with an arrow, for tables. Colour it with [Trend Status Color].

```dax
Trend Label =
SWITCH([Trend Status],"Rising", "▲ Rising", "Declining", "▼ Declining", "Stable", "● Stable", "Low volume", "○ Low volume")
```

**Recent Interest** · _on a page_  
Average search score over the last month (cricket scale). Below 0.5 a keyword counts as Low volume.

```dax
Recent Interest =
CALCULATE([Interest], DATESINPERIOD(dim_date[date], MAX(dim_date[date]), -1, MONTH))
```

### State (region) measures (5)

**State Index** · _on a page · format `0.0`_  
0-100 within a keyword: how strongly each state searches it relative to the top state.

```dax
State Index =
AVERAGE(fact_trends_region[state_index])
```

**Interest vs Cricket** · _on a page · format `0.00`_  
State interest in the keyword relative to 'cricket' in the same state (1.0 = as popular as cricket).

```dax
Interest vs Cricket =
AVERAGE(fact_trends_region[ratio_to_anchor])
```

**Top State** · _available, not on the current pages_  
State with the highest State Index for the keywords in the current filter.

```dax
Top State =
MAXX(
    TOPN(1, FILTER(VALUES(dim_state[state]), NOT ISBLANK([State Index])), [State Index]),
    dim_state[state]
)
```

**Top Keyword in State** · _on a page_  
Keyword with the highest State Index in the current state(s). Excludes the anchor.

```dax
Top Keyword in State =
MAXX(
    TOPN(1, FILTER(CALCULATETABLE(VALUES(dim_keyword[keyword]), dim_keyword[is_anchor] = FALSE()), NOT ISBLANK([State Index])), [State Index]),
    dim_keyword[keyword]
)
```

**Map Strength** · _on a page_  
State Index relative to the strongest state in view (0-1). The map hides states below 0.1 so it zooms to where searches come from.

```dax
Map Strength =
DIVIDE([State Index], MAXX(CALCULATETABLE(VALUES(dim_state[state_map_name]), ALLSELECTED(dim_state), dim_state[is_small_region] = FALSE()), [State Index]))
```

### Niche / opportunity measures (9)

**Demand Index** · _on a page · format `0.0`_  
Average normalised Trends interest over the last 12 weeks.

```dax
Demand Index =
AVERAGE(fact_keyword_opportunity[demand_index])
```

**Supply (30d videos, est.)** · _available, not on the current pages · format `#,0`_  
Search API totalResults for videos in the last 30 days. Approximate and capped at 1,000,000, so a relative signal only.

```dax
Supply (30d videos, est.) =
SUM(fact_keyword_opportunity[videos_last_30d_est])
```

**Growth 12w %** · _on a page · format `0.0%`_  
Interest in the last 12 weeks vs the previous 12 weeks.

```dax
Growth 12w % =
AVERAGE(fact_keyword_opportunity[growth_12w])
```

**Small Channel Share** · _on a page · format `0.0%`_  
Share of the keyword's top recent videos from channels under 100K subscribers.

```dax
Small Channel Share =
AVERAGE(fact_keyword_opportunity[small_channel_share])
```

**Keywords Tracked** · _on a page_  
Number of keywords tracked in the current filter (excluding the cricket anchor).

```dax
Keywords Tracked =
CALCULATE(DISTINCTCOUNT(dim_keyword[keyword]), dim_keyword[is_anchor] = FALSE())
```

**Niche Quadrant** · _helper for another measure_  
Opportunity-map quadrant: Hot = demand above the average of the keywords in view and growing (12 weeks); Emerging = growing; Big but flat = high demand, not growing; Skip = neither.

```dax
Niche Quadrant =
VAR d = [Demand Index]
VAR g = [Growth 12w %]
VAR avgD = CALCULATE(AVERAGEX(VALUES(dim_keyword[keyword]), [Demand Index]), ALLSELECTED(dim_keyword))
RETURN IF(ISBLANK(d) || ISBLANK(g), BLANK(), SWITCH(TRUE(), d > avgD && g > 0, "Hot", g > 0, "Emerging", d > avgD, "Big but flat", "Skip"))
```

**Hot Niche Flag** · _on a page_  
1 when the keyword is in the Hot quadrant, else 0. Used to filter the Hot niches table.

```dax
Hot Niche Flag =
VAR q = [Niche Quadrant]
RETURN IF(ISBLANK(q), BLANK(), IF(q = "Hot", 1, 0))
```

**Hot Niches** · _on a page_  
Number of keywords in the Hot quadrant (high demand and growing).

```dax
Hot Niches =
SUMX(CALCULATETABLE(VALUES(dim_keyword[keyword]), dim_keyword[is_anchor] = FALSE()), [Hot Niche Flag])
```

**Demand Within Language** · _on a page · format `0`_  
Demand Index scaled within the language in context: 100 = the language's top topic. Compare down a column, not across.

```dax
Demand Within Language =
VAR v = [Demand Index]
VAR mx = MAXX(ALLSELECTED(dim_keyword[topic_group]), [Demand Index])
RETURN IF(ISBLANK(v), BLANK(), 100 * DIVIDE(v, mx))
```

### Text measures (headlines and labels) (10)

**Data As Of** · _on a page_  
Header text showing the latest snapshot date (ignores slicers and filters).

```dax
Data As Of =
"Data as of " & FORMAT(CALCULATE(MAX(fact_video_snapshot[snapshot_date]), REMOVEFILTERS()), "d mmm yyyy")
```

**Selected Keyword Label** · _available, not on the current pages_  
Dynamic title fragment describing the keyword selection.

```dax
Selected Keyword Label =
VAR n = COUNTROWS(VALUES(dim_keyword[keyword]))
RETURN SWITCH(TRUE(),
    NOT ISFILTERED(dim_keyword[keyword]) && NOT ISFILTERED(dim_keyword[topic_group]), "All keywords",
    n = 1, SELECTEDVALUE(dim_keyword[keyword]),
    ISFILTERED(dim_keyword[topic_group]) && HASONEVALUE(dim_keyword[topic_group]), SELECTEDVALUE(dim_keyword[topic_group]) & " keywords",
    FORMAT(n, "0") & " keywords")
```

**Map Title** · _available, not on the current pages_  
Dynamic title for the India map.

```dax
Map Title =
VAR lbl = [Selected Keyword Label]
RETURN IF(lbl = "All keywords", "Where India searches on YouTube (all tracked keywords)", "Where India searches for " & lbl & " on YouTube")
```

**State Page Title** · _on a page_  
Title for the state drill-through page.

```dax
State Page Title =
SELECTEDVALUE(dim_state[state], "Select a state") & ": what people search on YouTube"
```

**Top Video Title** · _on a page_  
Title of the most-viewed video in the current filter.

```dax
Top Video Title =
VAR vid = MAXX(TOPN(1, VALUES(fact_video_snapshot[video_id]), CALCULATE(MAX(fact_video_snapshot[views])), DESC, fact_video_snapshot[video_id], ASC), fact_video_snapshot[video_id])
RETURN LOOKUPVALUE(dim_video[title], dim_video[video_id], vid)
```

**Top Video Detail** · _on a page_  
Channel and view count of the most-viewed video in the current filter.

```dax
Top Video Detail =
VAR vid = MAXX(TOPN(1, VALUES(fact_video_snapshot[video_id]), CALCULATE(MAX(fact_video_snapshot[views])), DESC, fact_video_snapshot[video_id], ASC), fact_video_snapshot[video_id])
VAR ch = LOOKUPVALUE(dim_channel[channel_name], dim_channel[channel_id], LOOKUPVALUE(dim_video[channel_id], dim_video[video_id], vid))
VAR v = CALCULATE(MAX(fact_video_snapshot[views]), fact_video_snapshot[video_id] = vid)
RETURN IF(ISBLANK(vid), BLANK(), "by " & ch & "  ·  " & FORMAT(v / 1000000, "#,0.0") & "M views")
```

**Overview Headline** · _on a page_  
One-line summary for the Overview page: fastest-rising topic, Shorts share and top category.

```dax
Overview Headline =
VAR tp = TOPN(1, FILTER(VALUES(dim_keyword[topic_group]), dim_keyword[topic_group] <> "Anchor" && NOT ISBLANK([Interest MoM %])), [Interest MoM %], DESC)
VAR topic = MAXX(tp, dim_keyword[topic_group])
VAR mom = MAXX(tp, [Interest MoM %])
VAR part1 = IF(ISBLANK(topic), BLANK(), IF(mom > 0, "Fastest-rising topic: ", "Best-performing topic: ") & topic & " (" & FORMAT(mom, "+0%;-0%") & " vs last month)")
VAR part2 = IF(ISBLANK([Videos Tracked]), "No videos match these filters yet, try another language or topic", "Shorts are " & FORMAT([Shorts Share], "0%") & " of videos")
VAR part3 = IF(ISBLANK([Top Category]), BLANK(), "Most videos are in " & [Top Category])
VAR parts = FILTER({(1, part1), (2, part2), (3, part3)}, NOT ISBLANK([Value2]))
RETURN CONCATENATEX(parts, [Value2], "  ·  ", [Value1], ASC)
```

**Niche Headline** · _on a page_  
One-line summary for the Find your niche page.

```dax
Niche Headline =
VAR hot = [Hot Niches]
VAR best = TOPN(1, FILTER(CALCULATETABLE(VALUES(dim_keyword[keyword]), dim_keyword[is_anchor] = FALSE()), [Hot Niche Flag] = 1 && NOT ISBLANK([Small Channel Share])), [Small Channel Share], DESC, dim_keyword[keyword], ASC)
VAR kw = MAXX(best, dim_keyword[keyword])
VAR sh = MAXX(best, [Small Channel Share])
RETURN IF(ISBLANK(hot) || hot = 0, "No Hot niche in this selection, try another topic or language",
    hot & " Hot niches (high demand, growing)" & IF(ISBLANK(kw), "", "  ·  Most open: " & kw & ", " & FORMAT(sh, "0%") & " of top videos from small channels"))
```

**Grow Headline** · _on a page_  
One-line summary for the Make it & grow it page.

```dax
Grow Headline =
VAR ms = CALCULATE([Median Views], dim_video[video_format] = "Shorts")
VAR ml = CALCULATE([Median Views], dim_video[video_format] = "Long-form")
VAR ratio = DIVIDE(ms, ml)
VAR es = CALCULATE([Engagement Rate], dim_video[video_format] = "Shorts")
VAR el = CALCULATE([Engagement Rate], dim_video[video_format] = "Long-form")
VAR p1 = IF(ISBLANK(ratio), BLANK(), IF(ratio >= 1, "Shorts get " & FORMAT(ratio, "0.0") & "x the views", "Long-form gets " & FORMAT(DIVIDE(1, ratio), "0.0") & "x the views") & IF(el > es, ", long-form more engagement", IF(es > el, ", Shorts more engagement", "")))
VAR sc = [Small Channels in Top Results]
VAR young = DIVIDE(CALCULATE([Small Channels in Top Results], dim_channel[channel_age_bucket] = "1. Under 1 year"), sc)
VAR p2 = IF(ISBLANK(sc), BLANK(), FORMAT(young, "0%") & " of top small channels are under 1 year old")
VAR up = [Median Uploads per Month (Small)]
VAR p3 = IF(ISBLANK(up), BLANK(), "~" & FORMAT(up, "0") & " uploads a month")
VAR parts = FILTER({(1, p1), (2, p2), (3, p3)}, NOT ISBLANK([Value2]))
RETURN CONCATENATEX(parts, [Value2], "  ·  ", [Value1], ASC)
```

**Audience Headline** · _on a page_  
One-line summary for the Know your audience page.

```dax
Audience Headline =
VAR t = TOPN(3, FILTER(CALCULATETABLE(VALUES(dim_state[state]), dim_state[is_small_region] = FALSE()), NOT ISBLANK([State Index])), [State Index], DESC, dim_state[state], ASC)
VAR names = CONCATENATEX(t, dim_state[state], ", ", [State Index], DESC)
VAR p1 = IF(names = "", BLANK(), "Searches are strongest in " & names)
VAR p2 = IF(ISBLANK([Videos Tracked]), BLANK(), FORMAT([Regional Language Share], "0%") & " of matching videos are in Indian languages")
VAR parts = FILTER({(1, p1), (2, p2)}, NOT ISBLANK([Value2]))
RETURN CONCATENATEX(parts, [Value2], "  ·  ", [Value1], ASC)
```

### Colour measures (conditional formatting) (13)

**HL Videos** · _on a page_  
Bar colour: red scale, darkest for the largest bar (Videos Tracked).

```dax
HL Videos =
VAR v = [Videos Tracked]
VAR mx = SWITCH(TRUE(), ISINSCOPE(dim_category[category_name]), MAXX(ALLSELECTED(dim_category[category_name]), [Videos Tracked]), ISINSCOPE(dim_language[language_name]), MAXX(ALLSELECTED(dim_language[language_name]), [Videos Tracked]), ISINSCOPE(dim_language[language_label]), MAXX(ALLSELECTED(dim_language[language_label]), [Videos Tracked]), ISINSCOPE(dim_video[duration_bucket]), MAXX(ALLSELECTED(dim_video[duration_bucket]), [Videos Tracked]), ISINSCOPE(dim_video[publish_hour_ist]), MAXX(ALLSELECTED(dim_video[publish_hour_ist]), [Videos Tracked]), ISINSCOPE(dim_channel[subscriber_tier]), MAXX(ALLSELECTED(dim_channel[subscriber_tier]), [Videos Tracked]), v)
VAR r = DIVIDE(v, mx)
RETURN IF(ISBLANK(v), BLANK(), SWITCH(TRUE(), r >= 0.999, "#c4002b", r >= 0.8, "#d2434b", r >= 0.6, "#de686a", r >= 0.4, "#e98889", r >= 0.2, "#f2a8a9", "#f9c6c9"))
```

**HL Channels** · _available, not on the current pages_  
Bar colour: red scale, darkest for the largest bar (Channels).

```dax
HL Channels =
VAR v = [Channels]
VAR mx = SWITCH(TRUE(), ISINSCOPE(dim_channel[channel_origin]), MAXX(ALLSELECTED(dim_channel[channel_origin]), [Channels]), v)
VAR r = DIVIDE(v, mx)
RETURN IF(ISBLANK(v), BLANK(), SWITCH(TRUE(), r >= 0.999, "#c4002b", r >= 0.8, "#d2434b", r >= 0.6, "#de686a", r >= 0.4, "#e98889", r >= 0.2, "#f2a8a9", "#f9c6c9"))
```

**HL Median Views** · _on a page_  
Bar colour: red scale, darkest for the largest bar (Median Views).

```dax
HL Median Views =
VAR v = [Median Views]
VAR mx = SWITCH(TRUE(), ISINSCOPE(dim_category[category_name]), MAXX(ALLSELECTED(dim_category[category_name]), [Median Views]), ISINSCOPE(dim_video[duration_bucket]), MAXX(ALLSELECTED(dim_video[duration_bucket]), [Median Views]), ISINSCOPE(dim_channel[subscriber_tier]), MAXX(ALLSELECTED(dim_channel[subscriber_tier]), [Median Views]), ISINSCOPE(dim_video[publish_hour_ist]), MAXX(ALLSELECTED(dim_video[publish_hour_ist]), [Median Views]), ISINSCOPE(dim_video[publish_weekday]), MAXX(ALLSELECTED(dim_video[publish_weekday]), [Median Views]), ISINSCOPE(dim_video[title_length_bucket]), MAXX(ALLSELECTED(dim_video[title_length_bucket]), [Median Views]), ISINSCOPE(dim_video[tag_count_bucket]), MAXX(ALLSELECTED(dim_video[tag_count_bucket]), [Median Views]), ISINSCOPE(dim_video[video_format]), MAXX(ALLSELECTED(dim_video[video_format]), [Median Views]), v)
VAR r = DIVIDE(v, mx)
RETURN IF(ISBLANK(v), BLANK(), SWITCH(TRUE(), r >= 0.999, "#c4002b", r >= 0.8, "#d2434b", r >= 0.6, "#de686a", r >= 0.4, "#e98889", r >= 0.2, "#f2a8a9", "#f9c6c9"))
```

**HL Engagement** · _on a page_  
Bar colour: red scale, darkest for the largest bar (Engagement Rate).

```dax
HL Engagement =
VAR v = [Engagement Rate]
VAR mx = SWITCH(TRUE(), ISINSCOPE(dim_category[category_name]), MAXX(ALLSELECTED(dim_category[category_name]), [Engagement Rate]), ISINSCOPE(dim_video[duration_bucket]), MAXX(ALLSELECTED(dim_video[duration_bucket]), [Engagement Rate]), ISINSCOPE(dim_video[video_format]), MAXX(ALLSELECTED(dim_video[video_format]), [Engagement Rate]), v)
VAR r = DIVIDE(v, mx)
RETURN IF(ISBLANK(v), BLANK(), SWITCH(TRUE(), r >= 0.999, "#c4002b", r >= 0.8, "#d2434b", r >= 0.6, "#de686a", r >= 0.4, "#e98889", r >= 0.2, "#f2a8a9", "#f9c6c9"))
```

**HL State Index** · _on a page_  
Bar colour: red scale, darkest for the largest bar (State Index).

```dax
HL State Index =
VAR v = [State Index]
VAR mx = SWITCH(TRUE(), ISINSCOPE(dim_state[state]), MAXX(ALLSELECTED(dim_state[state]), [State Index]), ISINSCOPE(dim_state[zone]), MAXX(ALLSELECTED(dim_state[zone]), [State Index]), ISINSCOPE(dim_keyword[keyword]), MAXX(ALLSELECTED(dim_keyword[keyword]), [State Index]), ISINSCOPE(dim_keyword[topic_group]), MAXX(ALLSELECTED(dim_keyword[topic_group]), [State Index]), ISINSCOPE(dim_keyword[keyword_language]), MAXX(ALLSELECTED(dim_keyword[keyword_language]), [State Index]), v)
VAR r = DIVIDE(v, mx)
RETURN IF(ISBLANK(v), BLANK(), SWITCH(TRUE(), r >= 0.999, "#c4002b", r >= 0.8, "#d2434b", r >= 0.6, "#de686a", r >= 0.4, "#e98889", r >= 0.2, "#f2a8a9", "#f9c6c9"))
```

**HL Interest vs Cricket** · _available, not on the current pages_  
Bar colour: red scale, darkest for the largest bar (Interest vs Cricket).

```dax
HL Interest vs Cricket =
VAR v = [Interest vs Cricket]
VAR mx = SWITCH(TRUE(), ISINSCOPE(dim_state[state]), MAXX(ALLSELECTED(dim_state[state]), [Interest vs Cricket]), v)
VAR r = DIVIDE(v, mx)
RETURN IF(ISBLANK(v), BLANK(), SWITCH(TRUE(), r >= 0.999, "#c4002b", r >= 0.8, "#d2434b", r >= 0.6, "#de686a", r >= 0.4, "#e98889", r >= 0.2, "#f2a8a9", "#f9c6c9"))
```

**Map Color** · _on a page_  
Filled-map colour: 7-step red scale of State Index relative to the top state in view (small regions excluded).

```dax
Map Color =
VAR v = [State Index]
VAR mx = MAXX(CALCULATETABLE(VALUES(dim_state[state_map_name]), ALLSELECTED(dim_state), dim_state[is_small_region] = FALSE()), [State Index])
VAR r = DIVIDE(v, mx)
RETURN IF(ISBLANK(v), "#f2f2f2", SWITCH(TRUE(), r >= 0.86, "#c4002b", r >= 0.71, "#d2434b", r >= 0.57, "#de686a", r >= 0.43, "#e98889", r >= 0.29, "#f2a8a9", r >= 0.14, "#f9c6c9", "#ffe5ea"))
```

**Heat Color State** · _available, not on the current pages_  
Heatmap cell colour for State Index (state x topic).

```dax
Heat Color State =
VAR v = [State Index]
VAR r = DIVIDE(v, MAXX(CROSSJOIN(ALLSELECTED(dim_state[state]), ALLSELECTED(dim_keyword[topic_group])), [State Index]))
RETURN IF(ISBLANK(v), BLANK(), SWITCH(TRUE(), r >= 0.86, "#c4002b", r >= 0.71, "#d2434b", r >= 0.57, "#de686a", r >= 0.43, "#e98889", r >= 0.29, "#f2a8a9", r >= 0.14, "#f9c6c9", "#ffe5ea"))
```

**Heat Font State** · _available, not on the current pages_  
Heatmap text colour (white on dark cells).

```dax
Heat Font State =
VAR r = DIVIDE([State Index], MAXX(CROSSJOIN(ALLSELECTED(dim_state[state]), ALLSELECTED(dim_keyword[topic_group])), [State Index]))
RETURN IF(r >= 0.57, "#ffffff", "#0f0f0f")
```

**Heat Color Demand** · _on a page_  
Heatmap cell colour: demand within each language.

```dax
Heat Color Demand =
VAR v = [Demand Within Language]
VAR r = DIVIDE(v, 100)
RETURN IF(ISBLANK(v), BLANK(), SWITCH(TRUE(), r >= 0.86, "#c4002b", r >= 0.71, "#d2434b", r >= 0.57, "#de686a", r >= 0.43, "#e98889", r >= 0.29, "#f2a8a9", r >= 0.14, "#f9c6c9", "#ffe5ea"))
```

**Heat Font Demand** · _on a page_  
Heatmap text colour (white on dark cells).

```dax
Heat Font Demand =
VAR r = DIVIDE([Demand Within Language], 100)
RETURN IF(r >= 0.57, "#ffffff", "#0f0f0f")
```

**HL Small Channels** · _on a page_  
Bar colour: red scale, darkest for the largest bar (Small Channels in Top Results).

```dax
HL Small Channels =
VAR v = [Small Channels in Top Results]
VAR mx = SWITCH(TRUE(), ISINSCOPE(dim_channel[channel_age_bucket]), MAXX(ALLSELECTED(dim_channel[channel_age_bucket]), [Small Channels in Top Results]), ISINSCOPE(dim_channel[upload_pace_bucket]), MAXX(ALLSELECTED(dim_channel[upload_pace_bucket]), [Small Channels in Top Results]), v)
VAR r = DIVIDE(v, mx)
RETURN IF(ISBLANK(v), BLANK(), SWITCH(TRUE(), r >= 0.999, "#c4002b", r >= 0.8, "#d2434b", r >= 0.6, "#de686a", r >= 0.4, "#e98889", r >= 0.2, "#f2a8a9", "#f9c6c9"))
```

**Quadrant Color** · _on a page_  
Opportunity-map point colour by quadrant (Hot = dark red).

```dax
Quadrant Color =
SWITCH([Niche Quadrant], "Hot", "#c4002b", "Emerging", "#f2a8a9", "Big but flat", "#909090", "#d9d9d9")
```

### Icon measures (SVG images) (22)

Each icon is a small SVG drawing returned as a `data:image/svg+xml` text, with **Data category = Image URL**, so Power BI shows it as a picture. They all follow one pattern (a colour, a path, then the SVG wrapper); one example is shown, the rest differ only in colour and path:

```dax
Icon Videos =
VAR c = "%23e8002d"
VAR p = "<rect x='2' y='5' width='20' height='14' rx='3'/><path d='M10 9l5 3-5 3z' fill='" & c & "'/>"
RETURN "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 40 40'><rect width='40' height='40' rx='12' fill='" & c & "' fill-opacity='0.13'/><g transform='translate(8 8)' fill='none' stroke='" & c & "' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'>" & p & "</g></svg>"
```

All icon measures: `Icon Videos`, `Icon Views`, `Icon Engagement`, `Icon Shorts`, `Icon Language`, `Icon Category`, `Icon Channels`, `Icon Subscribers`, `Icon Trending`, `Icon Rising`, `Icon Declining`, `Icon Interest`, `Icon State`, `Icon Opportunity`, `Icon Growth`, `Icon Median`, `Icon Per Day`, `Icon Supply`, `Icon Small Channels`, `Icon Keywords`, `Icon Calendar`, `Trend Status Icon`.

## Calculated columns

Columns computed inside the model with DAX (row by row, when data is refreshed).

**dim_category[has_videos]**  
True when at least one tracked video is in this category. Used to hide empty categories in slicers.

```dax
has_videos = CALCULATE(COUNTROWS(dim_video)) > 0
```

**dim_channel[channel_age_bucket]**  
Channel age, grouped.

```dax
channel_age_bucket = SWITCH(TRUE(), ISBLANK(dim_channel[channel_age_years]) || dim_channel[channel_age_years] <= 0, BLANK(), dim_channel[channel_age_years] < 1, "1. Under 1 year", dim_channel[channel_age_years] < 2, "2. 1-2 years", dim_channel[channel_age_years] < 5, "3. 2-5 years", "4. 5+ years")
```

**dim_channel[uploads_per_month]**  
Average uploads per month over the channel's life (total videos / age in months). Not its current pace.

```dax
uploads_per_month = DIVIDE(dim_channel[video_count], dim_channel[channel_age_years] * 12)
```

**dim_channel[upload_pace_bucket]**  
Average upload pace over the channel's life, grouped.

```dax
upload_pace_bucket = VAR u = DIVIDE(dim_channel[video_count], dim_channel[channel_age_years] * 12) RETURN SWITCH(TRUE(), ISBLANK(u), BLANK(), u < 4, "1. Under once a week", u < 12, "2. 1-3 a week", u < 30, "3. 3-7 a week", "4. Daily or more")
```

**dim_keyword[has_state_data]**  
True when Google Trends returned state-level data for this keyword (17 low-volume keywords have none).

```dax
has_state_data = CALCULATE(COUNT(fact_trends_region[state_index])) > 0
```

**dim_language[has_videos]**  
True when at least one tracked video is in this language. Used to hide empty languages in slicers.

```dax
has_videos = CALCULATE(COUNTROWS(dim_video)) > 0
```

**dim_language[language_label]**  
English and Indian languages by name; everything else grouped as Other languages.

```dax
language_label = IF(dim_language[is_indian_regional] || dim_language[language] = "en", dim_language[language_name], "Other languages")
```

**dim_state[is_small_region]**  
True for states/UTs under 2 million people (Census 2011). Their Google Trends scores are noisy, so they're hidden on the audience page.

```dax
is_small_region = dim_state[state] IN {"Andaman and Nicobar Islands", "Arunachal Pradesh", "Chandigarh", "Dadra and Nagar Haveli", "Daman and Diu", "Goa", "Lakshadweep", "Mizoram", "Nagaland", "Puducherry", "Sikkim"}
```

**dim_video[video_format]**  
Shorts or Long-form, as a readable label.

```dax
video_format = IF(dim_video[is_short], "Shorts", "Long-form")
```

**dim_video[publish_weekday_num]**  
Upload day number in IST (1 = Monday). Sort column for publish_weekday.

```dax
publish_weekday_num = WEEKDAY(dim_video[published_at] + 5.5 / 24, 2)
```

**dim_video[publish_weekday]**  
Upload day of week in IST (Mon-Sun).

```dax
publish_weekday = FORMAT(dim_video[published_at] + 5.5 / 24, "ddd")
```

**dim_video[title_length_bucket]**  
Title length in characters, grouped (YouTube allows up to 100).

```dax
title_length_bucket = SWITCH(TRUE(), dim_video[title_length] < 40, "1. Under 40", dim_video[title_length] < 60, "2. 40-59", dim_video[title_length] < 80, "3. 60-79", "4. 80-100")
```

**dim_video[tag_count_bucket]**  
Number of tags on the video, grouped.

```dax
tag_count_bucket = SWITCH(TRUE(), dim_video[tag_count] = 0, "1. No tags", dim_video[tag_count] <= 10, "2. 1-10", dim_video[tag_count] <= 20, "3. 11-20", "4. 21+")
```
