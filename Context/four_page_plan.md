> **STATUS (6 Nov 2026): project closed and signed off by the user (Q38).** The 4 pages are final. **Do not run `build_report.py` on the report pages again**; any further polish is done by hand in Power BI. The daily GitHub Actions pipeline keeps collecting data. Interview material: [interview_prep.md](interview_prep.md).

# 4-page dashboard plan (for review, nothing built yet)

**Goal:** cut 8 pages down to 4. Each page answers one question a new YouTuber asks, in the order they'd ask it. Each page has a **question as its title** and a **live headline that gives the answer**, so the viewer gets the conclusion before reading any chart.

**The story in one line:** *"What's happening → where should I play → how should I make it → who am I making it for."*

Questions where I need your decision are marked **❓ Q1, Q2…** and collected at the end.

---

## 0. How much data do we have?

There are two very different kinds of data:

| Data | Time covered | Rows | Can we get more years? |
|---|---|---|---|
| **Search interest** (Google Trends, YouTube search, India) | **5 years, weekly**: 31 Oct 2021 → 1 Nov 2026 (262 weeks) | 27,772 | Already the maximum for weekly data. Google gives monthly points beyond 5 years |
| **Search interest by state** | One snapshot covering the same 5 years combined | 3,816 | Fine as is |
| **Videos** (views, likes, comments) | **1 day**: 5 Nov 2026. Videos published 6 Oct → 5 Nov | 3,443 videos | **Not from the YouTube API.** It only gives today's numbers, so history builds only by running daily |
| **Channels** (subscribers, size) | **1 day**: 5 Nov 2026 | 2,707 channels | Same: daily runs only |
| **Keyword opportunity data** (demand, growth, small-channel share) | Built from the above | 35 of 105 keywords have small-channel share so far | Fills in after about 3 daily runs (new keywords too). The Content Gap Score was **removed** (Q31) |

**Important finding (6 Nov):** the daily run was **never scheduled**, so only 5 Nov data exists. This is solved by the **GitHub Actions** daily job (see "Automation and GitHub setup"). It starts collecting once the repo is pushed and the API key secret is added. Creating a Windows scheduled task was blocked by the permission system, and it's no longer wanted anyway.

**What this means for the design:**
- Anything about **trends over time** (growing, falling, seasonality) uses search interest, which has 5 years. That's strong.
- Anything about **videos** (format, length, channel size) is a **snapshot of the last 30 days of popular videos**. That's fine for "what works now", but it can't show change over time yet.
- So the plan uses time-based charts only for search data, and doesn't fake history for videos.

**❓ Q1. Backfill video history?** Public Kaggle datasets of YouTube India trending videos exist (daily, roughly 2020–2024). Adding one would give years of video history, for example "how Shorts took over trending since 2021". The trade-off is that it's a different source with older dates, and I'd need to check what's available now. Options:
- (a) Live data only. Run daily for 2 weeks before interviews. Simple and fully your own pipeline.
- (b) Add a historical Kaggle dataset as a separate "history" layer. More impressive and more work, and the source has to be explained.

> **✅ Decided (Q1): (a) live data only.** The pipeline runs every day by itself on **GitHub Actions** (see "Automation and GitHub setup"), with no manual steps and no need for the laptop to be on, so history builds up automatically.

---

## Page 1: Market pulse
**Title:** *"What's happening on YouTube India right now?"*
**Why this page exists:** a creator needs the big picture before choosing anything. Is search growing, what's rising, what's dying, and when do topics peak?
**What it replaces:** Overview + Trending topics.

**Live headline (example):** "Fastest-rising topic: Gaming (+18% vs last month) · Shorts are 53% of popular videos · Most videos are in People & Blogs"

**Filters:** Topic · Video language · Content (Shorts / Long-form)

**KPI row (5 cards):**

| Card | Why it's there |
|---|---|
| Videos tracked | Shows the size of the sample, so the numbers can be trusted |
| Median views per video | What a *typical* popular video gets, used as a benchmark |
| Shorts share | How much of the market is Shorts |
| Indian-language share | How big the non-English audience is |
| Rising keywords (count) | Is the market heating up or cooling down |

**Visuals:**

| Visual | What it shows | How it helps a creator | Interview line |
|---|---|---|---|
| **Search interest, 5 years** (line) | Monthly search score for the selected topic | Is this topic a growing market or a shrinking one? | "5 years of weekly Google Trends data, scaled with cricket as a fixed reference so different batches compare fairly." |
| **Seasonality** (line, Jan–Dec) | Average score per calendar month across 5 years | When to publish: for example, exam topics peak before exams, travel before holidays | "This turns 5 years of history into a content calendar." |
| **Rising and falling keywords** (table, top 5 each) | Biggest month-on-month moves, with arrows and hover for the 5-year trend | Ride the rising ones, avoid the falling ones | "Rising means more than +15% vs last month. Smaller moves are noise in sampled data." |
| **Number of videos by YouTube category** (bar) | Where popular videos sit | Which categories YouTube is pushing right now | |
| **Most-viewed video right now** (panel) | Title, channel, views | A concrete example that makes the page feel live | |

**Removed from today's Overview:** videos by language (moves to page 4), videos by channel size (moves to page 3), engagement card (moves to page 3).

---

## Page 2: Find your niche ⭐ (hero page)
**Title:** *"Where is demand high and competition weak?"*
**Why this page exists:** this is the decision the whole project is built for. The original thinking here is the **competition signal**: the API can't count competitors (it caps at 1M results), so the page measures whether **small channels still reach the top results** for a keyword.
**What it replaces:** Creator opportunities.

> **✅ Decided (Q22/Q31): no Content Gap Score.** No weighted score, no weights, no "gap score" anywhere. Remove `content_gap_score` from the model and remove the `Content Gap Score`, `HL Gap`, `Icon Gap` and `Keywords Scored` measures (and any visuals using them) during the build. The page ranks niches with the **opportunity map quadrants** and plain measures instead.

**Live headline (example):** "12 niches are Hot right now (high demand and growing) · most open: *AI tools*: 41% of top videos are from small channels"

**Filters:** Topic · Keyword language

**KPI row:** Keywords tracked · **Hot niches** (count in the top-right quadrant) · Demand index · Growth (12 weeks) · Small-channel share

**Quadrant rules (simple, no weights):**
- **Right** = demand above the average of the keywords in view. **Up** = growth over the last 12 weeks above 0%.
- **Hot** (top right: high demand, growing) · **Emerging** (top left: smaller but growing) · **Big but flat** (bottom right) · **Skip** (bottom left).

**Visuals:**

| Visual | What it shows | How it helps a creator | Interview line |
|---|---|---|---|
| **Opportunity map** (scatter, 4 named quadrants) | Each keyword: demand (→) vs growth (↑), bubble size = small-channel share | The top-right quadrant, **"Hot"**, is where to start; bigger bubbles there are the most open | "Labelled quadrants turn a scatter plot into a decision, with no arbitrary weights." |
| **Hot niches, most open first** (table) | Keywords in the Hot quadrant: demand, 12-week growth, small-channel share, trend arrow. Sorted by small-channel share | A shortlist of niches to start with, and *why* each is on it | "I couldn't count competition directly, because the API caps results at 1M, so I measured whether small channels still reach the top results." |
| **Demand by language × topic** (heatmap) | Search demand for each language and topic pair | Spots regional-language gaps, such as Tamil education or Bengali food | "Regional languages are the under-served opportunity in India." |
| Hover on any keyword | 5-year trend and status | Quick check before deciding | Hidden tooltip page, a nice demo moment |

**My view on removing the score (the user asked):** it's **not crucial**. The quadrant map plus the "Hot niches, most open first" table answers the same question ("where should I start?"), and it's easier to explain because there are no weights to defend. The one thing lost is a single 0–100 number per keyword. The small-channel share already carries the "competition" story.

**❓ Q2. Should the dashboard give a final recommendation?** For example, a card on this page: *"If I started today: [keyword], in [language], as [format]."* Options:
- (a) A live card worked out from the data (changes with the filters)
- (b) A fixed sentence you write after studying the data. This is your own judgment, and interviewers like that
- (c) No card. You say it out loud in the interview

> **✅ Decided (Q2): (c).** No recommendation card on the dashboard. The user says the recommendation out loud in the interview ("If I started today: X, in language Y, as Shorts/long-form"). Prepare that sentence in the interview appendix once a few weeks of data have built up.

---

## Page 3: Make it and grow it
**Title:** *"How should I make it, and what does it take to grow?"*
**Why this page exists:** once the niche is chosen, the next questions are practical: Shorts or long-form, how long, how to title it, can a small channel compete, and how much effort (age, upload pace) the channels that made it put in.
**What it replaces:** Categories + Videos & channels + Upload playbook (3 pages become 1).

> **✅ Decided (Q32): option A.** Four pages; page 3 has two rows, "Make it" and "Grow it".

**Live headline (example):** "Shorts get 2.5x the views; long-form gets more engagement · 35% of small channels in top results are under a year old · they post about twice a week"

