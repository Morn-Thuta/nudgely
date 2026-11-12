import os
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from nudgely import supabase_sync  # noqa: E402

REC = {"customer_id": "WA001", "name": "Aisha Tan", "label": "New", "handover": True, "opted_out": False,
       "chat": [{"from": "customer", "text": "Is oat milk back?"}, {"from": "store", "text": "Someone will follow up."}]}


class SyncTests(unittest.TestCase):
    def test_off_without_keys(self):
        with patch.dict(os.environ, {"SUPABASE_URL": "", "SUPABASE_SERVICE_KEY": ""}), \
                patch("nudgely.supabase_sync.http") as post:
            supabase_sync.sync(REC, REC["chat"], [], wait=True)
            post.assert_not_called()

    def test_writes_customer_messages_and_tags(self):
        ok = MagicMock(status_code=201, text="")
        tags = [{"type": "restock_request", "value": "oat milk", "evidence": "oat milk"}]
        with patch.dict(os.environ, {"SUPABASE_URL": "https://x.supabase.co", "SUPABASE_SERVICE_KEY": "k"}), \
                patch("nudgely.supabase_sync.http", return_value=ok) as post:
            supabase_sync.sync(REC, REC["chat"], tags, handover_reply=True, wait=True)
        calls = {c.args[1].split("/rest/v1/")[1]: c.kwargs["json"] for c in post.call_args_list}
        cust = calls["customers"][0]
        self.assertEqual((cust["id"], cust["channel"], cust["handover"]), ("WA001", "whatsapp", True))
        self.assertNotIn("6591234567", str(calls))  # no phone numbers ever
        self.assertEqual([m["sender"] for m in calls["messages"]], ["customer", "store"])
        self.assertEqual([m["handover"] for m in calls["messages"]], [False, True])
        self.assertEqual(calls["tags?on_conflict=customer_id,type,value"][0]["value"], "oat milk")

    def test_failure_never_raises(self):
        with patch.dict(os.environ, {"SUPABASE_URL": "https://x.supabase.co", "SUPABASE_SERVICE_KEY": "k"}), \
                patch("nudgely.supabase_sync.http", side_effect=OSError("down")):
            supabase_sync.sync(REC, REC["chat"], [], wait=True)  # logs, does not raise


if __name__ == "__main__":
    unittest.main()
