# Team plan: Finals (Fri 14 Nov 2026)

> Hackathon plan (21–23 Oct) is archived in [docs/archive/TEAM_hackathon.md](docs/archive/TEAM_hackathon.md).
> Full reasoning is in the finals plan shared in the group chat (`Nudgely_Finals_Plan.md`).

## Goal

Turn Nudgely from a demo on fake data into **a real product a shop can sign up for**: real chats in, real sales in, automatic WhatsApp sends that deliver, and a **real measured result from a pilot**.

## What "done" looks like on 14 Nov

- [ ] A shop can **sign up, log in and connect its MantaGO bot** on our own web app (not Streamlit)
- [ ] **New customer messages arrive live** through MantaGO's webhook and get tagged in seconds
- [ ] The shop can **upload a sales CSV** and see customers scored
- [ ] **Run campaign** picks customers, holds some back, fills approved templates, and the messages **arrive on real phones**
- [ ] The **AI reply bot** answers customers or hands over to a person
- [ ] **One real pilot** sent by Sun 9 Nov, with outcomes on the results page
- [ ] **Live audience demo** (QR → chat → personal reply) plus a backup video
- [ ] Business slides: customer interviews, pricing, competitors, go-to-market

## Who owns what

| Person | Owns |
|---|---|
| **Thuta** | Lead · MantaGO (webhook, WhatsApp Business number, templates, sending) · FastAPI backend |
| **Jack** | LLM: live tagging, reply bot (`jack/next-phase`), template filling, rule checks, test set · outcome tracking |
| **Jayden** | Next.js dashboard · Supabase (database + login) · deploys |
| **Dythan** | Product design + UX of the new app · pitch, live demo, backup video |
| **Shareef** | Pilot shop + owner interviews · business case · transferable model retrain |

## Repo layout (new folders, so nobody edits the same files)

| Folder | Owner | What |
|---|---|---|
| `api/` | Thuta | FastAPI backend: webhook, MantaGO, campaigns, jobs |
| `web/` | Jayden (+ Dythan on design) | Next.js dashboard |
| `nudgely/` | Jack (LLM), Thuta (MantaGO) | Shared Python library used by `api/` |
| `notebooks/`, `models/` | Shareef | Model training and evaluation |
| `app/` | — | Old Streamlit app: keep as the "lab" for model evidence; no new features |
| `docs/` | Shareef, Dythan | Business case, pitch material |

**Git rules:** work on a branch named `yourname/what` (for example `jayden/login-page`), open a pull request, and get one teammate to look before merging to `main`. Never commit keys, phone numbers or real customer data.

---

## Thuta: MantaGO + backend

**Mon 3 Nov**
- [ ] Email Eslitec the 7 questions (bottom of this page)
- [ ] **Webhook test:** set MantaGO's callback URL to a test endpoint, message the bot, save what arrives in `docs/MANTAGO_API.md`. Done when we know if message text comes through
- [ ] Start moving the bot to an **official WhatsApp Business number** (not personal)

**Tue 4 Nov**
- [ ] `api/` FastAPI skeleton deployed (Render or Railway) with a health check
- [ ] Write **6 WhatsApp templates** with blanks (one per tag type) with Jack, and **submit them to Meta**
- [ ] Agree the database tables with Jayden

**Wed 5 – Thu 6 Nov**
- [ ] `POST /webhooks/mantago`: store each incoming message, link it to the customer, call Jack's tagger
- [ ] Member import from MantaGO into the database
- [ ] Shop connect: save bot ID, token, secret (encrypted) per shop

**Fri 7 – Sat 8 Nov**
- [ ] Campaign run: score → pick + holdout → fill template → send through MantaGO → log each send
- [ ] Daily job: refresh scores, close outcome windows
- [ ] **Sat night checkpoint:** the app sends a WhatsApp message that **arrives**, with no manual step

**Sun 9 Nov:** send the **pilot campaign**. **Mon 10 – Fri 14:** bug fixes, demo rehearsal, final review.

## Jack: LLM + replies + outcomes

**Mon 3 – Tue 4 Nov**
- [ ] Finish and merge `jack/next-phase` (reply bot, provider fallback)
- [ ] Move to a **paid LLM key** for real customer data (the team decides which); free tiers stay for testing only
- [ ] Turn tag extraction into a function the API calls **per new message** (not a batch script)

**Wed 5 – Thu 6 Nov**
- [ ] Template filling: given a customer's tags, pick 1 of the 6 templates and fill its blanks; every result passes `check_message`
- [ ] Reply bot connected to the webhook (answer, or hand to a person on HUMAN / complaint)
- [ ] **Test set:** 30+ realistic chats with expected tags; report accuracy

**Fri 7 – Sat 8 Nov**
- [ ] Outcome tracking: a unique coupon code or tracked link per customer, redemptions recorded as returns
- [ ] Results data for the new dashboard: messaged vs holdout, with a confidence range

**Sun 9 – Wed 12 Nov:** watch pilot outcomes, fix bad messages, give Dythan 3 real example messages for the deck.

## Jayden: web app + database + deploy

