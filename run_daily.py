"""Run the whole daily pipeline in the right order.

Daily: trending -> topic search (a third of the keywords) -> channels
       -> Google Trends (a seventh of the keywords + any without data yet) -> rebuild model

Runs on GitHub Actions every day (.github/workflows/daily.yml). Can also be run by hand:
       python run_daily.py            (normal)
       python run_daily.py --trends   (Google Trends for every keyword, not just today's slice)

If a step fails, the remaining steps still run and the model is rebuilt from the data that
exists (old files are never deleted), then the script exits with code 1 so the GitHub run is
marked as failed and GitHub sends an email.
"""
import os, subprocess, sys, datetime as dt
from config import DATA_DIR

PY = sys.executable
HERE = os.path.dirname(os.path.abspath(__file__))
TODAY = dt.date.today()
failed = []


def run(script, *args):
    print(f"\n=== {script} {' '.join(args)}", flush=True)
    r = subprocess.run([PY, "-X", "utf8", script, *args], cwd=HERE)
    if r.returncode != 0:
        print(f"!!! {script} failed (exit {r.returncode}) - continuing, previous data is kept", flush=True)
        failed.append(script)
    return r.returncode == 0


def write_summary():
    """Short report for the GitHub Actions run page (and the failure email links to it)."""
    path = os.environ.get("GITHUB_STEP_SUMMARY")
    if not path:
        return
    lines = [f"## Daily pipeline {TODAY}", ""]
    if failed:
        lines.append("**Failed steps (previous data kept):** " + ", ".join(failed))
        if "fetch_trends.py" in failed:
            lines.append("")
            lines.append("Google Trends probably blocked the GitHub server. The last good Trends data is still used. "
                         "It retries automatically tomorrow; or run `python fetch_trends.py` locally and push.")
    else:
        lines.append("All steps succeeded.")
    with open(path, "a", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


already = os.path.exists(os.path.join(HERE, DATA_DIR, f"trending_videos_{TODAY}.csv"))
if already:
    print("Today's trending snapshot already exists - skipping YouTube pulls")
else:
    run("fetch_trending.py")
    run("fetch_topics.py")
    run("fetch_channels.py")

run("fetch_trends.py", *(["--all"] if "--trends" in sys.argv else []))

run("build_model.py")
write_summary()

if failed:
    print(f"\nPipeline finished WITH FAILURES: {', '.join(failed)}")
    sys.exit(1)
print("\nPipeline finished.")
