"""Writes the report pages of Dashboards/India YouTube Trends.pbip (PBIR format).

Run with Power BI Desktop CLOSED:  python build_report.py
It rebuilds every page from scratch, so manual edits made in Power BI to these
pages are overwritten. Make layout changes here, or stop using this script once
you start polishing by hand.

What it does
  1. Small model additions (helper measures, a has_state_data column, filter-proof "Data As Of").
  2. Registers the YouTube Light theme and the icon SVGs as report resources.
  3. Writes the 4 report pages + a State detail drill-through page + a Keyword tooltip page.
"""
import json, re, shutil, uuid
from pathlib import Path

ROOT = Path(__file__).parent / "Dashboards"
REPORT = ROOT / "India YouTube Trends.Report"
DEF = REPORT / "definition"
TABLES = ROOT / "India YouTube Trends.SemanticModel" / "definition" / "tables"
MEASURES_TMDL = TABLES / "_Measures.tmdl"
KEYWORD_TMDL = TABLES / "dim_keyword.tmdl"
THEME_SRC = ROOT / "youtube_light_theme.json"
RES = REPORT / "StaticResources" / "RegisteredResources"

SCHEMA = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition"
VC_SCHEMA = f"{SCHEMA}/visualContainer/2.4.0/schema.json"
PAGE_SCHEMA = f"{SCHEMA}/page/2.1.0/schema.json"

W, H = 1280, 720
M, G = 24, 12                       # page margin, gap between visuals
INK, INK2, INK3, CARD, RED, GREY = "#0f0f0f", "#606060", "#909090", "#f2f2f2", "#ff0033", "#d9d9d9"
RAMP = ["#ffe5ea", "#f9c6c9", "#f2a8a9", "#e98889", "#de686a", "#d2434b", "#c4002b"]

# vertical layout (same on every page)
NAV_Y, NAV_H = 70, 36
SLICER_Y, SLICER_H = 114, 56
KPI_Y, KPI_H = 180, 78
BODY_Y = KPI_Y + KPI_H + G          # 270: first chart row under the KPI row
FOOT_Y = H - 26                     # footnote
BODY_END = FOOT_Y - 6               # charts end here

# ---------------------------------------------------------------- icons (same drawings/colours as the Icon measures)
ICON_COLOURS = dict(red="#e8002d", blue="#2a7ae6", green="#1f9142", violet="#8b5cf6", orange="#c4630b", cyan="#08899b", pink="#d93a87")
ICONS = {
    "videos": ("red", "<rect x='2' y='5' width='20' height='14' rx='3'/><path d='M10 9l5 3-5 3z' fill='{c}'/>"),
    "views": ("blue", "<path d='M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12z'/><circle cx='12' cy='12' r='3'/>"),
    "engagement": ("pink", "<path d='M12 20s-7-4.4-9.2-8.6C1.3 8.5 3 5 6.5 5c2 0 3.5 1.2 5.5 3.2C14 6.2 15.5 5 17.5 5c3.5 0 5.2 3.5 3.7 6.4C19 15.6 12 20 12 20z'/>"),
    "shorts": ("violet", "<rect x='6' y='2' width='12' height='20' rx='3'/><path d='M13 7l-3 5h4l-3 5'/>"),
    "language": ("green", "<circle cx='12' cy='12' r='9'/><path d='M3 12h18'/><path d='M12 3c3 3.5 3 14.5 0 18c-3-3.5-3-14.5 0-18z'/>"),
    "category": ("orange", "<path d='M8 4h8v5a4 4 0 0 1-8 0z'/><path d='M8 6H5a3 3 0 0 0 3 4'/><path d='M16 6h3a3 3 0 0 1-3 4'/><path d='M12 13v4'/><path d='M8 20h8'/><path d='M10 17h4'/>"),
    "channels": ("cyan", "<circle cx='12' cy='8' r='4'/><path d='M4 20c1.5-4 4.5-6 8-6s6.5 2 8 6'/>"),
    "subscribers": ("violet", "<path d='M6 16v-5a6 6 0 0 1 12 0v5l1.5 2h-15z'/><path d='M10 21h4'/>"),
    "trending": ("red", "<path d='M12 3c1 3 5 5.5 5 10a5 5 0 0 1-10 0c0-2.2 1-3.6 2.2-4.6 0 2 1 3.4 2.3 3.4C11.5 9 11 6 12 3z'/>"),
    "rising": ("green", "<path d='M3 17l6-6 4 4 8-8'/><path d='M15 7h6v6'/>"),
    "declining": ("orange", "<path d='M3 7l6 6 4-4 8 8'/><path d='M15 17h6v-6'/>"),
    "interest": ("blue", "<circle cx='11' cy='11' r='7'/><path d='M20 20l-4-4'/>"),
    "state": ("pink", "<path d='M12 21s-7-6.2-7-11a7 7 0 0 1 14 0c0 4.8-7 11-7 11z'/><circle cx='12' cy='10' r='2.5'/>"),
    "opportunity": ("orange", "<path d='M9 18h6'/><path d='M10 21h4'/><path d='M12 3a6 6 0 0 0-3.5 10.9c.6.5 1 1.2 1 2.1h5c0-.9.4-1.6 1-2.1A6 6 0 0 0 12 3z'/>"),
    "growth": ("violet", "<path d='M7 17L17 7'/><path d='M9 7h8v8'/>"),
    "median": ("violet", "<path d='M4 20h16'/><path d='M7 20v-6'/><path d='M12 20V7'/><path d='M17 20v-9'/>"),
    "perday": ("cyan", "<circle cx='12' cy='12' r='9'/><path d='M12 7v5l3 2'/>"),
    "supply": ("violet", "<path d='M12 3l9 5-9 5-9-5z'/><path d='M3 13l9 5 9-5'/>"),
    "gap": ("red", "<circle cx='12' cy='12' r='9'/><circle cx='12' cy='12' r='5'/><circle cx='12' cy='12' r='1' fill='{c}'/>"),
    "smallch": ("green", "<path d='M12 21v-8'/><path d='M12 13c0-4 3-6 7-6 0 4-3 6-7 6z'/><path d='M12 15c0-3-2-5-6-5 0 3 2 5 6 5z'/>"),
    "keywords": ("cyan", "<path d='M3 12V4h8l10 10-8 8z'/><circle cx='7.5' cy='8.5' r='1.5'/>"),
    "calendar": ("blue", "<rect x='3' y='5' width='18' height='16' rx='3'/><path d='M3 10h18'/><path d='M8 3v4'/><path d='M16 3v4'/>"),
}


def icon_svg(key):
    colour = ICON_COLOURS[ICONS[key][0]]
    body = ICONS[key][1].replace("{c}", colour)
    return (f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 40 40'><rect width='40' height='40' rx='12' fill='{colour}' "
            f"fill-opacity='0.13'/><g transform='translate(8 8)' fill='none' stroke='{colour}' stroke-width='2' "
            f"stroke-linecap='round' stroke-linejoin='round'>{body}</g></svg>")


ACCENT_SVG = f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 6 40' preserveAspectRatio='none'><rect width='6' height='40' rx='3' fill='{RED}'/></svg>"

# ---------------------------------------------------------------- model additions
def ramp_switch(r):
    steps = [(0.86, 6), (0.71, 5), (0.57, 4), (0.43, 3), (0.29, 2), (0.14, 1)]
    return "SWITCH(TRUE(), " + ", ".join(f'{r} >= {t}, "{RAMP[i]}"' for t, i in steps) + f', "{RAMP[0]}")'


BAR_RAMP = [(0.999, "#c4002b"), (0.8, "#d2434b"), (0.6, "#de686a"), (0.4, "#e98889"), (0.2, "#f2a8a9")]
BAR_RAMP_MIN = "#f9c6c9"


def hl_measure(name, measure, axes, desc):
    """Bar colour on a light-to-dark red scale: the biggest bar in view is the darkest red."""
    branches = ", ".join(f"ISINSCOPE({a}), MAXX(ALLSELECTED({a}), [{measure}])" for a in axes)
    steps = ", ".join(f'r >= {t}, "{c}"' for t, c in BAR_RAMP)
    expr = (f"VAR v = [{measure}]\n\t\t\tVAR mx = SWITCH(TRUE(), {branches}, v)\n"
            f"\t\t\tVAR r = DIVIDE(v, mx)\n"
            f'\t\t\tRETURN IF(ISBLANK(v), BLANK(), SWITCH(TRUE(), {steps}, "{BAR_RAMP_MIN}"))')
    return name, expr, desc, "Colors"


