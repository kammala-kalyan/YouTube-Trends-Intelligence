# Report build guide: India YouTube Trends

Build guide for the 7 report pages in `Dashboards/India YouTube Trends.pbix`, plus a state drill-through page and a keyword tooltip page.
Every field and measure named here already exists in the model. Measures live in **`_Measures`**, grouped in display folders.

Build one page at a time, then send a screenshot so I can review it before you move on.

---

## 0. One-time setup (about 10 minutes)

1. **Theme (YouTube style, minimal):** View → Themes → Browse for themes → pick one:
   - `Dashboards/youtube_light_theme.json`: white page, grey `#f2f2f2` rounded cards and slicers, near-black text, YouTube red accent
   - `Dashboards/youtube_dark_theme.json`: `#0f0f0f` page, `#272727` cards, YouTube red accent

   See `Dashboards/theme_preview.html` in a browser for both looks; it has a toggle. Optional: install the free **Roboto** font from Google Fonts (YouTube's typeface), then restart Power BI. Without it the theme falls back to Segoe UI.

   **YouTube-style touches to apply by hand:**
   - **Page navigator as chips.** Format → Style → Fill: `#f2f2f2` (dark theme `#272727`), corner radius 8. Selected state: fill `#0f0f0f`, text white (dark theme: fill `#f1f1f1`, text `#0f0f0f`). No border.
   - **Red accent bar.** Insert → Shapes → Rectangle, 6 × 34 px, fill `#ff0033`, corner radius 3, placed left of the page title. Use no logos.
   - **Highlight one bar, mute the rest.** On bar charts, set all bars to grey `#d9d9d9` (dark theme `#3f3f3f`). Then, under Format → Bars → Colors → Show all, set the top bar to red. Use red only where you want the eye to go.
   - **Titles.** 13pt, sentence case. Add a one-line grey subtitle (Format → Title → Subtitle) explaining the metric.
   - **No borders or shadows.** Separate visuals with whitespace (16px), the way YouTube does.

   **Icons (every KPI and chart header gets one):** the model has 22 icon measures in `_Measures → Icons`. Each is a line icon on a soft tinted tile of the same colour, tagged as an image URL. They use 7 colours (red, blue, pink, violet, green, orange, cyan), assigned so the KPIs on each page differ, and each clears 3:1 contrast on both light and dark cards. Rising is always green and declining always orange. The preview page shows them all.
   - **KPI cards (new Card visual):** add the KPI measure, then Format → Images → On → Image type **Image URL** → fx → Field value → pick the icon measure (for example `[Icon Views]`). Position: Left of the value. Size: 40px. With several measures in one card, set the image per measure (Apply settings to → series).
   - **Chart headers:** add a tiny new Card holding only the icon measure (callout off, 26px image), and place it left of the chart title. Or turn off the visual title and put the icon card and a text box together as the header.
   - **Tables:** add `[Trend Status Icon]` as a column next to the keyword. It shows a green up arrow, an orange down arrow or a grey flat arrow. Image height 16–20px (Format → Image size).
   - **Header date:** pair `[Icon Calendar]` with `[Data As Of]`.
   - **Why images instead of emoji:** emoji render differently on every PC and in the Power BI service. These drawings match the theme exactly. They have a transparent tint, so the same icons work on both the light and dark theme.

   | KPI measure | Icon measure |
   |---|---|
   | Videos Tracked, Videos Published | Icon Videos |
   | Total Views, Avg Views per Video | Icon Views |
   | Engagement Rate, Total Likes | Icon Engagement |
   | Shorts Share | Icon Shorts |
   | Regional Language Share, Channels Outside India Share | Icon Language |
   | Top Category | Icon Category |
   | Channels | Icon Channels |
   | Total Subscribers, Avg Subscribers per Channel | Icon Subscribers |
   | Trending Videos | Icon Trending |
   | Rising Keywords | Icon Rising |
   | Declining Keywords | Icon Declining |
   | Interest, Demand Index, Interest MoM %, Interest YoY % (3M) | Icon Interest |
   | Top State, State Index, Top Keyword in State, Interest vs Cricket | Icon State |
   | Content Gap Score | Icon Gap |
   | Growth 12w % | Icon Growth |
   | Median Views | Icon Median |
   | Avg Views per Day | Icon Per Day |
   | Supply (30d videos, est.) | Icon Supply |
   | Small Channel Share | Icon Small Channels |
   | Keywords Scored | Icon Keywords |
   | Opportunities page header | Icon Opportunity |
   | Data As Of | Icon Calendar |

2. **Canvas:** Format page → Canvas settings → 16:9 (1280 × 720). Use the same size on every page.
3. **Map visuals:** File → Options → Security → tick **Use Map and Filled Map visuals**. Restart if Power BI asks.
4. **Turn off auto date/time:** File → Options → Current file → Data load → untick **Auto date/time**. The model already has `dim_date`, and auto date tables bloat the file.
5. **Page layout (same on every page):**

```
┌──────────────────────────────────────────────────────────────┐
│ Page title (text box)                  [Data As Of] card     │  ← header, 60px
│ [page navigator buttons ...........................]          │  ← 36px
├──────────────────────────────────────────────────────────────┤
│ [slicer] [slicer] [slicer]                                    │  ← filter row, 48px
├──────────────────────────────────────────────────────────────┤
│ [KPI] [KPI] [KPI] [KPI] [KPI]                                 │  ← cards, ~100px
├──────────────────────────────────────────────────────────────┤
│ main visuals                                                  │
│                                              footnote (text)  │  ← data caveat, 9pt grey
└──────────────────────────────────────────────────────────────┘
```

   - Build the header on page 1, then copy and paste it onto each new page.
   - **Navigator:** Insert → Buttons → Navigator → **Page navigator**. Hide the drill-through and tooltip pages so they don't appear in it.
   - **Data As Of:** a card visual (new card) showing the measure `[Data As Of]`, with the category label turned off.
   - **Spacing:** a 16px gap between visuals and a 16px page margin. View → Snap to grid helps.

6. **Number formats** are already set on the measures. Don't override them in the visuals. For big numbers in cards, set Display units = Auto (shows 23.2bn).

**Chart rules for every page:**
- one value axis per chart (no dual-axis combo charts)
- bars sorted by value
- no 3D and no pie charts
- gridlines kept faint (the theme handles this)
- at most 8 coloured series per chart
- with more than 3 series on a scatter or map, filter down or use small multiples

---

## Page 1: Overview

**Question it answers:** what's trending in India on YouTube right now, at a glance?

```
[Topic group ▼] [Category ▼] [Shorts? ▼]
[Videos Tracked] [Total Views] [Engagement Rate] [Shorts Share] [Regional Language Share] [Top Category]
┌ Videos by category (bar) ───┐ ┌ Search interest over time (line) ──────┐
│                              │ │                                         │
└──────────────────────────────┘ └─────────────────────────────────────────┘
┌ Videos by language (bar) ───┐ ┌ Rising / Declining keyword cards ┐ ┌ Channel origin (bar) ┐
```

| Visual | Fields | Settings |
|---|---|---|
| Slicer (dropdown) | `dim_keyword[topic_group]` | Title "Topic". Affects only the trends line (see Interactions) |
| Slicer (dropdown) | `dim_category[category_name]` | Title "YouTube category" |
| Slicer (tile) | `dim_video[is_short]` | Rename items in the slicer header to "Shorts"/"Long-form", or leave True/False |
| 6 × Card (new) | `[Videos Tracked]`, `[Total Views]`, `[Engagement Rate]`, `[Shorts Share]`, `[Regional Language Share]`, `[Top Category]` | One card visual with 6 measures, or 6 cards. Display units Auto |
| Clustered **bar** chart | Y: `dim_category[category_name]` · X: `[Videos Tracked]` · Tooltips: `[Total Views]`, `[Engagement Rate]`, `[Median Views]` | Sort by Videos Tracked, descending. Filter: Top N 10 by Videos Tracked. Data labels on. Grey bars, top bar red |
| **Line** chart | X: `dim_date[date]` · Y: `[Interest]` | Title "Search interest on YouTube (relative to cricket)". X-axis type Continuous. Filter `dim_date[date]` to the last 2 years (relative date). Single series |
| Clustered bar | Y: `dim_language[language_name]` · X: `[Videos Tracked]` | Top N 8. Sort descending |
| 2 × Card | `[Rising Keywords]`, `[Declining Keywords]` | Labels "Rising keywords (MoM)" and "Declining keywords (MoM)" |
| Clustered bar | Y: `dim_channel[channel_origin]` · X: `[Channels]` | 3 bars: India / Outside India / Unknown |

**Interactions:**
- Select the topic slicer → Format → Edit interactions → set it to **None** on every video visual. Topic groups belong to keywords, not trending videos, so they shouldn't filter video stats.
- Set the category and Shorts slicers to **None** on the trends line.

**Footnote:** "Trending = YouTube's India 'mostPopular' chart, not all of YouTube. Search interest is a Google Trends index (0–100, scaled to 'cricket'), not search counts."

---

## Page 2: India map

**Question it answers:** which states search most for a topic on YouTube?

```
[Topic group ▼] [Keyword ▼ (single select)] [Zone ▼]
┌ Filled map (dim_state) ────────────────┐ ┌ Top 10 states (bar) ────┐
│  title = [Map Title]                    │ │                          │
│                                         │ ├ Top State card ─────────┤
└─────────────────────────────────────────┘ └──────────────────────────┘
```

| Visual | Fields | Settings |
|---|---|---|
| Slicer (dropdown) | `dim_keyword[topic_group]` | |
| Slicer (dropdown, single select) | `dim_keyword[keyword]` | Add visual filter `dim_keyword[is_anchor]` = False. Turn on search |
| Slicer (tile) | `dim_state[zone]` | |
| **Filled map** | Location: `dim_state[state_map_name]` · Tooltips: `[State Index]`, `[Interest vs Cricket]`, `[Top Keyword in State]` | Fill colours → fx → Gradient on `[State Index]`, minimum `#ffe5ea`, maximum `#c4002b` (one hue, light to dark; dark theme `#3a1d23` → `#ff5c7a`). Title → fx → Field value → `[Map Title]`. Map style Light/Grayscale. Turn off auto-zoom and zoom to India |
| Clustered bar | Y: `dim_state[state]` · X: `[State Index]` · Tooltips: `[Interest vs Cricket]` | Top N 10 by State Index. Sort descending. Data labels on |
| Card | `[Top State]` | Label "Highest interest" |

**Drill-through:** after building page 8 (State detail), right-click a state on the map or bar → Drill through → State detail.

**If the filled map won't place states correctly:**
- use **Azure Maps** (Insert → Azure map) with Location `dim_state[state_map_name]`, or
- use **Shape map** (enable it under Options → Preview features) with an India states TopoJSON. The `state` column matches common India TopoJSON names.

**Footnote:** "State Index = 0–100 within each keyword (100 = the state with the highest share of searches). Small states and union territories (for example Lakshadweep and Mizoram) can score high from very few searches."

---

## Page 3: Content categories

**Question it answers:** which categories get the views and the engagement, and where's the volume?

```
[Shorts? ▼] [Language ▼] [Channel origin ▼]
[Videos Tracked] [Median Views] [Engagement Rate] [Avg Views per Day]
┌ Bubble: views vs engagement per category ─┐ ┌ Median views by category (bar) ┐
└────────────────────────────────────────────┘ └─────────────────────────────────┘
┌ Engagement rate by category (bar) ────────┐ ┌ Uploads over time (column) ─────┐
```

| Visual | Fields | Settings |
|---|---|---|
| Slicers | `dim_video[is_short]`, `dim_language[language_name]`, `dim_channel[channel_origin]` | Dropdowns |
| 4 × Card | `[Videos Tracked]`, `[Median Views]`, `[Engagement Rate]`, `[Avg Views per Day]` | |
| **Scatter** chart | Values: `dim_category[category_name]` · X: `[Median Views]` · Y: `[Engagement Rate]` · Size: `[Videos Tracked]` | Leave Legend empty (one colour). Category labels on. X-axis log scale (views are skewed). Filter: `[Videos Tracked]` ≥ 10, which removes tiny categories |
| Clustered bar | Y: `dim_category[category_name]` · X: `[Median Views]` | Sort descending. Top N 12 |
| Clustered bar | Y: `dim_category[category_name]` · X: `[Engagement Rate]` | Sort descending. Same Top N filter |
| Clustered **column** | X: `dim_date[date]` · Y: `[Videos Published]` | Title "Tracked videos by publish date". Relative date filter: last 60 days |

Median views and engagement rate get **separate** bar charts on purpose, because they're on different scales (no dual axis).

**Footnote:** "Median is used instead of average because a few viral videos dominate the totals. Engagement = (likes + comments) / views, for videos with public like counts."

---

## Page 4: Trending topics

**Question it answers:** which keywords are rising, which are fading, and how does now compare with last year?

```
[Topic group ▼] [Language ▼] [Date range (between)]
[Rising Keywords] [Declining Keywords] [Interest] [Interest MoM %] [Interest YoY % (3M)]
┌ Interest over time for selected keywords (line, ≤ 6 keywords) ───────────────────┐
└───────────────────────────────────────────────────────────────────────────────────┘
┌ Keyword table: keyword | topic | Interest | sparkline | MoM | YoY | Status ───────┐
```

| Visual | Fields | Settings |
|---|---|---|
| Slicer (dropdown) | `dim_keyword[topic_group]` | |
| Slicer (dropdown) | `dim_keyword[keyword_language]` | |
| Slicer (between) | `dim_date[date]` | Default: last 2 years |
| 5 × Card | `[Rising Keywords]`, `[Declining Keywords]`, `[Interest]`, `[Interest MoM %]`, `[Interest YoY % (3M)]` | |
| **Line** chart | X: `dim_date[date]` · Y: `[Interest]` · Legend: `dim_keyword[keyword]` | Visual filter `dim_keyword[keyword]`: Top N **6** by `[Interest]`, so there are never more than 6 lines. Legend at top. 2px lines, no markers |
| **Table** | `dim_keyword[keyword]`, `dim_keyword[topic_group]`, `[Interest]`, `[Interest MoM %]`, `[Interest YoY % (3M)]`, `[Trend Status]` | Filter `dim_keyword[is_anchor]` = False. Sparkline: select `[Interest]` in the field well → Add a sparkline → X-axis `dim_date[year_month]`, line. Conditional formatting on `[Trend Status]` → Font colour → Field value → `[Trend Status Color]`. Sort by MoM % descending |

**Footnote:** "Status: Rising = interest up more than 15% versus the previous month; Declining = down more than 15%. Google Trends samples its data, so small changes are noise."

---

## Page 5: Video & channel performance

**Question it answers:** which videos and channels win, and do length and timing matter?

```
[Category ▼] [Language ▼] [Shorts? ▼] [Trending only? ▼]
┌ Top 15 videos (table) ──────────────────┐ ┌ Channel leaderboard (table) ───┐
└──────────────────────────────────────────┘ └────────────────────────────────┘
┌ Median views by duration (column) ┐ ┌ Engagement by duration (column) ┐ ┌ Uploads by hour (column) ┐
```

| Visual | Fields | Settings |
|---|---|---|
| Slicers | `dim_category[category_name]`, `dim_language[language_name]`, `dim_video[is_short]`, `fact_video_snapshot[in_trending]` | |
| **Table**: top videos | `dim_video[title]`, `dim_channel[channel_name]`, `dim_category[category_name]`, `[Total Views]`, `[Avg Views per Day]`, `[Engagement Rate]`, `dim_video[published_date]` | Top N 15 by Total Views on `dim_video[title]`. Data bars on Total Views (red). Word wrap off on title |
| **Table**: channels | `dim_channel[channel_name]`, `dim_channel[country]`, `dim_channel[subscriber_tier]`, `[Videos Tracked]`, `[Total Views]`, `[Total Subscribers]`, `[Engagement Rate]` | Top N 20 by Total Views |
| Clustered column | X: `dim_video[duration_bucket]` · Y: `[Median Views]` | Sort by `duration_bucket` ascending (the buckets are prefixed 1., 2., ... so they sort in order) |
| Clustered column | X: `dim_video[duration_bucket]` · Y: `[Engagement Rate]` | Same sort |
| Clustered column | X: `dim_video[publish_hour_ist]` · Y: `[Videos Tracked]` | Title "When trending videos are published (IST hour)". X-axis Categorical, sorted by hour |

**Footnote:** "Views are each video's latest public count. Like counts hidden by creators are left out of the engagement rate."

---

## Page 6: Creator opportunities

**Question it answers:** where is demand growing faster than established creators are serving it, and in which languages?

```
[Topic group ▼] [Keyword language ▼]
[Keywords Scored] [Content Gap Score] [Demand Index] [Growth 12w %] [Small Channel Share]
┌ Opportunity map: demand vs growth (scatter) ─┐ ┌ Top 10 gaps (bar) ─────────────┐
└───────────────────────────────────────────────┘ └────────────────────────────────┘
┌ Language × topic matrix (Demand Index heatmap) ─────────────────────────────────┐
```

| Visual | Fields | Settings |
|---|---|---|
| Slicers | `dim_keyword[topic_group]`, `dim_keyword[keyword_language]` | |
| 5 × Card | `[Keywords Scored]`, `[Content Gap Score]`, `[Demand Index]`, `[Growth 12w %]`, `[Small Channel Share]` | |
| **Scatter** | Values: `dim_keyword[keyword]` · X: `[Demand Index]` · Y: `[Growth 12w %]` · Size: `[Small Channel Share]` | Filter `is_anchor` = False. Analytics pane: add an X **average line** and a Y **constant line at 0** to make 4 quadrants. Top right = high demand and growing. Category labels on. Single colour |
| Clustered bar | Y: `dim_keyword[keyword]` · X: `[Content Gap Score]` · Tooltips: `[Demand Index]`, `[Growth 12w %]`, `[Small Channel Share]` | Top N 10 by Content Gap Score. Sort descending |
| **Matrix** | Rows: `dim_keyword[keyword_language]` · Columns: `dim_keyword[topic_group]` · Values: `[Demand Index]` | Cell elements → Background colour → Gradient, `#ffe5ea` → `#c4002b` (dark theme `#3a1d23` → `#ff5c7a`) (font switches to white on dark cells: use Font colour rules, or turn on "Apply to values" with auto contrast). Turn off subtotals |

**Footnote:**
- "Content gap score (0–100) = 40% demand + 30% growth + 30% share of top recent videos from channels under 100K subscribers, each as a percentile."
- "35 of 105 keywords are scored so far. The daily search rotation fills the rest within 3 days."

---

## Page 7: Business & marketing

**Question it answers:** which regions should a brand target for a given topic?

```
[Topic group ▼ (single)] [Zone ▼]
┌ State × topic heatmap (matrix) ─────────────────────────────┐ ┌ Best states for [topic] (bar) ┐
│                                                              │ │                               │
└──────────────────────────────────────────────────────────────┘ ├ Interest vs cricket (bar) ────┤
```

| Visual | Fields | Settings |
|---|---|---|
| Slicer (dropdown, single select) | `dim_keyword[topic_group]` | Title "Target topic". Edit interactions: **None** on the heatmap, so the heatmap always shows every topic |
| Slicer (tile) | `dim_state[zone]` | |
| **Matrix** heatmap | Rows: `dim_state[state]` · Columns: `dim_keyword[topic_group]` · Values: `[State Index]` | Background gradient `#ffe5ea` → `#c4002b` (dark theme `#3a1d23` → `#ff5c7a`). Visual filter `is_anchor` = False. Subtotals off. Narrow columns (about 70px) |
| Clustered bar | Y: `dim_state[state]` · X: `[State Index]` | Title "Best states to target" (or fx → a measure if you want it dynamic). Top N 10. Sort descending |
| Clustered bar | Y: `dim_state[state]` · X: `[Interest vs Cricket]` | Top N 10. Shows how big the topic is in each state relative to cricket, not just its share |

**Footnote:** "State Index compares states for the same topic. Interest vs Cricket shows the topic's size relative to cricket in that state, which is a better signal of absolute demand."

---

## Page 8: State detail (drill-through, hidden)

1. Add a new page called "State detail" and hide it (right-click the tab → Hide page).
2. Format page → Page information → Page type = **Drill-through**. Drill-through from: `dim_state[state]`. Keep "Keep all filters" on.
3. Power BI adds a back button automatically. Place it top left.

| Visual | Fields | Settings |
|---|---|---|
| Card (title) | `[State Page Title]` | Large text, category label off |
| 3 × Card | `[Top Keyword in State]`, `[Interest vs Cricket]`, `dim_state[zone]` (First) | |
| Clustered bar | Y: `dim_keyword[keyword]` · X: `[State Index]` | Filter `is_anchor` = False. Top N 15 |
| Clustered bar | Y: `dim_keyword[topic_group]` · X: `[State Index]` | Sort descending |
| Clustered bar | Y: `dim_keyword[keyword_language]` · X: `[State Index]` | Shows which language terms the state searches most |

---

## Page 9: Keyword tooltip (hidden)

1. Add a new page called "Keyword tooltip". Page type = **Tooltip**, canvas size Tooltip (320 × 240). Hide it.
2. In the Tooltip field well (Format page → Page information), add `dim_keyword[keyword]`.
3. Visuals:
   - card `[Trend Status]`, with conditional font colour from `[Trend Status Color]`
   - card `[Interest MoM %]`
   - small line chart, X `dim_date[date]` (last 12 months), Y `[Interest]`
4. On pages 4, 6 and 7, select the keyword visuals → Format → General → Tooltips → Type = Report page → Page = Keyword tooltip.

---

## Polish checklist (after all pages)

- [ ] **Data notes:** add an info button (Insert → Buttons → Information) on each page, linked to a bookmark that shows a text box with all the caveats from POWERBI_SETUP.md section 4.
- [ ] **Slicers:** View → Sync slicers. Sync `topic_group` across pages 2, 4, 6 and 7, and `category_name` across pages 1, 3 and 5.
- [ ] **Alt text:** every chart has alt text (Format → General → Alt text). For example: "Bar chart of tracked videos by category".
- [ ] **Titles:** every title says what the chart shows, for example "Median views by video length", not "Median Views by duration_bucket".
- [ ] **Refresh check:** run `python run_daily.py`, then Home → Refresh in Power BI, and confirm `Data As Of` updates.
- [ ] Save, then File → Export → PDF for a portfolio snapshot.

## Known data limits to keep in mind while building

- **Video and channel snapshots:** there's only one day so far. Anything "over time" on video stats will be flat until more days arrive. Trends charts already have 5 years of weekly data.
- **Content gap score:** 35 of 105 keywords are scored today.
- **"Regional" languages:** this includes Hindi. Every Indian language except English counts.
