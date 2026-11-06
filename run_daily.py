"""Run the whole daily pipeline in the right order.

Daily:  trending -> topic search (rotating group) -> channels -> rebuild model
Weekly: Google Trends (only if the last Trends file is 7+ days old)

Usage: python run_daily.py            (normal)
       python run_daily.py --trends   (force a Trends run today)
"""
import glob, os, subprocess, sys, datetime as dt
from config import DATA_DIR

PY = sys.executable
HERE = os.path.dirname(os.path.abspath(__file__))
TODAY = dt.date.today()


def run(script, *args):
    print(f"\n=== {script} {' '.join(args)}", flush=True)
    r = subprocess.run([PY, "-X", "utf8", script, *args], cwd=HERE)
    if r.returncode != 0:
        print(f"!!! {script} failed (exit {r.returncode}) - continuing")
    return r.returncode == 0


def trends_due():
    files = sorted(glob.glob(os.path.join(HERE, DATA_DIR, "trends_over_time_*.csv")))
    if not files:
        return True
    last = dt.date.fromisoformat(os.path.basename(files[-1])[17:27])
    return (TODAY - last).days >= 7


already = os.path.exists(os.path.join(HERE, DATA_DIR, f"trending_videos_{TODAY}.csv"))
if already:
    print("Today's trending snapshot already exists - skipping YouTube pulls")
else:
    run("fetch_trending.py")
    run("fetch_topics.py")
    run("fetch_channels.py")

if "--trends" in sys.argv or trends_due():
    run("fetch_trends.py")

run("build_model.py")
print("\nPipeline finished.")
