"""The shop owner's whole loop, through the real API: sign up, upload sales, plan, write, approve,
rehearse, send for real, record who came back, see the result. Local store, fake AI, fake WhatsApp."""

import base64
import io
import os
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient  # noqa: E402

from api import main  # noqa: E402
from nudgely import shops, supabase_sync  # noqa: E402

SAMPLE = (ROOT / "data" / "examples" / "sales_sample.csv").read_bytes()
A, B = {"Authorization": "Bearer dev-owner-a"}, {"Authorization": "Bearer dev-owner-b"}


def upload(data, name="sales.csv"):
    return {"filename": name, "data_base64": base64.b64encode(data).decode()}


class FakeWhatsApp:
    def __init__(self, fail_for=()):
        self.sent, self.fail_for = [], set(fail_for)

    def send_template(self, to, name, language, params=None):
        if to in self.fail_for:
            raise RuntimeError("HTTP 400, code 131026: not a WhatsApp number")
        self.sent.append((to, name, language, params))


class OwnerFlowTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.patches = [
            patch.object(shops, "_store", shops.LocalStore(str(Path(self.tmp.name) / "shops.json"))),
            patch.object(supabase_sync, "enabled", return_value=False),
            patch.dict(os.environ, {"NUDGELY_DEV_AUTH": "1"}),
            # The AI writes a good sentence, except for one customer where it invents a price.
            patch.object(shops, "_ai_blank", side_effect=lambda shop, row, allowed:
                         "Fancy a basket of the new durians for $9?" if row["ref"].endswith("3412")
                         else "Shall we put some fresh durians aside for you?"),
        ]
        for p in self.patches:
            p.start()
        self.c = TestClient(main.app)

    def tearDown(self):
        for p in reversed(self.patches):
            p.stop()
        self.tmp.cleanup()

    def ok(self, method, path, headers=A, **kw):
        r = getattr(self.c, method)(path, headers=headers, **kw)
        self.assertLess(r.status_code, 300, f"{path}: {r.status_code} {r.text[:300]}")
        return r.json()

    def write_all(self, cid):
        """The page asks again until every message is written; so do the tests."""
        for _ in range(50):
            camp = self.ok("post", f"/api/owner/campaigns/{cid}/write")
            if all(r["message"] for r in camp["rows"] if r["group"] == "messaged"):
                return camp
        self.fail("messages never finished writing")

    def make_shop(self):
        self.ok("post", "/api/owner/shop", json={"name": "Ah Seng Provision"})
        self.ok("post", "/api/owner/settings", json={"offer": "10% off your next basket",
                                                     "note": "Fresh durians came in this week"})
        return self.ok("post", "/api/owner/sales", json=upload(SAMPLE))

    def test_sign_in_is_required_and_dev_bypass_needs_the_flag(self):
        self.assertEqual(self.c.get("/api/owner/shop").status_code, 401)
        with patch.dict(os.environ, {"NUDGELY_DEV_AUTH": "0"}):
            self.assertEqual(self.c.get("/api/owner/shop", headers=A).status_code, 503)
        self.assertIsNone(self.ok("get", "/api/owner/shop")["shop"])

    def test_dev_bypass_never_works_once_supabase_is_set_up(self):
        with patch.object(supabase_sync, "enabled", return_value=True), \
                patch.object(supabase_sync, "_config", return_value=("https://x.supabase.co", "k")), \
                patch("api.owner.requests.get") as get:
            get.return_value.ok, get.return_value.json = False, lambda: {}
            self.assertEqual(self.c.get("/api/owner/shop", headers=A).status_code, 401)

    def test_shop_setup_and_sales_upload(self):
        saved = self.make_shop()
        self.assertEqual(saved["saved"], 48)
        shop = self.ok("get", "/api/owner/shop")["shop"]
        self.assertEqual((shop["customers"], shop["persuadable"]), (48, 17))
        self.assertIn("Ah Seng Provision", shop["template_text"])
        self.assertFalse(shop["whatsapp_connected"])
        customers = self.ok("get", "/api/owner/customers")["customers"]
        self.assertTrue(all("phone" not in c and c["ref"].startswith("••••") for c in customers))
        self.assertEqual(self.c.post("/api/owner/shop", headers=A, json={"name": "Again"}).status_code, 409)
        self.assertEqual(self.c.post("/api/owner/settings", headers=A,
                                     json={"offer": "20% off everything"}).status_code, 400)
        # a re-upload updates the same customers rather than duplicating them
        self.ok("post", "/api/owner/sales", json=upload(SAMPLE))
        self.assertEqual(len(self.ok("get", "/api/owner/customers")["customers"]), 48)

    def test_one_shop_never_sees_another(self):
        self.make_shop()
        camp = self.ok("post", "/api/owner/campaigns", json={"size": 5})
        self.assertEqual(self.c.get("/api/owner/customers", headers=B).status_code, 404)
        self.assertIsNone(self.ok("get", "/api/owner/shop", headers=B)["shop"])
        self.ok("post", "/api/owner/shop", headers=B, json={"name": "Other Mart"})
        self.assertEqual(self.c.get(f"/api/owner/campaigns/{camp['id']}", headers=B).status_code, 404)
        self.assertEqual(self.c.post(f"/api/owner/campaigns/{camp['id']}/send", headers=B,
                                     json={"live": False}).status_code, 404)

    def test_writing_goes_in_batches_so_no_request_runs_long(self):
        self.make_shop()
        camp = self.ok("post", "/api/owner/campaigns", json={"holdout_pct": 0})
        first = self.ok("post", f"/api/owner/campaigns/{camp['id']}/write")
        written = [r for r in first["rows"] if r["message"]]
        self.assertEqual(len(written), shops.WRITE_BATCH)
        self.assertEqual(len(self.write_all(camp["id"])["rows"]), 17)

    def test_plan_write_edit_approve_rehearse(self):
        self.make_shop()
        camp = self.ok("post", "/api/owner/campaigns", json={"size": 10, "holdout_pct": 20})
        groups = [r["group"] for r in camp["rows"]]
        self.assertEqual((groups.count("messaged"), groups.count("holdout")), (8, 2))
        self.assertTrue(all(r["label"] == "Persuadable" for r in camp["rows"]))

        camp = self.write_all(camp["id"])
        written = [r for r in camp["rows"] if r["group"] == "messaged"]
        self.assertTrue(all(r["message"].endswith("Reply STOP to opt out") for r in written))
        self.assertTrue(all("Ah Seng Provision" in r["message"] and r["since"] in r["message"] for r in written))
        self.assertTrue(all(len(r["message"]) <= 300 and r["problems"] == [] for r in written))
        invented = [r for r in written if r["ref"].endswith("3412")]
        if invented:  # the AI's made-up $9 was thrown away for the plain sentence
            self.assertEqual(invented[0]["source"], "template")
            self.assertNotIn("$9", invented[0]["message"])

        row = written[0]
        bad = self.ok("post", f"/api/owner/campaigns/{camp['id']}/rows/{row['id']}",
                      json={"blank": "Get 50% off today!"})
        edited = next(r for r in bad["rows"] if r["id"] == row["id"])
        self.assertTrue(edited["problems"])
        self.assertEqual(self.c.post(f"/api/owner/campaigns/{camp['id']}/rows/{row['id']}", headers=A,
                                     json={"approved": True}).status_code, 400)
        self.ok("post", f"/api/owner/campaigns/{camp['id']}/rows/{row['id']}",
                json={"blank": "Would you like us to keep some durians for you?"})

        self.assertEqual(self.c.post(f"/api/owner/campaigns/{camp['id']}/send", headers=A,
                                     json={"live": False}).status_code, 400)  # nothing approved yet
        self.ok("post", f"/api/owner/campaigns/{camp['id']}/approve-all")
        sent = self.ok("post", f"/api/owner/campaigns/{camp['id']}/send", json={"live": False})
        self.assertEqual((sent["status"], sent["mode"]), ("sent", "rehearsal"))
        self.assertTrue(all(r["status"] == "simulated" for r in sent["rows"] if r["group"] == "messaged"))
        self.assertTrue(all(r["status"] == "not messaged" for r in sent["rows"] if r["group"] == "holdout"))
        self.assertEqual(self.c.post(f"/api/owner/campaigns/{camp['id']}/write", headers=A).status_code, 409)

    def test_live_send_uses_the_shops_own_number_and_template(self):
        self.make_shop()
        camp = self.ok("post", "/api/owner/campaigns", json={"size": 4, "holdout_pct": 25})
        self.write_all(camp["id"])
        self.ok("post", f"/api/owner/campaigns/{camp['id']}/approve-all")
        r = self.c.post(f"/api/owner/campaigns/{camp['id']}/send", headers=A, json={"live": True})
        self.assertEqual(r.status_code, 400)
        self.assertIn("Connect your WhatsApp", r.json()["detail"])

        shop = self.ok("post", "/api/owner/settings", json={"whatsapp": {
            "wa_token": "secret-token", "wa_phone_number_id": "123", "template_name": "win_back"}})["shop"]
        self.assertTrue(shop["whatsapp_connected"])
        self.assertNotIn("secret-token", str(shop))                     # the token is never served back

        phones = [x["phone"] for x in shops.store().select("campaign_rows", campaign_id=camp["id"])
                  if x["group"] == "messaged"]
        fake = FakeWhatsApp(fail_for=phones[:1])
        with patch.object(shops, "_whatsapp", return_value=fake):
            sent = self.ok("post", f"/api/owner/campaigns/{camp['id']}/send", json={"live": True})
        statuses = sorted(r["status"] for r in sent["rows"] if r["group"] == "messaged")
        self.assertEqual(statuses, ["failed", "sent", "sent"])
        to, name, lang, params = fake.sent[0]
        self.assertEqual((name, lang), ("win_back", "en"))
        self.assertEqual(len(params), 2)                               # {{1}} since, {{2}} the sentence

    def test_returns_measure_messaged_against_kept_back(self):
        self.make_shop()
        camp = self.ok("post", "/api/owner/campaigns", json={"holdout_pct": 30})
        cid = camp["id"]
        self.write_all(cid)
        self.ok("post", f"/api/owner/campaigns/{cid}/approve-all")
        self.ok("post", f"/api/owner/campaigns/{cid}/send", json={"live": False})
        sent_at = datetime.now(timezone.utc) - timedelta(days=40)
        shops.store().update("shop_campaigns", {"id": cid}, {"sent_at": sent_at.isoformat()})

        rows = shops.store().select("campaign_rows", campaign_id=cid)
        messaged = [r["phone"] for r in rows if r["group"] == "messaged"]
        held = [r["phone"] for r in rows if r["group"] == "holdout"]
        day = lambda n: (sent_at + timedelta(days=n)).strftime("%d/%m/%Y")  # noqa: E731
        sales = [{"Mobile": "+65 " + p, "Date": day(5), "Total": "$20"} for p in messaged[:6]]
        sales += [{"Mobile": held[0], "Date": day(10), "Total": "$9"}]
        sales += [{"Mobile": "99999999", "Date": day(1), "Total": "$5"}]    # file starts right after the send
        sales += [{"Mobile": "99999999", "Date": day(35), "Total": "$5"}]   # and runs past the window
        sales += [{"Mobile": "", "Date": day(3), "Total": "$1"}]            # unreadable row, counted
        buf = io.BytesIO()
        pd.DataFrame(sales).to_excel(buf, index=False)

        out = self.ok("post", f"/api/owner/campaigns/{cid}/returns", json=upload(buf.getvalue(), "after.xlsx"))
        res = out["results"]
        self.assertEqual((res["messaged"], res["kept_back"]), (len(messaged), len(held)))
        self.assertEqual((res["messaged_back"], res["kept_back_back"]), (6, 1))
        self.assertEqual(res["waiting"], 0)
        self.assertLessEqual(res["low"], res["difference"])
        self.assertIn(res["verdict"], ("worked", "did not help", "too early to call"))
        self.assertEqual(out["upload"]["unreadable_rows"], 1)


class BlankCheckTests(unittest.TestCase):
    def test_numbers_prices_and_discounts_must_come_from_the_owner(self):
        offer, note = "10% off your next basket", "Fresh durians came in this week"
        self.assertEqual(shops.check_blank("Shall we keep some durians for you?", "Persuadable", offer, note), [])
        self.assertTrue(shops.check_blank("Durians are $9 today, want some?", "Persuadable", offer, note))
        self.assertTrue(shops.check_blank("Enjoy 10% off - see you soon?", "Sure Thing", offer, note))
        self.assertTrue(shops.check_blank("We have durians.", "Persuadable", offer, note))   # no question
        self.assertEqual(shops.check_blank("Enjoy 10% off your next basket?", "Persuadable", offer, note), [])

    def test_since_reads_naturally(self):
        self.assertEqual([shops._since(d) for d in (2, 9, 21, 45, 70, 200)],
                         ["a few days", "a week", "3 weeks", "6 weeks", "2 months", "7 months"])


if __name__ == "__main__":
    unittest.main()
