"""Measure the tagger against hand-written chats with known answers.

Run from repo root:
  python scripts/test_tagging.py                  # whole chat at once (batch path)
  python scripts/test_tagging.py --per-message    # one message at a time (API path)
  python scripts/test_tagging.py --limit 10       # stop after 10, for a free-tier key
  python scripts/test_tagging.py --only T15,T17   # re-run specific cases

Answers are cached in data/tagging_results.json, so a run that dies halfway to a
quota limit is not wasted and the next run carries on. Use --force to re-ask.

Two numbers matter and they fail differently. **Recall** is how much the tagger
finds; miss a complaint and the shop sends a promotion to an angry customer.
**Precision** is how much of what it finds is real; invent a tag and the message
references something the customer never said. The cases named `expect_not` exist
for the second kind, which is the one a casual eyeball test never catches.
"""

import argparse
import json
import os
import sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from dotenv import load_dotenv  # noqa: E402

from nudgely import llm  # noqa: E402

load_dotenv(os.path.join(ROOT, ".env"))

TEST_SET = os.path.join(ROOT, "data", "examples", "tagging_test_set.json")
CACHE = os.path.join(ROOT, "data", "tagging_results.json")


def predict(case, per_message):
    """Tag one case, either whole-chat or message by message."""
    if not per_message:
        return llm.extract_tags(case["id"], case["chat"])

    held = {}
    for message in case["chat"]:
        if message["from"] != "customer":
            continue  # the API only sees incoming messages
        one = llm.tag_message(case["id"], message["text"], date=message.get("date", ""), prior=held)
        held = llm.merge_tags(held, one)
    return held or {"customer_id": case["id"], "tags": [], "sentiment": ""}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--per-message", action="store_true",
                   help="use tag_message per incoming message, the path the API takes")
    p.add_argument("--limit", type=int, default=0, help="stop after this many LLM calls")
    p.add_argument("--only", default="", help="case ids, comma separated")
    p.add_argument("--force", action="store_true", help="re-ask cases already cached")
    a = p.parse_args()

    suite = json.load(open(TEST_SET, encoding="utf-8"))
    cases = suite["cases"]
    tag_types = suite["tag_types"]
    mode = "per-message" if a.per_message else "whole-chat"

    cache = json.load(open(CACHE, encoding="utf-8")) if os.path.exists(CACHE) else {}
    cache.setdefault(mode, {})
    only = set(filter(None, a.only.split(",")))

    asked = 0
    for case in cases:
        if only and case["id"] not in only:
            continue
        if case["id"] in cache[mode] and not a.force:
            continue
        if a.limit and asked >= a.limit:
            break
        try:
            out = predict(case, a.per_message)
            cache[mode][case["id"]] = {"tags": sorted({t["type"] for t in out.get("tags", [])}),
                                       "sentiment": out.get("sentiment", "")}
            asked += 1
            print(f"{case['id']} -> {', '.join(cache[mode][case['id']]['tags']) or '(none)'}")
        except Exception as e:  # noqa: BLE001 - a dead provider should not lose the run
            print(f"{case['id']} FAILED: {str(e)[:160]}")
            break
        finally:
            with open(CACHE, "w", encoding="utf-8") as f:
                json.dump(cache, f, indent=2, ensure_ascii=False)

    report(cases, cache[mode], tag_types, mode)


def report(cases, answers, tag_types, mode):
    scored = [c for c in cases if c["id"] in answers]
    if not scored:
        print("\nNothing scored yet. Check LLM_PROVIDER and LLM_API_KEY in .env.")
        return

    hits = defaultdict(int)       # found and expected
    misses = defaultdict(int)     # expected, not found
    spurious = defaultdict(int)   # found, not expected
    arguable = defaultdict(int)   # found, not required, but defensible
    exact = lenient = 0
    sentiment_right = sentiment_total = 0
    forbidden_hits = []

    for case in scored:
        got = set(answers[case["id"]]["tags"])
        want = set(case["expect"])
        allowed = want | set(case.get("also_acceptable", []))
        if got == want:
            exact += 1
        if want <= got <= allowed:
            lenient += 1
        for t in tag_types:
            if t in want and t in got:
                hits[t] += 1
            elif t in want:
                misses[t] += 1
            elif t in got and t in allowed:
                arguable[t] += 1
            elif t in got:
                spurious[t] += 1
        for t in case.get("expect_not", []):
            if t in got:
                forbidden_hits.append((case["id"], t, case["note"]))
        if case.get("sentiment"):
            sentiment_total += 1
            if answers[case["id"]].get("sentiment") == case["sentiment"]:
                sentiment_right += 1

    def pct(n, d):
        return f"{n / d:.0%}" if d else "  -"

    print(f"\n=== tagging accuracy ({mode}, {len(scored)} of {len(cases)} cases) ===\n")
    print(f"  {'tag type':<22} {'found':>6} {'missed':>7} {'invented':>9} {'arguable':>9} "
          f"{'recall':>7} {'precision':>10}")
    for t in tag_types:
        found, missed, extra = hits[t], misses[t], spurious[t]
        print(f"  {t:<22} {found:>6} {missed:>7} {extra:>9} {arguable[t]:>9} "
              f"{pct(found, found + missed):>7} {pct(found, found + extra):>10}")

    total_hits, total_miss, total_extra = sum(hits.values()), sum(misses.values()), sum(spurious.values())
    print(f"\n  {'ALL TAGS':<22} {total_hits:>6} {total_miss:>7} {total_extra:>9} "
          f"{sum(arguable.values()):>9} "
          f"{pct(total_hits, total_hits + total_miss):>7} {pct(total_hits, total_hits + total_extra):>10}")
    print(f"\n  exactly right (every tag, no extras):   {exact}/{len(scored)}  {pct(exact, len(scored))}")
    print(f"  right, allowing judgement calls:        {lenient}/{len(scored)}  {pct(lenient, len(scored))}")
    if sentiment_total:
        print(f"  sentiment correct:                      {sentiment_right}/{sentiment_total}  "
              f"{pct(sentiment_right, sentiment_total)}")
    print("\n  'invented' is a tag nothing in the chat supports. 'arguable' is one the\n"
          "  wording defends but the case does not require - counted apart, not forgiven.")

    if forbidden_hits:
        print(f"\n  {len(forbidden_hits)} tag(s) the case says must NOT appear - these are the dangerous ones:")
        for cid, tag, note in forbidden_hits:
            print(f"    {cid}  {tag:<20} ({note})")
    else:
        print("\n  no forbidden tags - nothing invented on the trap cases")

    if len(scored) < len(cases):
        print(f"\n  {len(cases) - len(scored)} case(s) not yet run. Re-run to continue; answers are cached.")


if __name__ == "__main__":
    main()
