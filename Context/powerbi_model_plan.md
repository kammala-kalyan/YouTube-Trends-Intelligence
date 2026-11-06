# Plan: build the Power BI semantic model for "India YouTube Trends"

**Target:** `Dashboards/India YouTube Trends.pbix`, open in Power BI Desktop. I'm connected to it through the Power BI modeling MCP.
**Current state:** the model is empty, with no tables, relationships or measures.
**Source:** 13 CSVs in `data/model/`, written by `build_model.py`.

**Status (2026-11-05): built.** Default answers used for all 4 questions: many-to-one, bridge filtering both ways, channel date relationship **active**, snake_case names. All 13 tables loaded; row counts and totals match the CSVs; 29 measures validated. Note: the measure "Top State for Keyword" was created as **Top State**.

---

## 0. Data check (done, read-only)

I loaded every CSV in pandas and checked the model keys:

| Check | Result |
|---|---|
| Duplicate or blank keys in dimension tables | None |
| Fact or bridge rows whose key has no matching dimension row | None, across all 13 relationships |
| `dim_date` range | 2021-10-31 → 2026-11-05 (covers all Trends weeks and snapshots) |
| Video snapshots | 1 day so far (2026-11-05) |
| Keywords with a content gap score | 35 of 105 (expected: the daily rotation fills the rest within 3 days) |

Row counts: dim_video 3,443 · dim_channel 2,707 · dim_category 31 · dim_language 42 · dim_keyword 106 · dim_state 36 · dim_date 1,832 · fact_video_snapshot 3,443 · fact_channel_snapshot 2,707 · fact_trends_keyword 27,772 · fact_trends_region 3,816 · fact_keyword_opportunity 105 · bridge_keyword_video 1,750.

---

## 1. Folder parameter