HELPERS = [
    hl_measure("HL Videos", "Videos Tracked", ["dim_category[category_name]", "dim_language[language_name]", "dim_language[language_label]",
                                               "dim_video[duration_bucket]", "dim_video[publish_hour_ist]", "dim_channel[subscriber_tier]"],
               "Bar colour: red scale, darkest for the largest bar (Videos Tracked)."),
    hl_measure("HL Channels", "Channels", ["dim_channel[channel_origin]"], "Bar colour: red scale, darkest for the largest bar (Channels)."),
    hl_measure("HL Median Views", "Median Views", ["dim_category[category_name]", "dim_video[duration_bucket]", "dim_channel[subscriber_tier]",
                                                   "dim_video[publish_hour_ist]", "dim_video[publish_weekday]", "dim_video[title_length_bucket]",
                                                   "dim_video[tag_count_bucket]", "dim_video[video_format]"],
               "Bar colour: red scale, darkest for the largest bar (Median Views)."),
    hl_measure("HL Engagement", "Engagement Rate", ["dim_category[category_name]", "dim_video[duration_bucket]", "dim_video[video_format]"],"Bar colour: red scale, darkest for the largest bar (Engagement Rate)."),
    hl_measure("HL State Index", "State Index", ["dim_state[state]", "dim_keyword[keyword]", "dim_keyword[topic_group]", "dim_keyword[keyword_language]"],
               "Bar colour: red scale, darkest for the largest bar (State Index)."),
    hl_measure("HL Interest vs Cricket", "Interest vs Cricket", ["dim_state[state]"], "Bar colour: red scale, darkest for the largest bar (Interest vs Cricket)."),
    hl_measure("HL Small Channels", "Small Channels in Top Results", ["dim_channel[channel_age_bucket]", "dim_channel[upload_pace_bucket]"],
               "Bar colour: red scale, darkest for the largest bar (Small Channels in Top Results)."),
    ("Map Color", "VAR v = [State Index]\n\t\t\tVAR r = DIVIDE(v, MAXX(ALLSELECTED(dim_state[state]), [State Index]))\n"
                  f'\t\t\tRETURN IF(ISBLANK(v), "{CARD}", {ramp_switch("r")})',
     "Filled-map colour: 7-step red scale of State Index relative to the top state in view.", "Colors"),
    ("Heat Color State", "VAR v = [State Index]\n\t\t\tVAR r = DIVIDE(v, MAXX(CROSSJOIN(ALLSELECTED(dim_state[state]), ALLSELECTED(dim_keyword[topic_group])), [State Index]))\n"
                         f'\t\t\tRETURN IF(ISBLANK(v), BLANK(), {ramp_switch("r")})', "Heatmap cell colour for State Index (state x topic).", "Colors"),
    ("Heat Font State", "VAR r = DIVIDE([State Index], MAXX(CROSSJOIN(ALLSELECTED(dim_state[state]), ALLSELECTED(dim_keyword[topic_group])), [State Index]))\n"
                        f'\t\t\tRETURN IF(r >= 0.57, "#ffffff", "{INK}")', "Heatmap text colour (white on dark cells).", "Colors"),
    ("Heat Color Demand", "VAR v = [Demand Index]\n\t\t\tVAR r = DIVIDE(v, MAXX(CROSSJOIN(ALLSELECTED(dim_keyword[keyword_language]), ALLSELECTED(dim_keyword[topic_group])), [Demand Index]))\n"
                          f'\t\t\tRETURN IF(ISBLANK(v), BLANK(), {ramp_switch("r")})', "Heatmap cell colour for Demand Index (language x topic).", "Colors"),
    ("Heat Font Demand", "VAR r = DIVIDE([Demand Index], MAXX(CROSSJOIN(ALLSELECTED(dim_keyword[keyword_language]), ALLSELECTED(dim_keyword[topic_group])), [Demand Index]))\n"
                         f'\t\t\tRETURN IF(r >= 0.57, "#ffffff", "{INK}")', "Heatmap text colour (white on dark cells).", "Colors"),
    ("Top Video Title",
     "VAR vid = MAXX(TOPN(1, VALUES(fact_video_snapshot[video_id]), CALCULATE(MAX(fact_video_snapshot[views])), DESC, fact_video_snapshot[video_id], ASC), fact_video_snapshot[video_id])\n"
     "\t\t\tRETURN LOOKUPVALUE(dim_video[title], dim_video[video_id], vid)",
     "Title of the most-viewed video in the current filter.", "Labels"),
    ("Top Video Detail",
     "VAR vid = MAXX(TOPN(1, VALUES(fact_video_snapshot[video_id]), CALCULATE(MAX(fact_video_snapshot[views])), DESC, fact_video_snapshot[video_id], ASC), fact_video_snapshot[video_id])\n"
     "\t\t\tVAR ch = LOOKUPVALUE(dim_channel[channel_name], dim_channel[channel_id], LOOKUPVALUE(dim_video[channel_id], dim_video[video_id], vid))\n"
     "\t\t\tVAR v = CALCULATE(MAX(fact_video_snapshot[views]), fact_video_snapshot[video_id] = vid)\n"
     '\t\t\tRETURN IF(ISBLANK(vid), BLANK(), "by " & ch & "  ·  " & FORMAT(v / 1000000, "#,0.0") & "M views")',
     "Channel and view count of the most-viewed video in the current filter.", "Labels"),
    ("Overview Headline",
     'VAR tp = TOPN(1, FILTER(VALUES(dim_keyword[topic_group]), dim_keyword[topic_group] <> "Anchor" && NOT ISBLANK([Interest MoM %])), [Interest MoM %], DESC)\n'
     "\t\t\tVAR topic = MAXX(tp, dim_keyword[topic_group])\n"
     "\t\t\tVAR mom = MAXX(tp, [Interest MoM %])\n"
     '\t\t\tVAR part1 = IF(ISBLANK(topic), BLANK(), IF(mom > 0, "Fastest-rising topic: ", "Best-performing topic: ") & topic & " (" & FORMAT(mom, "+0%;-0%") & " vs last month)")\n'
     '\t\t\tVAR part2 = IF(ISBLANK([Videos Tracked]), "No videos match these filters yet, try another language or topic", "Shorts are " & FORMAT([Shorts Share], "0%") & " of videos")\n'
     '\t\t\tVAR part3 = IF(ISBLANK([Top Category]), BLANK(), "Most videos are in " & [Top Category])\n'
     "\t\t\tVAR parts = FILTER({(1, part1), (2, part2), (3, part3)}, NOT ISBLANK([Value2]))\n"
     '\t\t\tRETURN CONCATENATEX(parts, [Value2], "  ·  ", [Value1], ASC)',
     "One-line summary for the Overview page: fastest-rising topic, Shorts share and top category.", "Labels"),
    # ---- page 2: niches (quadrants instead of a weighted score, decision Q31)
    ("Keywords Tracked", "CALCULATE(DISTINCTCOUNT(dim_keyword[keyword]), dim_keyword[is_anchor] = FALSE())",
     "Number of keywords tracked in the current filter (excluding the cricket anchor).", "Opportunities"),
    ("Niche Quadrant",
     "VAR d = [Demand Index]\n"
     "\t\t\tVAR g = [Growth 12w %]\n"
     "\t\t\tVAR avgD = CALCULATE(AVERAGEX(VALUES(dim_keyword[keyword]), [Demand Index]), ALLSELECTED(dim_keyword))\n"
     '\t\t\tRETURN IF(ISBLANK(d) || ISBLANK(g), BLANK(), SWITCH(TRUE(), d > avgD && g > 0, "Hot", g > 0, "Emerging", d > avgD, "Big but flat", "Skip"))',
     "Opportunity-map quadrant: Hot = demand above the average of the keywords in view and growing (12 weeks); Emerging = growing; Big but flat = high demand, not growing; Skip = neither.", "Opportunities"),
    ("Quadrant Color",
     'SWITCH([Niche Quadrant], "Hot", "#c4002b", "Emerging", "#f2a8a9", "Big but flat", "#909090", "#d9d9d9")',
     "Opportunity-map point colour by quadrant (Hot = dark red).", "Colors"),
    ("Hot Niche Flag", 'VAR q = [Niche Quadrant]\n\t\t\tRETURN IF(ISBLANK(q), BLANK(), IF(q = "Hot", 1, 0))',
     "1 when the keyword is in the Hot quadrant, else 0. Used to filter the Hot niches table.", "Opportunities"),
    ("Hot Niches", "SUMX(CALCULATETABLE(VALUES(dim_keyword[keyword]), dim_keyword[is_anchor] = FALSE()), [Hot Niche Flag])",
     "Number of keywords in the Hot quadrant (high demand and growing).", "Opportunities"),
    ("Niche Headline",
     "VAR hot = [Hot Niches]\n"
     "\t\t\tVAR best = TOPN(1, FILTER(CALCULATETABLE(VALUES(dim_keyword[keyword]), dim_keyword[is_anchor] = FALSE()), [Hot Niche Flag] = 1 && NOT ISBLANK([Small Channel Share])), [Small Channel Share], DESC, dim_keyword[keyword], ASC)\n"
     "\t\t\tVAR kw = MAXX(best, dim_keyword[keyword])\n"
     "\t\t\tVAR sh = MAXX(best, [Small Channel Share])\n"
     '\t\t\tRETURN IF(ISBLANK(hot) || hot = 0, "No niche is both high-demand and growing in this selection, try another topic or language",\n'
     '\t\t\t    hot & " niches are Hot right now (high demand and growing)" & IF(ISBLANK(kw), "", "  ·  Most open: " & kw & " (" & FORMAT(sh, "0%") & " of top videos are from small channels)"))',
     "One-line summary for the Find your niche page.", "Labels"),
    # ---- page 3: grow it (small channels = under 100K subscribers, in topic search results)
    ("Small Channels in Top Results",
     "CALCULATE([Channels], KEEPFILTERS(dim_channel[subscribers] < 100000), dim_channel[subscribers_hidden] = FALSE(), fact_video_snapshot[in_topic_search] = TRUE())",
     "Channels under 100K subscribers behind videos in the top search results for the tracked keywords.", "Channels"),
    ("Median Uploads per Month (Small)",
     "MEDIANX(CALCULATETABLE(SUMMARIZE(fact_video_snapshot, dim_channel[channel_id], dim_channel[uploads_per_month]), KEEPFILTERS(dim_channel[subscribers] < 100000), dim_channel[subscribers_hidden] = FALSE(), fact_video_snapshot[in_topic_search] = TRUE()), dim_channel[uploads_per_month])",
     "Median uploads per month (lifetime average) of small channels in top search results.", "Channels"),
    ("Grow Headline",
     'VAR ms = CALCULATE([Median Views], dim_video[video_format] = "Shorts")\n'
     '\t\t\tVAR ml = CALCULATE([Median Views], dim_video[video_format] = "Long-form")\n'
     "\t\t\tVAR ratio = DIVIDE(ms, ml)\n"
     '\t\t\tVAR es = CALCULATE([Engagement Rate], dim_video[video_format] = "Shorts")\n'
     '\t\t\tVAR el = CALCULATE([Engagement Rate], dim_video[video_format] = "Long-form")\n'
     '\t\t\tVAR p1 = IF(ISBLANK(ratio), BLANK(), IF(ratio >= 1, "Shorts get " & FORMAT(ratio, "0.0") & "x the views of long-form", "Long-form gets " & FORMAT(DIVIDE(1, ratio), "0.0") & "x the views of Shorts") & IF(el > es, "; long-form gets more engagement", IF(es > el, "; Shorts get more engagement", "")))\n'
     "\t\t\tVAR sc = [Small Channels in Top Results]\n"
     '\t\t\tVAR young = DIVIDE(CALCULATE([Small Channels in Top Results], dim_channel[channel_age_bucket] = "1. Under 1 year"), sc)\n'
     '\t\t\tVAR p2 = IF(ISBLANK(sc), BLANK(), FORMAT(young, "0%") & " of small channels in top results are under a year old")\n'
     "\t\t\tVAR up = [Median Uploads per Month (Small)]\n"
     '\t\t\tVAR p3 = IF(ISBLANK(up), BLANK(), "they post about " & FORMAT(up, "0") & " videos a month")\n'
     "\t\t\tVAR parts = FILTER({(1, p1), (2, p2), (3, p3)}, NOT ISBLANK([Value2]))\n"
     '\t\t\tRETURN CONCATENATEX(parts, [Value2], "  ·  ", [Value1], ASC)',
     "One-line summary for the Make it & grow it page.", "Labels"),
    # ---- page 4: audience
    ("Map Strength", "DIVIDE([State Index], MAXX(ALLSELECTED(dim_state[state_map_name]), [State Index]))",
     "State Index relative to the strongest state in view (0-1). The map hides states below 0.1 so it zooms to where searches come from.", "Regions"),
    ("Audience Headline",
     "VAR t = TOPN(3, FILTER(VALUES(dim_state[state]), NOT ISBLANK([State Index])), [State Index], DESC, dim_state[state], ASC)\n"
     '\t\t\tVAR names = CONCATENATEX(t, dim_state[state], ", ", [State Index], DESC)\n'
     '\t\t\tVAR p1 = IF(names = "", BLANK(), "Searches are strongest in " & names)\n'
     '\t\t\tVAR p2 = IF(ISBLANK([Videos Tracked]), BLANK(), FORMAT([Regional Language Share], "0%") & " of matching videos are in Indian languages")\n'
     "\t\t\tVAR parts = FILTER({(1, p1), (2, p2)}, NOT ISBLANK([Value2]))\n"
     '\t\t\tRETURN CONCATENATEX(parts, [Value2], "  ·  ", [Value1], ASC)',
     "One-line summary for the Know your audience page.", "Labels"),
    ("Trend Label",'SWITCH([Trend Status],"Rising", "▲ Rising", "Declining", "▼ Declining", "Stable", "● Stable", "Low volume", "○ Low volume")',
     "Trend Status with an arrow, for tables. Colour it with [Trend Status Color].", "Trends"),
]

