"""Google Trends (YouTube Search, India): 5-year weekly interest + state breakdown.

Runs every day on a SLICE of the keywords (decision Q25), so each run makes few requests and is
less likely to be blocked:
  - one-seventh of the keywords, rotating by date (every keyword refreshes once a week)
  - plus any keyword with no Trends data yet (new keywords don't wait a week)

Small keywords use a chained reference (decision Q40, keywords.ANCHOR_CHAIN): each keyword is
batched with the reference that suits its size, and moves down a level automatically when its last
result was (almost) all zero. Each batch records the reference it used (column anchor_used), and
build_model.py converts every level back to the cricket scale.

Usage: python fetch_trends.py          (today's slice)
       python fetch_trends.py --all    (every keyword, e.g. a first full load)

Exit codes: 0 = all batches fine; 1 = nothing collected (blocked, no file written, old data kept);
2 = partly blocked (what arrived is saved, old data kept for the rest). run_daily.py treats 1 and 2
as failures so GitHub sends an email.
"""
import glob, os, sys, time, datetime as dt
import warnings
import pandas as pd
from pytrends.request import TrendReq
from config import DATA_DIR
from keywords import all_keywords, ANCHOR, ANCHOR_CHAIN

warnings.filterwarnings("ignore", category=FutureWarning)   # pytrends + new pandas noise

TODAY = dt.date.today().isoformat()
N_SLICES = 7
STOP_AFTER_FAILED_BATCHES = 3   # in a row: Google is blocking us, stop wasting time
MIN_MEAN, MIN_NONZERO = 1.0, 0.5   # below either: too small for this level, go one level down

# No retries/backoff_factor here: pytrends' built-in retry crashes with urllib3 2.x.
# We retry ourselves in with_retry().
pt = TrendReq(hl="en-IN", tz=330)

cat_of = {kw: cat for cat, kw, _ in all_keywords()}
cat_of[ANCHOR] = "Anchor"
kws = [kw for kw in cat_of if kw != ANCHOR]


def latest_results():
    """keyword -> (date, anchor_used, too_small) from the latest Trends file or keyword test that has it."""
    res = {}
    for f in sorted(glob.glob(os.path.join(DATA_DIR, "trends_over_time_*.csv"))):
        d = pd.read_csv(f)
        if "anchor_used" not in d.columns:
            d["anchor_used"] = ANCHOR
        for (kw, anc), g in d.groupby(["keyword", "anchor_used"]):
            if kw == anc:
                continue
            small = g["interest"].mean() < MIN_MEAN or (g["interest"] > 0).mean() < MIN_NONZERO
            res[kw] = (os.path.basename(f)[17:27], anc, small)
    for f in sorted(glob.glob(os.path.join(DATA_DIR, "keyword_test_*.csv"))):
        d = pd.read_csv(f)
        date = os.path.basename(f)[13:23]
        for r in d.itertuples():
            if r.status.startswith("not tested"):
                continue
            if r.keyword not in res or res[r.keyword][0] < date:
                res[r.keyword] = (date, getattr(r, "anchor_used", ANCHOR) if hasattr(r, "anchor_used") else ANCHOR,
                                  r.status != "ok")
    return res


RESULTS = latest_results()


def keywords_with_trends_data():
    """Keywords measured in an actual Trends file (a keyword test alone doesn't count as data)."""
    have = set()
    for f in glob.glob(os.path.join(DATA_DIR, "trends_over_time_*.csv")):
        d = pd.read_csv(f)
        if "anchor_used" not in d.columns:
            d["anchor_used"] = ANCHOR
        have |= set(d.loc[d["keyword"] != d["anchor_used"], "keyword"])
    return have


HAVE_DATA = keywords_with_trends_data()


def level_of(kw):
    """Chain level for a keyword; len(ANCHOR_CHAIN) means too small to measure even at the last level."""
    if kw in ANCHOR_CHAIN[1:]:
        return ANCHOR_CHAIN.index(kw) - 1           # a reference is measured one level up
    if kw not in RESULTS:
        return 0
    _, anc, small = RESULTS[kw]
    lvl = ANCHOR_CHAIN.index(anc) if anc in ANCHOR_CHAIN else 0
    return lvl + 1 if small else lvl


if "--all" in sys.argv:
    todays = list(kws)
    print(f"Full run: {len(todays)} keywords")
else:
    sl = dt.date.today().toordinal() % N_SLICES
    rotation = kws[sl::N_SLICES]
    today_file = os.path.join(DATA_DIR, f"trends_over_time_{TODAY}.csv")
    done_today = set(pd.read_csv(today_file, usecols=["keyword"])["keyword"]) if os.path.exists(today_file) else set()
    rotation = [k for k in rotation if k not in done_today]
    new = [k for k in kws if k not in HAVE_DATA and k not in rotation]
    # keywords measured today that came back too small for their level: one more try, one level down
    retry = [k for k in kws if k in done_today and k in RESULTS and RESULTS[k][2] and k not in rotation + new]
    todays = rotation + new + retry
    print(f"Slice {sl + 1}/{N_SLICES}: {len(rotation)} keywords + {len(new)} without data yet + {len(retry)} retried one level down")

