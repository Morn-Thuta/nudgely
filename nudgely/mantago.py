"""Small MantaGO Open API client.

Docs: https://doc.mantago.cc/llms.txt
Every call is POST https://mantago.cc/api/openapi/<path>?botId=<botId>
with header "Authorization: Bearer <token>" and JSON body {"secret": ..., ...}.
"""

import os

import requests

BASE_URL = "https://mantago.cc/api/openapi"
PLATFORMS = ("line", "facebook", "instagram", "whatsapp")
TOKEN_EXPIRED = 1004


class MantaGOError(Exception):
    def __init__(self, status, code, message, body=None):
        super().__init__(f"HTTP {status}, code {code}: {message}")
        self.status = status
        self.code = code
        self.body = body


class MantaGO:
    def __init__(self, bot_id, token, secret, timeout=20):
        if not (bot_id and token and secret):
            raise ValueError("bot_id, token and secret are all required")
        self.bot_id = bot_id
        self.token = token
        self.secret = secret
        self.timeout = timeout

    @classmethod
    def from_env(cls):
        """Read MANTAGO_BOT_ID / MANTAGO_TOKEN / MANTAGO_SECRET (loads .env if present)."""
        try:
            from dotenv import load_dotenv

            load_dotenv()
        except ImportError:
            pass
        return cls(
            os.getenv("MANTAGO_BOT_ID", ""),
            os.getenv("MANTAGO_TOKEN", ""),
            os.getenv("MANTAGO_SECRET", ""),
        )

    @classmethod
    def from_streamlit(cls, st):
        s = st.secrets["mantago"]
        return cls(s["bot_id"], s["token"], s["secret"])

    # ---- low level -------------------------------------------------------

    def _post(self, path, body=None, params=None, retry=True):
        url = f"{BASE_URL}/{path}"
        query = {"botId": self.bot_id, **(params or {})}
        payload = {"secret": self.secret, **(body or {})}
        headers = {"Authorization": f"Bearer {self.token}"}
        r = requests.post(url, params=query, json=payload, headers=headers, timeout=self.timeout)
        try:
            data = r.json()
        except ValueError:
            data = {"success": False, "errResponse": {"code": None, "message": r.text[:300]}}

        if r.ok and data.get("success", True):
            return data

        err = data.get("errResponse") or {}
        code = err.get("code")
        if code == TOKEN_EXPIRED and retry:
            self.refresh_token()
            return self._post(path, body, params, retry=False)
        raise MantaGOError(r.status_code, code, err.get("message", r.reason), data)

    # ---- API calls -------------------------------------------------------

    def refresh_token(self):
        """Get a new token + secret. The old pair stops working, so save the new one."""
        data = self._post("token", retry=False)
        self.token = data["apiToken"]
        self.secret = data["apiSecret"]
        print("[mantago] token refreshed - update MANTAGO_TOKEN / MANTAGO_SECRET with the new values")
        return data

    def list_clients(self, platform=None, limit=100, offset=0):
        """Members who have messaged the bot: clientId, clientName, platform, lastInteractAt, tags."""
        params = {"limit": limit, "offset": offset}
        if platform:
            params["platform"] = platform
        data = self._post("clients", params=params)
        return (data.get("clientList") or {}).get("list", [])

    def send(self, platform, client_ids, message, name="Nudgely campaign", fb_tag=None):
        """Broadcast one text message to a list of clientIds on one platform."""
        if platform not in PLATFORMS:
            raise ValueError(f"platform must be one of {PLATFORMS}")
        body = {"platform": platform, "name": name, "message": message, "clientIds": list(client_ids)}
        if platform == "facebook":
            if not fb_tag:
                raise ValueError("fb_tag is required for facebook")
            body["fbTag"] = fb_tag
        return self._post("broadcast", body)

    def list_tags(self, search="", perpage=100):
        """Manual tags: id, name."""
        data = self._post("clientTags/list", params={"search": search, "perpage": perpage})
        return data.get("clientTagList", [])

    def create_tag(self, name):
        """Create a manual tag. The API does not return the id, so look it up with list_tags()."""
        return self._post("clientTag", {"name": name})

    def get_or_create_tag_id(self, name):
        for _ in range(2):
            for t in self.list_tags(search=name):
                if t.get("name") == name:
                    return t["id"]
            self.create_tag(name)
        raise MantaGOError(404, None, f"tag '{name}' not found after create")

    def assign_tag(self, tag_id, client_id):
        """Put a manual tag on a member (F6 write-back)."""
        return self._post("clientTagMapping", {"tagId": tag_id, "clientId": client_id})