DATA_AS_OF = ('\t/// Header text showing the latest snapshot date (ignores slicers and filters).\n'
              '\tmeasure \'Data As Of\' = "Data as of " & FORMAT(CALCULATE(MAX(fact_video_snapshot[snapshot_date]), REMOVEFILTERS()), "d mmm yyyy")\n')

HAS_STATE_COLUMN = ("\t/// True when Google Trends returned state-level data for this keyword (17 low-volume keywords have none).\n"
                    "\tcolumn has_state_data = CALCULATE(COUNT(fact_trends_region[state_index])) > 0\n"
                    "\t\tdataType: boolean\n\t\tlineageTag: {tag}\n\t\tsummarizeBy: none\n\n")


VIDEO_TMDL = TABLES / "dim_video.tmdl"

# Calculated columns on dim_video for the creator questions (format, upload day, packaging).
# published_at is UTC, so +5.5h gives the India (IST) day.
VIDEO_COLUMNS = [
    ("video_format", 'IF(dim_video[is_short], "Shorts", "Long-form")', "string", None, False,
     "Shorts or Long-form, as a readable label."),
    ("publish_weekday_num", "WEEKDAY(dim_video[published_at] + 5.5 / 24, 2)", "int64", None, True,
     "Upload day number in IST (1 = Monday). Sort column for publish_weekday."),
    ("publish_weekday", 'FORMAT(dim_video[published_at] + 5.5 / 24, "ddd")', "string", "publish_weekday_num", False,
     "Upload day of week in IST (Mon-Sun)."),
    ("title_length_bucket", 'SWITCH(TRUE(), dim_video[title_length] < 40, "1. Under 40", dim_video[title_length] < 60, "2. 40-59", '
                            'dim_video[title_length] < 80, "3. 60-79", "4. 80-100")', "string", None, False,
     "Title length in characters, grouped (YouTube allows up to 100)."),
    ("tag_count_bucket", 'SWITCH(TRUE(), dim_video[tag_count] = 0, "1. No tags", dim_video[tag_count] <= 10, "2. 1-10", '
                         'dim_video[tag_count] <= 20, "3. 11-20", "4. 21+")', "string", None, False,
     "Number of tags on the video, grouped."),
]


# Slicer helpers: only list categories/languages that have videos (17 of 31 YouTube categories have none,
# which made pages go blank), and group rare foreign language codes (ES, PT, ZH...) as "Other languages".
CALC_COLUMNS = {
    "dim_video": VIDEO_COLUMNS,
    "dim_category": [
        ("has_videos", "CALCULATE(COUNTROWS(dim_video)) > 0", "boolean", None, False,
         "True when at least one tracked video is in this category. Used to hide empty categories in slicers."),
    ],
    "dim_language": [
        ("has_videos", "CALCULATE(COUNTROWS(dim_video)) > 0", "boolean", None, False,
         "True when at least one tracked video is in this language. Used to hide empty languages in slicers."),
        ("language_label", 'IF(dim_language[is_indian_regional] || dim_language[language] = "en", dim_language[language_name], "Other languages")',
         "string", None, False, "English and Indian languages by name; everything else grouped as Other languages."),
    ],
    # page 3 "Grow it" row (decisions Q14, Q15)
    "dim_channel": [
        ("channel_age_bucket", 'SWITCH(TRUE(), ISBLANK(dim_channel[channel_age_years]) || dim_channel[channel_age_years] <= 0, BLANK(), '
                               'dim_channel[channel_age_years] < 1, "1. Under 1 year", dim_channel[channel_age_years] < 2, "2. 1-2 years", '
                               'dim_channel[channel_age_years] < 5, "3. 2-5 years", "4. 5+ years")', "string", None, False,
         "Channel age, grouped."),
        ("uploads_per_month", "DIVIDE(dim_channel[video_count], dim_channel[channel_age_years] * 12)", "double", None, False,
         "Average uploads per month over the channel's life (total videos / age in months). Not its current pace."),
        ("upload_pace_bucket", 'VAR u = DIVIDE(dim_channel[video_count], dim_channel[channel_age_years] * 12) '
                               'RETURN SWITCH(TRUE(), ISBLANK(u), BLANK(), u < 4, "1. Under once a week", u < 12, "2. 1-3 a week", '
                               'u < 30, "3. 3-7 a week", "4. Daily or more")', "string", None, False,
         "Average upload pace over the channel's life, grouped."),
    ],
}

# Removed with the Content Gap Score (decision Q31).
REMOVED_MEASURES = ["Content Gap Score", "Keywords Scored", "Icon Gap", "HL Gap"]


def video_column_tmdl(name, expr, dtype, sort_by, hidden, desc):
    lines = [f"\t/// {desc}", f"\tcolumn {name} = {expr}", f"\t\tdataType: {dtype}"]
    if hidden:
        lines.append("\t\tisHidden")
    if dtype == "int64":
        lines.append("\t\tformatString: 0")
    if dtype == "double":
        lines.append("\t\tformatString: 0.0")
    lines += [f"\t\tlineageTag: {uuid.uuid4()}", "\t\tsummarizeBy: none"]
    if sort_by:
        lines.append(f"\t\tsortByColumn: {sort_by}")
    return "\n".join(lines) + "\n\n"


