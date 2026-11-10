import hashlib
import hmac
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from nudgely import whatsapp as wa  # noqa: E402

# Shape of a real Cloud API webhook POST (one text message + one delivery status)
SAMPLE = {
    "object": "whatsapp_business_account",
    "entry": [{"id": "WABA_ID", "changes": [{"field": "messages", "value": {
        "messaging_product": "whatsapp",
        "metadata": {"display_phone_number": "15550000000", "phone_number_id": "123"},
        "contacts": [{"profile": {"name": "Aisha"}, "wa_id": "6591234567"}],
        "messages": [{"from": "6591234567", "id": "wamid.A", "timestamp": "1762780000",
                      "type": "text", "text": {"body": "Is oat milk back?"}}],
        "statuses": [{"id": "wamid.B", "status": "delivered", "timestamp": "1762780001",
                      "recipient_id": "6598765432"}],
    }}]}],
}


class WhatsAppTests(unittest.TestCase):
    def test_parse_text_message_and_status(self):
        out = wa.parse_webhook(SAMPLE)
        self.assertEqual(out["messages"], [{"id": "wamid.A", "from": "6591234567", "name": "Aisha",
                                            "timestamp": "1762780000", "type": "text",
                                            "text": "Is oat milk back?"}])
        self.assertEqual(out["statuses"][0]["status"], "delivered")
        self.assertIsNone(out["statuses"][0]["error"])

    def test_parse_ignores_empty_and_non_text(self):
        self.assertEqual(wa.parse_webhook({}), {"messages": [], "statuses": []})
        img = {"entry": [{"changes": [{"value": {"messages": [
            {"from": "1", "id": "x", "type": "image", "image": {"id": "m"}}]}}]}]}
        self.assertEqual(wa.parse_webhook(img)["messages"][0]["text"], "")

    def test_signature(self):
        body, secret = b'{"a":1}', "s3cret"
        good = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
        self.assertTrue(wa.valid_signature(body, good, secret))
        self.assertFalse(wa.valid_signature(body, "sha256=00", secret))
        self.assertFalse(wa.valid_signature(body, None, secret))

    def test_verify_subscription(self):
        ok = {"hub.mode": "subscribe", "hub.verify_token": "tok", "hub.challenge": "42"}
        self.assertEqual(wa.verify_subscription(ok, "tok"), "42")
        self.assertIsNone(wa.verify_subscription({**ok, "hub.verify_token": "no"}, "tok"))

    def test_normalise_number(self):
        self.assertEqual(wa.normalise_number("+65 9123-4567"), "6591234567")


if __name__ == "__main__":
    unittest.main()
