import time, datetime as dt
import warnings
import pandas as pd
from pytrends.request import TrendReq
from config import DATA_DIR
from keywords import all_keywords, ANCHOR

warnings.filterwarnings("ignore", category=FutureWarning)   # pytrends + new pandas noise

TODAY = dt.date.today().isoformat()
# No retries/backoff_factor here: pytrends' built-in retry crashes with urllib3 2.x.
# We retry ourselves in with_retry().
pt = TrendReq(hl="en-IN", tz=330)

cat_of = {kw: cat for cat, kw, _ in all_keywords()}
cat_of[ANCHOR] = "Anchor"
kws = [kw for kw in cat_of if kw != ANCHOR]
batches = [kws[i:i + 4] for i in range(0, len(kws), 4)]


def with_retry(fn, tries=4):
    for n in range(tries):
        try:
            return fn()
        except Exception as e:
            wait = 60 * (n + 1)
            print(f"  retry in {wait}s ({type(e).__name__}: {str(e)[:120]})")
            time.sleep(wait)
    return None


over_time, by_state, failed = [], [], []
for b_id, batch in enumerate(batches):
    terms = batch + [ANCHOR]
    print(f"Batch {b_id + 1}/{len(batches)}: {terms}")
    ok = with_retry(lambda: pt.build_payload(terms, geo="IN", timeframe="today 5-y",
                                             gprop="youtube") or True)
    if not ok:
        failed.append(b_id)
        continue

    ot = with_retry(pt.interest_over_time)
    if ot is not None and not ot.empty:
        ot = ot.drop(columns=["isPartial"], errors="ignore").reset_index()
        ot = ot.melt(id_vars="date", var_name="keyword", value_name="interest")
        ot["batch_id"] = b_id
        over_time.append(ot)
    else:
        failed.append(b_id)
    time.sleep(10)

    bs = with_retry(lambda: pt.interest_by_region(resolution="REGION", inc_low_vol=True))
    if bs is not None and not bs.empty:
        bs = bs.reset_index().melt(id_vars="geoName", var_name="keyword", value_name="interest")
        bs = bs.rename(columns={"geoName": "state"})
        bs["batch_id"] = b_id
        by_state.append(bs)
    time.sleep(10)

if not over_time:
    raise SystemExit("No Trends data collected (probably blocked). Wait an hour and rerun.")

ot = pd.concat(over_time)
ot["category"] = ot["keyword"].map(cat_of)
ot["snapshot_date"] = TODAY
ot.to_csv(f"{DATA_DIR}/trends_over_time_{TODAY}.csv", index=False)

bs = pd.concat(by_state) if by_state else pd.DataFrame(
    columns=["state", "keyword", "interest", "batch_id"])
bs["category"] = bs["keyword"].map(cat_of)
bs["snapshot_date"] = TODAY
bs.to_csv(f"{DATA_DIR}/trends_by_state_{TODAY}.csv", index=False)

print(f"Saved {len(ot)} time rows and {len(bs)} state rows")
if failed:
    print(f"Batches with missing data: {sorted(set(failed))} - rerun later to fill them")