def update_model():
    changes = []
    text = MEASURES_TMDL.read_text(encoding="utf-8")
    # drop removed measures (whole block: description lines + measure + its properties, up to the blank line)
    for name in REMOVED_MEASURES:
        pat = re.compile(rf"(?:\t///[^\n]*\n)*\tmeasure '{re.escape(name)}' =.*?\n\n", re.S)
        text, k = pat.subn("", text)
        if k:
            changes.append(f"{name} (removed)")
    opp_path = TABLES / "fact_keyword_opportunity.tmdl"
    ot = opp_path.read_text(encoding="utf-8")
    if "content_gap_score" in ot:
        ot = re.sub(r"(?:\t///[^\n]*\n)*\tcolumn content_gap_score\n.*?\n\n", "", ot, flags=re.S)
        ot = ot.replace(', {"content_gap_score", type number}', "")
        opp_path.write_text(ot, encoding="utf-8")
        changes.append("fact_keyword_opportunity[content_gap_score] (removed)")
    block = ""
    for name, expr, desc, folder in HELPERS:
        if f"measure '{name}'" in text:
            # keep existing helper measures (description + expression) in sync with the definition here
            pat = re.compile(rf"(?:\t/// [^\n]*\n)?\tmeasure '{re.escape(name)}' =\n\t\t\t(.*?)\n\t\tdisplayFolder:", re.S)
            m = pat.search(text)
            if m and (m.group(1) != expr or f"/// {desc}\n\tmeasure '{name}'" not in text):
                new = f"\t/// {desc}\n\tmeasure '{name}' =\n\t\t\t{expr}\n\t\tdisplayFolder:"
                text = text[:m.start()] + new + text[m.end():]
                changes.append(f"{name} (updated)")
            continue
        block += f"\t/// {desc}\n\tmeasure '{name}' =\n\t\t\t{expr}\n\t\tdisplayFolder: {folder}\n\t\tlineageTag: {uuid.uuid4()}\n\n"
        changes.append(name)
    if block:
        idx = text.index("\tcolumn _")
        text = text[:idx] + block + text[idx:]
    # make "Data As Of" ignore filters (it went blank when a keyword with no videos was selected)
    new_text = re.sub(r"(\t/// [^\n]*\n)?\tmeasure 'Data As Of' = [^\n]*\n", DATA_AS_OF, text, count=1)
    if new_text != text and "REMOVEFILTERS()), \"d mmm yyyy\")" not in text:
        changes.append("Data As Of (ignores filters)")
    MEASURES_TMDL.write_text(new_text, encoding="utf-8")

    kw = KEYWORD_TMDL.read_text(encoding="utf-8")
    if "column has_state_data" not in kw:
        idx = kw.index("\tpartition ")
        kw = kw[:idx] + HAS_STATE_COLUMN.format(tag=uuid.uuid4()) + kw[idx:]
        KEYWORD_TMDL.write_text(kw, encoding="utf-8")
        changes.append("dim_keyword[has_state_data]")

    for table, specs in CALC_COLUMNS.items():
        path = TABLES / f"{table}.tmdl"
        tt = path.read_text(encoding="utf-8")
        add = ""
        for spec in specs:
            if f"\tcolumn {spec[0]} " not in tt:
                add += video_column_tmdl(*spec)
                changes.append(f"{table}[{spec[0]}]")
        if add:
            idx = tt.index("\tpartition ")
            path.write_text(tt[:idx] + add + tt[idx:], encoding="utf-8")
    return changes


# ---------------------------------------------------------------- query / formatting helpers
def L(v):
    return {"expr": {"Literal": {"Value": v}}}


def s(text):
    return L("'" + text.replace("'", "''") + "'")


def n(x):
    return L(f"{x}D")


def b(x):
    return L("true" if x else "false")


def solid(hexc):
    return {"solid": {"color": s(hexc)}}


def col(table, column):
    return {"Column": {"Expression": {"SourceRef": {"Entity": table}}, "Property": column}}


def mea(name, table="_Measures"):
    return {"Measure": {"Expression": {"SourceRef": {"Entity": table}}, "Property": name}}


def ref(field):
    k = "Column" if "Column" in field else "Measure"
    return f'{field[k]["Expression"]["SourceRef"]["Entity"]}.{field[k]["Property"]}'


def proj(field, display=None, fmt=None):
    p = {"field": field, "queryRef": ref(field), "nativeQueryRef": list(field.values())[0]["Property"]}
    if display:
        p["displayName"] = display
    if fmt:
        p["format"] = fmt
    return p


def measure_colour(name):
    return {"solid": {"color": {"expr": mea(name)}}}


def pad(top=0, right=0, bottom=0, left=0):
    return [{"properties": {"top": n(top), "right": n(right), "bottom": n(bottom), "left": n(left)}}]


ALL_POINTS = {"data": [{"dataViewWildcard": {"matchingOption": 1}}]}
MILLIONS = '#,0.0,,"M"'
_names = set()


def uid(prefix):
    base = re.sub(r"[^a-z0-9]", "", prefix.lower())[:24] or "v"
    i, name = 1, base
    while name in _names:
        i += 1
        name = f"{base}{i}"
    _names.add(name)
    return name


class Page:
    def __init__(self, key, display, width=W, height=H, ptype=None, hidden=False):
        self.key, self.display, self.width, self.height = key, display, width, height
        self.ptype, self.hidden = ptype, hidden
        self.visuals, self.interactions, self.filters, self.binding = [], [], [], None
        self.z = 0

    def add(self, visual_type, x, y, w, h, query=None, objects=None, vco=None, filters=None, sort=None, name=None, tooltip_page=None):
        self.z += 1
        name = uid(name or f"{self.key}_{visual_type}")
        visual = {"visualType": visual_type, "drillFilterOtherVisuals": True}
        if query:
            q = {"queryState": query}
            if sort:
                q["sortDefinition"] = {"sort": [{"field": sort[0], "direction": sort[1]}], "isDefaultSort": False}
            visual["query"] = q
        if objects:
            visual["objects"] = objects
        vco = dict(vco or {})
        if tooltip_page:
            vco["visualTooltip"] = [{"properties": {"type": s("Canvas"), "section": s(tooltip_page)}}]
        if vco:
            visual["visualContainerObjects"] = vco
        container = {"$schema": VC_SCHEMA, "name": name,
                     "position": {"x": round(x, 2), "y": round(y, 2), "z": self.z * 1000, "height": round(h, 2), "width": round(w, 2), "tabOrder": self.z * 1000},
                     "visual": visual}
        if filters:
            container["filterConfig"] = {"filters": filters}
        self.visuals.append(container)
        return name


# ---------------------------------------------------------------- filters
def f_bool(table, column, value):
    return {"name": uid(f"f{column}"), "field": col(table, column), "type": "Categorical",
            "filter": {"Version": 2, "From": [{"Name": "t", "Entity": table, "Type": 0}],
                       "Where": [{"Condition": {"In": {"Expressions": [{"Column": {"Expression": {"SourceRef": {"Source": "t"}}, "Property": column}}],
                                                       "Values": [[{"Literal": {"Value": "true" if value else "false"}}]]}}}]},
            "howCreated": "User"}


def f_exclude_anchor():
    return f_bool("dim_keyword", "is_anchor", False)


def f_has_state():
    return f_bool("dim_keyword", "has_state_data", True)


def f_not_blank(table, column):
    return {"name": uid(f"fnb{column}"), "field": col(table, column), "type": "Categorical",
            "filter": {"Version": 2, "From": [{"Name": "t", "Entity": table, "Type": 0}],
                       "Where": [{"Condition": {"Not": {"Expression": {"In": {
                           "Expressions": [{"Column": {"Expression": {"SourceRef": {"Source": "t"}}, "Property": column}}],
                           "Values": [[{"Literal": {"Value": "null"}}], [{"Literal": {"Value": "''"}}]]}}}}}]},
            "howCreated": "User"}


COMPARE = {"eq": 0, "gt": 1, "ge": 2, "le": 3, "lt": 4}


def f_measure(measure, op, value):
    """Visual-level filter on a measure, e.g. f_measure("Map Strength", "ge", 0.1)."""
    lit = f"{value}L" if isinstance(value, int) else f"{value}D"
    return {"name": uid("fm"), "field": mea(measure), "type": "Advanced",
            "filter": {"Version": 2, "From": [{"Name": "m", "Entity": "_Measures", "Type": 0}],
                       "Where": [{"Condition": {"Comparison": {"ComparisonKind": COMPARE[op],
                                                               "Left": {"Measure": {"Expression": {"SourceRef": {"Source": "m"}}, "Property": measure}},
                                                               "Right": {"Literal": {"Value": lit}}}}}]},
            "howCreated": "User"}


