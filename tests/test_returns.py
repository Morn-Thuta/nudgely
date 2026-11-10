import io
import sys
import unittest
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from nudgely import returns as R  # noqa: E402

LOG = pd.DataFrame({
    "campaign_id": ["c1"] * 4, "sent_at": ["2026-08-03T10:00:00"] * 4,
    "customer_id": ["C001", "C002", "C003", "C004"], "name": list("ABCD"),
    "group": ["messaged", "messaged", "holdout", "holdout"], "platform": "", "status": "",
    "returned": "", "returned_at": "",
})


def purchases(rows, today="2026-11-10"):
    frame = pd.DataFrame(rows, columns=["who", "when"])
    return R.read_purchases(frame, "who", "when", today=today)


class CleaningTests(unittest.TestCase):
    def test_same_phone_written_differently_matches(self):
        for raw in ["+65 9123-4567", "6591234567", "91234567.0", "(65) 9123 4567", "91234567"]:
            self.assertEqual(R.clean_id(raw), "91234567", raw)
        self.assertEqual(R.clean_id(" c001 "), "C001")
        self.assertEqual(R.clean_id("nan"), "")

    def test_dates_are_day_first_except_year_first(self):
        for raw in ["2026-08-03", "03/08/2026", "3 Aug 2026", "3-8-2026", 46237, "46237"]:
            self.assertEqual(R.parse_date(raw), pd.Timestamp("2026-08-03"), raw)
        self.assertTrue(pd.isna(R.parse_date("32/13/2026")))
        self.assertTrue(pd.isna(R.parse_date("next Tuesday")))

    def test_bad_rows_are_kept_with_a_reason(self):
        good, bad = purchases([["C001", "5/8/2026"], ["", "5/8/2026"], ["C002", "junk"], ["C003", "2031-01-01"]])
        self.assertEqual(len(good), 1)
        self.assertEqual(bad["row"].tolist(), [3, 4, 5])      # spreadsheet rows, header is row 1
        self.assertIn("No customer", bad["problem"][0])
        self.assertIn("not readable", bad["problem"][1])
        self.assertIn("looks wrong", bad["problem"][2])


class MatchingTests(unittest.TestCase):
    def test_both_groups_are_marked_the_same_way(self):
        good, _ = purchases([["C099", "4/8/2026"], ["C001", "10/08/2026"], ["C003", "20/08/2026"], ["C099", "10/09/2026"]])
        res, unmatched = R.match_returns(LOG, good)
        self.assertEqual(res.came_back.tolist(), [1, 0, 1, 0])
        self.assertEqual(res.returned_at_new[0], "2026-08-10")
        self.assertEqual(unmatched.who.tolist(), ["C099", "C099"])

    def test_too_early_when_the_file_stops_inside_the_window(self):
        good, _ = purchases([["C099", "4/8/2026"], ["C001", "10/08/2026"]])
        res, _ = R.match_returns(LOG, good)
        self.assertEqual(res.came_back[0], 1)
        self.assertTrue(res.came_back[1:].isna().all())
        self.assertIn("Too early", res.evidence[1])

    def test_file_starting_weeks_after_the_send_settles_no_one_as_no(self):
        good, _ = purchases([["C001", "25/08/2026"], ["C099", "1/10/2026"]])
        res, _ = R.match_returns(LOG, good)
        self.assertEqual(res.came_back[0], 1)
        self.assertTrue(res.came_back[1:].isna().all())
        self.assertIn("include sales from the send date", res.evidence[1])

    def test_purchase_on_send_day_or_after_window_does_not_count(self):
        good, _ = purchases([["C001", "3/8/2026"], ["C002", "3/9/2026"], ["C004", "1/10/2026"]])
        res, _ = R.match_returns(LOG, good)
        self.assertEqual(res.came_back[:2].tolist(), [0, 0])

    def test_typo_is_flagged_not_lost(self):
        good, _ = purchases([["C0O2", "10/08/2026"], ["C001", "1/10/2026"]])
        _, unmatched = R.match_returns(LOG, good)
        self.assertIn("Probably C002", unmatched.check[0])

    def test_a_fix_can_turn_no_into_yes_but_not_back(self):
        log = LOG.assign(returned=["0", "1", "", ""], returned_at="")
        good, _ = purchases([["C099", "4/8/2026"], ["C001", "10/08/2026"], ["C004", "1/10/2026"]])
        res, _ = R.match_returns(log, good)
        updated, changed = R.apply_to_log(log, res)
        self.assertEqual(updated.returned.tolist(), [1, "1", 0, 0])
        self.assertEqual(changed, 3)


