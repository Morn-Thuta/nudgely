import hashlib
import hmac
import json
import os
import sys
import tempfile
import unittest
import uuid
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient  # noqa: E402

from api import main  # noqa: E402
from nudgely import conversations, supabase_sync  # noqa: E402

TAGS = {"customer_id": "x", "tags": [{"type": "product_interest", "value": "durian",
                                      "evidence": "durian", "date": ""}]}
ANSWER = {"reply": "Yes, we have durian today!", "handover": False, "reason": "in stock"}


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.patches = [
            patch.object(conversations, "STORE", str(Path(self.tmp.name) / "wa.json")),
            patch("nudgely.llm.tag_message", return_value=TAGS),
            patch("nudgely.reply.answer", return_value=dict(ANSWER)),
            patch.object(supabase_sync, "enabled", return_value=False),
            patch.dict(os.environ, {"WA_VERIFY_TOKEN": "vt", "WA_APP_SECRET": "secret"}),
        ]
        for p in self.patches:
            p.start()
        main._sessions.clear()
        self.client = TestClient(main.app)

    def tearDown(self):
        for p in reversed(self.patches):
            p.stop()
        self.tmp.cleanup()

    def sid(self):
        return str(uuid.uuid4())

    def test_chat_replies_with_tags_and_web_id(self):
        r = self.client.post("/api/chat", json={"session_id": self.sid(), "name": "Judge A", "text": "Do you have durian?"})
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertEqual(body["reply"], ANSWER["reply"])
        self.assertFalse(body["handover"])
        self.assertTrue(body["customer_id"].startswith("WEB"))
        self.assertEqual(body["tags"][0]["value"], "durian")

    def test_chat_rate_limit_and_cap(self):
        s = self.sid()
        self.assertEqual(self.client.post("/api/chat", json={"session_id": s, "text": "hi"}).status_code, 200)
        self.assertEqual(self.client.post("/api/chat", json={"session_id": s, "text": "hi"}).status_code, 429)
        main._sessions[s] = (0.0, main.MAX_PER_SESSION)
        self.assertEqual(self.client.post("/api/chat", json={"session_id": s, "text": "hi"}).status_code, 429)

    def test_chat_rejects_bad_input(self):
        self.assertEqual(self.client.post("/api/chat", json={"session_id": "short", "text": "hi"}).status_code, 400)
        self.assertEqual(self.client.post("/api/chat", json={"session_id": self.sid(), "text": ""}).status_code, 422)
        self.assertEqual(self.client.post("/api/chat", json={"session_id": self.sid(), "text": "x" * 501}).status_code, 422)

    def test_chat_stop_and_start(self):
        s = self.sid()
        self.assertIn("won't get any more", self.client.post("/api/chat", json={"session_id": s, "text": "STOP"}).json()["reply"])
        main._sessions.clear()
        self.assertIsNone(self.client.post("/api/chat", json={"session_id": s, "text": "durian?"}).json()["reply"])

    def test_whatsapp_verify(self):
        ok = self.client.get("/whatsapp", params={"hub.mode": "subscribe", "hub.verify_token": "vt", "hub.challenge": "42"})
        self.assertEqual((ok.status_code, ok.text), (200, "42"))
        self.assertEqual(self.client.get("/whatsapp", params={"hub.mode": "subscribe", "hub.verify_token": "no",
                                                               "hub.challenge": "42"}).status_code, 403)

    def test_whatsapp_rejects_unsigned(self):
        self.assertEqual(self.client.post("/whatsapp", content=b"{}").status_code, 401)

    def test_whatsapp_signed_message_is_answered(self):
        payload = {"entry": [{"changes": [{"value": {
            "contacts": [{"profile": {"name": "Aisha"}, "wa_id": "6591234567"}],
            "messages": [{"from": "6591234567", "id": "wamid.1", "type": "text", "text": {"body": "durian?"}}]}}]}]}
        raw = json.dumps(payload).encode()
        sig = "sha256=" + hmac.new(b"secret", raw, hashlib.sha256).hexdigest()
        with patch.object(main, "_wa") as wa:
            r = self.client.post("/whatsapp", content=raw, headers={"X-Hub-Signature-256": sig,
                                                                    "Content-Type": "application/json"})
            self.assertEqual(r.status_code, 200)
            wa.return_value.send_text.assert_called_once_with("6591234567", ANSWER["reply"])

    def test_judge_pages(self):
        self.assertIn("Kampung Fresh", self.client.get("/try").text)
        self.assertEqual(self.client.get("/", follow_redirects=False).headers["location"], "/try")
        self.assertIn("/try", self.client.get("/qr").text)
        svg = self.client.get("/qr.svg")
        self.assertEqual(svg.headers["content-type"], "image/svg+xml")
        self.assertIn("<svg", svg.text)
        with patch.dict(os.environ, {"TRY_URL": "https://nudgely.vercel.app/try"}):
            self.assertIn("https://nudgely.vercel.app/try", self.client.get("/qr").text)

    def test_health(self):
        self.assertTrue(self.client.get("/health").json()["ok"])


if __name__ == "__main__":
    unittest.main()