def f_topn(table, column, measure, top, bottom=False):
    return {"name": uid("ftop"), "field": col(table, column), "type": "TopN",
            "filter": {"Version": 2,
                       "From": [{"Name": "subquery", "Expression": {"Subquery": {"Query": {
                           "Version": 2,
                           "From": [{"Name": "d", "Entity": table, "Type": 0}, {"Name": "m", "Entity": "_Measures", "Type": 0}],
                           "Select": [{"Column": {"Expression": {"SourceRef": {"Source": "d"}}, "Property": column}, "Name": "field"}],
                           "OrderBy": [{"Direction": 1 if bottom else 2, "Expression": {"Measure": {"Expression": {"SourceRef": {"Source": "m"}}, "Property": measure}}}],
                           "Top": top}}}, "Type": 2},
                                {"Name": "d", "Entity": table, "Type": 0}],
                       "Where": [{"Condition": {"In": {"Expressions": [{"Column": {"Expression": {"SourceRef": {"Source": "d"}}, "Property": column}}],
                                                       "Table": {"SourceRef": {"Source": "subquery"}}}}}]},
            "howCreated": "User"}


# ---------------------------------------------------------------- building blocks
def title_vco(title, subtitle=None):
    v = {"title": [{"properties": {"show": b(True), "text": s(title), "fontSize": n(12), "bold": b(True), "fontColor": solid(INK)}}],
         "subTitle": [{"properties": {"show": b(bool(subtitle)), **({"text": s(subtitle)} if subtitle else {}), "fontSize": n(9), "fontColor": solid(INK2)}}],
         "padding": pad(8, 12, 8, 12)}
    return v


def bare(background=False):
    """No title, no padding (for icons, text, shapes, buttons)."""
    v = {"title": [{"properties": {"show": b(False)}}], "padding": pad()}
    if not background:
        v["background"] = [{"properties": {"show": b(False)}}]
    return v


def textbox(page, x, y, w, h, runs, name=None):
    """runs: list of paragraphs, each a list of (text, size_pt, colour, bold)."""
    paragraphs = [{"textRuns": [{"value": t, "textStyle": {"fontSize": f"{sz}pt", "color": c, **({"fontWeight": "bold"} if bold else {})}} for t, sz, c, bold in para]}
                  for para in runs]
    return page.add("textbox", x, y, w, h, objects={"general": [{"properties": {"paragraphs": paragraphs}}]}, vco=bare(), name=name or "text")


def image(page, x, y, w, h, item, name=None):
    return page.add("image", x, y, w, h,
                    objects={"general": [{"properties": {"imageUrl": {"expr": {"ResourcePackageItem": {"PackageName": "RegisteredResources", "PackageType": 1, "ItemName": item}}}}}],
                             "imageScaling": [{"properties": {"imageScalingType": s("Fit")}}]},
                    vco=bare(), name=name or "image")


def card(page, x, y, w, h, field, label, size=20, pad_left=8, background=True, label_show=True, colour_measure=None, units=None, precision=None, name=None):
    labels = {"fontSize": n(size), "color": solid(INK), "bold": b(True)}
    if colour_measure:
        labels["color"] = measure_colour(colour_measure)
    if units is not None:
        labels["labelDisplayUnits"] = n(units)
    if precision is not None:
        labels["labelPrecision"] = L(f"{precision}L")
    vco = {"title": [{"properties": {"show": b(False)}}], "padding": pad(4, 8, 4, pad_left)}
    if not background:
        vco["background"] = [{"properties": {"show": b(False)}}]
    return page.add("card", x, y, w, h, query={"Values": {"projections": [proj(field, label)]}},
                    objects={"labels": [{"properties": labels}],
                             "categoryLabels": [{"properties": {"show": b(label_show), "fontSize": n(9), "color": solid(INK2)}}]},
                    vco=vco, name=name or "card")


def text_card(page, x, y, w, h, measure, label, size=12, label_show=True, background=True, pad_left=12, name="textcard"):
    """Left-aligned, wrapping text from a measure (multi-row card without the bar)."""
    vco = {"title": [{"properties": {"show": b(False)}}], "padding": pad(6, 10, 6, pad_left)}
    if not background:
        vco["background"] = [{"properties": {"show": b(False)}}]
    return page.add("multiRowCard", x, y, w, h, query={"Values": {"projections": [proj(mea(measure), label)]}},
                    objects={"dataLabels": [{"properties": {"fontSize": n(size), "color": solid(INK)}}],
                             "categoryLabels": [{"properties": {"show": b(label_show), "fontSize": n(9), "color": solid(INK2)}}],
                             "card": [{"properties": {"barShow": b(False), "outline": s("None")}}]},
                    vco=vco, name=name)


def kpi(page, x, y, w, h, measure, label, icon, size=20, units=None, precision=None):
    name = card(page, x, y, w, h, mea(measure), label, size=size, pad_left=60, units=units, precision=precision, name=f"kpi_{measure}")
    image(page, x + 14, y + (h - 40) / 2, 40, 40, f"icon_{icon}.svg", name=f"icon_{icon}")
    return name


def kpi_row(page, y, items, h=KPI_H, x0=M, total=W - 2 * M):
    w = (total - G * (len(items) - 1)) / len(items)
    names = []
    for i, it in enumerate(items):
        measure, label, icon, *opts = it
        opts = opts[0] if opts else {}
        names.append(kpi(page, x0 + i * (w + G), y, w, h, measure, label, icon, **opts))
    return names


def slicer(page, x, y, w, field, label, mode="Dropdown", filters=None, h=SLICER_H):
    tiles = mode == "Tile"            # buttons side by side (list slicer, horizontal)
    objects = {"data": [{"properties": {"mode": s("Basic" if tiles else mode)}}],
               "header": [{"properties": {"show": b(True), "fontColor": solid(INK2), "textSize": n(9)}}],
               "items": [{"properties": {"fontColor": solid(INK), "textSize": n(10)}}]}
    if tiles:
        objects["general"] = [{"properties": {"orientation": L("1D")}}]
    vco = {"title": [{"properties": {"show": b(False)}}], "padding": pad(4, 10, 4, 10)}
    return page.add("slicer", x, y, w, h, query={"Values": {"projections": [proj(field, label)]}},
                    objects=objects, vco=vco, filters=filters, name="slicer")


def bar(page, x, y, w, h, cat, measure, title, subtitle=None, colour_measure=None, top=None, tooltips=(), horizontal=True,
        filters=None, label=None, sort_desc=True, tooltip_page=None, units=1, precision=None):
    vt = "clusteredBarChart" if horizontal else "clusteredColumnChart"
    q = {"Category": {"projections": [proj(col(*cat))]}, "Y": {"projections": [proj(mea(measure), label)]}}
    if tooltips:
        q["Tooltips"] = {"projections": [proj(mea(t)) for t in tooltips]}
    labels = {"show": b(True), "fontSize": n(9), "color": solid(INK), "labelDisplayUnits": n(units)}
    if precision is not None:
        labels["labelPrecision"] = L(f"{precision}L")
    objects = {"labels": [{"properties": labels}],
               "valueAxis": [{"properties": {"show": b(False), "gridlineShow": b(False)}}],
               "categoryAxis": [{"properties": {"show": b(True), "fontSize": n(9), "labelColor": solid(INK2), "showAxisTitle": b(False)}}],
               "legend": [{"properties": {"show": b(False)}}]}
    if colour_measure:
        objects["dataPoint"] = [{"properties": {"fill": measure_colour(colour_measure)}, "selector": ALL_POINTS}]
    else:
        objects["dataPoint"] = [{"properties": {"defaultColor": solid(RED)}}]
    fl = list(filters or [])
    if top:
        fl.append(f_topn(cat[0], cat[1], measure, top))
    sort = (mea(measure), "Descending") if sort_desc else (col(*cat), "Ascending")
    return page.add(vt, x, y, w, h, query=q, objects=objects, vco=title_vco(title, subtitle), filters=fl or None, sort=sort, name="bar", tooltip_page=tooltip_page)


def line(page, x, y, w, h, title, subtitle, series=None, filters=None, name="line", axis=("dim_date", "year_month")):
    q = {"Category": {"projections": [proj(col(*axis), "Month")]}, "Y": {"projections": [proj(mea("Interest"), "Search interest")]}}
    if series:
        q["Series"] = {"projections": [proj(col(*series))]}
    objects = {"lineStyles": [{"properties": {"strokeWidth": n(2), "showMarker": b(False)}}],
               "legend": [{"properties": {"show": b(bool(series)), "position": s("Top"), "fontSize": n(9), "showTitle": b(False)}}],
               "categoryAxis": [{"properties": {"showAxisTitle": b(False), "labelColor": solid(INK3), "fontSize": n(8)}}],
               "valueAxis": [{"properties": {"showAxisTitle": b(False), "labelColor": solid(INK3), "fontSize": n(8)}}]}
    if not series:
        objects["dataPoint"] = [{"properties": {"defaultColor": solid(RED)}}]
    return page.add("lineChart", x, y, w, h, query=q, objects=objects, vco=title_vco(title, subtitle), filters=filters,
                    sort=(col(*axis), "Ascending"), name=name)


