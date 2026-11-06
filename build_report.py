"""Writes the report pages of Dashboards/India YouTube Trends.pbip (PBIR format).

Run with Power BI Desktop CLOSED:  python build_report.py
It rebuilds every page from scratch, so manual edits made in Power BI to these
pages are overwritten. Make layout changes here, or stop using this script once
you start polishing by hand.

What it does
  1. Small model additions (helper measures, a has_state_data column, filter-proof "Data As Of").
  2. Registers the YouTube Light theme and the icon SVGs as report resources.
  3. Writes 7 report pages + a State detail drill-through page + a Keyword tooltip page.
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


def hl_measure(name, measure, axes, desc):
    branches = ", ".join(f"ISINSCOPE({a}), MAXX(ALLSELECTED({a}), [{measure}])" for a in axes)
    expr = (f"VAR v = [{measure}]\n\t\t\tVAR mx = SWITCH(TRUE(), {branches}, v)\n"
            f'\t\t\tRETURN IF(ISBLANK(v), BLANK(), IF(v = mx, "{RED}", "{GREY}"))')
    return name, expr, desc, "Colors"


HELPERS = [
    hl_measure("HL Videos", "Videos Tracked", ["dim_category[category_name]", "dim_language[language_name]", "dim_video[duration_bucket]", "dim_video[publish_hour_ist]"],
               "Bar colour: red for the largest bar, grey for the rest (Videos Tracked)."),
    hl_measure("HL Channels", "Channels", ["dim_channel[channel_origin]"], "Bar colour: red for the largest bar (Channels)."),
    hl_measure("HL Median Views", "Median Views", ["dim_category[category_name]", "dim_video[duration_bucket]"], "Bar colour: red for the largest bar (Median Views)."),
    hl_measure("HL Engagement", "Engagement Rate", ["dim_category[category_name]", "dim_video[duration_bucket]"], "Bar colour: red for the largest bar (Engagement Rate)."),
    hl_measure("HL State Index", "State Index", ["dim_state[state]", "dim_keyword[keyword]", "dim_keyword[topic_group]", "dim_keyword[keyword_language]"],
               "Bar colour: red for the largest bar (State Index)."),
    hl_measure("HL Interest vs Cricket", "Interest vs Cricket", ["dim_state[state]"], "Bar colour: red for the largest bar (Interest vs Cricket)."),
    hl_measure("HL Gap", "Content Gap Score", ["dim_keyword[keyword]"], "Bar colour: red for the largest bar (Content Gap Score)."),
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
    ("Trend Label", 'SWITCH([Trend Status], "Rising", "▲ Rising", "Declining", "▼ Declining", "Stable", "● Stable", "Low volume", "○ Low volume")',
     "Trend Status with an arrow, for tables. Colour it with [Trend Status Color].", "Trends"),
]

DATA_AS_OF = ('\t/// Header text showing the latest snapshot date (ignores slicers and filters).\n'
              '\tmeasure \'Data As Of\' = "Data as of " & FORMAT(CALCULATE(MAX(fact_video_snapshot[snapshot_date]), REMOVEFILTERS()), "d mmm yyyy")\n')

HAS_STATE_COLUMN = ("\t/// True when Google Trends returned state-level data for this keyword (17 low-volume keywords have none).\n"
                    "\tcolumn has_state_data = CALCULATE(COUNT(fact_trends_region[state_index])) > 0\n"
                    "\t\tdataType: boolean\n\t\tlineageTag: {tag}\n\t\tsummarizeBy: none\n\n")


def update_model():
    changes = []
    text = MEASURES_TMDL.read_text(encoding="utf-8")
    block = ""
    for name, expr, desc, folder in HELPERS:
        if f"measure '{name}'" in text:
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


def f_topn(table, column, measure, top):
    return {"name": uid("ftop"), "field": col(table, column), "type": "TopN",
            "filter": {"Version": 2,
                       "From": [{"Name": "subquery", "Expression": {"Subquery": {"Query": {
                           "Version": 2,
                           "From": [{"Name": "d", "Entity": table, "Type": 0}, {"Name": "m", "Entity": "_Measures", "Type": 0}],
                           "Select": [{"Column": {"Expression": {"SourceRef": {"Source": "d"}}, "Property": column}, "Name": "field"}],
                           "OrderBy": [{"Direction": 2, "Expression": {"Measure": {"Expression": {"SourceRef": {"Source": "m"}}, "Property": measure}}}],
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
    objects = {"data": [{"properties": {"mode": s(mode)}}],
               "header": [{"properties": {"show": b(True), "fontColor": solid(INK2), "textSize": n(9)}}],
               "items": [{"properties": {"fontColor": solid(INK), "textSize": n(10)}}]}
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


def line(page, x, y, w, h, title, subtitle, series=None, filters=None, name="line"):
    q = {"Category": {"projections": [proj(col("dim_date", "year_month"), "Month")]}, "Y": {"projections": [proj(mea("Interest"), "Search interest")]}}
    if series:
        q["Series"] = {"projections": [proj(col(*series))]}
    objects = {"lineStyles": [{"properties": {"strokeWidth": n(2), "showMarker": b(False)}}],
               "legend": [{"properties": {"show": b(bool(series)), "position": s("Top"), "fontSize": n(9), "showTitle": b(False)}}],
               "categoryAxis": [{"properties": {"showAxisTitle": b(False), "labelColor": solid(INK3), "fontSize": n(8)}}],
               "valueAxis": [{"properties": {"showAxisTitle": b(False), "labelColor": solid(INK3), "fontSize": n(8)}}]}
    if not series:
        objects["dataPoint"] = [{"properties": {"defaultColor": solid(RED)}}]
    return page.add("lineChart", x, y, w, h, query=q, objects=objects, vco=title_vco(title, subtitle), filters=filters,
                    sort=(col("dim_date", "year_month"), "Ascending"), name=name)


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


def scatter(page, x, y, w, h, cat, xm, ym, size, title, subtitle, filters=None, tooltip_page=None, name="scatter"):
    return page.add("scatterChart", x, y, w, h,
                    query={"Category": {"projections": [proj(col(*cat[:2]), cat[2])]}, "X": {"projections": [proj(mea(xm))]},
                           "Y": {"projections": [proj(mea(ym))]}, "Size": {"projections": [proj(mea(size))]}},
                    objects={"categoryLabels": [{"properties": {"show": b(True), "fontSize": n(8), "color": solid(INK2)}}],
                             "dataPoint": [{"properties": {"defaultColor": solid(RED)}}], "legend": [{"properties": {"show": b(False)}}],
                             "categoryAxis": [{"properties": {"showAxisTitle": b(True), "labelColor": solid(INK3), "fontSize": n(8)}}],
                             "valueAxis": [{"properties": {"showAxisTitle": b(True), "labelColor": solid(INK3), "fontSize": n(8)}}]},
                    vco=title_vco(title, subtitle), filters=filters, name=name, tooltip_page=tooltip_page)


def footnote(page, text):
    textbox(page, M, FOOT_Y, W - 2 * M, 22, [[(text, 8, INK3, False)]], name="footnote")


def header(page, title, subtitle, navigator=True):
    image(page, M, 16, 6, 40, "accent_bar.svg", name="accent")
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


def slicer_row(page, specs):
    """specs: list of (width, field, label, extra_kwargs)."""
    x, names = M, []
    for w, field, label, *kw in specs:
        names.append(slicer(page, x, SLICER_Y, w, field, label, **(kw[0] if kw else {})))
        x += w + G
    return names


# ---------------------------------------------------------------- pages
def build_pages():
    pages = []
    tip = Page("keywordtooltip", "Keyword tooltip", width=320, height=240, ptype="Tooltip", hidden=True)
    TIP = tip.key
    full = W - 2 * M
    half = (full - G) / 2
    third = (full - 2 * G) / 3

    # 1. Overview ---------------------------------------------------------
    p = Page("overview", "Overview")
    header(p, "India YouTube Trends", "What India watches and searches on YouTube: trending videos (YouTube API) and search interest (Google Trends)")
    s_topic, s_cat, s_fmt = slicer_row(p, [(220, col("dim_keyword", "topic_group"), "Topic", {"filters": [f_exclude_anchor()]}),
                                           (220, col("dim_category", "category_name"), "YouTube category"),
                                           (160, col("dim_video", "is_short"), "Shorts?")])
    kpis = kpi_row(p, KPI_Y, [("Videos Tracked", "Videos tracked", "videos"), ("Total Views", "Total views", "views", {"units": 1000000000, "precision": 1}),
                              ("Engagement Rate", "Engagement rate", "engagement"), ("Shorts Share", "Shorts share", "shorts"),
                              ("Regional Language Share", "Indian-language videos", "language"), ("Top Category", "Top category", "category", {"size": 13})])
    r1 = 214
    v_cat = bar(p, M, BODY_Y, 480, r1, ("dim_category", "category_name"), "Videos Tracked", "Videos by category",
                "Trending and keyword-search videos, top 6", colour_measure="HL Videos", top=6, tooltips=("Total Views", "Engagement Rate", "Median Views"))
    v_line = line(p, M + 480 + G, BODY_Y, full - 480 - G, r1, "Search interest on YouTube", "Monthly average of all tracked keywords, index relative to 'cricket' (Google Trends)")
    y3 = BODY_Y + r1 + G
    h3 = BODY_END - y3
    v_rise = table(p, M, y3, 420, h3, [proj(col("dim_keyword", "keyword"), "Keyword"), proj(mea("Trend Label"), "Trend"),
                                       proj(mea("Interest MoM %"), "MoM"), proj(col("dim_keyword", "topic_group"), "Topic")],
                   "Fastest-moving keywords", "Biggest month-on-month change in search interest",
                   filters=[f_exclude_anchor(), f_topn("dim_keyword", "keyword", "Interest MoM %", 5)],
                   sort=(mea("Interest MoM %"), "Descending"), status_colour=True, tooltip_page=TIP, name="rising")
    v_lang = bar(p, M + 420 + G, y3, 394, h3, ("dim_language", "language_name"), "Videos Tracked", "Videos by language",
                 "Audio track, then title script, top 5", colour_measure="HL Videos", top=5)
    v_orig = bar(p, M + 826 + G, y3, full - 826 - G, h3, ("dim_channel", "channel_origin"), "Channels", "Where channels are based",
                 "Channels behind the tracked videos", colour_measure="HL Channels")
    footnote(p, "Trending = YouTube's India 'mostPopular' chart, not all of YouTube. Search interest is a Google Trends index (0-100, scaled to 'cricket'), not search counts. Click any bar to filter the page.")
    p.interactions += [{"source": s_topic, "target": t, "type": "NoFilter"} for t in kpis + [v_cat, v_lang, v_orig]]
    p.interactions += [{"source": sl, "target": t, "type": "NoFilter"} for sl in (s_cat, s_fmt) for t in (v_line, v_rise)]
    pages.append(p)

    # 2. India map --------------------------------------------------------
    p = Page("indiamap", "India map")
    header(p, "India map", "Which states search most for a topic on YouTube (Google Trends, YouTube Search)")
    slicer_row(p, [(240, col("dim_keyword", "topic_group"), "Topic", {"filters": [f_exclude_anchor()]}),
                   (280, col("dim_keyword", "keyword"), "Keyword", {"filters": [f_exclude_anchor(), f_has_state()]}),
                   (200, col("dim_state", "zone"), "Zone")])
    map_w = 740
    p.add("filledMap", M, KPI_Y, map_w, BODY_END - KPI_Y,
          query={"Category": {"projections": [proj(col("dim_state", "state_map_name"), "State")]},
                 "Tooltips": {"projections": [proj(mea("State Index")), proj(mea("Interest vs Cricket")), proj(mea("Top Keyword in State"))]}},
          objects={"dataPoint": [{"properties": {"fill": measure_colour("Map Color")}, "selector": ALL_POINTS}],
                   "mapControls": [{"properties": {"autoZoom": b(True)}}]},
          vco={"title": [{"properties": {"show": b(True), "text": {"expr": mea("Map Title")}, "fontSize": n(12), "bold": b(True), "fontColor": solid(INK)}}],
               "subTitle": [{"properties": {"show": b(True), "text": s("Darker = higher share of searches. Right-click a state > Drill through > State detail."), "fontSize": n(9), "fontColor": solid(INK2)}}],
               "padding": pad(8, 12, 8, 12)},
          filters=[f_has_state()], name="map")
    rx, rw = M + map_w + G, full - map_w - G
    kpi_row(p, KPI_Y, [("Top State", "Highest interest", "state", {"size": 14}), ("Interest vs Cricket", "Interest vs cricket", "interest")], x0=rx, total=rw)
    bar(p, rx, BODY_Y, rw, BODY_END - BODY_Y, ("dim_state", "state"), "State Index", "Top 10 states", "State Index, 0-100 within each keyword",
        colour_measure="HL State Index", top=10, tooltips=("Interest vs Cricket", "Top Keyword in State"), filters=[f_has_state()], precision=0)
    footnote(p, "State Index = 0-100 within each keyword (100 = highest share of searches). 17 low-volume keywords (mostly regional-language) have no state data and are hidden here.")
    pages.append(p)

    # 3. Content categories ----------------------------------------------
    p = Page("categories", "Categories")
    header(p, "Content categories", "Which categories get the views and the engagement")
    slicer_row(p, [(160, col("dim_video", "is_short"), "Shorts?"), (220, col("dim_language", "language_name"), "Language"),
                   (200, col("dim_channel", "channel_origin"), "Channel origin")])
    kpi_row(p, KPI_Y, [("Videos Tracked", "Videos tracked", "videos"), ("Median Views", "Median views", "median", {"units": 1000000, "precision": 1}),
                       ("Engagement Rate", "Engagement rate", "engagement"), ("Avg Views per Day", "Avg views per day", "perday", {"units": 1000, "precision": 0})])
    rh = (BODY_END - BODY_Y - G) / 2
    scatter(p, M, BODY_Y, half, rh, ("dim_category", "category_name", "Category"), "Median Views", "Engagement Rate", "Videos Tracked",
            "Reach vs engagement", "Top 8 categories; bubble size = videos tracked", filters=[f_topn("dim_category", "category_name", "Videos Tracked", 8)])
    bar(p, M + half + G, BODY_Y, half, rh, ("dim_category", "category_name"), "Median Views", "Median views by category", "Median is less skewed by viral hits; top 6",
        colour_measure="HL Median Views", top=6, units=1000000, precision=1)
    bar(p, M, BODY_Y + rh + G, half, rh, ("dim_category", "category_name"), "Engagement Rate", "Engagement rate by category", "(Likes + comments) / views; top 6",
        colour_measure="HL Engagement", top=6, units=0)
    bar(p, M + half + G, BODY_Y + rh + G, half, rh, ("dim_video", "duration_bucket"), "Videos Tracked", "Videos by length", "How long tracked videos are",
        colour_measure="HL Videos", horizontal=False, sort_desc=False)
    footnote(p, "Median used instead of average because a few viral videos dominate totals. Engagement uses only videos with public like counts. Click any bar to filter the page.")
    pages.append(p)

    # 4. Trending topics -------------------------------------------------
    p = Page("trending", "Trending topics")
    header(p, "Trending topics", "Which keywords are rising, which are fading, and how now compares with last year")
    slicer_row(p, [(240, col("dim_keyword", "topic_group"), "Topic", {"filters": [f_exclude_anchor()]}),
                   (220, col("dim_keyword", "keyword_language"), "Keyword language"),
                   (360, col("dim_date", "date"), "Date range", {"mode": "Between"})])
    kpi_row(p, KPI_Y, [("Rising Keywords", "Rising keywords", "rising"), ("Declining Keywords", "Declining keywords", "declining"),
                       ("Interest", "Avg search interest", "interest"), ("Interest MoM %", "Month on month", "growth"),
                       ("Interest YoY % (3M)", "Year on year (3M)", "interest")])
    lh = 196
    line(p, M, BODY_Y, full, lh, "Search interest over time", "Monthly, top 5 keywords in the current selection. Pick a topic to compare its keywords.",
         series=("dim_keyword", "keyword"), filters=[f_exclude_anchor(), f_topn("dim_keyword", "keyword", "Interest", 5)], name="trendline")
    ty = BODY_Y + lh + G
    table(p, M, ty, full, BODY_END - ty,
          [proj(col("dim_keyword", "keyword"), "Keyword"), proj(col("dim_keyword", "topic_group"), "Topic"), proj(mea("Trend Label"), "Trend"),
           proj(mea("Interest"), "Interest"), proj(mea("Interest MoM %"), "MoM"), proj(mea("Interest YoY % (3M)"), "YoY (3M)")],
          "All keywords", "Sorted by month-on-month change. Hover a keyword to see its 5-year trend.",
          filters=[f_exclude_anchor()], sort=(mea("Interest MoM %"), "Descending"), status_colour=True, tooltip_page=TIP,
          widths={"dim_keyword.keyword": 260, "dim_keyword.topic_group": 200, "_Measures.Trend Label": 160, "_Measures.Interest": 120,
                  "_Measures.Interest MoM %": 120, "_Measures.Interest YoY % (3M)": 120}, name="kwtable")
    footnote(p, "Rising = interest up more than 15% vs the previous month; Declining = down more than 15%. Google Trends samples its data, so small changes are noise.")
    pages.append(p)

    # 5. Videos & channels -----------------------------------------------
    p = Page("videoschannels", "Videos & channels")
    header(p, "Videos & channels", "Which videos and channels win, and whether length and timing matter")
    slicer_row(p, [(220, col("dim_category", "category_name"), "Category"), (200, col("dim_language", "language_name"), "Language"),
                   (160, col("dim_video", "is_short"), "Shorts?"), (180, col("fact_video_snapshot", "in_trending"), "In trending chart?")])
    kpi_row(p, KPI_Y, [("Channels", "Channels", "channels"), ("Total Subscribers", "Subscribers (channels in view)", "subscribers", {"units": 1000000000, "precision": 1}),
                       ("Trending Videos", "In trending charts", "trending"), ("Avg Views per Video", "Avg views per video", "views", {"units": 1000000, "precision": 1})])
    th = 236
    vw = 724
    table(p, M, BODY_Y, vw, th,
          [proj(col("dim_video", "title"), "Video"), proj(col("dim_channel", "channel_name"), "Channel"),
           proj(mea("Total Views"), "Views", MILLIONS), proj(mea("Avg Views per Day"), "Views/day", MILLIONS), proj(mea("Engagement Rate"), "Engagement")],
          "Top 15 videos", "By latest public view count (M = millions)",
          filters=[f_topn("dim_video", "title", "Total Views", 15)], sort=(mea("Total Views"), "Descending"),
          widths={"dim_video.title": 330, "dim_channel.channel_name": 130, "_Measures.Total Views": 80, "_Measures.Avg Views per Day": 80, "_Measures.Engagement Rate": 80},
          name="topvideos")
    table(p, M + vw + G, BODY_Y, full - vw - G, th,
          [proj(col("dim_channel", "channel_name"), "Channel"), proj(col("dim_channel", "country"), "Country"),
           proj(mea("Videos Tracked"), "Videos"), proj(mea("Total Views"), "Views", MILLIONS), proj(mea("Total Subscribers"), "Subs", MILLIONS)],
          "Channel leaderboard", "Top 20 channels by views of their tracked videos (M = millions)",
          filters=[f_topn("dim_channel", "channel_name", "Total Views", 20)], sort=(mea("Total Views"), "Descending"),
          widths={"dim_channel.channel_name": 170, "dim_channel.country": 60, "_Measures.Videos Tracked": 55, "_Measures.Total Views": 70, "_Measures.Total Subscribers": 65},
          name="channels")
    cy = BODY_Y + th + G
    ch = BODY_END - cy
    bar(p, M, cy, third, ch, ("dim_video", "duration_bucket"), "Median Views", "Median views by length", None, colour_measure="HL Median Views",
        horizontal=False, sort_desc=False, units=1000000, precision=1)
    bar(p, M + third + G, cy, third, ch, ("dim_video", "duration_bucket"), "Engagement Rate", "Engagement by length", None, colour_measure="HL Engagement",
        horizontal=False, sort_desc=False, units=0)
    bar(p, M + 2 * (third + G), cy, third, ch, ("dim_video", "publish_hour_ist"), "Videos Tracked", "Publish hour (IST)", None, colour_measure="HL Videos",
        horizontal=False, sort_desc=False)
    footnote(p, "Views are each video's latest public count. Like counts hidden by creators are left out of the engagement rate. Click any bar to filter the page.")
    pages.append(p)

    # 6. Creator opportunities -------------------------------------------
    p = Page("opportunities", "Creator opportunities")
    header(p, "Creator opportunities", "Where demand is growing faster than established creators are serving it")
    slicer_row(p, [(240, col("dim_keyword", "topic_group"), "Topic", {"filters": [f_exclude_anchor()]}),
                   (220, col("dim_keyword", "keyword_language"), "Keyword language")])
    kpi_row(p, KPI_Y, [("Keywords Scored", "Keywords scored", "keywords"), ("Content Gap Score", "Content gap score", "gap"),
                       ("Demand Index", "Demand index", "interest"), ("Growth 12w %", "Growth (12 weeks)", "growth"),
                       ("Small Channel Share", "Small-channel share", "smallch")])
    rh = 226
    scatter(p, M, BODY_Y, half, rh, ("dim_keyword", "keyword", "Keyword"), "Demand Index", "Growth 12w %", "Small Channel Share",
            "Opportunity map", "Top 20 keywords by demand. Right = more demand, up = growing", filters=[f_exclude_anchor(), f_topn("dim_keyword", "keyword", "Demand Index", 20)],
            tooltip_page=TIP, name="oppscatter")
    bar(p, M + half + G, BODY_Y, half, rh, ("dim_keyword", "keyword"), "Content Gap Score", "Top content gaps", "0-100: demand + growth + small-channel share; top 6",
        colour_measure="HL Gap", top=6, tooltips=("Demand Index", "Growth 12w %", "Small Channel Share"), filters=[f_exclude_anchor()], tooltip_page=TIP, units=0, precision=0)
    my = BODY_Y + rh + G
    matrix(p, M, my, full, BODY_END - my, ("dim_keyword", "keyword_language", "Language"), ("dim_keyword", "topic_group", "Topic"), "Demand Index",
           "Heat Color Demand", "Heat Font Demand", "Demand by language and topic", "Darker = more search demand. Empty cells = no keyword tracked there yet.",
           filters=[f_exclude_anchor()], name="langmatrix")
    footnote(p, "Content gap score = 40% demand + 30% growth + 30% share of top recent videos from channels under 100K subscribers. Scores fill in as the daily search rotation runs.")
    pages.append(p)

    # 7. Business & marketing --------------------------------------------
    p = Page("business", "Business")
    header(p, "Business & marketing", "Which regions to target for a topic")
    s_topic, _ = slicer_row(p, [(260, col("dim_keyword", "topic_group"), "Target topic", {"filters": [f_exclude_anchor()]}),
                                (200, col("dim_state", "zone"), "Zone")])
    heat_h = 286
    heat = matrix(p, M, KPI_Y, full, heat_h, ("dim_state", "state", "State"), ("dim_keyword", "topic_group", "Topic"), "State Index",
                  "Heat Color State", "Heat Font State", "State x topic interest", "State Index; darker = stronger interest. Scroll for all states. Not filtered by the topic slicer.",
                  filters=[f_exclude_anchor(), f_has_state()], font_size=8, name="heatmap")
    p.interactions.append({"source": s_topic, "target": heat, "type": "NoFilter"})
    by = KPI_Y + heat_h + G
    bar(p, M, by, half, BODY_END - by, ("dim_state", "state"), "State Index", "Best states to target", "Top 6 by State Index for the selected topic",
        colour_measure="HL State Index", top=6, filters=[f_exclude_anchor(), f_has_state()], precision=0)
    bar(p, M + half + G, by, half, BODY_END - by, ("dim_state", "state"), "Interest vs Cricket", "Topic size vs cricket", "Top 6; 1.0 = as popular as cricket in that state",
        colour_measure="HL Interest vs Cricket", top=6, filters=[f_exclude_anchor(), f_has_state()], units=0, precision=2)
    footnote(p, "State Index compares states for the same topic. Interest vs Cricket shows how big the topic is relative to cricket in that state. Small UTs can score high from few searches.")
    pages.append(p)

    # 8. State detail (drill-through) ------------------------------------
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
    kpi_row(p, KPI_Y - 90, [("Top Keyword in State", "Most-searched keyword", "keywords", {"size": 14}), ("State Index", "Avg State Index", "state"),
                            ("Interest vs Cricket", "Interest vs cricket", "interest")])
    top_y = KPI_Y + 2
    bar(p, M, top_y, half, BODY_END - top_y, ("dim_keyword", "keyword"), "State Index", "Top 12 keywords", "State Index for this state",
        colour_measure="HL State Index", top=12, filters=[f_exclude_anchor(), f_has_state()], precision=0)
    hh = (BODY_END - top_y - G) / 2
    bar(p, M + half + G, top_y, half, hh, ("dim_keyword", "topic_group"), "State Index", "By topic", "Average State Index, top 6",
        colour_measure="HL State Index", top=6, filters=[f_exclude_anchor(), f_has_state()], precision=0)
    bar(p, M + half + G, top_y + hh + G, half, hh, ("dim_keyword", "keyword_language"), "State Index", "By keyword language", "Average State Index, top 6",
        colour_measure="HL State Index", top=6, filters=[f_exclude_anchor(), f_has_state()], precision=0)
    footnote(p, "Drill-through page: right-click a state on the India map or Business page and choose Drill through > State detail. Use the back arrow to return.")
    pages.append(p)

    # 9. Keyword tooltip ---------------------------------------------------
    card(tip, 8, 8, 148, 60, mea("Trend Label"), "Trend", size=13, colour_measure="Trend Status Color", name="tipstatus")
    card(tip, 164, 8, 148, 60, mea("Interest MoM %"), "Month on month", size=13, name="tipmom")
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
