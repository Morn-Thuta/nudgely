# Nudgely

Message the right customers, say the right thing, prove it worked.

Nudgely picks which customers to message (uplift model), writes each one a personal message from their own chat history (LLM), sends it through MantaGO, and proves the effect against a no-message group.

AI-GNITION 2026 · MVP due **Fri 23 Oct 2026**

- Full spec: [docs/PRD.md](docs/PRD.md)
- One-page brief: [docs/One_Page_Brief.md](docs/One_Page_Brief.md)
- Team plan, roles and checklist: [TEAM.md](TEAM.md)
- MantaGO API notes: [docs/MANTAGO_API.md](docs/MANTAGO_API.md)

## Setup (5 minutes)

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows  (Mac/Linux: source .venv/bin/activate)
pip install -r requirements.txt
copy .env.example .env          # Mac/Linux: cp .env.example .env  - then fill it in
```

## Test MantaGO right now

1. Create a bot at mantago.cc. Copy the `botId` from the URL `mantago.cc/chatbot/<botId>`.
2. Connect WhatsApp to the bot and **publish** the bot.
3. Bot console > Settings > Advanced Settings > API Integration Settings > Refresh. Copy the token and secret into `.env`.
4. Send any message to the bot's WhatsApp number **from your own phone**. This makes you a member and opens the 24-hour window.
5. Run:

```bash
python scripts/test_mantago.py members
```

6. Copy your `clientId` from the output, then send yourself a test message:

```bash
python scripts/test_mantago.py send --platform whatsapp --to <your clientId> --yes
```

If the message lands on your phone, the riskiest part of the project works. Leave out `--yes` for a dry run.

## Repo layout

| Folder | Owner | What |
|---|---|---|
| `notebooks/` | A: Data/ML | Uplift model training on Lenta (offline) |
| `scripts/` | B: LLM | `extract_tags.py`, `write_messages.py` (offline, cached output) |
| `nudgely/` | C: MantaGO | `mantago.py` API client |
| `app/` | D: App | Streamlit app, 5 pages |
| `data/` | everyone | Small CSV/JSON only. `data/examples/` shows the agreed format |
| `docs/` | E: Pitch | PRD, brief, deck notes |

## Rules

- **No API keys in code or GitHub.** Use `.env` locally and Streamlit secrets in the cloud.
- The deployed app never calls the LLM on page load. It reads cached files.
- Chats and names are fake. Model results come from public datasets (Lenta, Hillstrom).
