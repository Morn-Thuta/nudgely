# Team plan

## Where we are (Wed 21 Oct)

Already done: repo, uplift model (top 30% captures ~53% of extra visits, about 1.8x random), 30 demo customers + chats, LLM scripts, full 5-page app, MantaGO client + test script.
Still open: MantaGO token (waiting on Eslitec), WhatsApp connection, LLM run for all 30, deploy, pitch.

## Who does what

| Person | Role | Owns | Why it matters |
|---|---|---|---|
| **Thuta** | Lead + MantaGO | Live send (F5), tag write-back (F6), integration, final review | Riskiest part. Without a real message on a phone, the demo is only a simulation |
| **Dythan** | Pitch + demo lead | Story, deck, 7-min video, presenting, Q&A | Creativity 30% + Presentation 25% = 55% of marks |
| **Jack** | Message quality | Run LLM scripts, hand-check and fix all 30 messages | The messages are what judges read |
| **Jayden** | App + deploy | Streamlit Cloud, signed-out test, UI polish, README | The judges' link has to just work |
| **Shareef** | Numbers + docs | Update numbers everywhere, responsible AI, brief, submission form | Wrong or old numbers lose trust |

---

## Thuta: MantaGO + lead

**Wed**
- [ ] Get the API token + secret (Eslitec), put them in `.env`, run `python scripts/test_mantago.py members`
- [ ] Connect WhatsApp (fallback: Instagram) and publish the bot
- [ ] First real test message lands on your phone (`test_mantago.py send ... --yes`)

**Thu**
- [ ] All 5 teammates message the bot. Map them to Persuadable customers in `data/test_accounts.json` (C001-C010)
- [ ] Add the MantaGO token, secret and test accounts to Streamlit secrets (with Jayden)
- [ ] Try tag write-back (F6): `test_mantago.py tag --to <clientId> --yes`. Skip it if the API fights back
- [ ] 6pm: full flow works locally, from customers through to a real send

**Fri**
- [ ] Live send rehearsal for the video. Test phones message the bot within 24h of recording
- [ ] Final review of everything before submit

## Dythan: pitch + demo lead

**Wed**
- [ ] Read `docs/One_Page_Brief.md` and click through the app (`streamlit run app/streamlit_app.py`)
- [ ] Deck outline: problem → who/what/prove → live demo → evidence → responsible AI → impact → next steps
- [ ] Write the demo script: the exact 2-minute click path a judge follows

**Thu**
- [ ] Full slides with real numbers (from Shareef)
- [ ] 7-min video script, timed. The demo section ends with the phone getting the message
- [ ] Prepare Q&A answers: why uplift and not churn score? Why is the 53% noisy? What about the WhatsApp 24h rule? Cost?

**Fri**
- [ ] Record the video (by 1pm), final deck. 3pm: everything done

## Jack: message quality

**Wed / Thu morning** (needs the OpenRouter key in `.env`)
- [ ] `python scripts/extract_tags.py` (rerun if it stops at the free daily limit)
- [ ] `python scripts/write_messages.py`
- [ ] Hand-check all 30 in the app's Customer detail page. Every message must:
  - be under 300 characters, friendly, Singapore tone
  - use a real tag from the chat, with nothing invented (stock, prices, offers)
  - apologise first for complaints (C002, C009), with no sales push
  - offer a discount only to Persuadables, max 10%
  - end with "Reply STOP to opt out"
- [ ] Fix bad ones: rerun with `--only C00X --force`, or edit `data/messages.json` by hand
- [ ] Give Dythan the 3 best messages for the slides

**Fri**
- [ ] Final read of all 30. Commit and push

## Jayden: app + deploy

**Wed**
- [ ] Run the app locally: `pip install -r requirements.txt`, then `streamlit run app/streamlit_app.py`
- [ ] Deploy on share.streamlit.io: repo `Morn-Thuta/nudgely`, main file `app/streamlit_app.py`, Python 3.12
- [ ] Paste secrets (see `.streamlit/secrets.toml.example`). Ask Thuta for the keys, and never commit them

