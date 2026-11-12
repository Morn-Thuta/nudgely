"""Live campaign send: allow-list, 24-hour window, linking the phone to the demo customer, team-only API."""

import os
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fastapi.testclient import TestClient  # noqa: E402

from api import main  # noqa: E402
from nudgely import bot, live_send, remote_store  # noqa: E402
sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_remote_store import ENV, FakePostgrest  # noqa: E402

PHONE = "6591234567"
NOW = datetime(2026, 11, 11, 12, 0, tzinfo=timezone.utc)  # fake messages are stamped 2026-11-11T00:00


class LiveSendTests(unittest.TestCase):
    def setUp(self):
        self.db = FakePostgrest()
        self.db.t["customers"].append({"id": "C001", "channel": "demo", "name": "Aisha Rahman", "label": "Persuadable",
                                       "memory": {}, "seen_ids": [], "msg_count": 0, "replied": False,
                                       "opted_out": False, "handover": False, "key_hash": None})
        self.db.t["tags"].append({"customer_id": "C001", "type": "restock_request", "value": "oat milk",
                                  "evidence": "oat milk back?", "created_at": "2026-10-20T00:00:00Z"})
        self.patches = [patch.dict(os.environ, {**ENV, "LIVE_RECIPIENTS": f'{{"C001": "+65 9123 4567"}}'}),
                        patch("nudgely.supabase_sync.http", side_effect=self.db),
                        patch("nudgely.llm.tag_message", return_value={"tags": []}),
                        patch("nudgely.reply.answer", return_value={"reply": "Yes, oat milk is in!",
                                                                    "handover": False, "reason": "ok"})]
        for p in self.patches:
            p.start()
        self.wa = MagicMock()
        self.wa.send_text.return_value = {"messages": [{"id": "wamid.X"}]}

    def tearDown(self):
        for p in reversed(self.patches):
            p.stop()

    def open_window(self):
        bot.handle(PHONE, "Dythan", "hi", prefix="WA")  # the demo phone messages the shop first

    def test_only_allow_listed_customers(self):
        with self.assertRaises(live_send.SendError) as e:
            live_send.send("C002", "Hello", wa=self.wa, now=NOW)
        self.assertEqual(e.exception.status, 403)
        self.wa.send_text.assert_not_called()

    def test_refuses_outside_24h_window(self):
        with self.assertRaises(live_send.SendError) as e:
            live_send.send("C001", "Hi Aisha", wa=self.wa, now=NOW)
        self.assertEqual(e.exception.status, 409)
        self.wa.send_text.assert_not_called()

    def test_sends_links_phone_and_reply_has_history(self):
        self.open_window()
        out = live_send.send("C001", "Hi Aisha, oat milk is back!", wa=self.wa, now=NOW)
        self.assertEqual(out["message_id"], "wamid.X")
        to, text = self.wa.send_text.call_args.args
        self.assertEqual(to, "+65 9123 4567")
        self.assertTrue(text.endswith("Reply STOP to opt out"))
        aisha = next(c for c in self.db.t["customers"] if c["id"] == "C001")
        self.assertEqual(aisha["key_hash"], remote_store.key_hash(PHONE))
        self.assertEqual(aisha["memory"]["tags"][0]["value"], "oat milk")
        self.assertIn(text, [m["text"] for m in self.db.t["messages"] if m["customer_id"] == "C001"])
        # The phone's reply now lands on C001, with the nudge in its history.
        self.assertEqual(bot.handle(PHONE, "Dythan", "is it really back?", prefix="WA")["customer_id"], "C001")

    def test_opted_out_customer_is_never_sent(self):
        self.open_window()
        next(c for c in self.db.t["customers"] if c["id"] == "C001")["opted_out"] = True
        with self.assertRaises(live_send.SendError) as e:
            live_send.send("C001", "Hi", wa=self.wa, now=NOW)
        self.assertEqual(e.exception.status, 409)

    def test_api_needs_a_team_sign_in(self):
        client = TestClient(main.app)
        body = {"customer_id": "C001", "message": "Hi"}
        self.assertEqual(client.post("/api/campaign/send", json=body).status_code, 401)
        not_team = MagicMock(ok=True, json=lambda: {"id": "u1", "app_metadata": {}})
        with patch("requests.get", return_value=not_team):
            r = client.post("/api/campaign/send", json=body, headers={"Authorization": "Bearer t"})
            self.assertEqual(r.status_code, 403)
        team = MagicMock(ok=True, json=lambda: {"id": "u2", "app_metadata": {"nudgely_team": True}})
        with patch("requests.get", return_value=team):
            self.assertEqual(client.get("/api/campaign/live", headers={"Authorization": "Bearer t"}).json(),
                             {"customer_ids": ["C001"]})


if __name__ == "__main__":
    unittest.main()
