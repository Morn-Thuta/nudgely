import importlib.util
import json
import sys
import tempfile
import threading
import time
import unittest
from datetime import datetime, timedelta
from http.server import HTTPServer
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from nudgely import conversation as C  # noqa: E402
from nudgely.reply import HOLDING  # noqa: E402

NOW = datetime(2026, 11, 11, 10, 0, 0)


def msg(text, mid, number="6591234567", kind="text", name="Aisha"):
    return {"id": mid, "from": number, "name": name, "timestamp": "1762840000", "type": kind, "text": text}


class Bot:
    """Fakes for the tagger, the reply writer and the sender, recording every call."""

    def __init__(self, reply="Yes, oat milk is back in stock today!", handover=False, tag_fails=False):
        self.sent, self.answered, self.tagged = [], [], []
        self.reply, self.handover, self.tag_fails = reply, handover, tag_fails

    def tag(self, cid, text, date, prior, names):
        self.tagged.append((cid, text, names))
        if self.tag_fails:
            raise RuntimeError("rate limited")
        return {"customer_id": cid, "tags": [{"type": "product_interest", "value": "oat milk",
                                              "evidence": "oat milk"}], "sentiment": "positive"}

    def answer(self, customer, chat, text, tags, first_reply):
        self.answered.append({"customer": dict(customer), "chat": list(chat), "text": text,
                              "tags": tags, "first_reply": first_reply})
        return {"reply": self.reply, "handover": self.handover, "reason": "asked for a refund" if self.handover else ""}

    def send(self, number, text):
        self.sent.append((number, text))


