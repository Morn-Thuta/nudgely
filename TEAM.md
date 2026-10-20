# Team plan

> **Status: draft.** Roles get assigned once everyone agrees on the idea. Put your name next to a role when you take it.

## Roles

| Role | Owns | Name |
|---|---|---|
| A: Data/ML | F1 uplift model, F2 labels, F7 chart data | _TBD_ |
| B: LLM | F3 tag extraction, F4 message writer, fake chats | _TBD_ |
| C: MantaGO + backend | F5 send, F6 tag write-back, `nudgely/mantago.py` | _TBD_ |
| D: App + deploy | Streamlit pages 1-5, deploy, secrets | _TBD_ |
| E: Pitch + docs | Deck, brief, video, submission form | _TBD_ |

## Decide first (everyone, 30 min)

- [ ] Everyone agrees on the idea (read [docs/One_Page_Brief.md](docs/One_Page_Brief.md))
- [ ] Assign roles A-E
- [ ] Problem statement number (1 or 2)
- [ ] Exact team name as registered
- [ ] Submission deadline time on Fri 23 Oct
- [ ] LLM provider and whose paid key
- [ ] Lenta dataset licence (for the disclosure field)
- [ ] Channel: **WhatsApp** (fallback: Instagram)

## Day 1: Wed 21 Oct, build the parts

| Role | Tasks |
|---|---|
| C | Create bot, connect WhatsApp, publish, get token. Run `scripts/test_mantago.py`. 3-5 teammates message the bot and their `clientId`s get collected |
| A | Drop gender from features. Train two-model uplift on 50% of Lenta (float32). Save `lenta_scored_test.csv` + `uplift_summary.json`. **Pick the 30 demo rows today** (10 per label) |
| B | Write `chats.json` (30 customers, 3-8 messages each) to match A's rows. Draft prompt 1 |
| D | Streamlit skeleton, 5 pages, using `data/examples/`. **Deploy to Streamlit Cloud today** |
| E | Deck outline, brief draft, 150-word summary |

- [ ] **Wed 11pm:** a MantaGO message lands on a phone, and the uplift CSVs are saved

## Day 2: Thu 22 Oct, join it up

| Role | Tasks |
|---|---|
| A | `customers.csv` (fake names, scores, labels, features, `mantago_client_id`). Chart data |
| B | Prompt 2. Run both scripts. **Hand-check all 30 messages** |
| C | Finish `mantago.py` (send, members, tags). Map test `clientId`s |
| D | Wire real files + MantaGO client. Sliders, three lists, Send, `send_log.csv`, regenerate max 3. Secrets |
| E | Real numbers in slides. Video script |

- [ ] **Thu 6pm:** full flow works locally, from customers through to send
- [ ] **Thu 11pm:** the deployed link works in a signed-out browser

## Day 3: Fri 23 Oct, polish and submit

- [ ] A: final numbers check. If dropping gender changed 45% / 1.5x, update everywhere
- [ ] B: fix bad messages
- [ ] C: live send rehearsal. **Test phones message the bot within 24h of recording** (WhatsApp window)
- [ ] D: signed-out browser test, "How to try this" box, README
- [ ] E: record the 7-min video, final deck, form
- [ ] **Fri 3pm:** video, deck and brief done. All links open without access requests
- [ ] Everyone reviews, then submit well before the deadline

## Agreed rules (so we can work in parallel)

- **File formats** are fixed by `data/examples/`. Don't change columns or keys without telling the team.
- **Holdout:** 10% is held out at random (fixed seed) from the *chosen* top-N customers, not from all 30.
- **Expected extra visits** for a campaign = sum of `uplift` across messaged customers.
- **Labels:** Persuadable = top 30% uplift. Sure Thing = not Persuadable and top 30% `p_no_msg`. Lost Cause = everyone else.
- **Message rules:** ≤300 characters, uses at least one real tag, apology first for complaints, discount only for Persuadable and capped at 10%, ends with "Reply STOP to opt out".
- **No keys in GitHub.** `.env` and `.streamlit/secrets.toml` are git-ignored.

## WhatsApp limits to know

- Free text can only be sent within **24h of the customer's last message**. After that, only Meta-approved templates. Demo fix: test phones message the bot shortly before the demo.
- Customers must opt in. Every message ends with an opt-out line.
- Unverified businesses can start about 250 new conversations per day. That's fine for a demo.

## Ask Eslitec (Day 1)

- [ ] Does a free-trial bot support the Open API? (Error 1002 means no)
- [ ] WhatsApp: does MantaGO give us a number, or do we bring our own?
- [ ] What happens if we broadcast free text outside the 24h window? Is there a template option?
- [ ] What does the callback URL receive (reply events)?
- [ ] Rate limits?

## Risks and fallbacks

| Risk | Fallback |
|---|---|
| MantaGO/WhatsApp setup blocked | Switch to Instagram. If that's blocked too, the app marks messages "ready to send" and we send one by hand for the video |
| Tag API unclear | Skip F6; show tags in the app only |
| LLM invents facts | Strict prompt rules + hand-check all 30 |
| Judges burn API credits | Cached outputs; regenerate max 3 per session |
| Lenta too big | 50% sample, float32; deploy small CSVs only |

## Judging (Top 10 shortlist)

Creativity 30% · Technical 25% · Presentation 25% · Real-world impact 20%. Responsible AI, disclosure and safe data use are **mandatory**.
