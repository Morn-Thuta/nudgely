"""Supabase mode (NUDGELY_STORE=supabase) against a tiny in-memory fake of PostgREST."""

import json
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch
from urllib.parse import parse_qsl, urlparse

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from nudgely import bot, conversations, remote_store  # noqa: E402

ENV = {"NUDGELY_STORE": "supabase", "SUPABASE_URL": "https://x.supabase.co",
       "SUPABASE_SERVICE_KEY": "k", "KEY_SALT": "salt"}


class FakePostgrest:
    def __init__(self):
        self.t = {"customers": [], "messages": [], "tags": []}

    def _match(self, row, params):
        for col, cond in params.items():
            if col in ("select", "order", "limit", "on_conflict"):
                continue
            op, _, val = cond.partition(".")
            v = row.get(col)
            if op == "eq" and str(v) != val:
                return False
            if op == "like" and not str(v).startswith(val.rstrip("*")):
                return False
            if op == "in" and str(v) not in val.strip("()").split(","):
                return False
        return True

    def __call__(self, method, url, json=None, timeout=None, headers=None):  # noqa: A002 - mirrors requests
        u = urlparse(url)
        table = u.path.split("/rest/v1/")[1]
        params = dict(parse_qsl(u.query))
        rows = self.t[table]
        r = MagicMock()
        if method == "GET":
            out = [x for x in rows if self._match(x, params)]
            if params.get("order", "").endswith(".desc"):
                out = list(reversed(out))
            out = out[: int(params.get("limit", 10 ** 6))]
            r.status_code, r.text = 200, "x"
            r.json.return_value = [dict(x) for x in out]
        elif method == "POST":
            new = json if isinstance(json, list) else [json]
            for row in new:
                if table == "customers" and any(c["id"] == row["id"] for c in rows):
                    existing = next(c for c in rows if c["id"] == row["id"])
                    if "merge-duplicates" in (headers or {}).get("Prefer", ""):
                        existing.update(row)
                        continue
                    r.status_code, r.text = 409, "dup"
                    return r
                base = {"memory": {}, "seen_ids": [], "msg_count": 0, "replied": False, "opted_out": False,
                        "handover": False, "label": "New", "created_at": "2026-11-11T00:00:00Z"} if table == "customers" else {"created_at": f"2026-11-11T00:00:{len(rows):02d}Z"}
                rows.append({**base, **row})
            r.status_code, r.text = 201, "x"
            r.json.return_value = [dict(rows[-1])]
        elif method == "PATCH":
            for x in rows:
                if self._match(x, params):
                    x.update(json)
            r.status_code, r.text = 204, ""
        elif method == "DELETE":
            gone = {x["id"] for x in rows if self._match(x, params)}
            self.t[table] = [x for x in rows if not self._match(x, params)]
            if table == "customers":
                self.t["messages"] = [m for m in self.t["messages"] if m["customer_id"] not in gone]
            r.status_code, r.text = 204, ""
        return r


class RemoteStoreTests(unittest.TestCase):
    def setUp(self):
        self.db = FakePostgrest()
        self.patches = [patch.dict(os.environ, ENV),
                        patch("nudgely.remote_store.requests.request", side_effect=self.db),
                        patch("nudgely.supabase_sync.requests.post",
                              side_effect=lambda url, json=None, timeout=None, headers=None: self.db("POST", url, json, timeout, headers)),
                        patch("nudgely.llm.tag_message", return_value={"tags": [
                            {"type": "product_interest", "value": "durian", "evidence": "durian"}]}),
                        patch("nudgely.reply.answer", return_value={"reply": "Yes, durian is in!", "handover": False,
                                                                    "reason": "ok"})]
        for p in self.patches:
            p.start()

    def tearDown(self):
        for p in reversed(self.patches):
            p.stop()

    def test_number_is_never_stored(self):
        bot.handle("6591234567", "Aisha", "durian?", prefix="WA")
        self.assertNotIn("6591234567", json.dumps(self.db.t))
        self.assertEqual(len(self.db.t["customers"][0]["key_hash"]), 64)

    def test_history_survives_between_turns(self):
        bot.handle("web:abc12345", "Judge", "durian?", prefix="WEB")
        rec = conversations.get_or_create("web:abc12345", prefix="WEB")
        self.assertEqual(rec["customer_id"], "WEB001")
        self.assertEqual([m["from"] for m in rec["chat"]], ["customer", "store"])
        self.assertEqual(rec["msg_count"], 1)
        self.assertTrue(rec["replied"])
        self.assertEqual(rec["tags"]["tags"][0]["value"], "durian")

    def test_ids_per_channel_and_same_person_same_id(self):
        a = bot.handle("web:aaaaaaaa", "", "hi", prefix="WEB")["customer_id"]
        b = bot.handle("web:bbbbbbbb", "", "hi", prefix="WEB")["customer_id"]
        c = bot.handle("6591234567", "", "hi", prefix="WA")["customer_id"]
        again = bot.handle("web:aaaaaaaa", "", "hi again", prefix="WEB")["customer_id"]
        self.assertEqual((a, b, c, again), ("WEB001", "WEB002", "WA001", "WEB001"))

    def test_cap_and_duplicates(self):
        for i in range(3):
            bot.handle("web:capcap01", "", f"m{i}", prefix="WEB", max_messages=3)
        self.assertTrue(bot.handle("web:capcap01", "", "one more", prefix="WEB", max_messages=3)["limited"])
        bot.handle("6599999999", "", "hi", msg_id="wamid.1")
        self.assertTrue(bot.handle("6599999999", "", "hi", msg_id="wamid.1")["duplicate"])

    def test_handover_resolve_and_reset(self):
        with patch("nudgely.reply.answer", return_value={"reply": "A person will follow up.", "handover": True,
                                                          "reason": "asked"}):
            cid = bot.handle("web:hand0001", "", "HUMAN", prefix="WEB")["customer_id"]
        self.assertTrue(conversations.all_customers()[cid]["handover"])
        conversations.set_handover(cid, False)
        self.assertFalse(conversations.all_customers()[cid]["handover"])
        conversations.reset()
        self.assertEqual(conversations.all_customers(), {})

    def test_missing_salt_fails_loudly(self):
        with patch.dict(os.environ, {"KEY_SALT": ""}):
            with self.assertRaises(remote_store.RemoteStoreError):
                remote_store.key_hash("x")


if __name__ == "__main__":
    unittest.main()