- Create the Power Query parameter `DataFolder` (Text), set to `D:\E\Placement\All projects\YouTube Trends Intelligence\data\model\`.
- Every table reads `DataFolder & "<file>.csv"`, so moving the project only means changing one value.

## 2. Import the 13 tables (Power Query / M)

Each table gets an M query that:
- reads the CSV as UTF-8 (code page 65001), so Hindi, Tamil and other scripts display correctly
- promotes headers
- sets explicit column types:

| Type | Columns |
|---|---|
| Date | `date`, `snapshot_date`, `published_date`, `week_start`, `supply_snapshot_date` |
| Date/Time | `published_at`, `created_at` |
| Whole number | views, likes, comments, subscribers, total_views, video_count, ranks, `charts_count`, `duration_sec`, `tag_count`, `title_length`, `publish_hour_ist`, `year`, `month_num`, `weekday_num`, `videos_last_30d_est` (values such as `63500.0` convert cleanly) |
| Decimal | `interest_*`, `ratio_to_anchor`, `state_index`, `interest_share`, `engagement_rate`, `views_per_day`, `days_since_publish`, `channel_age_years`, `demand_index`, `growth_*`, `small_channel_share`, `content_gap_score`, `top_videos_*` |
| True/False | `is_*`, `in_trending`, `in_topic_search`, `likes_hidden`, `subscribers_hidden`, `supply_capped`, `assignable` |
| Text | IDs and everything else (`category_id` stays text on both sides of its relationship) |

Then I refresh all tables and confirm the row counts match section 0.

## 3. Relationships

All are many-to-one with single-direction filtering, unless noted.

| # | From (many) | To (one) | Notes |
|---|---|---|---|
| 1 | fact_video_snapshot[video_id] | dim_video[video_id] | |
| 2 | fact_video_snapshot[snapshot_date] | dim_date[date] | |
| 3 | dim_video[channel_id] | dim_channel[channel_id] | |
| 4 | dim_video[category_id] | dim_category[category_id] | |
| 5 | dim_video[language] | dim_language[language] | |
| 6 | fact_channel_snapshot[channel_id] | dim_channel[channel_id] | |
| 7 | fact_channel_snapshot[snapshot_date] | dim_date[date] | Inactive, as POWERBI_SETUP.md specifies (see question 3) |
| 8 | fact_trends_keyword[keyword] | dim_keyword[keyword] | |
| 9 | fact_trends_keyword[date] | dim_date[date] | |
| 10 | fact_trends_region[keyword] | dim_keyword[keyword] | |
| 11 | fact_trends_region[state] | dim_state[state] | |
| 12 | fact_keyword_opportunity[keyword] | dim_keyword[keyword] | Many-to-one rather than one-to-one (see question 1) |
| 13 | bridge_keyword_video[keyword] | dim_keyword[keyword] | |
| 14 | bridge_keyword_video[video_id] | dim_video[video_id] | Cross-filter: Both, so a keyword slicer filters videos |
| 15 | dim_video[published_date] | dim_date[date] | New, inactive. Used with USERELATIONSHIP for upload-volume-over-time charts |

I've checked the filter paths and none of them conflict.

## 4. Model tidy-up

- Mark `dim_date` as the date table using `date`.
- Sort `month_name` by `month_num`, `weekday` by `weekday_num`, and `quarter` and `year_month` in date order.
- Hide every key and foreign-key column on fact and bridge tables, plus `snapshot_date` duplicates. Users slice by dimensions instead.
- Set `summarizeBy = None` on IDs, `year`, `month_num`, ranks, `publish_hour_ist` and the like, so Power BI doesn't sum them by default.
- Set `dim_state[state_map_name]` and `fact_trends_region[state_map_name]` to the **Place** data category (Place is more reliable than State/Province for Indian state names, because the value includes ", India"). Set the `state` columns to **State or Province**.
- Add descriptions to the main tables and measures. The tooltips also carry the data caveats from POWERBI_SETUP.md section 4.
- Keep the snake_case table names to match the CSVs and docs (see question 4).

## 5. Measures (in a `_Measures` table, grouped in display folders)

Every measure from POWERBI_SETUP.md, plus a few extras. All measures go into a new `_Measures` table.

**Videos:** Videos Tracked · Latest Snapshot · Total Views · Total Likes · Total Comments · Engagement Rate · Avg Views per Day · Median Views · Shorts Share · Regional Language Share · Trending Videos · Top Category · Channels

**Channels:** Total Subscribers (latest snapshot) · Avg Subscribers per Channel · Channels Outside India Share

**Trends:** Interest · Interest MoM % · Interest YoY % (3-month window, renamed to say so) · Trend Status

**Regions:** State Index · Interest vs Cricket · Top State for Keyword

**Opportunities:** Content Gap Score · Demand Index · Supply (30d videos, est.) · Growth 12w % · Small Channel Share · Keywords Scored

**Formats:** rates and `%` measures as percentages with 1 decimal; counts as whole numbers with thousands separators; indexes with 1 decimal.

Caveat: measures that compare two video or channel snapshots (day-over-day view growth) would show blank until a second daily snapshot exists, so I'm leaving them out for now. Trends measures work today, because Trends already has 5 years of weekly data.

## 6. Validation

- Run DAX queries to check row counts, every measure with no filters, and a few measures sliced by category, state and keyword. Each result gets a sanity check against pandas totals from the CSVs.
- Confirm there are no blank-key rows ("(Blank)" members) in any dimension.
- Show you a summary table of the results.

## 7. What you do after I finish

- **Save the .pbix in Power BI Desktop (Ctrl+S).** My changes live in the open session until then.
- Check the model view and confirm it looks right.

## Out of scope for this step

- **Report pages and visuals.** The MCP edits only the model; it can't place visuals. After the model is done, I'll write page-by-page specs (visuals, fields, formatting) for the 7 pages in context.txt, and you can share screenshots for review.
- Changes to the Python pipeline.

---

## Questions for you

1. **fact_keyword_opportunity → dim_keyword:** many-to-one (my recommendation) or one-to-one, as the setup doc says? Power BI makes one-to-one relationships filter both ways, which can cause surprising slicer behaviour. Many-to-one gives the same results here.
2. **Bridge filtering both ways (relationship 14):** keep it, as the setup doc says (simplest, and keyword slicers filter videos automatically), or keep it single-direction and use `CROSSFILTER` inside specific measures (safer, but more DAX)? I recommend keeping it both ways.
3. **fact_channel_snapshot date (relationship 7):** the setup doc says inactive, but I checked and an active relationship wouldn't conflict with anything. Make it active (my recommendation, so a date slicer also filters channel stats) or keep it inactive?
4. **Table names:** keep snake_case (`fact_video_snapshot`) or switch to friendly names (`Video Snapshots`)? Friendly names look better in the field list for a portfolio piece, but they no longer match the docs.