def table(page, x, y, w, h, columns, title, subtitle, filters=None, sort=None, widths=None, status_colour=False, tooltip_page=None, name="table"):
    objects = {"total": [{"properties": {"totals": b(False)}}],
               "values": [{"properties": {"fontSize": n(10)}}],
               "columnHeaders": [{"properties": {"fontSize": n(9), "fontColor": solid(INK2)}}],
               "grid": [{"properties": {"rowPadding": n(4)}}]}
    if status_colour:
        objects["values"].append({"properties": {"fontColor": measure_colour("Trend Status Color")},
                                  "selector": {**ALL_POINTS, "metadata": "_Measures.Trend Label"}})
    if widths:
        objects["columnWidth"] = [{"properties": {"value": n(px)}, "selector": {"metadata": qref}} for qref, px in widths.items()]
    return page.add("tableEx", x, y, w, h, query={"Values": {"projections": columns}}, objects=objects,
                    vco=title_vco(title, subtitle), filters=filters, sort=sort, name=name, tooltip_page=tooltip_page)


def matrix(page, x, y, w, h, rows, cols_, value, back, font, title, subtitle, filters=None, font_size=9, name="matrix"):
    return page.add("pivotTable", x, y, w, h,
                    query={"Rows": {"projections": [proj(col(*rows[:2]), rows[2])]}, "Columns": {"projections": [proj(col(*cols_[:2]), cols_[2])]},
                           "Values": {"projections": [proj(mea(value))]}},
                    objects={"values": [{"properties": {"fontSize": n(font_size)}},
                                        {"properties": {"backColor": measure_colour(back), "fontColor": measure_colour(font)},
                                         "selector": {**ALL_POINTS, "metadata": f"_Measures.{value}"}}],
                             "subTotals": [{"properties": {"rowSubtotals": b(False), "columnSubtotals": b(False)}}],
                             "columnHeaders": [{"properties": {"fontSize": n(font_size), "fontColor": solid(INK2), "wordWrap": b(True)}}],
                             "rowHeaders": [{"properties": {"fontSize": n(font_size)}}],
                             "grid": [{"properties": {"rowPadding": n(3)}}]},
                    vco=title_vco(title, subtitle), filters=filters, name=name)


def scatter(page, x, y, w, h, cat, xm, ym, size, title, subtitle, filters=None, tooltip_page=None, name="scatter",
            colour_measure=None, labels=True):
    point = ({"properties": {"fill": measure_colour(colour_measure)}, "selector": ALL_POINTS} if colour_measure
             else {"properties": {"defaultColor": solid(RED)}})
    return page.add("scatterChart", x, y, w, h,
                    query={"Category": {"projections": [proj(col(*cat[:2]), cat[2])]}, "X": {"projections": [proj(mea(xm))]},
                           "Y": {"projections": [proj(mea(ym))]}, "Size": {"projections": [proj(mea(size))]}},
                    objects={"categoryLabels": [{"properties": {"show": b(labels), "fontSize": n(8), "color": solid(INK2)}}],
                             "dataPoint": [point], "legend": [{"properties": {"show": b(False)}}],
                             "categoryAxis": [{"properties": {"showAxisTitle": b(True), "labelColor": solid(INK3), "fontSize": n(8)}}],
                             "valueAxis": [{"properties": {"showAxisTitle": b(True), "labelColor": solid(INK3), "fontSize": n(8)}}]},
                    vco=title_vco(title, subtitle), filters=filters, name=name, tooltip_page=tooltip_page)


def footnote(page, text):
    textbox(page, M, FOOT_Y, W - 2 * M, 22, [[(text, 8, INK3, False)]], name="footnote")


def header(page, title, subtitle, navigator=True, headline=None):
    """headline: optional measure shown as a live one-line summary instead of the static subtitle."""
    image(page, M, 16, 6, 40, "accent_bar.svg", name="accent")
    if headline:
        textbox(page, M + 16, 8, 820, 32, [[(title, 18, INK, True)]], name="pagetitle")
        text_card(page, M + 12, 38, 900, 28, headline, "Headline", size=10, label_show=False, background=False, pad_left=4, name="pagetitle_headline")
    else:
        textbox(page, M + 16, 10, 820, 56, [[(title, 18, INK, True)], [(subtitle, 9.5, INK2, False)]], name="pagetitle")
    card(page, W - M - 230, 16, 230, 40, mea("Data As Of"), "Data as of", size=10, pad_left=44, label_show=False, name="asof")
    image(page, W - M - 222, 24, 24, 24, "icon_calendar.svg", name="asof_icon")
    if navigator:
        page.add("pageNavigator", M, NAV_Y, W - 2 * M, NAV_H,
                 objects={"pages": [{"properties": {"showHiddenPages": b(False), "showTooltipPages": b(False)}}],
                          "shape": [{"properties": {"tileShape": s("rectangleRounded")}}],
                          "fill": [{"properties": {"fillColor": solid(CARD), "transparency": n(0)}, "selector": {"id": "default"}},
                                   {"properties": {"fillColor": solid("#e5e5e5"), "transparency": n(0)}, "selector": {"id": "hover"}},
                                   {"properties": {"fillColor": solid("#d9d9d9"), "transparency": n(0)}, "selector": {"id": "press"}},
                                   {"properties": {"fillColor": solid(INK), "transparency": n(0)}, "selector": {"id": "selected"}}],
                          "text": [{"properties": {"fontColor": solid(INK), "fontSize": n(10), "bold": b(True)}, "selector": {"id": "default"}},
                                   {"properties": {"fontColor": solid("#ffffff"), "fontSize": n(10), "bold": b(True)}, "selector": {"id": "selected"}}],
                          "outline": [{"properties": {"show": b(False)}}]},
                 vco=bare(), name="nav")


def sl_content(w=200):
    return (w, col("dim_video", "video_format"), "Content", {"mode": "Tile"})


def f_has_videos():
    """Slicer filter: only list items that have videos under the other filters (avoids picking empty combinations)."""
    return {"name": uid("fhasvid"), "field": mea("Videos Tracked"), "type": "Advanced",
            "filter": {"Version": 2, "From": [{"Name": "m", "Entity": "_Measures", "Type": 0}],
                       "Where": [{"Condition": {"Comparison": {"ComparisonKind": 1,
                                                               "Left": {"Measure": {"Expression": {"SourceRef": {"Source": "m"}}, "Property": "Videos Tracked"}},
                                                               "Right": {"Literal": {"Value": "0L"}}}}}]},
            "howCreated": "User"}


def sl_language(w=200):
    return (w, col("dim_language", "language_label"), "Video language", {"filters": [f_bool("dim_language", "has_videos", True), f_has_videos()]})


def sl_category(w=220):
    return (w, col("dim_category", "category_name"), "YouTube category", {"filters": [f_bool("dim_category", "has_videos", True), f_has_videos()]})


def slicer_row(page, specs):
    """specs: list of (width, field, label, extra_kwargs)."""
    x, names = M, []
    for w, field, label, *kw in specs:
        names.append(slicer(page, x, SLICER_Y, w, field, label, **(kw[0] if kw else {})))
        x += w + G
    return names


# ---------------------------------------------------------------- pages
def sl_topic(w=240, has_videos=True):
    filters = [f_exclude_anchor()] + ([f_has_videos()] if has_videos else [])
    return (w, col("dim_keyword", "topic_group"), "Topic", {"filters": filters})


def sl_search_language(w=180):
    """Language of the search term (pages 2 and 4, decision Q39a): e.g. 'UPSC Telugu' counts as Telugu."""
    return (w, col("dim_keyword", "keyword_language"), "Language")


def note(page, x, text, w=420):
    """Small grey explanation placed in the filter row, right of the slicers."""
    textbox(page, x, SLICER_Y + 8, w, SLICER_H - 12, [[(text, 8.5, INK2, False)]], name="filternote")


