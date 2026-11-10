import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from nudgely import conversations  # noqa: E402

spec = importlib.util.spec_from_file_location("whatsapp_webhook", ROOT / "scripts" / "whatsapp_webhook.py")
hook = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hook)


def msg(text, mid="m1"):
    return {"id": mid, "from": "6591234567", "name": "Aisha Tan", "timestamp": "1", "type": "text", "text": text}


class BotTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = patch.object(conversations, "STORE", str(Path(self.tmp.name) / "wa.json"))
        self.store.start()
        self.wa = MagicMock()
        self.tag = patch("nudgely.llm.tag_message", return_value={"customer_id": "WA001", "tags": [
            {"type": "restock_request", "value": "oat milk", "evidence": "oat milk", "date": ""}]})
        self.answer = patch("nudgely.reply.answer", return_value={"reply": "Hi Aisha! Let me check.",
                                                                  "handover": False, "reason": "ok"})
        self.tag_mock, self.answer_mock = self.tag.start(), self.answer.start()

    def tearDown(self):
        self.tag.stop()
        self.answer.stop()
        self.store.stop()
        self.tmp.cleanup()

    def sent(self):
        return [c.args[1] for c in self.wa.send_text.call_args_list]

    def test_normal_message_is_tagged_and_answered(self):
        hook.bot_turn(self.wa, msg("is oat milk back?"))
        self.assertEqual(self.sent(), ["Hi Aisha! Let me check."])
        rec = conversations.all_customers()["6591234567"]
        self.assertEqual(rec["tags"]["tags"][0]["value"], "oat milk")
        self.assertEqual(rec["label"], "New")  # never Persuadable by default: no discounts
        self.assertTrue(rec["replied"])
        self.assertEqual([m["from"] for m in rec["chat"]], ["customer", "store"])
        self.assertEqual(self.answer_mock.call_args.args[0]["name"], "Aisha")  # first name only

    def test_duplicate_delivery_answered_once(self):
        hook.bot_turn(self.wa, msg("hi", "same"))
        hook.bot_turn(self.wa, msg("hi", "same"))
        self.assertEqual(len(self.sent()), 1)

    def test_stop_then_silence_then_start(self):
        hook.bot_turn(self.wa, msg("STOP", "a"))
        self.assertIn("won't get any more messages", self.sent()[0])
        hook.bot_turn(self.wa, msg("is oat milk back?", "b"))
        self.assertEqual(len(self.sent()), 1)  # opted out: no automatic answer
        self.answer_mock.assert_not_called()
        hook.bot_turn(self.wa, msg("start", "c"))
        self.assertIn("Welcome back", self.sent()[-1])
        self.assertFalse(conversations.all_customers()["6591234567"]["opted_out"])

    def test_media_message_flagged_for_person(self):
        m = msg("", "img")
        m["type"] = "image"
        hook.bot_turn(self.wa, m)
        self.assertEqual(self.sent(), [])
        self.assertTrue(conversations.all_customers()["6591234567"]["handover"])

    def test_tagging_failure_still_replies(self):
        self.tag_mock.side_effect = RuntimeError("LLM down")
        hook.bot_turn(self.wa, msg("hello"))
        self.assertEqual(len(self.sent()), 1)


if __name__ == "__main__":
    unittest.main()
