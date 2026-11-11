# Team plan: Finals (updated Wed 11 Nov 2026)

> Earlier plans: [3 Nov finals plan](docs/archive/TEAM_finals_plan_3nov.md) · [hackathon plan](docs/archive/TEAM_hackathon.md)
> How the pieces fit: **[docs/V1_ARCHITECTURE.md](docs/V1_ARCHITECTURE.md)** (database tables + API contract)

**Finals: Saturday 14 Nov.** Feature freeze **Fri 13 Nov, noon**. (Confirmed by Thuta. Earlier versions of this plan were one day late.)

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
| **Shareef** | Evidence (cited research, public quotes, classmate test) · business case · numbers |
| ~~Jayden~~ | On another project |

---

## Thuta: backend + data (Jayden's backend half)

**Wed 11 Nov (today)**
- [x] **`api/` FastAPI**: `/health`, `/api/chat` (web chat → tagger + reply bot → Supabase), WhatsApp webhook moved in
- [x] Rate limit `/api/chat` per session (2 s gap, 30 messages per session)
- [x] **Backend deployed on Render**: https://nudgely-api.onrender.com. Meta's webhook points at it, so **no laptop tunnel**
- [x] Supabase migrations (`supabase/migrations/`) + seed script (`scripts/seed_supabase.py`) written
- [ ] **Supabase project** (Dythan creates it, invites Thuta): run the migrations, seed the 30 demo customers, put the keys in Render, share URL + publishable key with Dythan **privately**
- [ ] Backup judge chat page served by the backend itself (in case `web/` isn't ready)

**Thu 12 Nov**
- [ ] End-to-end: web chat and WhatsApp messages both appear in Supabase within seconds
- [ ] **Mock POS** (good-to-have, **hard half-day limit, only after the end-to-end works; drop it if Thursday slips**): `GET /pos/products`, `POST /pos/sale`, `POST /pos/restock` in the backend, the bot reads stock from it instead of the fixed `STORE_INFO`, plus a small "Demo POS" page with + / − buttons. Demo: judge asks "oat milk?" → yes, $4.50 → we sell the last one → judge asks again → sold out
- [ ] **Stretch:** real WhatsApp number (spare SIM + payment method + Meta display name approval, which can take days) for a `wa.me` QR code

**Fri 13 Nov:** load test (10 people chatting at once), keep Render awake, demo-day checklist, fix bugs.

## Dythan: frontend (Jayden's frontend half) + pitch

**Wed 11 Nov (today)**
- [ ] `web/` Next.js app on **Vercel**, Tailwind, the same look as the current landing page (dark green, Nudgely brand)
- [ ] **Landing page**: what Nudgely does, the evidence (53% / 1.8x, with the caveat), the live demo QR code, team
- [ ] **`/try` web chat** (mobile first): name field (optional), chat bubbles, typing indicator, calls `POST /api/chat`. Until Thuta's API is live, mock it with the response shape from the contract

**Thu 12 Nov**
- [ ] **Dashboard** (behind Supabase login): Live conversations (realtime, the star screen), Customers (labels, uplift, tags), Campaign, Results. The existing Streamlit pages are the reference for content
- [ ] QR code on the landing page and a big-screen "Scan to try" view
- [ ] Check on phone + desktop, incognito

**Fri 13 Nov**
- [ ] Polish, then **record the backup video** (in case Wi-Fi fails on stage)
- [ ] Deck v1 with Shareef's business slides; live demo script (judges scan → chat → dashboard updates)

## Jack: AI

- [ ] Test the bot from your phone (reply in the Jasper's Market chat; nothing from your number has arrived yet)
- [x] `/api/chat` uses `tag_message` + `reply.answer` (same `bot.handle()` as WhatsApp)
- [ ] Outcome tracking (coupon or tracked link) for the pilot
- [ ] 3 good real conversations for the deck

## Shareef: evidence + business

No real-shop pilot or owner interviews: not enough time before Sat. Use public data and our own live test instead.
**Never present mock data or made-up quotes as real.** Label anything simulated as "simulated".

**Wed 11 Nov (today)**
- [ ] **3-4 cited sources** on the problem: Singapore SME numbers, customer retention / repeat purchase studies, WhatsApp Business use in SEA. Each with a link, for "research shows..." slides
- [ ] **Real owners' public words**: 3-5 quotes from forums, Reddit or Google reviews about slow replies or customers not coming back, with the source shown

**Thu 12 Nov**
- [ ] **Business slides** (draft by Thu night): customer, problem size (from the sources above), pricing, cost per shop (about $0.00025 per AI reply + WhatsApp fees), competitors (incl. "why not just MantaGO broadcasts?"), go-to-market
- [ ] **Classmate test, evening** (doubles as the load test): 10-15 classmates chat with the live bot on WhatsApp or `/try` for 10 min. Thuta pulls the real numbers after: chats, % tagged right, % handed to a person, average reply time

**Fri 13 Nov (before noon)**
- [ ] Hand slides + classmate test numbers to Dythan for the deck
- [ ] `docs/Numbers.md` stays the single source for every number

**Finals day:** play Mei Ling (shop owner) on the dashboard, and run the Demo POS if we build it.

---

## Checkpoints

| When | Must be true | Owner |
|---|---|---|
| **Wed 11 Nov, night** | Supabase live + seeded · `/api/chat` live on Render ✅ · landing + `/try` deployed on Vercel (mocked is fine) | Thuta · Dythan |
| **Thu 12 Nov, night** | Backend deployed publicly ✅ · `/try` talks to the real AI · dashboard shows live chats · business slides drafted | Thuta · Dythan · Shareef |
| **Fri 13 Nov, noon** | **Feature freeze** · 10-person test · backup video recorded | Everyone |
| **Sat 14 Nov** | Finals | Everyone |

## Judge pinch points (questions to be ready for)

| Question judges may ask | Honest answer today | Work before finals | Owner |
|---|---|---|---|
| "How do you know it brought people back?" | Holdout group + Jack's `returns.py` matches the sales file to who was messaged | Show one worked example; coupon code or tracked link for the pilot | Jack |
| "Your evidence is Russian grocery data (Lenta)" | True. Model retrained on 10 features any shop has; 53% of extra visits from top 30% (90% CI 31-89%) | Classmate test numbers + "a paid pilot is our next step" | Shareef |
| "300 customers and a 30-person holdout proves nothing" | Right for one campaign; results add up over several campaigns | Say it before they do | Shareef |
| "How does the bot know what's in stock?" | Fixed list in `nudgely/llm.py`; anything else goes to a person on purpose | Mock POS (Thu, if time) | Thuta |
| "What if it makes up a price?" | `review_reply` checks every reply; invented price → handed to a person | Show the durian $3 example | Jack |
| "Can I break it? (ignore your rules, 90% off)" | Prompt + checker | **Test jailbreaks, fake products, rude messages** and fix what slips | Jack |
| "Singlish / Chinese / Malay?" | Untested | **Test a few chats in each** | Jack |
| "What does it cost per shop?" | ~$0.00025 per AI reply (Claude Haiku via OpenRouter) + WhatsApp fees | Unit economics slide | Shareef |
| "What if 10 of us chat at once?" | Paid model, rate limit per session | **10-person load test Fri** | Thuta |
| "Is my data safe? PDPA?" | Phone numbers never stored in the database (hashed); keys never in git; STOP/START opt-out works | Check Supabase RLS is on | Thuta |
| "Is the tagging accurate?" | 97% / 86% from `docs/TAGGING_ACCURACY.md`, measured on a free model | **Rerun on the paid model** | Jack |
| "How does a shop start using it?" | Sign up → connect WhatsApp → upload sales CSV → first campaign → results in 2-4 weeks | One onboarding slide | Dythan |
| "Why not just use MantaGO broadcasts?" | MantaGO sends; Nudgely decides **who** (uplift) and **what** (their own chat) | Comparison slide | Shareef |
| "What if WhatsApp / Wi-Fi fails on stage?" | Backup video + Streamlit fallback | Record the video Fri | Dythan |

## Fallback

If the Next.js dashboard isn't solid by **Fri 13 Nov, noon**, the demo uses the **Streamlit app + its Live WhatsApp page** on the laptop (works today), with team phones on the WhatsApp test number.

## Demo rules

- The bot answers about items the shop stocks (oat milk, durian, kai lan, eggs, rice, Gardenia bread, Pokka green tea, frozen dumplings, party snack packs). Anything else is handed to a person **on purpose**.
- Never show phone numbers on screen.
- Keys go in host settings and `.env`, never in git or chat.

## Git rules

Branches `yourname/what`, pull request, one teammate looks before merge. Frontend lives in `web/`, backend in `api/`, so you won't edit the same files.
