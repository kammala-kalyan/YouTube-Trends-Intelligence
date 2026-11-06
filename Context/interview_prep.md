# India YouTube Trends: interview prep

Everything you need to present and defend the project. Numbers are from the data as of **6 Nov 2026**. The pipeline keeps collecting daily, so **re-check the numbers on the dashboard before each interview** (refresh first).

---

## 1. The 30-second pitch

> Thousands of Indians start a YouTube channel every month and pick a topic on gut feeling. **India YouTube Trends** tells a new creator, before they upload anything, what India is searching for, which topics are growing, where competition from big channels is weak, which format and language work, and where their audience is.
>
> It combines the **YouTube Data API** (trending videos, top videos for 184 keywords, channel stats) with **Google Trends for YouTube Search** (5 years of weekly interest + state breakdown), across **26 topic groups and 10 languages**. A Python pipeline runs **every day on GitHub Actions**, builds a **star schema**, and a **4-page Power BI report** turns it into decisions.

**One line:** "A data-driven way to choose a YouTube niche in India: what people want, what's growing, and where small creators can still win."

---

## 2. Demo walkthrough (about 5 minutes, one creator's journey)

| Page | Question | What to point at | Line to say |
|---|---|---|---|
| **1. Market pulse** | What's happening right now? | Live headline · 5-year search trend · "When does interest peak?" · Rising/Falling fastest · most-viewed video | "Before choosing anything, I check the market: what's rising, what's dying, and when topics peak in the year." |
| **2. Find your niche** ⭐ | Where is demand high and competition weak? | Opportunity map (dark red = Hot) · "Which topics lead within each language?" · Hot niches table | "Top-right is Hot: above-average demand and growing. The table sorts those by how often small channels reach the top results. That's my competition signal." |
| **3. Make it & grow it** | How should I make it, and what does it take to grow? | Shorts vs long-form · video length · title length · small channels' views · channel age · upload pace | "Shorts get about 2.5x the views, long-form gets more engagement. A third of small channels in top results are under a year old, and they post about twice a week." |
| **4. Know your audience** | Who am I making it for, and where? | Pick Language = Telugu → map zooms to Andhra Pradesh and Telangana · Top 10 states · "Which part of India?" | "YouTube doesn't share viewer location, so I use YouTube search popularity by state as the audience signal." |

Demo moments: **hover a keyword** (5-year trend tooltip) · **right-click a state → Drill through → State detail** · pick **Telugu** on page 4 and watch the map zoom.

---

## 3. Talking points (as of 6 Nov 2026, re-check before interviews)

- **Shorts get ~2.5x the median views** of long-form (3.34M vs 1.34M), but **long-form gets more engagement** (1.4% vs 1.1%).
- **Small channels can win:** channels with 10K–100K subscribers get a higher median (2.68M) than 100K–10M channels (1.99M). Under 10K is the hard part (0.96M).
- **A third of small channels in top search results are under 1 year old** (138 of ~430); they post ~8 videos a month.
- **Short titles do better:** under 40 characters → 3.65M median; 80–100 → 1.79M.
- **12 Hot niches** (high demand + growing); most open: **bhajan**, where 72% of top videos come from small channels.
- **Regional search is real but small:** "UPSC Telugu" is searched almost only in Andhra Pradesh and Telangana; "health tips Kannada" almost only in Karnataka.

Say out loud: *these are patterns among popular videos, not proof of cause.*

---

## 4. Technical deep-dives (the "how does it work?" questions)