def build_pages():
    """The 4-page creator journey (Context/four_page_plan.md) + hidden State detail and Keyword tooltip pages."""
    pages = []
    tip = Page("keywordtooltip", "Keyword tooltip", width=320, height=240, ptype="Tooltip", hidden=True)
    TIP = tip.key
    full = W - 2 * M
    half = (full - G) / 2
    third = (full - 2 * G) / 3

    # 1. Market pulse ------------------------------------------------------
    p = Page("pulse", "Market pulse")
    header(p, "What's happening on YouTube India right now?", None, headline="Overview Headline")
    s_topic, s_lang, s_fmt = slicer_row(p, [sl_topic(), sl_language(220), sl_content(240)])
    kpis = kpi_row(p, KPI_Y, [("Videos Tracked", "Videos tracked", "videos"),
                              ("Median Views", "Median views per video", "views", {"units": 1000000, "precision": 2}),
                              ("Shorts Share", "Shorts share", "shorts"),
                              ("Regional Language Share", "Indian-language videos", "language"),
                              ("Rising Keywords", "Keywords rising vs last month", "rising")])
    r1 = 200
    lw = 780
    v_line = line(p, M, BODY_Y, lw, r1, "How much India searches on YouTube",
                  "Google Trends score per month over 5 years, higher = more searches", name="pulseline")
    v_season = line(p, M + lw + G, BODY_Y, full - lw - G, r1, "When does interest peak?",
                    "Average score by calendar month, across 5 years", name="season", axis=("dim_date", "month_name"),
                    filters=[f_exclude_anchor()])
    y2 = BODY_Y + r1 + G
    h2 = BODY_END - y2
    qw = (full - 3 * G) / 4
    kw_cols = [proj(col("dim_keyword", "keyword"), "Keyword"), proj(mea("Trend Label"), "Trend"), proj(mea("Interest MoM %"), "vs last month")]
    kw_widths = {"dim_keyword.keyword": 130, "_Measures.Trend Label": 85, "_Measures.Interest MoM %": 70}
    v_up = table(p, M, y2, qw, h2, kw_cols, "Rising fastest", "Biggest increase in searches vs last month",
                 filters=[f_exclude_anchor(), f_measure("Interest MoM %", "gt", 0.0), f_topn("dim_keyword", "keyword", "Interest MoM %", 5)],
                 sort=(mea("Interest MoM %"), "Descending"), status_colour=True, tooltip_page=TIP, widths=kw_widths, name="risingfast")
    v_down = table(p, M + qw + G, y2, qw, h2, kw_cols, "Falling fastest", "Biggest drop in searches vs last month",
                   filters=[f_exclude_anchor(), f_measure("Interest MoM %", "lt", 0.0), f_topn("dim_keyword", "keyword", "Interest MoM %", 5, bottom=True)],
                   sort=(mea("Interest MoM %"), "Ascending"), status_colour=True, tooltip_page=TIP, widths=kw_widths, name="fallingfast")
    bar(p, M + 2 * (qw + G), y2, qw, h2, ("dim_category", "category_name"), "Videos Tracked", "Number of videos by YouTube category",
        "Top 6 categories", colour_measure="HL Videos", top=6, tooltips=("Median Views", "Engagement Rate"), label="Videos")
    tvx = M + 3 * (qw + G)
    hh, dh = 46, 40
    textbox(p, tvx + 12, y2 + 8, qw - 24, hh - 8,
            [[("Most-viewed video right now", 12, INK, True)], [("Top video in the current filter, by views", 9, INK2, False)]], name="topvideo_heading")
    text_card(p, tvx, y2 + hh, qw, h2 - hh - dh, "Top Video Title", "Video", size=12, label_show=False, background=False, name="topvideo")
    text_card(p, tvx, y2 + h2 - dh, qw, dh, "Top Video Detail", "Channel and views", size=9, label_show=False, background=False, name="topvideodetail")
    footnote(p, "Videos = YouTube India trending chart + top recent videos for each tracked keyword; picking a topic shows the videos found for it. "
                "Search score = Google Trends (YouTube Search, India), scaled against 'cricket' so all keywords compare fairly.")
    # video language and content describe videos, not searches: they don't filter the search visuals
    search_visuals = (v_line, v_season, v_up, v_down, kpis[4])
    p.interactions += [{"source": sl, "target": t, "type": "NoFilter"} for sl in (s_lang, s_fmt) for t in search_visuals]
    pages.append(p)

    # 2. Find your niche ---------------------------------------------------
    p = Page("niche", "Find your niche")
    header(p, "Where is demand high and competition weak?", None, headline="Niche Headline")
    slicer_row(p, [sl_topic(has_videos=False), sl_search_language()])
    note(p, M + 240 + 180 + 2 * G, "Language = searches for content in that language, for example 'UPSC Telugu'.")
    kpi_row(p, KPI_Y, [("Keywords Tracked", "Keywords tracked", "keywords"), ("Hot Niches", "Hot niches (high demand, growing)", "opportunity"),
                       ("Demand Index", "Demand (search score, 12 weeks)", "interest"), ("Growth 12w %", "Growth (12 weeks)", "growth"),
                       ("Small Channel Share", "Top videos from small channels", "smallch")])
    rh = 250
    scatter(p, M, BODY_Y, half, rh, ("dim_keyword", "keyword", "Keyword"), "Demand Index", "Growth 12w %", "Small Channel Share",
            "Opportunity map", "Right = more demand than average · up = growing · dark red = Hot · bubble = small-channel share",
            filters=[f_exclude_anchor()], tooltip_page=TIP, name="oppscatter", colour_measure="Quadrant Color", labels=False)
    table(p, M + half + G, BODY_Y, half, rh,
          [proj(col("dim_keyword", "keyword"), "Keyword"), proj(col("dim_keyword", "topic_group"), "Topic"),
           proj(mea("Demand Index"), "Demand"), proj(mea("Growth 12w %"), "Growth"), proj(mea("Small Channel Share"), "Small channels"),
           proj(mea("Trend Label"), "Trend")],
          "Hot niches, most open first", "High demand and growing; sorted by share of top videos from small channels",
          filters=[f_exclude_anchor(), f_measure("Hot Niche Flag", "eq", 1)], sort=(mea("Small Channel Share"), "Descending"),
          status_colour=True, tooltip_page=TIP,
          widths={"dim_keyword.keyword": 150, "dim_keyword.topic_group": 130, "_Measures.Demand Index": 60, "_Measures.Growth 12w %": 60,
                  "_Measures.Small Channel Share": 90, "_Measures.Trend Label": 85}, name="hotniches")
    my = BODY_Y + rh + G
    matrix(p, M, my, full, BODY_END - my, ("dim_keyword", "topic_group", "Topic"), ("dim_keyword", "keyword_language", "Language"), "Demand Index",
           "Heat Color Demand", "Heat Font Demand", "Demand by topic and language", "Darker = more search demand. Empty = no keyword tracked for that pair.",
           filters=[f_exclude_anchor()], font_size=8, name="langmatrix")
    footnote(p, "Hot = demand above the average of the keywords in view, and growing over the last 12 weeks. Small channels = under 100K subscribers: "
                "the API can't count competitors, so this measures whether small channels still reach the top results.")
    pages.append(p)

    # 3. Make it & grow it -------------------------------------------------
    p = Page("grow", "Make it & grow it")
    header(p, "How should I make it, and what does it take to grow?", None, headline="Grow Headline")
    _, _, s_fmt = slicer_row(p, [sl_topic(), sl_language(220), sl_content(240)])
    kpi_row(p, KPI_Y, [("Median Views", "Median views per video", "views", {"units": 1000000, "precision": 2}),
                       ("Engagement Rate", "Engagement rate", "engagement"), ("Shorts Share", "Shorts share", "shorts"),
                       ("Median Uploads per Month (Small)", "Uploads a month (small channels)", "perday", {"precision": 1})])
    rh = (BODY_END - BODY_Y - G) / 2
    y2 = BODY_Y + rh + G
    sw = (third - G) / 2
    v_f1 = bar(p, M, BODY_Y, sw, rh, ("dim_video", "video_format"), "Median Views", "Shorts vs long-form",
               "Median views", colour_measure="HL Median Views", horizontal=False, units=1000000, precision=2, tooltips=("Videos Tracked",))
    v_f2 = bar(p, M + sw + G, BODY_Y, sw, rh, ("dim_video", "video_format"), "Engagement Rate", "Shorts vs long-form",
               "Engagement rate", colour_measure="HL Engagement", horizontal=False, units=0, tooltips=("Videos Tracked",))
    bar(p, M + third + G, BODY_Y, third, rh, ("dim_video", "duration_bucket"), "Median Views", "Median views by video length", "Typical views for each length",
        colour_measure="HL Median Views", horizontal=False, sort_desc=False, units=1000000, precision=1, tooltips=("Videos Tracked",))
    bar(p, M + 2 * (third + G), BODY_Y, third, rh, ("dim_video", "title_length_bucket"), "Median Views", "Title length",
        "Median views by title length in characters (YouTube max 100)", colour_measure="HL Median Views",
        horizontal=False, sort_desc=False, units=1000000, precision=2, tooltips=("Videos Tracked",))
    bar(p, M, y2, third, rh, ("dim_channel", "subscriber_tier"), "Median Views", "Can small channels get views?",
        "Median views per video by channel size (subscribers)", colour_measure="HL Median Views",
        horizontal=False, sort_desc=False, units=1000000, precision=2, tooltips=("Videos Tracked",), filters=[f_not_blank("dim_channel", "subscriber_tier")])
    bar(p, M + third + G, y2, third, rh, ("dim_channel", "channel_age_bucket"), "Small Channels in Top Results", "How new are the small channels in top results?",
        "Channels under 100K subscribers, by channel age", colour_measure="HL Small Channels", horizontal=False, sort_desc=False, label="Channels",
        filters=[f_not_blank("dim_channel", "channel_age_bucket")])
    bar(p, M + 2 * (third + G), y2, third, rh, ("dim_channel", "upload_pace_bucket"), "Small Channels in Top Results", "How often do they upload?",
        "Channels under 100K subscribers, by average uploads", colour_measure="HL Small Channels", horizontal=False, sort_desc=False, label="Channels",
        filters=[f_not_blank("dim_channel", "upload_pace_bucket")])
    p.interactions += [{"source": s_fmt, "target": t, "type": "NoFilter"} for t in (v_f1, v_f2)]
    footnote(p, "Patterns among popular videos, not proof of cause. Median used because a few viral videos skew averages. Upload pace = a channel's "
                "total videos / its age (lifetime average). Small channels = under 100K subscribers, in top search results.")
    pages.append(p)

    # 4. Know your audience ------------------------------------------------
    p = Page("audience", "Know your audience")
    header(p, "Who am I making it for, and where are they?", None, headline="Audience Headline")
    slicer_row(p, [sl_topic(200, has_videos=False), sl_search_language(170),
                   (260, col("dim_keyword", "keyword"), "Keyword", {"filters": [f_exclude_anchor(), f_has_state()]}),
                   (160, col("dim_state", "zone"), "Zone")])
    note(p, M + 200 + 170 + 260 + 160 + 4 * G, "Language = searches for content in that language, for example 'UPSC Telugu'. Picking one zooms the map.", w=390)
    map_w = 640
    p.add("filledMap", M, KPI_Y, map_w, BODY_END - KPI_Y,
          query={"Category": {"projections": [proj(col("dim_state", "state_map_name"), "State")]},
                 "Tooltips": {"projections": [proj(mea("State Index")), proj(mea("Interest vs Cricket")), proj(mea("Top Keyword in State"))]}},
          objects={"dataPoint": [{"properties": {"fill": measure_colour("Map Color")}, "selector": ALL_POINTS}],
                   "mapControls": [{"properties": {"autoZoom": b(True)}}]},
          vco={**title_vco("Where people search for it on YouTube",
                           "Darker = more searches. States with almost none are left blank. Right-click a state > Drill through > State detail.")},
          filters=[f_has_state(), f_measure("Map Strength", "ge", 0.1)], name="map")
    rx, rw = M + map_w + G, full - map_w - G
    th = 230
    bar(p, rx, KPI_Y, rw, th, ("dim_state", "state"), "State Index", "Top 10 states", "Search score, 0-100 within each keyword",
        colour_measure="HL State Index", top=10, tooltips=("Interest vs Cricket", "Top Keyword in State"), filters=[f_has_state()], precision=0)
    by = KPI_Y + th + G
    bw = (rw - G) / 2
    bar(p, rx, by, bw, BODY_END - by, ("dim_state", "state"), "Interest vs Cricket", "How big is the topic there?",
        "Top 6 states; 1.0 = as searched as cricket", colour_measure="HL Interest vs Cricket", top=6, filters=[f_exclude_anchor(), f_has_state()],
        units=0, precision=2)
    bar(p, rx + bw + G, by, bw, BODY_END - by, ("dim_language", "language_label"), "Videos Tracked", "Videos found, by video language",
        "Top 5 languages of the videos these searches return", colour_measure="HL Videos", top=5, label="Videos")
    footnote(p, "YouTube doesn't share where viewers are, so this page uses YouTube search interest by state (Google Trends) as the audience signal. "
                "Search score = 0-100 within each keyword. Small states can score high from few searches.")
    pages.append(p)

    # State detail (drill-through, hidden) ----------------------------------
    p = Page("statedetail", "State detail", ptype="Drillthrough", hidden=True)
    p.filters.append({"name": uid("fdrill"), "field": col("dim_state", "state"), "type": "Categorical", "howCreated": "Drillthrough"})
    p.binding = {"name": uid("drillstate"), "type": "Drillthrough", "parameters": []}
    image(p, M, 16, 6, 40, "accent_bar.svg", name="accent")
    p.add("actionButton", M + 16, 18, 36, 36,
          objects={"icon": [{"properties": {"shapeType": s("back"), "lineColor": solid(INK), "lineWeight": n(2)}, "selector": {"id": "default"}}],
                   "fill": [{"properties": {"show": b(True), "fillColor": solid(CARD), "transparency": n(0)}, "selector": {"id": "default"}}],
                   "outline": [{"properties": {"show": b(False)}, "selector": {"id": "default"}}]},
          vco={**bare(), "visualLink": [{"properties": {"show": b(True), "type": s("Back")}}]}, name="back")
    card(p, M + 64, 14, 860, 44, mea("State Page Title"), "State", size=17, label_show=False, background=False, name="statetitle")
    kpi_row(p, KPI_Y - 90, [("Top Keyword in State", "Most-searched keyword", "keywords", {"size": 14}), ("State Index", "Average search score", "state"),
                            ("Interest vs Cricket", "Interest vs cricket", "interest")])
    top_y = KPI_Y + 2
    bar(p, M, top_y, half, BODY_END - top_y, ("dim_keyword", "keyword"), "State Index", "Top 12 keywords", "Search score in this state",
        colour_measure="HL State Index", top=12, filters=[f_exclude_anchor(), f_has_state()], precision=0)
    hh = (BODY_END - top_y - G) / 2
    bar(p, M + half + G, top_y, half, hh, ("dim_keyword", "topic_group"), "State Index", "By topic", "Average search score, top 6",
        colour_measure="HL State Index", top=6, filters=[f_exclude_anchor(), f_has_state()], precision=0)
    bar(p, M + half + G, top_y + hh + G, half, hh, ("dim_keyword", "keyword_language"), "State Index", "By search language", "Average search score, top 6",
        colour_measure="HL State Index", top=6, filters=[f_exclude_anchor(), f_has_state()], precision=0)
    footnote(p, "Drill-through page: right-click a state on the Know your audience map and choose Drill through > State detail. Use the back arrow to return.")
    pages.append(p)

    # Keyword tooltip (hidden) ---------------------------------------------
    card(tip, 8, 8, 148, 60, mea("Trend Label"), "Trend", size=13, colour_measure="Trend Status Color", name="tipstatus")
    card(tip, 164, 8, 148, 60, mea("Interest MoM %"), "vs last month", size=13, name="tipmom")
    line(tip, 8, 76, 304, 156, "Search interest, 5 years", None, name="tipline")
    tip.binding = {"name": uid("tipbinding"), "type": "Tooltip", "parameters": []}
    pages.append(tip)
    return pages