by_level = {}
too_small = []
for kw in todays:
    lvl = level_of(kw)
    if lvl >= len(ANCHOR_CHAIN):
        too_small.append(kw)
    else:
        by_level.setdefault(lvl, []).append(kw)
# a level needs its reference measured one level up; add it if it has no result yet
for lvl in sorted(by_level):
    ref = ANCHOR_CHAIN[lvl]
    if lvl > 0 and ref not in HAVE_DATA and ref not in by_level.get(lvl - 1, []):
        by_level.setdefault(lvl - 1, []).append(ref)
if too_small:
    print(f"Too small to measure even with the last reference (skipped; consider removing): {too_small}")

batches = [(lvl, group[i:i + 4]) for lvl in sorted(by_level) for group in [by_level[lvl]] for i in range(0, len(group), 4)]
print("Batches per level:", {lvl: sum(1 for l, _ in batches if l == lvl) for lvl in sorted(by_level)})
if "--dry" in sys.argv:          # show the plan only, no requests
    for lvl, b in batches:
        print(f"  level {lvl} ({ANCHOR_CHAIN[lvl]}): {b}")
    sys.exit(0)


def with_retry(fn, tries=3):
    for n in range(tries):
        try:
            return fn()
        except Exception as e:
            wait = 60 * (n + 1)
            print(f"  retry in {wait}s ({type(e).__name__}: {str(e)[:120]})")
            time.sleep(wait)
    return None


over_time, by_state, failed = [], [], []
fails_in_row = 0
for b_id, (lvl, batch) in enumerate(batches):
    if fails_in_row >= STOP_AFTER_FAILED_BATCHES:
        print(f"{fails_in_row} batches failed in a row - Google Trends is probably blocking. Stopping.")
        failed += list(range(b_id, len(batches)))
        break
    ref = ANCHOR_CHAIN[lvl]
    terms = batch + [ref]
    print(f"Batch {b_id + 1}/{len(batches)} (level {lvl}, reference '{ref}'): {batch}")
    ok = with_retry(lambda: pt.build_payload(terms, geo="IN", timeframe="today 5-y",
                                             gprop="youtube") or True)
    if not ok:
        failed.append(b_id)
        fails_in_row += 1
        continue

    ot = with_retry(pt.interest_over_time)
    if ot is not None and not ot.empty:
        ot = ot.drop(columns=["isPartial"], errors="ignore").reset_index()
        ot = ot.melt(id_vars="date", var_name="keyword", value_name="interest")
        ot["batch_id"] = b_id
        ot["anchor_used"] = ref
        over_time.append(ot)
        fails_in_row = 0
    else:
        failed.append(b_id)
        fails_in_row += 1
    time.sleep(10)

    bs = with_retry(lambda: pt.interest_by_region(resolution="REGION", inc_low_vol=True))
    if bs is not None and not bs.empty:
        bs = bs.reset_index().melt(id_vars="geoName", var_name="keyword", value_name="interest")
        bs = bs.rename(columns={"geoName": "state"})
        bs["batch_id"] = b_id
        bs["anchor_used"] = ref
        by_state.append(bs)
    time.sleep(10)

if not over_time:
    print("No Trends data collected (probably blocked). No file written; previous data is kept.")
    sys.exit(1)

def save_merged(new, path):
    """Write today's file; if a file for today already exists (a re-run), keep its other keywords.
    Only the re-fetched keywords' old rows are dropped; each old batch keeps its reference rows and
    its other keywords (so they can still be converted). Batch ids are kept unique."""
    if "date" in new.columns:   # always plain YYYY-MM-DD text, so merged files have one date format
        new = new.assign(date=pd.to_datetime(new["date"], format="mixed").dt.strftime("%Y-%m-%d"))
    if os.path.exists(path):
        old = pd.read_csv(path)
        if "date" in old.columns:
            old["date"] = pd.to_datetime(old["date"], format="mixed").dt.strftime("%Y-%m-%d")
        if "anchor_used" not in old.columns:
            old["anchor_used"] = ANCHOR
        refetched = set(new.loc[new["keyword"] != new["anchor_used"], "keyword"])
        old = old[~(old["keyword"].isin(refetched) & (old["keyword"] != old["anchor_used"]))]
        new = new.assign(batch_id=new["batch_id"] + (old["batch_id"].max() + 1 if len(old) else 0))
        new = pd.concat([old, new], ignore_index=True)
    new.to_csv(path, index=False)
    return new


ot = pd.concat(over_time)
ot["category"] = ot["keyword"].map(cat_of)
ot["snapshot_date"] = TODAY
ot = save_merged(ot, f"{DATA_DIR}/trends_over_time_{TODAY}.csv")

bs = pd.concat(by_state) if by_state else pd.DataFrame(
    columns=["state", "keyword", "interest", "batch_id", "anchor_used"])
bs["category"] = bs["keyword"].map(cat_of)
bs["snapshot_date"] = TODAY
bs = save_merged(bs, f"{DATA_DIR}/trends_by_state_{TODAY}.csv")

print(f"Saved {len(ot)} time rows and {len(bs)} state rows")
if failed:
    print(f"Batches with missing data: {sorted(set(failed))} - previous data kept for those keywords")
    sys.exit(2)