**Filters:** Topic · Video language · Content (Q37: no YouTube category filter)

**KPI row:** Median views per video · Engagement rate · Shorts share · Median uploads per month (small channels)

**Visuals (6 tiles, 2 rows):**

| Row | Visual | What it shows | How it helps a creator | Today's data says |
|---|---|---|---|---|
| Make it | **Shorts vs long-form** (2 small columns: views, engagement) | Median views and engagement for each format | Reach vs loyalty trade-off | Shorts 3.3M vs 1.3M views; long-form 1.4% vs 1.1% engagement |
| Make it | **Median views by video length** | Which length gets views | Plan the production effort | |
| Make it | **Title length** | Median views by title length | Packaging tip | Under 40 characters: 3.7M; 80–100: 1.8M |
| Grow it | **Can small channels get views?** (by channel size, including the under-10K split) | Median views by subscriber group | Realistic expectations, and motivation | 10K–100K: 2.7M, beating 100K–10M at 2.0M. Under 10K is the hard part |
| Grow it | **How new are the small channels in top results?** (Q15) | Number of small channels (under 100K) by channel age: under 1 year, 1–2, 2–5, 5+ | "Can a brand-new channel get there?" | 35% are under 1 year old; median age 2.3 years |
| Grow it | **How often do they upload?** (Q14) | Number of small channels by average upload pace: under once a week, 1–3 a week, 3–7 a week, daily or more | Sets a realistic posting schedule | Median 8.3 uploads a month (about 2 a week) |

**New model pieces for the "Grow it" row:** `dim_channel[channel_age_bucket]`, `dim_channel[uploads_per_month]` (total videos ÷ age in months, a lifetime average), `dim_channel[upload_pace_bucket]`, and a measure counting small channels behind the videos in the current filter. Method note for the footnote: "Upload pace is each channel's lifetime average, not its current pace."

**Dropped from the earlier page 3 plan (Q32):** "Category: reach vs engagement" (overlaps page 1's category chart and page 2's niche choice) and "Best day to upload" (a weaker signal).

**Dropped from today's pages:**
- Channel leaderboard and the top-15 video table (lists of names, not insights)
- Engagement by length
- Upload hour (noisy)
- Number of tags (half the videos have none, and the pattern is mostly a side effect of Shorts)

**❓ Q3.** Are you OK dropping **tags**, **upload hour** and the **channel leaderboard**? Or is there one you want to keep, for example a "top 5 videos to study" list?

> **✅ Decided (Q3): drop them all.** No tags chart, no upload-hour chart, no channel leaderboard, no top-videos table on page 3. (The `tag_count_bucket` column can stay in the model unused.)

**Footnote (said out loud too):** "These are patterns among popular videos, not proof of cause."

---

## Page 4: Know your audience
**Title:** *"Who am I making it for, and where are they?"*
**Why this page exists:** India isn't one market. The same topic is searched very differently by state, and that decides the language of the video.
**What it replaces:** India map + Business (+ the State detail drill-through stays, hidden).

**Live headline (example):** "Telugu searches come almost entirely from Andhra Pradesh and Telangana · 31% of popular videos are in Indian languages"

**Filters:** Topic · **Language** (the language of the search terms, `dim_keyword[keyword_language]`) · Keyword · Zone

**What the map measures (be precise):** the YouTube API does **not** give viewer location for public videos, so we **don't have views by state**. The map shows **where people search for the topic on YouTube** (Google Trends, YouTube Search, by state), which is the closest public signal of where the audience is. Title and footnote must say "searches", not "views".
- Interview line: *"YouTube doesn't share viewer geography, so I used YouTube-search interest by state from Google Trends as the audience signal."*

**Visuals:**

| Visual | What it shows | How it helps a creator | Interview line |
|---|---|---|---|
| **India heat map** (filled map, light-to-dark red) | Search interest by state for the chosen topic, language or keyword. Darkest = the state that searches most | See where the audience is | |
| **Top 10 states** (bar) | Same data, ranked | Exact targets | |
| **Number of videos by language** (bar, moved from page 1) | Which languages popular videos use. With a language picked, it shows the videos found by that language's keywords | Compare supply (videos) with demand (map): a state with high demand but few videos in its language is a gap | "I compare where people search with what language the supply is in." |
| **Topic size vs cricket** (bar, from Business) | How big the topic is in each state compared to cricket | Separates "a big share of a small topic" from "a big topic" | |
| **Right-click a state → State detail** (hidden page) | Top keywords, topics and languages for that state | Deep dive, a strong demo moment | |

