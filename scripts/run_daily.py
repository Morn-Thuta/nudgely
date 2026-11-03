"""Run the whole pipeline once, unattended.

  python scripts/run_daily.py              # the normal daily run
  python scripts/run_daily.py --dry-run    # say what would run, call nothing
  python scripts/run_daily.py --skip tags  # leave a step out

Steps, in order:
  tags     new customers get their chats read and tagged
  messages anyone with tags but no draft gets one written
  verify   every draft is checked against its chat
  returns  campaign rows past their 30-day window are closed

Each step is skipped when there is nothing for it to do, so a daily run on a
quiet day costs no API calls. The run keeps going when a step fails - a quota
limit on messages should not stop outcomes being closed - and the exit code is
non-zero if anything failed, so a scheduler can alert on it.

Schedule it on Windows:
  schtasks /create /tn "Nudgely daily" /tr "<repo>\\.venv\\Scripts\\python.exe
           <repo>\\scripts\\run_daily.py" /sc daily /st 09:00
On a server, the same line in cron.
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
PYTHON = sys.executable
LOG = os.path.join(DATA, "run_daily.log")
WINDOW_DAYS = 30

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def say(line):
    stamped = f"{datetime.now():%Y-%m-%d %H:%M:%S}  {line}"
    print(stamped)
    try:
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(stamped + "\n")
    except OSError:
        pass


def load(name, default):
    path = os.path.join(DATA, name)
    if not os.path.exists(path):
        return default
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


def untagged():
    chats, tags = load("chats.json", {}), load("tags.json", {})
    return [cid for cid in chats if cid not in tags]


def undrafted():
    tags, msgs = load("tags.json", {}), load("messages.json", {})
    consent = load("consent.json", {})
    opted_out = {cid for cid, v in consent.items() if v.get("opted_in") is False}
    return [cid for cid in tags if cid not in msgs and cid not in opted_out]


def closeable():
    """Campaign rows with no outcome whose window has passed."""
    path = os.path.join(DATA, "campaign_log.csv")
    if not os.path.exists(path):
        return 0
    import csv
    cutoff = datetime.now() - timedelta(days=WINDOW_DAYS)
    n = 0
    try:
        with open(path, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                if str(row.get("returned", "")).strip():
                    continue
                try:
                    if datetime.fromisoformat(row["sent_at"]) < cutoff:
                        n += 1
                except (KeyError, ValueError):
                    continue
    except OSError:
        return 0
    return n


def run(step, args, dry_run):
    script = os.path.join(ROOT, "scripts", step)
    if dry_run:
        say(f"  would run: {step} {' '.join(args)}")
        return True
    result = subprocess.run([PYTHON, script, *args], cwd=ROOT)
    ok = result.returncode == 0
    say(f"  {step} finished with exit {result.returncode}")
    return ok


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--skip", default="", help="comma-separated: tags,messages,verify,returns")
    a = p.parse_args()
    skip = {s.strip() for s in a.skip.split(",") if s.strip()}

    say("=== daily run ===" + (" (dry run)" if a.dry_run else ""))
    failed = []

    if "tags" in skip:
        say("tags: skipped")
    elif not untagged():
        say("tags: nothing new to tag")
    else:
        say(f"tags: {len(untagged())} customer(s) without tags")
        if not run("extract_tags.py", [], a.dry_run):
            failed.append("tags")

    if "messages" in skip:
        say("messages: skipped")
    elif not undrafted():
        say("messages: every tagged customer already has a draft")
    else:
        say(f"messages: {len(undrafted())} customer(s) without a draft")
        if not run("write_messages.py", [], a.dry_run):
            failed.append("messages")

    if "verify" in skip:
        say("verify: skipped")
    elif not load("messages.json", {}):
        say("verify: no drafts yet")
    else:
        say("verify: checking every draft")
        if not run("verify_messages.py", [], a.dry_run):
            failed.append("verify")  # exits 1 when a draft is flagged, which is a real finding

    n = closeable()
    if "returns" in skip:
        say("returns: skipped")
    elif not n:
        say("returns: nothing past its window")
    else:
        say(f"returns: closing {n} row(s) past {WINDOW_DAYS} days")
        if not run("record_returns.py", ["--close", "--window", str(WINDOW_DAYS)], a.dry_run):
            failed.append("returns")

    if failed:
        say(f"=== done, needs attention: {', '.join(failed)} ===")
        return 1
    say("=== done, all clear ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
