# MantaGO Open API notes

Checked against https://doc.mantago.cc on 21 Oct 2026. Client code: [nudgely/mantago.py](../nudgely/mantago.py).

**Every call:** `POST https://mantago.cc/api/openapi/<path>?botId=<botId>`
Header `Authorization: Bearer <token>`. JSON body always includes `"secret"`.

- **Token + secret:** bot console > 設定 Settings > 進階設定 Advanced Settings > API串接設定 API Integration > 刷新 Refresh. One pair per bot. **Expires after 30 days.**
- **botId:** from the URL `mantago.cc/chatbot/<botId>`.

| What | Path | Body (besides `secret`) | Notes |
|---|---|---|---|
| Refresh token | `token` | — | Returns `apiToken`, `apiSecret`. The old pair stops working (error 120000) |
| Member list | `clients` | — | Query: `platform`, `limit` (≤100), `offset`. Returns `clientList.list[]` with `clientId`, `clientName`, `platform`, `lastInteractAt`, `tags` |
| Send message | `broadcast` | `platform`, `name`, `message`, `clientIds[]` (+ `fbTag` on facebook) | `platform` is `line` / `facebook` / `instagram` / `whatsapp`. Returns `{success, message}` |
| Create manual tag | `clientTag` | `name` | Doesn't return the id, so call list next |
| List manual tags | `clientTags/list` | — | Query: `search`, `perpage`. Returns `clientTagList[]` with `id`, `name` |
| Tag a member | `clientTagMapping` | `tagId`, `platform`, `platformClientId` | **Use `platform` + `platformClientId`** with the `clientId` from the member list. Passing it as `clientId` tagged the wrong member while still returning success |

**Errors** look like `{"success": false, "errResponse": {"code": ..., "message": ...}}`

| Code | Meaning |
|---|---|
| 1002 | Wrong token/secret, **or plan has no Open API** |
| 1004 | Token expired → refresh |
| 5001 | Wrong botId |
| 36000 | Broadcast failed (bot not published, or delivery failed) |
| 37011 | No such member |
| 110000 | Missing required field |
| 120000 | Old token used after refresh |

**Open questions:** the broadcast doc calls `clientIds` "platform UUIDs". Check that the `clientId` from the member list works there (the smoke test answers this). There are no WhatsApp template fields in the API.

## What we tested ourselves (7–10 Nov 2026)

Eslitec no longer supports finalists, so these are our own findings.

### Sending
- **Free-text WhatsApp broadcasts** (`message`) are accepted by the API and show in MantaGO's Broadcast log, but stay **"Unsent"**: WhatsApp needs a Meta-approved template for business-started messages.
- **Approved template = message pack.** Our **Utility pack** was approved (green check in the dashboard). Its id is **`1aKOMGxaQ`**. Send it with `intentId`:
  `python scripts/test_mantago.py send --platform whatsapp --to <clientId> --intent 1aKOMGxaQ --yes`
- **Utility packs get approved; plan for those.** Marketing packs may take longer or be rejected.
- **No per-customer blanks.** The broadcast API has no field for template variables, so a pack is sent exactly as written. Personalised sends need one approved pack per message, or MantaGO support for variables (roadmap).

### Receiving (incoming chat text)
- **Callback URL:** `POST set/callback` returns "success", but **no request reached our endpoint** when a teammate messaged the bot (tested with a public tunnel, 7 Nov). Treat it as not delivering incoming messages.
- **Member and analytics APIs** return profiles, tags, `lastInteractAt` and aggregate counts, **never message text**.
- **Dashboard:** Conversations has no export; User list exports users only; the History page is empty.
- **Conclusion:** there is no supported way to read customer chat text from MantaGO. For two-way features:
  1. **Live demo:** capture chats in Nudgely's own chat page (audience scans a QR code), tag them live, reply on screen.
  2. **"Who just messaged":** poll the member list and watch `lastInteractAt` change (no text, but shows the customer is active and their 24-hour window is open).
  3. **Pitch:** "With a conversation API from MantaGO, incoming chats plug straight in."

> Note: the bot's callback URL still points at the stopped test tunnel. It's harmless; reset it once we have a real endpoint.