class SampleAndReportTests(unittest.TestCase):
    def test_sample_file_reproduces_the_example_campaign(self):
        sheets = R.read_file((ROOT / "data/examples/returns_sample.csv").read_bytes(), "returns_sample.csv")
        frame = sheets["file"]
        good, bad = R.read_purchases(frame, "Customer", "Date of purchase", today="2026-11-10")
        example = pd.read_csv(ROOT / "data/examples/campaign_log.csv")
        res, unmatched = R.match_returns(example.assign(returned="", returned_at=""), good)
        self.assertEqual(res.came_back.astype(int).tolist(), example.returned.tolist())
        self.assertEqual(len(bad), 3)
        self.assertEqual((unmatched.check != "").sum(), 1)

    def test_report_has_four_sheets_and_reads_back(self):
        good, bad = purchases([["C099", "4/8/2026"], ["C001", "10/08/2026"], ["", "x"], ["C099", "1/11/2026"]])
        res, unmatched = R.match_returns(LOG, good)
        data = R.report(res, bad, unmatched, "test.csv")
        book = pd.read_excel(io.BytesIO(data), sheet_name=None)
        self.assertEqual(list(book), ["Read me", "Campaign results", "Needs fixing", "Not in a campaign"])
        self.assertEqual(book["Campaign results"]["Came back"].tolist(), ["Yes", "No", "No", "No"])
        # the fixed report uploads again: the Excel reader keeps its sheets
        self.assertEqual(len(R.read_file(data, "fixed.xlsx")), 4)


    def test_fixed_needs_fixing_sheet_uploads_straight_back(self):
        frame = pd.DataFrame({"Customer": ["C099", "C0O2", "C001", "C003"],
                              "Date of purchase": ["4/8/2026", "10/08/2026", "32/13/2026", "1/10/2026"]})
        good, bad = R.read_purchases(frame, "Customer", "Date of purchase", today="2026-11-10")
        res, unmatched = R.match_returns(LOG, good)
        self.assertEqual(res.came_back.tolist(), [0, 0, 0, 0])
        data = R.report(res, bad, unmatched, "shop.csv", frame)
        sheet = R.read_file(data, "report.xlsx")["Needs fixing"]
        self.assertEqual(sheet["row"].tolist(), [3, 4])          # the typo and the bad date, original columns
        sheet["Customer"] = ["C002", "C001"]
        sheet["Date of purchase"] = ["10/08/2026", "12/8/2026"]
        who = R.guess_column(sheet.columns, R.WHO_HINTS)
        when = R.guess_column(sheet.columns, R.WHEN_HINTS)
        self.assertEqual((who, when), ("Customer", "Date of purchase"))
        fixed, still_bad = R.read_purchases(sheet, who, when, today="2026-11-10")
        self.assertTrue(still_bad.empty)
        # the fix only covers a few days, so it settles the two who bought and leaves the rest alone
        res2, _ = R.match_returns(LOG.assign(returned=["0", "0", "0", "0"]), fixed)
        updated, changed = R.apply_to_log(LOG.assign(returned=["0", "0", "0", "0"]), res2)
        self.assertEqual(updated.returned.tolist(), [1, 1, "0", "0"])
        self.assertEqual(changed, 2)


if __name__ == "__main__":
    unittest.main()