**Mon 3 – Tue 4 Nov**
- [ ] Supabase project: tables `shops, customers, messages, purchases, tags, scores, campaigns, campaign_members, sends, outcomes` (agree with Thuta)
- [ ] **Login + sign-up** (Supabase Auth); each shop sees only its own data (row-level security)
- [ ] `web/` Next.js app deployed on Vercel. **Tue night checkpoint:** log in on the live site

**Wed 5 – Thu 6 Nov**
- [ ] Onboarding: "Connect MantaGO" form (bot ID, token, secret) → calls the API
- [ ] **Sales CSV upload** (`phone, date, amount`) with a preview and error messages
- [ ] Customers page: list, label badge, last visit, top tag; customer page with live chat + tags

**Fri 7 – Sat 8 Nov**
- [ ] Campaign page: audience size, holdout %, message previews, Run campaign, per-customer status
- [ ] Results page: messaged vs holdout, lift with range, campaign history

**Sun 9 – Wed 12 Nov:** polish, phone-screen check, incognito test, error states, demo data reset button.

## Dythan: product design + pitch

**Mon 3 – Tue 4 Nov**
- [ ] Screens for the new app (Figma or sketches): sign-up, connect MantaGO, customers, customer detail, campaign, results. Hand them to Jayden by **Tue evening**
- [ ] New pitch story outline: problem → product → **live demo** → pilot results → business → ask

**Wed 5 – Sat 8 Nov**
- [ ] Design the **live audience demo**: QR code, what people should type, what they'll receive, timing (about 2 min)
- [ ] Deck v0 with placeholders for pilot numbers
- [ ] Work with Jayden on UI polish

**Sun 9 – Thu 13 Nov**
- [ ] Deck v1 with real pilot results and Shareef's business slides (**Wed**)
- [ ] **Record the backup demo video (Wed)**
- [ ] Run 3 dress rehearsals on Thu, including one with no Wi-Fi

## Shareef: pilot + business + model

**Mon 3 – Tue 4 Nov**
- [ ] **Find 1–2 real pilot shops** (family, friends, campus café; ask Eslitec too). Need: they use WhatsApp, agree to a 1-week test, can export sales
- [ ] Book **5+ short owner interviews**; collect quotes (with permission) on how they do promotions today
- [ ] Simple consent note for pilot customers (PDPA): what we collect, how to opt out

**Wed 5 – Thu 6 Nov**
- [ ] **Transferable model:** retrain uplift on features any shop has (recency, frequency, spend, tenure, chat signals) using Hillstrom + reduced Lenta; report lift and range honestly in `docs/Numbers.md`
- [ ] Export the model so `api/` can load it

**Fri 7 – Wed 12 Nov**
- [ ] Business case: target customer, problem size (**cited sources only**), pricing (subscription vs pay-for-lift), unit economics (LLM + WhatsApp cost per message), competitors, go-to-market through MantaGO
- [ ] Pilot report: what we sent, to whom (counts only), results with ranges
- [ ] Update `docs/Numbers.md` so every finals number has one source

---

## Checkpoints

| When | Must be true | Owner |
|---|---|---|
| **Mon 3 Nov, night** | We know whether the webhook sends message text | Thuta |
| **Tue 4 Nov, night** | Login works on the live web app · templates submitted · pilot shop contacted | Jayden · Thuta · Shareef |
| **Thu 6 Nov, night** | Live chats arrive and get tagged · CSV upload works · new model trained | Thuta + Jack · Jayden · Shareef |
| **Sat 8 Nov, night** | App sends a WhatsApp message that **arrives**, automatically | Thuta + Jack |
| **Sun 9 Nov** | **Pilot campaign sent** | Everyone |
| **Wed 12 Nov** | **Feature freeze** · deck v1 · backup video | Everyone · Dythan |
| **Thu 13 Nov** | 3 dress rehearsals done | Everyone |

## Fallbacks

| If… | Then… |
|---|---|
| The webhook doesn't send message text | Eslitec conversation API → shop chat export → pilot on our own bot with real people |
| Templates aren't approved by Sat | Utility templates, in-window free-text replies, or Instagram/Messenger |
| No real shop by Wed | Pilot with real people on the Kampung Fresh bot (classmates/friends), real coupons, real outcomes |
| New app isn't ready by Sat | Freeze scope; the Streamlit app stays as the fallback demo |

## Questions for Eslitec (Thuta, Mon 3 Nov)

1. Does the callback URL send incoming customer messages, with text? What does the payload look like?
2. Is there an API or export for conversation history?
3. How do we connect the official WhatsApp Business API (dedicated number) to our bot?
4. Do message packs support WhatsApp template variables ({{1}}) filled through the API?
5. Can the API send free-text replies inside the 24-hour window?
6. Can coupons and short links be created and tracked through the API?
7. Could Nudgely be listed in MantaGO's Applications, and can you introduce 1–2 shops for a pilot?

## Decide in today's team call

- [ ] Agree on the scope and stack above (Next.js + FastAPI + Supabase)
- [ ] Who has a real shop contact for the pilot?
- [ ] Paid LLM key: who pays, and the budget
- [ ] Pricing direction: subscription or pay-for-lift