**Thu**
- [ ] Click through all 5 pages on the deployed link and list anything broken or ugly. Fix it
- [ ] Check on a phone screen too
- [ ] 11pm: the deployed link works in an incognito/signed-out browser. Set app sharing to public

**Fri**
- [ ] Final incognito test after the last push. Update README with the live link

## Shareef: numbers + docs

**Wed**
- [x] Update the numbers in `docs/PRD.md` and `docs/One_Page_Brief.md`: targeting is now **top 30% captures ~53% of extra visits (about 1.8x random)**, not 45% / 1.5x. Source: `data/uplift_summary.json` (done by Jack, 21 Oct - all 5 places)
- [x] Find out: problem statement number, exact team name, deadline time on Fri, Lenta licence (PS1 · Nudgely · 11:59 PM SGT · see PRD open questions)

**Thu**
- [x] Responsible AI section for deck + form: fake data disclosure, opt-in + opt-out, no gender/age/children in the model, names and phones stripped before the LLM, owner previews every message, keys not in GitHub → `docs/Responsible_AI.md`
- [x] 150-word summary + finished one-page brief → `docs/Submission_Draft.md`, `docs/One_Page_Brief.md` + `.pdf`
- [x] Fill in the submission form as a draft → `docs/Submission_Draft.md`
- [ ] Check every link opens without an access request. **Failing now:** the repo is private (Thuta: make it public; history checked, no keys) and the app isn't deployed (Jayden). See `docs/Submission_Draft.md` section 4
- [x] Numbers sheet for deck and video → `docs/Numbers.md`. **Hillstrom corrected: +72% / 2.2x is the men's email group only; all email is +57% / about 1.9x**

**Fri**
- [ ] Final number check across deck, brief, video and app (they must all match)
- [ ] Submit the form after all 5 have reviewed it, well before the deadline

---

## Checkpoints

- [ ] **Wed 11pm:** a MantaGO message lands on a phone (Thuta). App deployed (Jayden)
- [ ] **Thu 6pm:** full flow works locally, from customers through to send. All 30 messages checked (Jack)
- [ ] **Thu 11pm:** the deployed link works signed out (Jayden). Slides have real numbers (Dythan)
- [ ] **Fri 3pm:** video, deck and brief done. All links open without access requests
- [ ] **Fri, well before the deadline:** form submitted, all 5 reviewed it

## Agreed rules

- **Data formats** are fixed by `data/examples/`. Don't change columns or keys without telling the team.
- **Holdout:** 10% held out at random (fixed seed) from the *chosen* top-N customers.
- **Expected extra visits** = sum of `uplift` across messaged customers.
- **Labels:** Persuadable = top 30% uplift. Sure Thing = not Persuadable and top 30% `p_no_msg`. Lost Cause = everyone else.
- **No keys in GitHub.** `.env`, `.streamlit/secrets.toml` and `data/test_accounts.json` are git-ignored.
- **Pull before you push.** Small commits, clear messages.

## WhatsApp limits

- Free text only within **24h of the customer's last message**. After that, Meta-approved templates only. Demo fix: test phones message the bot shortly before the demo.
- Customers must opt in. Every message ends with an opt-out line.

## Ask Eslitec

- [ ] How do we get the Open API token? "API Integration Settings" isn't in Setting → Advanced (bot ID KQe1rqRaJ)
- [ ] Does a free-trial bot support the Open API?
- [ ] WhatsApp: does MantaGO give us a number, or do we bring our own?
- [ ] What happens if we broadcast outside the 24h window?

## Risks and fallbacks

| Risk | Fallback |
|---|---|
| MantaGO token / WhatsApp blocked | Instagram. If that's blocked too, the app marks messages "ready to send" and we send one by hand in MantaGO for the video |
| Free LLM daily limit | Scripts resume where they stopped. Use a second teammate's key |
| LLM invents facts | Auto-check drops tags without real quotes. Jack hand-checks all 30 |
| Tag API unclear | Skip F6. Show tags in the app only |

## Judging (Top 10 shortlist)

Creativity 30% · Technical 25% · Presentation 25% · Real-world impact 20%. Responsible AI, disclosure and safe data use are **mandatory**.
