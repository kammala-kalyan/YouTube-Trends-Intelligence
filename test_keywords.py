"""Keyword test (decision Q13): check that Google Trends returns data for keywords before relying on them.

Usage: python test_keywords.py                 (keywords in keywords.py with no Trends data yet)
       python test_keywords.py "UPSC Telugu" "share market Tamil"   (specific keywords)

Uses Google Trends only (free). YouTube search isn't tested here, because each search costs 100
quota units; the daily pipeline flags keywords whose search returns no videos.
Prints a report and writes data/keyword_test_YYYY-MM-DD.csv. It doesn't change keywords.py:
drop the "no data" terms there by hand after reviewing the report.
"""
import glob, os, sys, time, datetime as dt
import warnings
import pandas as pd
from pytrends.request import TrendReq
from config import DATA_DIR
from keywords import all_keywords, ANCHOR

warnings.filterwarnings("ignore", category=FutureWarning)
TODAY = dt.date.today().isoformat()

if len(sys.argv) > 1:
    todo = sys.argv[1:]
else:
    have = set()
    for f in glob.glob(os.path.join(DATA_DIR, "trends_over_time_*.csv")):
        have |= set(pd.read_csv(f, usecols=["keyword"])["keyword"])
    todo = [kw for _, kw, _ in all_keywords() if kw not in have]
print(f"Testing {len(todo)} keywords against Google Trends (YouTube Search, India, 5 years)")

pt = TrendReq(hl="en-IN", tz=330)
rows = []
for i in range(0, len(todo), 4):
    batch = todo[i:i + 4]
    res = None
    for attempt in range(3):
        try:
            pt.build_payload(batch + [ANCHOR], geo="IN", timeframe="today 5-y", gprop="youtube")
            res = pt.interest_over_time()
            break
        except Exception as e:
            print(f"  retry in {60 * (attempt + 1)}s ({type(e).__name__})")
            time.sleep(60 * (attempt + 1))
    for kw in batch:
        if res is None:
            status, avg = "not tested (blocked)", None
        elif kw not in res.columns or res[kw].sum() == 0:
            status, avg = "NO DATA", 0.0
        else:
            avg = round(float(res[kw].mean()), 2)
            status = "ok" if res[kw].gt(0).mean() >= 0.5 else "weak (zero in most weeks)"
        rows.append(dict(keyword=kw, status=status, avg_interest_vs_cricket_batch=avg))
        print(f"  {status:<26} {kw}  (avg {avg})")
    time.sleep(12)

out = pd.DataFrame(rows)
out.to_csv(os.path.join(DATA_DIR, f"keyword_test_{TODAY}.csv"), index=False)
print("\nSummary:", out["status"].value_counts().to_dict())
