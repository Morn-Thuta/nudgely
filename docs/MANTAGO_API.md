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
| Tag a member | `clientTagMapping` | `tagId`, `clientId` | Or `platform` + `platformClientId` instead of `clientId` |

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