**Map behaviour (user's request, 6 Nov):**
1. **Heat map by state:** each state is coloured on the light-to-dark red scale (`Map Color` measure, relative to the strongest state in view). This already exists on today's India map page.
2. **Auto-zoom to where the interest is:** when a language like **Telugu** is picked, the map zooms in to the region where the searches come from.
   - How: the map hides states with almost no interest (State Index below about 10, relative to the strongest state in view), and the map's **auto-zoom** fits the remaining states.
   - Checked with today's data: Telugu → only Andhra Pradesh (100) and Telangana (96) pass, so it zooms to that region. Tamil → Tamil Nadu + Puducherry. Bengali → West Bengal + Tripura, Sikkim, Manipur. With no language picked, 33 states pass, so the whole of India shows.
   - Hidden states still appear on the base map, just without colour.
3. **The user can still zoom out:** turn on the map's **zoom buttons** (and mouse-wheel zoom).
4. ⚠️ **Check in Power BI:** filled-map auto-zoom with the threshold filter has not been tested yet. If auto-zoom misbehaves, the fallback is Azure Maps, which also zooms to the data.
5. **Data gap:** some low-volume keywords (mostly regional) have little or no state data (`dim_keyword[has_state_data]` hides them from the keyword filter). Every language has at least some keywords with state data, as checked above.

**Brand angle:** removed (Q4).

> **✅ Decided (Q4): main viewer is new creators only.** No brand or marketing wording anywhere. The Business page goes; "Topic size vs cricket" stays because it helps a creator judge how big a topic is in a state.

---

## Things that apply to all 4 pages

- **Same layout everywhere:** title as a question, live headline, filters, KPI row, charts, footnote.
- **Filters only show choices that have data** (the fix from the Education + Telugu issue).
- **Bars:** light-to-dark red, darkest = biggest.
- **Plain chart titles:** "Number of videos by…", not "Videos Tracked by duration_bucket".
- **Hidden helper pages stay:** keyword hover tooltip and state drill-through.

**❓ Q5. Foreign channels in the video data.** 641 videos (19%) are from channels based outside India, and 701 have no country set. Today's top video is from a foreign channel. Options:
- (a) Keep everything (it *is* what India watches) and label it
- (b) Add a "Channel origin: India / Outside / Unknown" filter, defaulting to all
- (c) Exclude outside-India channels from the video stats

**❓ Q6. Keyword gaps.** Some topic and language pairs have no keyword, for example Education has no Telugu term. Should I add regional keywords for the main gaps (Telugu, Kannada, Bengali, Malayalam for Education, Finance and Tech) so the language filters work better?

> **✅ Decided (Q5): keep all videos**, including foreign channels, because the audience is Indian viewers either way (they're on India's trending chart or India search results). **No channel-origin filter**: origin doesn't matter for this audience. The `channel_origin` column stays in the data but isn't shown. (Confirm in Q8.)
>
> **✅ Decided (Q6): yes, add regional keywords for the main gaps.** The goal is the best data without making the pipeline fragile. The details (which terms, which script, how many) are questions Q10–Q13 below.

---

## Automation and GitHub setup (decided 6 Nov 2026)

### Decisions

| Topic | Decision |
|---|---|
| Video history | **Live data only** (Q1). No Kaggle backfill |
| Who runs the daily pipeline | **GitHub Actions** (in the cloud, laptop can be off). **Not** the Windows Task Scheduler: only one scheduler may run, or the two will clash. Skip the Windows command given earlier |
| Repo visibility | **Public**: `github.com/kammala-kalyan/YouTube-Trends-Intelligence`, branch `main` |
| Power BI updates | **Option B:** fresh data on GitHub, refreshed in Power BI Desktop. **No** Power BI Service |
| What the daily job may change | **Only `data/`.** It must never touch `Dashboards/`, the .pbip/.pbix files or any code |
| If Google Trends is blocked | **Keep the old trends data**, still save the YouTube data, and **email a failure notice** |
| Someone clones the repo | Opens the .pbip → clicks **Refresh** → the dashboard fills with the latest data from GitHub. No path editing |

### How the daily job works (`.github/workflows/daily.yml`)

1. **Schedule:** every day at `cron: "30 3 * * *"` (03:30 UTC = **9:00 AM IST**), plus a manual "Run workflow" button (`workflow_dispatch`). GitHub can start scheduled runs 10–30 minutes late, which is fine.
2. **Steps:**
   1. Check out the repo, set up Python 3.14 (the version the local venv uses), `pip install -r requirements.txt`.
   2. **Run pipeline** (one step, `python run_daily.py`, marked `continue-on-error`). Inside, `run_daily.py` runs trending → topic search → channels → Google Trends (weekly, only when the last file is 7+ days old) → `build_model.py`. A failed script doesn't stop the others; the script exits with an error at the end and writes the failed step names to the run summary.
   3. **Check file sizes:** flags any data file over 90 MB (GitHub's hard limit is 100 MB).
   4. **Commit only `data/`** with the message `data: YYYY-MM-DD`, `git pull --rebase`, then push. Skip the commit if nothing changed.
   5. **Report failures:** if the pipeline or size check failed, the run is marked **failed**, so GitHub emails you. The run summary says what broke, for example "Google Trends probably blocked the GitHub server. The last good Trends data is still used."
   6. `TZ: Asia/Kolkata` is set, so file dates follow India time.
3. **API key:** stored as a repository secret named `YOUTUBE_API_KEY` (Settings → Secrets and variables → Actions). It is never written in code. `.env` stays git-ignored. Checked: the key has never been committed.
4. **Permissions:** the workflow gets `contents: write` (to push data commits) and nothing else. A `concurrency` group stops two runs from overlapping.
5. **Notifications:** GitHub emails failed scheduled runs to the account that last edited the workflow. Check that *GitHub → Settings → Notifications → Actions → "Notify me for failed workflows only"* is on, with email ticked.
6. **Keeping it alive:** GitHub turns off scheduled workflows in a public repo after 60 days without repo activity. Daily data commits should count as activity. If GitHub ever emails "scheduled workflow disabled", re-enable it from the Actions tab.
7. **YouTube API quota:** about 3,700 of 10,000 free units per run. One run a day is safe.

### How the old data is preserved

- **YouTube data:** every day's raw pull is a new dated file (`trending_videos_YYYY-MM-DD…`). Nothing is overwritten, and `build_model.py` combines all dated files, so history grows every day.
- **Trends fully blocked:** `fetch_trends.py` stops without writing a file (checked: `SystemExit`, no output). The model keeps using the last good trends file.
- **Trends partly blocked:** `build_model.py` keeps each keyword's *latest available* trends data, so keywords missing from the new file keep their older data. State-level trends do the same (checked). ✅ **Fixed 6 Nov:** the cricket reference values are now matched to each batch *before* keeping the latest data. Before, a keyword whose newest state data came from an older run lost its reference and got blank state scores.

### Fixes (found and done 6 Nov 2026)

| # | Problem | Fix |
|---|---|---|
| 1 | `run_daily.py` prints "failed – continuing" but still **exits with success**, so GitHub would never send a failure email | ✅ Done. Failures are remembered, all steps still run, then it **exits with an error**. It also writes a short report on the GitHub run page saying which step failed |
| 2 | `data/` is **git-ignored**, so nothing would be committed | ✅ Done. `data/` is no longer ignored. `.env`, `logs/`, `venv/` and `__pycache__/` still are |
| 3 | Raw data grows about **2 MB/day on average** (YouTube files ~1.7 MB daily, Trends ~2 MB weekly) | ✅ **Decided: no compression.** The pipeline runs for **4–6 months at most** (about 0.25–0.4 GB of raw CSVs; git compresses them in storage), and the user will revisit then. Safety net: the workflow **fails and emails** if any data file goes over 90 MB, since GitHub rejects files over 100 MB. Files to watch: `data/model/fact_video_snapshot.csv` (+0.35 MB per day) and `data/model/dim_video.csv` (grows with every new video). Both should stay under the limit for about 6 months |
| 4 | Power BI's local files are tracked in git: `.pbi/cache.abf` (a data cache) and `.pbi/localSettings.json` | ✅ Done. Untracked (`git rm --cached`, files still on disk) and added to `.gitignore` |
| 5 | `Dashboards/India YouTube Trends.pbix` is an **old copy** (from before all the recent changes) and is tracked in git | ✅ **Decided: keep it** (don't delete Power BI files). It's outdated, though: **always open the .pbip**, not the .pbix |
| 6 | The dashboard reads data from a **fixed local path** (`DataFolder = "D:\E\...\data\model\"`), which breaks on any other computer | ✅ **Done (6 Nov, after Power BI closed).** `DataFolder` = the GitHub raw URL, and all 13 tables use `Web.Contents`. Refresh works once `data/` is pushed |

### How the dashboard loads data after cloning

- Change the `DataFolder` parameter to `https://raw.githubusercontent.com/kammala-kalyan/YouTube-Trends-Intelligence/main/data/model/`.
- Change each table's query from `File.Contents(DataFolder & "x.csv")` to `Web.Contents(DataFolder & "x.csv")`.
- Result: anyone who clones the repo opens the .pbip, clicks **Refresh**, picks **Anonymous** the first time Power BI asks how to connect to the website, and gets the latest data. No local path, no setup.
- The .pbip itself never changes daily. Only the CSVs on GitHub change, and Power BI reads them on Refresh.
- GitHub's raw files can lag by up to about 5 minutes after a data commit.
- **Your own copy reads the GitHub data too.** So **Refresh fails until `data/` has been pushed** to the public repo. To test with local data instead, set `DataFolder` to the local `data\model\` folder *and* switch the queries back to `File.Contents` (a web URL and a local path need different functions).
- When cloned, the dashboard opens **empty** until Refresh is clicked, because the data cache is not in git. Say this in the README: "Open the .pbip and click Refresh."

---

## Current dashboard (built so far, 6 Nov 2026), to reuse in the 4-page build

**Pages today (8 visible + 2 hidden):** Overview · India map · Categories · Trending topics · Videos & channels · Upload playbook · Creator opportunities · Business, plus hidden **State detail** (drill-through) and **Keyword tooltip** (hover). The 4-page build replaces the 8 visible pages and keeps both hidden pages.

**Already built on the Overview (keep these ideas on page 1):**
- **One Topic filter** instead of Topic + YouTube category. It filters search trends directly, and videos through the keyword-search results (`bridge_keyword_video`, two-way filter). Side effect to explain: when a topic is picked, trending videos that don't match any of that topic's keywords drop out ("videos found for this topic").
- **Language** filter (`dim_language[language_label]`: English and Indian languages by name, everything else "Other languages") and **Content** filter (`dim_video[video_format]`: Shorts / Long-form as buttons). Neither filters the search-trend visuals, because they describe videos, not keywords.
- **Live headline** under the page title (`[Overview Headline]`).
- **KPI:** "Median views per video" replaced "Total views".
- **"Most-viewed video right now"** panel: a heading text box, then `[Top Video Title]`, then `[Top Video Detail]` ("by channel · views").
- **"Number of videos by channel size"** replaced "Where channels are based" (blank sizes hidden).
- Search chart titled **"How much India searches on YouTube"**, subtitle "Google Trends score per month, higher = more searches" (no cricket wording).

**Model pieces added (all defined in `build_report.py`):**

| Kind | Name | Purpose |
|---|---|---|
| Column | `dim_video[video_format]` | "Shorts" / "Long-form" label |
| Column | `dim_video[publish_weekday]` (+ hidden `publish_weekday_num`) | Upload day in **IST** (`published_at` is UTC, +5.5 h) |
| Column | `dim_video[title_length_bucket]`, `dim_video[tag_count_bucket]` | Packaging charts |
| Column | `dim_category[has_videos]`, `dim_language[has_videos]` | Hide empty items in filters |
| Column | `dim_language[language_label]` | Readable language list |
| Measure | `Overview Headline` | Fastest-rising topic (or "Best-performing topic" if none is rising) · Shorts share · top category. Says "No videos match these filters yet…" when empty |
| Measure | `Top Video Title`, `Top Video Detail` | Most-viewed video in the current filter |
| Measures | `HL Videos`, `HL Median Views`, `HL Engagement`, `HL Channels`, `HL State Index`, `HL Interest vs Cricket`, `HL Gap` (**remove**, Q31) | Bar colours: 6-step light-to-dark red, darkest = biggest bar in view |

**Builder helpers in `build_report.py` to reuse:** `sl_content()`, `sl_language()`, `sl_category()` (filters with the "only show choices that have data" rule), `f_has_videos()` (slicer filter `Videos Tracked > 0`), `f_not_blank()`, `text_card()` (left-aligned wrapping text from a measure), `header(..., headline=...)`, and `line(..., axis=...)` for the Jan–Dec seasonality chart.

**Why the Education + Telugu page went blank (6 Nov):** the data had **0 Telugu videos for any Education keyword**. The Education keywords are UPSC, JEE, NEET, coding, Excel, SSC CGL, English speaking, plus one Hindi and one Tamil general-knowledge term. Fixed in the dashboard (filters hide empty choices); the data gap itself is **Q6**.

---

## Design preferences from the user (follow these)

- **Write for a non-technical viewer:** plain titles ("Number of videos by language"), short subtitles, no jargon or field names.
- **Fewer, meaningful pages:** about 4, each with a clear purpose the user can explain in an interview.
- **No overlapping filters:** merge filters that sound the same (Topic replaced Topic + Category).
- **Name things by what they mean:** the Shorts filter is called **"Content"**, with **Shorts / Long-form** buttons.
- **Colour:** the user asked for intensity changes rather than one red bar and grey bars. They suggested red-to-blue or red-to-green; we chose **light-to-dark red**, because two-colour scales read as "good vs bad" or two opposite groups. The user accepted this.
- **Panels must say what they are:** a clear heading on top (for example "Most-viewed video right now"), then the content, cleanly laid out.
- **Don't let filters lead to blank pages.**
- **Workflow:** the user reviews plans as Markdown in `Context/` before building, answers the open questions, and wants every decision written down.

---

## Known issues and things not yet checked (as of 6 Nov 2026)

- **Never checked in Power BI:** the Content buttons (horizontal list slicer), the headline and top-video text cards (`multiRowCard`), and the `Videos Tracked > 0` filters on slicers were generated but never seen rendered. Check with screenshots during the 4-page build.
- **Only 1 day of video data** (5 Nov) and **35 of 105 keywords** with small-channel share. Both improve once the daily job runs.
- **Example headlines in this plan are made up** (for example "Gaming +18%", "12 niches are Hot", "AI tools 41%"). The real ones come from the data.
- **8 channels have no size group.** Hidden from the channel-size chart with a "not blank" filter.
- **Old `.pbix`** is outdated; open the .pbip.

---

## Pending actions for the user

1. ~~Close Power BI~~ (done: the data-source switch applied).
2. **Commit and push everything, including `data/`.** Until the data is on GitHub, Refresh in Power BI fails.
3. Add the repository secret **`YOUTUBE_API_KEY`** on GitHub.
4. Actions tab → **Daily data pipeline** → **Run workflow** once, and check it commits `data: YYYY-MM-DD`.
5. ✅ Build done (6 Nov): open the .pbip, click Refresh (after pushing `data/`), and send screenshots of the 4 pages for review. Then sign off (Q38).
6. Review the new keywords in `keywords.py` ("Your part" 2) and the keyword test report `data/keyword_test_YYYY-MM-DD.csv`.

---

## Remaining gaps (found 6 Nov 2026, after Q35)

**❓ Q36. "Language" means two different things.** On pages 1 and 3 it's the **language of the video** (`dim_language`). On pages 2 and 4 it's the **language of the search term** (`dim_keyword[keyword_language]`, for example "UPSC Telugu" → Telugu). Same word, different data, which a viewer (or interviewer) will trip over.
→ *Recommendation: name them differently everywhere: **"Video language"** (pages 1, 3) and **"Search language"** (pages 2, 4).*

> **✅ Decided (Q36), part 1: "Language" means the video language.** On pages 1 and 3 the filter is the **language of the video** (`dim_language[language_label]`), labelled **"Video language"**.
>
> **❓ Q39 (part 2, the catch):** pages 2 and 4 are built on **search data** (Google Trends), not on videos. The map knows how much each state searches "UPSC Telugu" or "తెలుగు సినిమా", but has no video languages, and can't, because YouTube doesn't share viewer location. So the **Telugu zoom on the map** (the user's request) has to come from **searches for Telugu content**. Options:
> - (a) **Keep a language filter on pages 2 and 4**, labelled simply **"Language"**, with a subtitle: "Based on searches for content in this language, e.g. 'UPSC Telugu'". To a creator it means the same thing ("I make Telugu content"), and the map zoom works.
> - (b) **No language filter on pages 2 and 4.** Use only Topic and Keyword (picking "UPSC Telugu" as a keyword still zooms to Andhra Pradesh and Telangana). Simpler, but "pick Telugu → zoom" is lost.
>
> → *Recommendation: (a).*
>
> **✅ Decided (Q39): (a).** Pages 2 and 4 keep a filter labelled **"Language"** (`dim_keyword[keyword_language]`) with a grey note beside it: "Language = searches for content in that language, for example 'UPSC Telugu'." Pages 1 and 3 use **"Video language"**.
>
> **Idea checked and ruled out (6 Nov): filter by where the viewer watches from.** Not possible with public data:
> - The **YouTube Data API** (what this project uses) gives **no viewer geography** for any video.
> - Viewer location exists only in **YouTube Analytics**, and only for **channels you own** (the owner has to log in). We can't get it for other people's videos.
> - The trending chart is per **country** (India as a whole), not per state.
> - Channel country is where the **creator** is, not the viewers.
>
> So **Google Trends search interest by state is the only public state-level audience signal.** It isn't "inaccurate" data. It measures searches, not views, which is a standard way to estimate regional demand. The issue is only how the filter is labelled, which option (a) solves.

**❓ Q37. Page 3 brings back Topic + YouTube category.** On the Overview you asked to merge these because they overlap. Page 3's plan still has both.
→ *Recommendation: page 3 uses **Topic only** (same as page 1). The YouTube category stays only as a chart on page 1.*

> **✅ Decided (Q37): page 3 uses Topic only.** No YouTube category filter on page 3 (category stays only as a chart on page 1).

**❓ Q38. When do hand edits take over from the build script?** `build_report.py` rebuilds every page from scratch, so anything you change by hand in Power BI is overwritten the next time it runs. For the dashboard to carry your own finishing touches, there needs to be a clear hand-over point.
→ *Recommendation: I build the 4 pages with the script → you review with screenshots → I fix → **you sign off, and from then on the script is no longer run on the report pages**. You do the final polish by hand in Power BI (layout tweaks, wording, tooltips). Model changes after that are made in Power BI too, or reported back so the script is updated.*

> **✅ Decided (Q38): as recommended.** The script builds the 4 pages → the user reviews with screenshots → fixes → **the user signs off**. After sign-off, **`build_report.py` is never run on the report pages again**; final polish is done by hand in Power BI. Later model changes are made in Power BI, or reported back so the script stays in step.

**Other gaps (no decision needed, just tracked):**
- The daily job hasn't run yet (needs your push and secret), so video data is still 1 day old.
- Several visuals have never been checked rendered (Content buttons, headline cards, slicer filters, map auto-zoom).
- The talking-point numbers come from 1 day of data. Recheck them before any interview.
- The new keyword lists (P2, P4) were drafted by me and need your review (see "Your part").

---

## Your part: what only you should do (so it's your project, not an AI's)

The honest interview framing: **"I used an AI coding assistant for implementation. I defined the problem, made the product decisions, checked the data and finished the dashboard myself."** This plan's decision log (Q1–Q38) is the evidence: every product decision in it was yours.

**1. Things only you can do (accounts):** push to GitHub, add the `YOUTUBE_API_KEY` secret, turn on failure emails, run the workflow once.

**2. Own the keyword list (most important, and your best story).**
- Review every new keyword in P2 (niches) and P4 (regional). You're the expert on how Indians actually search: you pointed out "UPSC Telugu" yourself.
- Change any term that doesn't sound like a real search. For other languages, ask a friend who speaks it: "How would you search for this on YouTube?" That's real user research you can mention.
- Interview story: *"I noticed regional native-script keywords returned almost no data, because people like me search 'UPSC Telugu' in English letters. So I redesigned the keyword strategy around how people really search."*

**3. Check the numbers yourself (about 30 minutes).** Pick 3 numbers on the dashboard and verify them:
- the top video's views against YouTube itself
- one state on the map against Google Trends (trends.google.com, YouTube Search, India)
- one median against the raw CSV in Excel

Then you can say *"I validated the pipeline against the sources"*, which interviewers love.

**4. Do the final polish by hand in Power BI** (after Q38's sign-off): layout spacing, chart titles and footnotes in your own words, tooltips, alt text, and anything that bothers you visually. Knowing the file hands-on is what lets you answer "how did you build this visual?".

**5. Write the conclusion yourself (Q2):** after 2–3 weeks of data, look at the 4 pages and write your own "If I started a channel today, I'd pick…" sentence. It's your judgment, and the most memorable moment in the interview.

**6. Learn the core logic well enough to explain it.** These are the questions you'll get. I can write a plain-English explainer for each when you're ready:
- How the cricket anchor makes Google Trends batches comparable
- Why median and not average; how the engagement rate is calculated
- Month-on-month change and the ±15% rising/declining rule
- The bridge table: how one Topic filter reaches both trends and videos
- How the quadrants are defined on page 2
- How the daily GitHub Actions job keeps old data when a source fails

**7. Write the README case study and resume bullets in your own words** (I can review them).

---

## Build log: 6 Nov 2026 (after "do it")

**Pipeline and data**
- `keywords.py`: 105 → **184 keywords in 26 groups**. Added Tier 1 (8 groups) and Tier 2 (5 groups, behind `INCLUDE_TIER2 = True`) and **28 regional keywords** (UPSC / share market / mobile review / health tips + Telugu, Tamil, Kannada, Malayalam, Bengali, Marathi, Gujarati). Moved `bhajan` → Devotional & Spiritual, `SSC CGL` → Government jobs, `family vlog` → Daily vlogs (Tier 2). One change from P2: the Tier 2 DIY keyword **"art" became "drawing"** (much clearer search intent).
- `fetch_trends.py`: now runs **daily on a slice** (a seventh of the keywords, rotating) **plus any keyword with no Trends data yet**; `--all` pulls everything. It stops after 3 failed batches in a row (blocked), and exits with code 2 when partly blocked, so the failure email goes out while the data that arrived is kept.
- `run_daily.py`: calls the Trends slice every day (`--trends` = all keywords).
- `build_model.py`: **one shared cricket reference across all snapshots** (needed because slices from different days must be comparable); `content_gap_score` removed; fixed column order for `fact_keyword_opportunity`.
- `test_keywords.py` (new, Q13): checks keywords without Trends data against Google Trends (free) and writes `data/keyword_test_YYYY-MM-DD.csv`. It doesn't edit `keywords.py`: drop "NO DATA" terms by hand after review.

**Dashboard (`build_report.py`, regenerated with Power BI closed; backup of the previous version in the session scratchpad)**
- **4 visible pages**: Market pulse · Find your niche · Make it & grow it · Know your audience, plus hidden State detail and Keyword tooltip. The other 6 old visible pages are gone.
- Removed: `Content Gap Score`, `Keywords Scored`, `Icon Gap`, `HL Gap` and the `content_gap_score` column.
- Added measures: `Keywords Tracked`, `Niche Quadrant`, `Quadrant Color`, `Hot Niche Flag`, `Hot Niches`, `Niche Headline`, `Small Channels in Top Results`, `Median Uploads per Month (Small)`, `Grow Headline`, `Map Strength`, `Audience Headline`, `HL Small Channels`.
- Added columns: `dim_channel[channel_age_bucket]`, `[uploads_per_month]`, `[upload_pace_bucket]`.
- Page 1 rising/falling tables only list keywords that actually rose (MoM > 0) or fell (MoM < 0). Page 2's scatter shows all keywords coloured by quadrant (labels off, hover for details). The page 4 map hides states with `Map Strength` < 0.1 and uses auto-zoom.

**Keyword test result (6 Nov, `data/keyword_test_2026-11-06.csv`):** of 79 new keywords, 33 ok, 7 weak and **39 "NO DATA"**, including **all 28 regional "topic + language" keywords**. The NO DATA list:
- Regional: mobile review / share market / UPSC / health tips + each of the 7 languages
- Niche: temple vlog, moral stories, new car launch, organic farming, govt jobs, science facts, history facts, success story, life lessons, pet care, house construction

Weak: bike review, railway exam, bank exam, amazing facts, daily vlog, couple vlog, home decor.
- **Cause (checked):** they're not empty. Tested alone (without cricket), "UPSC Telugu" has interest in 248 of 262 weeks, "share market Tamil" 261, "health tips Telugu" 237, "mobile review Telugu" 235. In a batch with **cricket**, they're so much smaller that Google's 0–100 scale rounds them to 0. So the anchor is too big for small keywords.
- They still work for **YouTube search** (video data for pages 1 and 3, e.g. Telugu education videos). Only the **search-score** visuals (pages 2 and 4, Trends charts) would show them as 0 or blank.
- **✅ Decided (Q40): (b), chained references**, implemented 6 Nov:
  - **Tests that shaped it:** against "unboxing" (~25% of cricket) or "Excel" (~20%), the regional keywords still round to 0, because they're about 1% of Excel. Against **"share market Tamil"** (itself one of the regional keywords), "pet care" scores ~30 and shows in 239 of 262 weeks. Even against that, "mobile review Gujarati" (1 week of 262) and "health tips Bengali" (27 weeks) are essentially zero: genuinely tiny search volume.
  - **Design:** `ANCHOR_CHAIN` in `keywords.py` (final: cricket → Excel → bike review, see the correction below). Level 0 keywords are batched with cricket, level 1 with Excel, level 2 with the last reference. Each reference is a tracked keyword measured one level up, so every level converts back to the cricket scale: `scale = reference's normalized mean (from one level up) / its raw mean in this batch`. States use the same idea: `ratio to cricket = keyword / reference x reference's ratio to cricket in that state`.
  - **Automatic levels:** `fetch_trends.py` reads each keyword's latest result (Trends files and keyword tests). If it was (almost) all zero (mean < 1 or zero in over half the weeks), the keyword moves down one level next time. A keyword still zero at the last level is listed as "too small to measure" and skipped (it stays in YouTube search). Each batch records `anchor_used`.
  - **Same-day re-runs merge** into the day's file instead of overwriting it.
  - **Checked:** on all existing data, the new `build_model.py` gives identical results (max difference 0.0) for every keyword and state.
  - **Correction during testing (same day):** the first level-2 reference, "share market Tamil", is searched almost only in Tamil Nadu. State results are chained through the reference, so every state where it's ~0 went blank: "UPSC Telugu" came out as Puducherry/Tamil Nadu. **Final chain: `["cricket", "Excel", "bike review"]`**. "bike review" is searched in 35 of 36 states and is ~5% of Excel. **Rule: every reference must be searched all over India.**
  - **Bugs found and fixed while testing:** (1) same-day re-runs wrote mixed date formats, so `build_model.py` crashed; dates are now always `YYYY-MM-DD` and parsed with `format="mixed"`. (2) The same-day merge deleted whole old batches, losing co-batched keywords and references; it now drops only the re-fetched keywords' rows. (3) A keyword test result was wrongly counted as "has Trends data"; it now only sets the starting level. Also added `python fetch_trends.py --dry` to show the plan without contacting Google.
  - **Verified result (6 Nov, after 4 Trends runs):** all 184 keywords have Trends data (48,470 weekly rows). Chained values match direct head-to-head tests within Google's sampling noise (UPSC Telugu 0.059 chained vs ~0.072 direct; share market Tamil 0.066 vs ~0.077). State results are right: UPSC Telugu → Andhra Pradesh 100, Telangana 90; health tips Telugu → Telangana 100, Andhra Pradesh 74; UPSC Tamil → Puducherry 100, Tamil Nadu 74; UPSC Malayalam → Kerala 100; share market Telugu → Andhra Pradesh 100, Telangana 90.
  - **Too small to measure, even against "bike review" (7 keywords):** mobile review Kannada, mobile review Marathi, mobile review Gujarati, share market Gujarati, health tips Bengali, health tips Marathi, health tips Gujarati. They're skipped in Trends but still used for YouTube video search. **Your part:** keep them (video data only) or remove them from `keywords.py`.
  - **Still showing 0 until their weekly slice comes round (automatic, within 7 days):** 25 older keywords last measured on 5 Nov at level 0, mostly native-script and Hindi terms (for example शेयर बाजार, తెలుగు సినిమా) plus "AI tools" and "make money online". On their next turn they move to level 1 or 2 automatically.
  - Interview line: *"Low-volume regional terms rounded to zero next to my reference term, so I chained references by size (cricket → Excel → bike review), each searched nationwide, so every keyword lands on one scale. The pipeline moves keywords between levels automatically, and I validated the chained values against direct comparisons."*

**Not yet seen rendered (check with screenshots):** quadrant colours on the scatter, the measure filters (Hot niches table, map zoom, rising/falling), all four headlines, the Content buttons, and the map zoom when "Telugu" is picked. Known fallback if the filled map doesn't zoom: Azure Maps.

---

## Screenshot review 1 (6 Nov 2026): diagnosis and proposed fixes

| # | What the user saw | Real cause (checked) | Proposed fix |
|---|---|---|---|
| 1 | "Data as of 5 Nov", today's data missing | It **was** extracted: GitHub has 4,707 video rows for 6 Nov. Power BI was refreshed a few minutes before the daily job finished committing | No fix. Refresh again. (GitHub raw files can lag ~5 min after a commit) |
| 2 | Mizoram (and the north-east) top every map and chart | State scores = keyword ÷ **cricket** in that state. Cricket is weak there (share 28 in Mizoram vs 60+ elsewhere), so every topic looks oversized | **❓ Q41.** Convert to **popularity within the state**: one extra daily request for cricket's own state profile, then `keyword popularity = ratio to cricket × cricket's popularity in that state`. Optional: also weight by state size |
| 3 | Map is one flat colour | The rule-based colour measure isn't applied per state on the filled map | Use Power BI's built-in **gradient colour rule** on the state score (light → dark red) |
| 4 | Language columns on page 2 all "0.0" | That grid is **search demand by search-term language**, not videos. Regional terms are tiny on the cricket scale (UPSC Telugu ≈ 0.06 vs UPSC ≈ 8.4), so they round to 0.0 | **❓ Q42.** Scale each language column to its own maximum ("within Telugu, which topic has the most demand?") |
| 5 | Only English and Hindi videos, "Telugu videos have English titles" | Video language comes from YouTube's audio-track setting first (4,232 videos), then default language (1,483), then title script (423). 224 videos labelled English name an Indian language in their title or tags (Hindi 84, Punjabi 45, Tamil 30, Telugu 16…) | **❓ Q43.** Smarter detection, in order: audio track → native script → **language named in title/tags** ("Telugu", "#tamil", "Hindi dubbed") → **language of the search that found it** (e.g. "UPSC Telugu") → **channel's main language** → English |
| 6 | Hot niches: "bhajan" Growth +15.7% but Trend "Declining" | Growth = 12 weeks; Trend = last month vs the month before. Both true, but it looks contradictory | Show the 12-week trend label in that table, or rename the column "Last month" |
| 7 | Rising/Falling lists show ±100% for tiny keywords | Tiny keywords flip between 0 and 1 on Google's scale, giving ±100% | Leave low-volume keywords out of Rising/Falling |
| 8 | Headlines cut off with a grey block; top video title cut off | The text card is too short and shows a scrollbar | Taller, wrapping text boxes for the headline and video title |
| 9 | Page 4 "Videos found, by video language" empty for Agriculture | New topics' videos are searched on a 3-day rotation; Agriculture keywords haven't had their turn yet | No fix; fills in within 3 days |
| 10 | Opportunity map squashed to the left | One very large keyword ("cartoon", ~330) stretches the axis | Log scale on the demand axis |

**Decisions (6 Nov):** Q41 = **popularity within the state** (no state-size weighting) · Q42 = **scale per language** · Q43 = **language named in title/tags + channel's main language** (not "language of the search").

**Done (6 Nov):**
- **Q41:** `fetch_trends.py` makes 1 extra request a day for cricket's own state profile (`data/trends_cricket_states_DATE.csv`). `build_model.py`: `popularity = ratio to cricket × cricket's popularity in the state`, then `state_index` = popularity scaled 0–100 per keyword (falls back to the plain ratio if no profile exists). Result: Mizoram no longer tops everything (Devotional → Kerala, Puducherry, Tamil Nadu; UPSC Telugu → Andhra Pradesh, Telangana).
- **Tiny regions hidden** on the audience page (map, top states, zone chart, headline): states/UTs under 2 million people (Census 2011): A&N Islands, Arunachal Pradesh, Chandigarh, Dadra & Nagar Haveli, Daman & Diu, Goa, Lakshadweep, Mizoram, Nagaland, Puducherry, Sikkim (`dim_state[is_small_region]`). They still exist in the data and on the State detail page.
- **Map colour:** Power BI's built-in gradient rule on the search score (light → dark red), replacing the rule-based colour measure.
- **"How big is the topic there?"** (ratio to cricket, the same bias) replaced by **"Which part of India?"**: average search score by zone.
- **Q42:** new measure `Demand Within Language` (100 = the language's top topic); the grid is titled "Which topics lead within each language?".
- **Q43:** language order is now: Indian-language audio track → native script → one Indian language named in title/tags ("Hindi dubbed" = Hindi) → English audio track → default language → English letters (weak); then **channel's main language** (≥60% of its strongly labelled videos, min 2) relabels weak ones. Result: 198 videos relabelled from title/tags and 30 from the channel; Punjabi 63 → 116, Telugu 230 → 250, Kannada 210 → 230; English 2,496 → 2,195.
- **Low volume:** `Trend Status` = "Low volume" when last month's search score is under 0.5 (new `Recent Interest` measure). Rising/Falling lists exclude these (no more ±100% noise).
- **Hot niches table:** Trend column removed; Growth labelled "(12 wk)".
- **Headlines** shortened, and the headline card has no inner padding (no grey scrollbar). **Top video title** uses a wrapping card.
- **Opportunity map:** log scale on demand.
- **Build-script bug fixed:** helper measures that Power BI had re-saved on one line weren't being updated (e.g. `Map Strength`). The sync now matches both layouts; a second run reports "no changes".

---

## Rules for anyone (or any AI) working on this project later

1. **Until the user signs off the 4 pages, the dashboard is generated by `build_report.py`.** Make report and page changes there, not by editing the PBIR JSON files by hand. The script rebuilds every page from scratch, so manual Power BI edits are overwritten. **After sign-off (Q38), never run `build_report.py` on the report pages again**: the user polishes by hand in Power BI, and those edits must be preserved.
2. **Close Power BI Desktop before running `build_report.py`.** If Power BI is open and then saves, it overwrites the regenerated files.
3. **Model changes** (new measures and columns) also live in `build_report.py` (`HELPERS`, `CALC_COLUMNS`) and are written into the TMDL files. Existing helper measures are kept in sync with the script.
4. **Only GitHub Actions runs the daily pipeline.** Don't also schedule it on Windows.
5. **The daily job commits only `data/`.** It never edits `Dashboards/`, code or the .pbip.
6. **Never commit secrets.** The API key lives in `.env` locally (git-ignored) and in the `YOUTUBE_API_KEY` secret on GitHub.
7. **Never delete or overwrite old data files.** History is the main asset, because the YouTube API only gives today's numbers.
8. **Back up before big changes:** commit to git first, so any change can be undone from history. The old `backups/` folder was removed on 6 Nov 2026.
9. **Filters must only show choices that have data** (the `has_videos` columns plus the `Videos Tracked > 0` slicer filter), so pages never go blank.
10. **Video numbers are a snapshot of popular videos, not proof of cause.** Say so in footnotes, and don't build "over time" charts on video data until weeks of history exist.
11. **Always `git pull` before you push.** The daily GitHub Actions job commits `data/` every morning (as `github-actions[bot]`), so the local copy is usually behind.
12. **No Claude / AI-tool attribution in the repo** (user's instruction, 6 Nov): no co-author lines in commits, and no tool-specific config files tracked (`.mcp.json` is git-ignored).

---

## Order of work after you approve

1. **Automation:** ✅ fixes 1–6 and the workflow (`.github/workflows/daily.yml`) are done. **Still for you:** commit and push everything (including `data/`), add the `YOUTUBE_API_KEY` secret on GitHub, then run the workflow once from the Actions tab to test.
2. Build the 4 pages, and delete the other 4 visible pages.
3. You check them in Power BI with screenshots, and I fix anything off.
4. After about 3 daily runs: every keyword (old and new) has opportunity data, and the headlines become reliable.
5. Write the README / case study with screenshots, "how to open" steps and resume bullets.

---

## Round 2 questions (6 Nov 2026): close the gaps before building

The aim is that nothing in the build rests on a guess. Each question has a **recommendation** (my default if you agree). Reply with the numbers, for example "Q9: add Devotional and Kids; Q12: yes".

### A. The creator and the scope

**Q8. Confirm Q5.** Keep every video (including foreign channels) and show **no** channel-origin filter anywhere?
→ *Recommendation: yes.*

**Q9. Are the 13 topic groups the right niches?** Today: Tech, Finance, Education, Gaming, Food, Travel, Music, Movies, Sports, News, Health & Fitness, Business & Startups, Beauty & Lifestyle. Big Indian YouTube niches that are **missing**:
- Devotional / Spiritual (bhajans are under Music today)
- Kids / Cartoons
- Comedy / Entertainment vlogs
- Motivation / Self-improvement
- Agriculture / Farming
- Automobiles (cars, bikes)
- Government jobs (partly under Education: SSC CGL)
- Astrology

Each new group adds about 4–8 keywords (more quota and Trends requests).
→ *Recommendation: add the 3–4 biggest (Devotional, Comedy, Automobiles, Agriculture), not all 8.*

**Q10. Which languages count as "main"?** Today: English, Hindi, Tamil, Telugu, Kannada, Malayalam, Bengali, Marathi, Punjabi. Add Gujarati, Odia or Bhojpuri?
→ *Recommendation: keep the 9, and maybe add Gujarati (large audience, almost no keywords today).*

### B. Regional keywords (Q6 details)

**Q11. Native script or English-style?** Many Indians search regional content in English letters ("UPSC Telugu", "Tamil news") rather than native script ("తెలుగు వార్తలు"). Native-script terms are often too low-volume for Google Trends to return state data.
- (a) Native script only (today's approach)
- (b) English-style only ("[topic] in Telugu")
- (c) Both for the main gaps

→ *Recommendation: (c), and keep a term only if Google Trends returns data for it (tested once before it's added for good).*

**Q12. Which gaps to fill?** Current coverage: 68 English keywords, 14 Hindi, then only 3–5 each for the other 7 languages. Proposed: for **Telugu, Tamil, Kannada, Malayalam, Bengali and Marathi**, add one term each for **Education, Finance, Tech and Health**, where missing (about 20–25 new keywords).
→ *Recommendation: yes, with the exact terms listed in the plan for you to approve before they're added.*

**Q13. Keep a "keyword test" step?** Before a new keyword goes live, one check confirms that YouTube search and Google Trends both return data for it. Terms that return nothing are left out, so they don't create blank spots.
→ *Recommendation: yes.*

### C. Creator questions the plan doesn't answer yet

**Q14. Upload frequency:** "How often do successful small channels post?" Can be estimated from each channel's video count and age (data we already have). Add to page 3?
→ *Recommendation: yes. It's one of the first things a new creator asks.*

**Q15. Time to take off:** "How old are the small channels that reach the top results?" (channel age, data we already have). Add to page 3?
→ *Recommendation: yes, as a small chart ("most small channels in top results are under N years old").*

**Q16. Channels to learn from:** you dropped the channel leaderboard (big names). A different list would be **"small channels winning in this niche"**: under 100K subscribers, appearing in top results. That's channels a beginner can actually study. Add a short list (top 5) on page 2?
→ *Recommendation: yes. It turns the niche choice into something actionable.*

**Q17. Title words that work:** the most common words in the top videos' titles for a topic (for example "how to", "2026", "in Telugu"). Add to page 3?
→ *Recommendation: yes, as a simple bar of the top 10 words. It also shows text-analysis skills.*

**Q18. Earnings (CPM / RPM) by niche:** there's **no reliable public data**, and estimates from blogs would be guesses.
→ *Recommendation: leave it out, and say why if asked.*

**Q19. Competition volume:** "How many videos were uploaded on this topic in the last 30 days?" The API caps the count at 1,000,000, so big topics all look the same.
→ *Recommendation: use it only inside the gap score (as now), not as its own chart.* (Superseded: the gap score was removed in Q31, so this count isn't shown anywhere.)

**Q20. Video growth speed** ("how many views a video gets in its first week"): possible only after 2–3 weeks of daily data.
→ *Recommendation: plan it as a later addition. Don't build it now.*

### D. Definitions to confirm

**Q21. "Small channel" = under 100K subscribers?** (Used in the gap score and Q16.) Alternative: under 10K, a true beginner.
→ *Recommendation: keep under 100K for the score, and show the 10K split in the channel-size chart.*

**Q22. Gap score weights:** 40% demand + 30% growth + 30% small-channel share. You'll defend this in interviews; are you comfortable with it?
→ *Recommendation: keep it. Reason: demand matters most, and growth and openness are equal tie-breakers.*

**Q23. Rising / declining = more than ±15% vs the previous month?**
→ *Recommendation: keep it.*

**Q24. Videos window = published in the last 30 days?**
→ *Recommendation: keep it. Recent enough to be "what works now".*

### E. Pipeline robustness

**Q25. Spread Google Trends over the week?** Today it pulls all keywords in one run (27 batches, about 35 with new keywords). Spreading it as **one-seventh of the keywords each day** means fewer requests per run, a lower chance of being blocked, and a failure costs only that day's slice (old data is kept).
→ *Recommendation: yes.*

**Q26. Failure emails:** email on **every** failed run, or only when the **same step fails 2 days in a row** (fewer false alarms from one-off blocks)?
→ *Recommendation: every failure for the first 2 weeks, then decide.*

**Quota check for new keywords (facts, 6 Nov):** YouTube search costs 100 units per keyword and runs a third of the keywords per day. 105 → about 140 keywords raises a day's use from about 3,700 to about 4,900 units, under the 9,000 safety limit in `fetch_topics.py`. Safe.

### F. Presentation

**Q27. Theme:** light (current) or dark?
→ *Recommendation: light. It prints and screenshots better.*

**Q28. How will you show it in interviews?** Live in Power BI on your laptop, screenshots or PDF, or a recorded walkthrough video? This decides how much polish the README needs and whether we need an "offline" copy in case the internet fails.
→ *Recommendation: live demo plus a PDF export as backup.*

**Q29. Product name:** keep "India YouTube Trends", or give it a product-style name (for example "NicheFinder India")?
→ *Recommendation: your choice. A name makes it feel like a product.*

**Q30. Anything a creator asked you for** (friends, other creators) that isn't in this plan? A real user request is the strongest interview story.

---

## Round 2 answers (6 Nov 2026) and round 3 proposals

### Decided

| # | Decision |
|---|---|
| Q14 Upload frequency | ✅ **Build it.** Placement: see proposal P1 |
| Q15 Channel age of small channels in top results | ✅ **Build it.** Placement: see proposal P1 |
| Q16 Small channels to learn from | ❌ **Don't build** |
| Q17 Title words | ❌ **Don't build** |
| Q18 Earnings / CPM | ❌ **Don't build** |
| Q19 Competition volume as a chart | ❌ Not built (and with the gap score removed, not used anywhere) |
| Q20 Video growth speed | ❌ **Don't build** (not now, not later) |
| Q21 Small channel = under 100K | ✅ Keep. Show the 10K split in the channel-size chart |
| Q22 Gap score weights | ❌ **Removed entirely**: no Content Gap Score, no weights (Q31) |
| Q23 Rising/declining ±15% | ✅ Keep |
| Q24 30-day video window | ✅ Keep |
| Q25 Spread Google Trends over the week | ✅ **Yes**, one-seventh of the keywords per day |
| Q27 Theme | ✅ Light, as before |
| Q28 Presentation | ✅ Don't spend time on presentation extras now. Build it well, keeping in mind it will be presented in interviews |
| Q29 Name | ✅ **India YouTube Trends** (product and project name) |
| Q11 How Indians search | ✅ The user confirms: people search regional content **in English letters**, like "UPSC Telugu". Options in P3 |

**Not answered yet, so I'll use the recommendation unless told otherwise:** Q8 (keep all videos, no origin filter, as the user already said in Q5) · Q10 (languages: see P4) · Q13 (keyword test step: yes) · Q26 (email on every failure for the first 2 weeks) · Q30 (real creator requests: none known).

### Facts behind Q14 and Q15 (data of 5 Nov 2026)

Among the channels behind videos found in topic searches:
- **Small channels (under 100K):** 429 channels, **median age 2.3 years**, **median 8.3 uploads a month** (about 2 a week).
- **All channels:** median age 5.1 years, 12.3 uploads a month.
- **Age of the small channels:** under 1 year: **149 (35%)** · 1–2 years: 54 · 2–5 years: 106 · 5+ years: 120.
- **How often the small channels post:** under once a week: 142 · 1–3 a week: 114 · 3–7 a week: 92 · daily or more: 78.
- Talking point: *"A third of the small channels reaching top search results started less than a year ago, and they post about twice a week."*
- Method: uploads per month = the channel's total videos ÷ its age in months (an average over its life, not its current pace).

### P1. Where Q14 and Q15 go (choose one)

Both are about **growing a channel**, which sits best on page 3 ("How should I make the video?"), next to "Can small channels get views?".

- **Option A, recommended: keep 4 pages and reshape page 3 into two rows**
  - Row 1, **Make it:** Shorts vs long-form (views + engagement) · Median views by video length · Title length
  - Row 2, **Grow it:** Can small channels get views? · **How new are the small channels in top results?** (Q15) · **How often do they upload?** (Q14)
  - Dropped from the earlier page 3 plan: "Category: reach vs engagement" (overlaps page 1's category chart and page 2's niche choice) and "Best day to upload" (a weaker signal).
  - Page 3 title becomes *"How should I make it, and what does it take to grow?"*
- **Option B: 5 pages.** Page 3 "Win the format" keeps its 6 tiles, and a new page 4 **"Grow your channel"** holds channel size, channel age, upload frequency and best upload day. Know your audience becomes page 5. More room, but one more page to explain.

**✅ Decided (Q32): A.** Four pages, page 3 reshaped. See the Page 3 section.

### P2. Missing niches to track (choose)

Today's 13 groups miss several of the biggest Indian YouTube niches. Proposed groups, each with 4 starter keywords in English-style search terms (the way people actually search):

**Tier 1, recommended to add (8 groups, 32 keywords):**

| New group | Starter keywords | Why |
|---|---|---|
| Devotional & Spiritual | devotional songs, Hanuman Chalisa, bhakti, temple vlog | One of India's largest YouTube audiences; `bhajan` moves here from Music |
| Comedy & Entertainment | comedy video, funny video, prank, roast | Huge, especially Shorts |
| Kids & Family | cartoon, kids songs, rhymes, moral stories | Very high views, a different audience |
| Automobiles | car review, bike review, electric scooter, new car launch | Strong, steady niche |
| Agriculture & Village life | farming, organic farming, village life, kisan | Large rural audience, low competition |
| Government jobs | govt jobs, railway exam, bank exam, police exam | Big separate demand; `SSC CGL` moves here from Education |
| Facts & Knowledge | amazing facts, science facts, history facts, mystery | Very popular "facts" channels in India |
| Motivation & Self-improvement | motivation, success story, study motivation, life lessons | Common beginner niche |

**Tier 2, optional (5 groups, 20 keywords):** Astrology (rashifal, horoscope, vastu, astrology) · Daily vlogs (daily vlog, couple vlog, family vlog (moves from Beauty & Lifestyle), village vlog) · DIY & Crafts (DIY, craft ideas, home decor, art) · Pets & Animals (dog, cat, pet care, animals) · Home & Interior (home tour, interior design, house construction, kitchen design).

Moving a keyword to another group only relabels it. Its history is kept.

**✅ Decided (Q33): hybrid.** Add **Tier 1 and Tier 2** (13 groups, 52 keywords). Tier 2 keywords are marked as tier 2 in `keywords.py` so they're easy to remove. **If Tier 2 slows the pipeline down** (quota close to the limit, Google Trends blocks, or many Tier 2 terms failing the keyword test), **drop Tier 2 and keep Tier 1.**

### P3. How to write regional keywords (choose)

The user and most Indians search like **"UPSC Telugu"** (topic in English + language name).

- **Option A, recommended: "topic + language" pattern.** For each gap, add one English-style term such as `UPSC Telugu`, `share market Tamil` or `health tips Kannada`, tagged with that language. YouTube search then also gets `relevanceLanguage` = that language, so it returns videos in that language. **Keep the existing native-script terms** (their history stays). The keyword test (Q13) drops any term that returns no data.
- **Option B: both styles for every gap** (English-style + native script). Double the keywords and quota, and native-script terms often return too little data.
- **Option C: native script only** (today). Doesn't match how people search, and is the main reason for the blank spots.

**✅ Decided (Q34): A**, the "topic + language" pattern (for example `UPSC Telugu`), keeping the existing native-script terms, with the keyword test dropping terms that return no data.

### P4. Which gaps to fill (Q12 suggestion)

Today the other languages have only 3–5 keywords each, and **Tech, Health, Business and Education have almost no regional terms**. Suggested fill, using P3 option A, for **6 languages × 4 topics = 24 keywords**:

| Topic | Pattern | Telugu | Tamil | Kannada | Malayalam | Bengali | Marathi |
|---|---|---|---|---|---|---|---|
| Education | UPSC + language | UPSC Telugu | UPSC Tamil | UPSC Kannada | UPSC Malayalam | UPSC Bengali | UPSC Marathi |
| Finance | share market + language | share market Telugu | share market Tamil | share market Kannada | share market Malayalam | share market Bengali | share market Marathi |
| Tech | mobile review + language | mobile review Telugu | mobile review Tamil | mobile review Kannada | mobile review Malayalam | mobile review Bengali | mobile review Marathi |
| Health | health tips + language | health tips Telugu | health tips Tamil | health tips Kannada | health tips Malayalam | health tips Bengali | health tips Marathi |

- Optional: add **Gujarati** (a 7th column, +4 keywords) and **Punjabi** (+4). Both have big audiences and few keywords today.
- Optional: the same pattern for the new Tier 1 niches later, for example `devotional songs Telugu`.
- The keyword test runs on all of them first. Anything with no data is dropped and listed for you.

**✅ Decided (Q35): as recommended.** Add the 24 keywords above **plus a Gujarati column** (+4: UPSC Gujarati, share market Gujarati, mobile review Gujarati, health tips Gujarati), following the Q10 recommendation. Punjabi is not added (it already has 3 keywords). All 28 go through the keyword test first.

### P5. Load check if everything above is added

| | Today | + Tier 1 (32) + P4 (24) | + Tier 2 (20) too |
|---|---|---|---|
| Keywords | 105 | ~161 | ~181 |
| YouTube quota per day (search a third of keywords) | ~3,700 | ~5,600 | ~6,300 |
| Google Trends batches per day (spread over the week, Q25) | 27 once a week | ~6 a day | ~7 a day |

**Final choice (Q33 + Q35):** 105 + 32 (Tier 1) + 20 (Tier 2) + 28 (regional) = **~185 keywords**, about **6,450 YouTube units a day** and about **7 Trends batches a day**. All of these fit under the 9,000-unit safety limit. The new keywords need about 3 days to get their first video data and a week to get Trends data.

### Q31. What did you mean by "remove Q22"?

The Content Gap Score is `40% demand + 30% growth + 30% small-channel share`.
- (a) Keep the score exactly as it is, and just drop the question
- (b) Keep the score but use **equal weights** (one third each). Easiest to defend: "no arbitrary weights"
- (c) Remove the score completely, and rank niches only with the opportunity map's quadrants

→ *Recommendation: (b).*

> **✅ Decided (Q31): remove the score completely** (the user's choice; option c). See the Page 2 section for the replacement design (quadrants + "Hot niches, most open first" table) and my view that it isn't crucial.

---

## Summary of questions

| # | Question | Options |
|---|---|---|
| Q1 | Backfill years of video history from a public dataset? | ✅ **(a) live only, scheduled daily** |
| Q2 | Final recommendation on page 2? | ✅ **(c) say it out loud only**, no card |
| Q3 | OK to drop tags, upload hour and the channel leaderboard? | ✅ **Drop them all** |
| Q4 | Main viewer: creators only, or also brands? | ✅ **New creators only** |
| Q5 | Foreign-channel videos? | ✅ **Keep all, no origin filter** |
| Q6 | Add regional keywords for missing topic and language pairs? | ✅ **Yes** (details in round 2) |
| Q8–Q30 | Round 2 (scope, keywords, new creator questions, definitions, pipeline, presentation) | ✅ Mostly answered, see "Round 2 answers" |
| Q31 | Gap score: keep as is, equal weights, or remove? | ✅ **Remove entirely** (score, weights, measures) |
| Q32 | Upload frequency and channel age: reshape page 3 (4 pages) or add a 5th page? | ✅ **A: 4 pages, page 3 reshaped** |
| Q33 | Which new niches to track (Tier 1 / Tier 2)? | ✅ **Tier 1 + Tier 2; drop Tier 2 if it slows things down** |
| Q34 | Regional keyword style: topic + language / both / native only? | ✅ **Topic + language** ("UPSC Telugu") |
| Q35 | Approve the 24 regional keywords? Add Gujarati / Punjabi? | ✅ **24 + Gujarati (28)** |
| Q36 | What "Language" means | ✅ **Video language** on pages 1 and 3 |
| Q39 | Language filter on pages 2 and 4 (search-based) | ✅ **(a)**: "Language" + note explaining it's based on searches |
| — | First GitHub Actions run (6 Nov, manual) | ✅ Passed in 1m43s: trending (2,123 rows), topic search (62 keywords, ~6,261 quota units), channels, Trends retry, model rebuild; committed `data: 2026-11-06` |
| Q40 | Small keywords round to 0 next to cricket in Google Trends | ✅ **(b) chained references**: cricket → Excel → bike review (all nationwide), with automatic levels; verified |
| Q37 | Page 3 has Topic + YouTube category again | ✅ **Topic only** |
| Q38 | When hand edits in Power BI take over from the build script | ✅ **After sign-off, no more script runs on pages** |
| Q7 | The old `India YouTube Trends.pbix` (outdated copy, tracked in git)? | ✅ Keep it. Open the .pbip, not the .pbix |

---

## Appendix: interview material

### Problem statement

> Thousands of people in India start a YouTube channel every month, and most pick a topic based on gut feeling. They don't know which topics people are searching for, which ones are growing or fading, which formats (Shorts or long-form, short or long videos, which language) get views, or whether a topic is already owned by big channels.
>
> **India YouTube Trends Intelligence** answers those questions before the creator uploads anything. It combines the YouTube Data API (trending videos, top videos per topic, channel stats) with Google Trends for YouTube Search (5 years of weekly interest and a state-level breakdown) for 105 keywords across 13 topic groups and 9 Indian languages. A Python pipeline runs every day on GitHub Actions and builds a star schema, and a 4-page Power BI report turns it into decisions: *what to make, in which format and language, for which audience, and where the competition is weakest.*

**One-line version:** "A data-driven way to choose a YouTube niche in India: what people want, what's growing, and where small creators can still win."

### Talking points from the data (snapshot of 5 Nov 2026; recheck after more daily runs)

- **Shorts get 2.5x the median views** (3.3M vs 1.3M), but **long-form gets higher engagement** (1.4% vs 1.1%). Shorts bring reach; long-form builds a loyal audience.
- **Small channels can win:** channels with 10K–100K subscribers have a higher median (2.7M) than 100K–1M or 1M–10M channels (2.0M). Under 10K is lowest (1.0M), so the first 10K is the hard part.
- **Short titles do better:** titles under 40 characters have a median of 3.7M, falling to 1.8M at 80–100 characters.
- **Day:** Friday and Saturday uploads have the highest median (about 2.8M), Wednesday the lowest (1.2M).

Caveat to say out loud: these are patterns among popular videos, not proof of cause.

### Questions interviewers may ask, and honest answers

| Question | Answer |
|---|---|
| "Trending isn't all of YouTube, is it?" | Correct. Trending is YouTube's India most-popular chart. That's why I also pull the top recent videos per keyword, so the opportunity analysis isn't only based on trending. |
| "Google Trends is relative, not real search counts." | Yes. I anchor every batch to "cricket" so keywords from different batches can be compared on one scale. |
| "Why median instead of average views?" | A few viral videos dominate totals. Median shows what a typical video gets. |
| "How did you measure competition?" | The search API caps result counts at 1M, so I use the share of top recent videos from channels under 100K subscribers. If small channels appear in the top results, the niche is still open. |
| "How is the data kept fresh?" | A GitHub Actions job runs the pipeline every morning, commits only the data, keeps old data if a source fails, and emails me on failure. Power BI reads the CSVs straight from the repo, so anyone who clones it just clicks Refresh. |
| "Why is video history short?" | The YouTube API only gives current numbers, so history has to be collected daily. The pipeline does that automatically; the Trends data already has 5 years. |
| "What would you add next?" | Views-over-time per video once more daily snapshots build up (growth speed in the first 48 hours), and common words in top titles. |