**1. Making Google Trends comparable: the cricket anchor and the chain.**
Google Trends scores each request 0–100 against the biggest term *in that request*, and allows only 5 terms. So every batch includes **cricket** as a fixed reference, and each keyword is rescaled by `cricket's reference level ÷ cricket's level in this batch`. Small regional keywords rounded to 0 next to cricket, so I **chained references by size**: cricket → **Excel** (~20% of cricket) → **bike review** (~5% of Excel). Each reference is measured one level up, so everything converts back to the cricket scale. Keywords move down a level automatically when they come back as zero. I checked chained values against direct head-to-head comparisons (e.g. "UPSC Telugu" 0.059 chained vs ~0.072 direct, within Google's sampling noise).

**2. Why the references must be national.** My first small reference was "share market Tamil". State results are chained through the reference, so any state where it's ~0 went blank, and "UPSC Telugu" showed up in Puducherry. I switched to "bike review" (searched in 35 of 36 states). *Good story: I found and fixed my own design flaw by checking the output.*

**3. The Mizoram problem (state bias).** I first scored states as "keyword ÷ cricket in that state". The north-east searches far less cricket, so every topic looked oversized there and Mizoram topped everything. Fix: one extra request a day for cricket's own popularity per state, then `popularity = ratio to cricket × cricket's popularity in that state`. I also hide states/UTs under 2 million people, because a handful of searches swings their scores.

**4. Measuring competition without counts.** The YouTube search API caps "total results" at 1,000,000, so I can't count competing videos. Instead I measure **what share of a keyword's top recent videos come from channels under 100K subscribers**. If small channels still reach the top, the niche is open.

**5. Median, not average.** A few viral videos (e.g. one Short at 330M views) dominate totals and averages. The median shows what a typical popular video gets.

**6. Rising / declining.** Rising = more than +15% vs the previous month; Declining = more than −15%. Smaller moves are noise, because Google Trends samples its data. Keywords with too little search (last month under 0.5 on the cricket scale) are "Low volume", so they don't show fake ±100% swings.

**7. Video language detection.** In order: Indian-language audio track → native script in the title → one Indian language named in the title/tags ("Telugu", "Hindi dubbed") → English audio → default language → English letters (weak) → then the **channel's main language** relabels weak cases. This moved 228 videos to the right language (e.g. Punjabi 63 → 116).

**8. One Topic filter for two data sources.** Topics belong to keywords (search data), videos belong to YouTube categories. A **bridge table** (which keyword search found which video), with two-way filtering, lets one Topic filter drive both search trends and video stats.

**9. The pipeline.** GitHub Actions runs daily at 9:00 AM IST: trending chart → topic search (a third of keywords per day, about 6,200 of 10,000 quota units) → channel stats → Google Trends (a seventh of keywords per day, plus new ones) → rebuild the star schema → commit only `data/`. If a source fails, the data that arrived is still saved, **old data is kept**, and the run is marked failed so I get an email. Power BI reads the CSVs straight from the public repo, so anyone who clones it just clicks Refresh.

**10. Data model.** Star schema: facts = video snapshot (video × day), channel snapshot, weekly trends, trends by state, keyword opportunity; dimensions = video, channel, category, keyword, language, state, date; bridge = keyword ↔ video.

---

## 5. Questions interviewers may ask, and honest answers

| Question | Answer |
|---|---|
| "Trending isn't all of YouTube, is it?" | Correct. It's India's most-popular chart. That's why I also pull the top recent videos for 184 keywords, so the analysis isn't only based on trending. |
| "Is the map showing views?" | No, searches. YouTube doesn't share viewer location for public videos (only channel owners see it in YouTube Studio), so search popularity by state is the best public signal. |
| "Google Trends is relative, not real counts." | Yes. I put every batch on one scale with the cricket anchor (and a chain for small keywords), and I only compare relative sizes. |
| "Why are foreign channels included?" | The audience is Indian either way: those videos are on India's trending chart or India's search results. |
| "How do you know your numbers are right?" | I checked chained Trends values against direct comparisons, and spot-checked the top video's views on YouTube and a state on Google Trends. *(Do these spot checks yourself before interviews.)* |
| "Why is video history short?" | The YouTube API only gives current numbers, so history has to be collected daily. The pipeline does that automatically; the search data already has 5 years. |
| "What was the hardest problem?" | Making tiny regional keywords measurable in Google Trends (the reference chain), and then finding that a regional reference broke the state results. |
| "What would you add next?" | How fast videos gain views in their first days (needs a few weeks of daily snapshots), and more regional keywords as the keyword test shows which ones have enough search volume. |
| "Did you use AI tools?" | Answer honestly in your own words: you used an AI coding assistant for implementation, and you defined the problem, made the product decisions (keywords, pages, definitions), and checked the data. The decision log in `four_page_plan.md` shows your decisions. |

---

## 6. Known limits (say them before they're asked)

- The map is **search popularity**, not views.
- States/UTs **under 2 million people are hidden** (noisy scores).
- **8 regional keywords are too small** for Google Trends even with the chain (e.g. "mobile review Gujarati"); they're still used for YouTube video search.
- Video language can't catch every Telugu video with an English title and no language setting.
- Patterns are **correlation, not cause**; video history is short until more daily snapshots build up.

---

## 7. Before each interview (10 minutes)

1. `git pull`, open `Dashboards/India YouTube Trends.pbip`, click **Refresh** (wait for it to finish).
2. Check "Data as of" is recent and all 4 pages render (map on page 4).
3. Re-read section 3 and update any numbers that moved.
4. Have the GitHub repo open (Actions tab shows the daily green runs).
