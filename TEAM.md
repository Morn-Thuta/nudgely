# Team plan: Finals (updated Tue 11 Nov 2026)

> Earlier plans: [3 Nov finals plan](docs/archive/TEAM_finals_plan_3nov.md) · [hackathon plan](docs/archive/TEAM_hackathon.md)

**Deadline: Saturday 15 Nov.** Feature freeze **Thu 13 Nov night**.

## What changed since 3 Nov

- **WhatsApp works for real, both ways** (Meta's WhatsApp Cloud API, not MantaGO). Customers message the Kampung Fresh test number, the AI tags each message and replies in about 6 s, or hands over to a person. STOP/START work. Details: [docs/WHATSAPP_CLOUD_API.md](docs/WHATSAPP_CLOUD_API.md)
- **MantaGO** can't give us chat text or deliver broadcasts on our link. We keep it for members and tags (both work) and say so honestly in the pitch. See [docs/MANTAGO_API.md](docs/MANTAGO_API.md)
- **Jayden is on another project.** His frontend work moves to **Dythan**.
- **Scope cut: no Next.js / Supabase rebuild.** Nobody started it, and it can't land by Saturday. The **Streamlit app is the product**. Login, multi-shop and a database go on the roadmap slide.

## Who owns what now

| Person | Owns |
|---|---|
| **Thuta** | Lead · WhatsApp + MantaGO · running the bot on demo day · final review |
| **Jack** | AI: tagger, reply bot, templates · outcome tracking |
| **Dythan** | **Frontend (from Jayden)** · pitch · live demo · backup video |
| **Shareef** | Pilot shop + owner interviews · business case · numbers |
| ~~Jayden~~ | On another project |

---

## Dythan: frontend + pitch (frontend taken over from Jayden)

**Frontend, by Thu 13 Nov**
- [ ] **New page: "Live WhatsApp"** (`app/views/live.py`). This is the screen for the live demo. It reads `data/wa_customers.json` (written by the bot) and shows, per customer: the chat bubbles, the AI's tags (with evidence), whether it was handed to a person, and opted-out status. Refresh every few seconds (`st.fragment(run_every=3)`) so new messages appear on stage without clicking. Add it to `app/streamlit_app.py`
- [ ] **Demo reset button** on that page: clears the test conversations so each rehearsal starts clean. Back up the file first, and ask Thuta before running it on demo day
- [ ] Polish the existing pages (Customers, Customer detail, Campaign, Results): wording, spacing, empty states
- [ ] **Deploy** the latest `main` to Streamlit Cloud (nudgely.streamlit.app). Check every page in incognito **and** on a phone
- [ ] Note: the Live WhatsApp page only has data on the laptop running the bot. On stage, show the **local** app (`streamlit run app/streamlit_app.py`), not the cloud link

**Pitch, by Fri 14 Nov**
- [ ] Live demo script (about 2 min): someone messages the test number → the Live WhatsApp page shows it, tagged → the reply lands on the phone → HUMAN → handed over
- [ ] Deck v1 with Shareef's business slides and real pilot numbers (if any)
- [ ] **Record the backup demo video** (in case Wi-Fi or WhatsApp fails on stage)
- [ ] Dress rehearsal with the team

## Thuta: WhatsApp + lead

- [x] Two-way WhatsApp, AI bot, long-lived token (until 9 Jan 2027), app secret, privacy policy, Meta app published
- [ ] Add Shareef (and anyone else demoing) as test recipients. 2 of 5 slots left
- [ ] Decide: audience messages live (needs a real number + payment method) **or** team phones on stage (works today)
- [ ] Demo-day checklist: start bot + tunnel, update the Meta callback URL, send one test message, open the Live WhatsApp page
- [ ] Rotate keys after the finals (OpenRouter, MantaGO)

## Jack: AI

- [x] Reply bot, provider fallback, per-message tagging, template filling, tagging test set
- [ ] Reply to the Jasper's Market chat from +1 555-164-9508 to test the bot yourself (nothing has arrived from your number yet)
- [ ] Coupon or tracked-link outcome tracking, so the pilot has a measurable "came back"
- [ ] Give Dythan 3 good real bot conversations for the deck

## Shareef: pilot + business

- [ ] **1 pilot shop**, or a "real people, demo shop" pilot with classmates on the test number
- [ ] 5 owner interviews, with quotes we're allowed to use
- [ ] Business case slides: customer, problem size (cited sources only), pricing, unit economics (LLM about $0.00025 per reply + WhatsApp fees), competitors, go-to-market
- [ ] Keep `docs/Numbers.md` as the one source for every number

---

## Checkpoints

| When | Must be true | Owner |
|---|---|---|
| **Wed 12 Nov, night** | Live WhatsApp page shows real messages · business slides drafted | Dythan · Shareef |
| **Thu 13 Nov, night** | **Feature freeze** · app deployed and checked on a phone · deck v1 | Dythan · everyone |
| **Fri 14 Nov** | Backup video recorded · full dress rehearsal | Dythan · everyone |
| **Sat 15 Nov** | Finals | Everyone |

## Demo rules

- Ask about items the shop stocks: oat milk, durian, kai lan, eggs, rice, Gardenia bread, Pokka green tea, frozen dumplings, party snack packs. Anything else is handed to a person **on purpose** (it never invents stock).
- Only numbers on the test-recipient list can receive messages (Thuta, Dythan, Jack, plus 2 free slots).
- Never show phone numbers on screen. The Live WhatsApp page should show names only.

## Git rules

Work on a branch named `yourname/what`, open a pull request, and get one teammate to look before merging. Never commit keys, phone numbers or real chats (`data/wa_*.json*` is git-ignored).
