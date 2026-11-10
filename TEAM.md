# Team plan: Finals (updated Tue 11 Nov 2026, evening)

> Earlier plans: [3 Nov finals plan](docs/archive/TEAM_finals_plan_3nov.md) · [hackathon plan](docs/archive/TEAM_hackathon.md)
> How the pieces fit: **[docs/V1_ARCHITECTURE.md](docs/V1_ARCHITECTURE.md)** (database tables + API contract)

**Deadline: Saturday 15 Nov.** Feature freeze **Fri 14 Nov, noon**. (The landing page says "Finals 14 Nov". Check the real date and fix it.)

## The goal

Impress the judges with **a commercial-grade product**: a landing page, a dashboard, and something they can **try on their own phones by scanning a QR code**.

## What changed

- **WhatsApp works for real, both ways** (Meta Cloud API). AI tags each message and replies in about 6 s, or hands over to a person. See [docs/WHATSAPP_CLOUD_API.md](docs/WHATSAPP_CLOUD_API.md)
- **Live WhatsApp page** added to the Streamlit app (the fallback demo screen)
- **Jayden is on another project.** His work is split between **Thuta (backend)** and **Dythan (frontend)**
- **The Next.js + Supabase rebuild is back on**, with Dythan building the frontend using Codex
- **New: judges try it themselves.** A QR code opens a web chat with the same AI. Their chat shows up live on the dashboard

## Who owns what

| Person | Owns |
|---|---|
| **Thuta** | Lead · **backend** (`api/`, FastAPI, from Jayden) · Supabase setup + seed · WhatsApp · real number (stretch) |
| **Dythan** | **Frontend** (`web/`, Next.js, from Jayden) · landing page · `/try` web chat · dashboard · pitch + video |
| **Jack** | AI quality (tagger, reply bot) · outcome tracking · help with `/api/chat` |
| **Shareef** | Pilot + owner interviews · business case · numbers |
| ~~Jayden~~ | On another project |

---

## Thuta: backend + data (Jayden's backend half)

**Wed 12 Nov**
- [ ] **Supabase project**: create the tables from `docs/V1_ARCHITECTURE.md`, turn on Realtime, share the URL + anon key with Dythan **privately**
- [ ] Seed the 30 Kampung Fresh demo customers from `data/customers.csv`
- [ ] **`api/` FastAPI**: `/health`, `/api/chat` (web chat → tagger + reply bot → Supabase), move the WhatsApp webhook in (writes to Supabase too)
- [ ] Rate limit `/api/chat` per session

**Thu 13 Nov**
- [ ] **Deploy the backend publicly** (Render or Railway), with secrets in the host's settings. Point Meta's webhook at it, so the **laptop tunnel is no longer needed**
- [ ] End-to-end: web chat and WhatsApp messages both appear in Supabase within seconds
- [ ] **Stretch, start today:** real WhatsApp number (spare SIM + payment method + Meta display name approval, which can take days) for a `wa.me` QR code

**Fri 14 Nov:** load test (10 people chatting at once), demo-day checklist, fix bugs.

## Dythan: frontend (Jayden's frontend half) + pitch

**Wed 12 Nov**
- [ ] `web/` Next.js app on **Vercel**, Tailwind, the same look as the current landing page (dark green, Nudgely brand)
- [ ] **Landing page**: what Nudgely does, the evidence (53% / 1.8x, with the caveat), the live demo QR code, team
- [ ] **`/try` web chat** (mobile first): name field (optional), chat bubbles, typing indicator, calls `POST /api/chat`. Until Thuta's API is live, mock it with the response shape from the contract

**Thu 13 Nov**
- [ ] **Dashboard** (behind Supabase login): Live conversations (realtime, the star screen), Customers (labels, uplift, tags), Campaign, Results. The existing Streamlit pages are the reference for content
- [ ] QR code on the landing page and a big-screen "Scan to try" view
- [ ] Check on phone + desktop, incognito

**Fri 14 Nov**
- [ ] Polish, then **record the backup video** (in case Wi-Fi fails on stage)
- [ ] Deck v1 with Shareef's business slides; live demo script (judges scan → chat → dashboard updates)

## Jack: AI

- [ ] Test the bot from your phone (reply in the Jasper's Market chat; nothing from your number has arrived yet)
- [ ] Help Thuta wire `/api/chat` to `tag_message` + `reply.answer` (same rules as WhatsApp)
- [ ] Outcome tracking (coupon or tracked link) for the pilot
- [ ] 3 good real conversations for the deck

## Shareef: pilot + business

- [ ] Pilot: 1 real shop, or classmates using the `/try` page and WhatsApp test number as "customers"
- [ ] 5 owner interviews with quotes we're allowed to use
- [ ] Business slides: customer, problem size (cited sources), pricing, unit economics (about $0.00025 per AI reply + WhatsApp fees), competitors, go-to-market
- [ ] `docs/Numbers.md` stays the single source for every number

---

## Checkpoints

| When | Must be true | Owner |
|---|---|---|
| **Wed 12 Nov, night** | Supabase live + seeded · `/api/chat` works locally · landing + `/try` deployed on Vercel (mocked is fine) | Thuta · Dythan |
| **Thu 13 Nov, night** | Backend deployed publicly · `/try` talks to the real AI · dashboard shows live chats · business slides drafted | Thuta · Dythan · Shareef |
| **Fri 14 Nov, noon** | **Feature freeze** · 10-person test · backup video recorded | Everyone |
| **Sat 15 Nov** | Finals | Everyone |

## Fallback

If the Next.js dashboard or the public backend isn't solid by **Fri noon**, the demo uses the **Streamlit app + its Live WhatsApp page** on the laptop (works today), with team phones on the WhatsApp test number.

## Demo rules

- The bot answers about items the shop stocks (oat milk, durian, kai lan, eggs, rice, Gardenia bread, Pokka green tea, frozen dumplings, party snack packs). Anything else is handed to a person **on purpose**.
- Never show phone numbers on screen.
- Keys go in host settings and `.env`, never in git or chat.

## Git rules

Branches `yourname/what`, pull request, one teammate looks before merge. Frontend lives in `web/`, backend in `api/`, so you won't edit the same files.