# ---------------------------------------------------------------- writing
def write_json(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")


def write_report(pages):
    if RES.exists():
        shutil.rmtree(RES)
    RES.mkdir(parents=True)
    shutil.copyfile(THEME_SRC, RES / "youtube_light_theme.json")
    for key in ICONS:
        (RES / f"icon_{key}.svg").write_text(icon_svg(key), encoding="utf-8")
    (RES / "accent_bar.svg").write_text(ACCENT_SVG, encoding="utf-8")

    report = json.loads((DEF / "report.json").read_text(encoding="utf-8"))
    base = report["themeCollection"]["baseTheme"]
    report["themeCollection"]["customTheme"] = {"name": "youtube_light_theme.json", "reportVersionAtImport": base["reportVersionAtImport"], "type": "RegisteredResources"}
    items = [{"name": "youtube_light_theme.json", "path": "youtube_light_theme.json", "type": "CustomTheme"},
             {"name": "accent_bar.svg", "path": "accent_bar.svg", "type": "Image"}]
    items += [{"name": f"icon_{k}.svg", "path": f"icon_{k}.svg", "type": "Image"} for k in ICONS]
    report["resourcePackages"] = [rp for rp in report["resourcePackages"] if rp["name"] != "RegisteredResources"]
    report["resourcePackages"].append({"name": "RegisteredResources", "type": "RegisteredResources", "items": items})
    write_json(DEF / "report.json", report)

    pages_dir = DEF / "pages"
    if pages_dir.exists():
        shutil.rmtree(pages_dir)
    for p in pages:
        page = {"$schema": PAGE_SCHEMA, "name": p.key, "displayName": p.display,
                "displayOption": "FitToPage", "height": p.height, "width": p.width}
        if p.filters:
            page["filterConfig"] = {"filters": p.filters}
        if p.binding:
            page["pageBinding"] = p.binding
        if p.ptype:
            page["type"] = p.ptype
        if p.hidden:
            page["visibility"] = "HiddenInViewMode"
        if p.interactions:
            page["visualInteractions"] = p.interactions
        page["objects"] = {"background": [{"properties": {"color": solid("#ffffff"), "transparency": n(0)}}],
                           "outspace": [{"properties": {"color": solid("#ffffff")}}]}
        write_json(pages_dir / p.key / "page.json", page)
        for v in p.visuals:
            write_json(pages_dir / p.key / "visuals" / v["name"] / "visual.json", v)
    write_json(pages_dir / "pages.json", {"$schema": f"{SCHEMA}/pagesMetadata/1.1.0/schema.json",
                                          "pageOrder": [p.key for p in pages], "activePageName": pages[0].key})


def check_layout(pages):
    """Flags visuals that leave the page or overlap another visual (icons/text inside cards are expected)."""
    issues = []
    layered = ("icon", "asof", "accent", "back", "statetitle", "pagetitle")
    for p in pages:
        boxes = []
        for v in p.visuals:
            x, y, w, h = (v["position"][k] for k in ("x", "y", "width", "height"))
            if x < 0 or y < 0 or x + w > p.width + 0.5 or y + h > p.height + 0.5:
                issues.append(f"{p.key}/{v['name']} is off the page")
            if not v["name"].startswith(layered) and not v["name"].startswith("kpi"):
                boxes.append((v["name"], x, y, x + w, y + h))
        for i, a in enumerate(boxes):
            for c in boxes[i + 1:]:
                if a[1] < c[3] - 0.5 and c[1] < a[3] - 0.5 and a[2] < c[4] - 0.5 and c[2] < a[4] - 0.5:
                    issues.append(f"{p.key}: {a[0]} overlaps {c[0]}")
    return issues


if __name__ == "__main__":
    print("Model changes:", update_model() or "none (already present)")
    pages = build_pages()
    problems = check_layout(pages)
    print("Layout check:", problems or "no overlaps, everything on the page")
    write_report(pages)
    print(f"Pages written: {len(pages)}, visuals: {sum(len(p.visuals) for p in pages)}")