class ConversationTests(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.store = C.Store(str(Path(self.dir.name) / "conv.json"))

    def tearDown(self):
        self.dir.cleanup()

    def run_msg(self, bot, m, now=NOW, **kw):
        return C.handle(m, self.store, bot.tag, bot.answer, bot.send, now=now, **kw)

    def test_new_customer_is_tagged_answered_and_remembered(self):
        bot = Bot()
        out = self.run_msg(bot, msg("Is oat milk back?", "m1"))
        self.assertEqual(out["action"], "replied")
        self.assertEqual(out["tags_added"], 1)
        self.assertEqual(bot.sent, [("6591234567", bot.reply)])
        self.assertTrue(bot.answered[0]["first_reply"])
        self.assertEqual(bot.answered[0]["customer"]["label"], "")        # unknown: no discounts
        self.assertNotIn("6591234567", bot.answered[0]["customer"]["customer_id"])
        saved = C.Store(self.store.path).get("6591234567")                # survives a restart
        self.assertEqual([m["from"] for m in saved["chat"]], ["customer", "store"])
        self.assertEqual(saved["tags"]["tags"][0]["value"], "oat milk")

    def test_second_message_sees_the_history_and_drops_the_first_reply_footer(self):
        bot = Bot()
        self.run_msg(bot, msg("Is oat milk back?", "m1"))
        self.run_msg(bot, msg("Great, how much?", "m2"))
        second = bot.answered[1]
        self.assertFalse(second["first_reply"])
        self.assertEqual([m["text"] for m in second["chat"]], ["Is oat milk back?", bot.reply])

    def test_a_retried_delivery_gets_no_second_reply(self):
        bot = Bot()
        self.run_msg(bot, msg("Is oat milk back?", "m1"))
        out = self.run_msg(bot, msg("Is oat milk back?", "m1"))
        self.assertEqual(out["action"], "duplicate, ignored")
        self.assertEqual(len(bot.sent), 1)

    def test_stop_is_honoured_without_the_model_and_silences_the_bot(self):
        bot = Bot()
        out = self.run_msg(bot, msg("STOP", "m1"))
        self.assertEqual(out["action"], "opted out")
        self.assertEqual(bot.sent, [("6591234567", C.STOPPED)])
        self.assertEqual(bot.tagged, [])
        self.assertEqual(bot.answered, [])
        out = self.run_msg(bot, msg("do you have durian?", "m2"))
        self.assertEqual(out["action"], "opted out earlier, no reply")
        self.assertEqual(len(bot.sent), 1)
        self.assertEqual(bot.tagged, [])                                   # not profiled after STOP
        self.run_msg(bot, msg("start", "m3"))
        self.assertEqual(bot.sent[-1][1], C.RESTARTED)
        self.run_msg(bot, msg("do you have durian?", "m4"))
        self.assertEqual(len(bot.answered), 1)

    def test_after_a_handover_the_bot_stays_quiet_until_cleared_or_expired(self):
        bot = Bot(reply=HOLDING, handover=True)
        out = self.run_msg(bot, msg("I want a refund", "m1"))
        self.assertTrue(out["handover"])
        bot.handover, bot.reply = False, "Sure!"
        out = self.run_msg(bot, msg("hello??", "m2", ), now=NOW + timedelta(hours=1))
        self.assertEqual(out["action"], "with a person, bot quiet")
        self.assertEqual(len(bot.sent), 1)
        self.assertEqual(len(bot.tagged), 2)                               # still remembered
        self.assertTrue(self.store.clear_handover("6591234567"))
        self.assertEqual(self.run_msg(bot, msg("hello?", "m3"), now=NOW + timedelta(hours=2))["action"], "replied")
        bot.reply, bot.handover = HOLDING, True
        self.run_msg(bot, msg("refund please", "m4"), now=NOW + timedelta(hours=3))
        bot.reply, bot.handover = "Hi again", False
        out = self.run_msg(bot, msg("hi", "m5"), now=NOW + timedelta(hours=3 + C.QUIET_HOURS, minutes=1))
        self.assertEqual(out["action"], "replied")

    def test_voice_note_hands_over_instead_of_being_ignored(self):
        bot = Bot()
        out = self.run_msg(bot, msg("", "m1", kind="audio"))
        self.assertTrue(out["handover"])
        self.assertEqual(bot.sent, [("6591234567", HOLDING)])
        self.assertEqual(bot.answered, [])

    def test_tagging_failure_still_gets_a_reply(self):
        bot = Bot(tag_fails=True)
        out = self.run_msg(bot, msg("Is oat milk back?", "m1"))
        self.assertEqual(out["action"], "replied")
        self.assertIn("tagging failed", out["reason"])

    def test_send_failure_is_reported_and_not_recorded_as_sent(self):
        bot = Bot()

        def broken(number, text):
            raise RuntimeError("HTTP 400, code 131047: outside the 24 hour window")
        out = C.handle(msg("hi", "m1"), self.store, bot.tag, bot.answer, broken, now=NOW)
        self.assertIn("send failed", out["action"])
        saved = self.store.get("6591234567")
        self.assertFalse(saved["replied"])
        self.assertEqual([m["from"] for m in saved["chat"]], ["customer"])

    def test_dry_run_drafts_but_sends_nothing(self):
        bot = Bot()
        out = self.run_msg(bot, msg("Is oat milk back?", "m1"), dry_run=True)
        self.assertEqual(out["reply"], bot.reply)
        self.assertIn("dry run", out["action"])
        self.assertEqual(bot.sent, [])

    def test_known_number_starts_from_the_demo_customer(self):
        bot = Bot()
        seed = {"customer_id": "C001", "name": "Aisha Rahman", "label": "Persuadable",
                "chat": [{"date": "2026-10-01", "from": "customer", "text": "party next week"}],
                "tags": {"tags": [{"type": "life_event", "value": "party"}]}}
        C.handle(msg("Is oat milk back?", "m1"), self.store, bot.tag, bot.answer, bot.send,
                 known=lambda n: seed, now=NOW)
        call = bot.answered[0]
        self.assertEqual(call["customer"]["customer_id"], "C001")
        self.assertEqual(call["customer"]["label"], "Persuadable")
        self.assertEqual(call["chat"][0]["text"], "party next week")
        self.assertEqual(len(call["tags"]["tags"]), 2)


def load_webhook():
    spec = importlib.util.spec_from_file_location("whatsapp_webhook", ROOT / "scripts" / "whatsapp_webhook.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FakeWhatsApp:
    def __init__(self):
        self.sent, self.read = [], []

    def send_text(self, to, body):
        self.sent.append((to, body))

    def mark_read(self, mid):
        self.read.append(mid)


class WebhookServerTests(unittest.TestCase):
    """The real HTTP handler: Meta gets its 200 before a slow AI finishes, and a retry is ignored."""

    def test_meta_is_answered_at_once_and_a_retry_gets_no_second_reply(self):
        hook = load_webhook()
        with tempfile.TemporaryDirectory() as temp:
            hook.ARGS = type("A", (), {"echo": False, "dry_run": False})()
            hook.STORE = C.Store(str(Path(temp) / "conv.json"))
            hook.INBOX = str(Path(temp) / "inbox.jsonl")
            hook.APP_SECRET = ""
            hook.WA = FakeWhatsApp()
            hook.known_customer = lambda number: None

            def slow_answer(customer, chat, incoming, tags=None, first_reply=True):
                time.sleep(1.5)
                return {"reply": "Yes, oat milk is back!", "handover": False, "reason": ""}
            hook.reply.answer, original_answer = slow_answer, hook.reply.answer
            hook.llm.tag_message, original_tag = (lambda cid, text, date="", prior=None, names=():
                                                  {"customer_id": cid, "tags": []}), hook.llm.tag_message
            try:
                server = HTTPServer(("127.0.0.1", 0), hook.Handler)
                threading.Thread(target=server.serve_forever, daemon=True).start()
                threading.Thread(target=hook.worker, daemon=True).start()
                url = f"http://127.0.0.1:{server.server_port}/whatsapp"
                body = {"entry": [{"changes": [{"value": {
                    "contacts": [{"profile": {"name": "Aisha"}, "wa_id": "6591234567"}],
                    "messages": [{"from": "6591234567", "id": "wamid.X", "timestamp": "1762840000",
                                  "type": "text", "text": {"body": "Is oat milk back?"}}]}}]}]}

                started = time.time()
                self.assertEqual(requests.post(url, json=body, timeout=5).status_code, 200)
                self.assertLess(time.time() - started, 1.0)        # not waiting for the 1.5 s AI
                requests.post(url, json=body, timeout=5)           # Meta retries the same message
                hook.WORK.join()
                self.assertEqual(hook.WA.sent, [("6591234567", "Yes, oat milk is back!")])
                self.assertEqual(hook.WA.read, ["wamid.X"])
                self.assertEqual(len(Path(hook.INBOX).read_text(encoding="utf-8").splitlines()), 2)
                server.shutdown()
            finally:
                hook.reply.answer, hook.llm.tag_message = original_answer, original_tag


if __name__ == "__main__":
    unittest.main()
