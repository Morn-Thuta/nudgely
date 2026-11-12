import base64
import io
import sys
import unittest
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from nudgely import shop_scores as S  # noqa: E402

SAMPLE = (ROOT / "data" / "examples" / "sales_sample.csv").read_bytes()


def b64(data):
    return base64.b64encode(data).decode()


class ScoreUploadTests(unittest.TestCase):
    def test_sample_shop_matches_the_command_line_scorer(self):
        out = S.score_upload(SAMPLE, "sales_sample.csv")
        self.assertEqual(out["summary"]["customers"], 48)
        self.assertEqual((out["summary"]["persuadable"], out["summary"]["sure_thing"],
                          out["summary"]["lost_cause"]), (17, 13, 18))
        ups = [c["uplift"] for c in out["customers"]]
        self.assertEqual(ups, sorted(ups, reverse=True))            # best to message first
        top = out["customers"][0]
        self.assertAlmostEqual(top["p_msg"] - top["p_no_msg"], top["uplift"], delta=0.02)
        self.assertEqual(out["columns"], {"phone": "phone", "date": "date", "amount": "amount"})

    def test_messy_till_export_is_read(self):
        sample = pd.read_csv(io.BytesIO(SAMPLE), dtype=str)
        messy = pd.DataFrame({
            "Mobile No": "+65 " + sample.phone.str[:4] + " " + sample.phone.str[4:],
            "Date of purchase": pd.to_datetime(sample.date).dt.strftime("%d/%m/%Y"),
            "Total (SGD)": "$" + sample.amount,
        })
        messy.loc[0, "Date of purchase"] = "not a date"
        messy.loc[1, "Mobile No"] = ""
        messy.loc[2, "Total (SGD)"] = "free"
        out = S.score_upload(messy.to_csv(index=False).encode(), "till.csv")
        self.assertEqual(out["dropped"], {"date not readable": 1, "no phone or member id": 1,
                                          "amount not a number": 1})
        self.assertEqual(out["rows_used"], len(sample) - 3)
        self.assertEqual(out["summary"]["customers"], 48)            # same shop, read the same way

    def test_excel_upload(self):
        frame = pd.read_csv(io.BytesIO(SAMPLE))
        buf = io.BytesIO()
        frame.to_excel(buf, index=False)
        out = S.score_upload(buf.getvalue(), "sales.xlsx")
        self.assertEqual(out["summary"]["customers"], 48)

    def test_problems_the_owner_can_fix_are_explained(self):
        with self.assertRaisesRegex(S.ScoreError, "Rename them to phone, date and amount"):
            S.score_upload(b"name,when\nA,2025-01-01\n", "x.csv")
        with self.assertRaisesRegex(S.ScoreError, "at least 5"):
            S.score_upload(b"phone,date,amount\n91234567,2025-01-01,5\n", "x.csv")
        with self.assertRaisesRegex(S.ScoreError, "under 2 MB"):
            S.score_upload(b"x" * (S.MAX_BYTES + 1), "x.csv")


class ScoreEndpointTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from fastapi.testclient import TestClient

        from api import main
        cls.main = main
        cls.client = TestClient(main.app)

    def setUp(self):
        self.main._score_hits.clear()

    def post(self, data, name="sales.csv", ip="1.2.3.4"):
        return self.client.post("/api/shop/score", json={"filename": name, "data_base64": b64(data)},
                                headers={"x-forwarded-for": ip})

    def test_scores_without_a_login(self):
        r = self.post(SAMPLE)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["summary"]["persuadable"], 17)

    def test_owner_mistakes_come_back_as_400_with_the_reason(self):
        r = self.post(b"name,when\nA,2025-01-01\n")
        self.assertEqual(r.status_code, 400)
        self.assertIn("Rename them", r.json()["detail"])
        r = self.client.post("/api/shop/score", json={"filename": "x.csv", "data_base64": "@@not base64@@"})
        self.assertEqual(r.status_code, 400)

    def test_one_visitor_is_rate_limited_others_are_not(self):
        tiny = b"phone,date,amount\n1,bad,1\n"
        codes = [self.post(tiny, ip="9.9.9.9").status_code for _ in range(self.main.SCORE_MAX + 1)]
        self.assertEqual(codes[-1], 429)
        self.assertEqual(self.post(tiny, ip="8.8.8.8").status_code, 400)  # someone else still gets in


if __name__ == "__main__":
    unittest.main()
