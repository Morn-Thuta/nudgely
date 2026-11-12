# Team plan: Finals (updated Thu 12 Nov 2026, afternoon)

> Earlier plans: [3 Nov finals plan](docs/archive/TEAM_finals_plan_3nov.md) · [hackathon plan](docs/archive/TEAM_hackathon.md)
> How the pieces fit: **[docs/V1_ARCHITECTURE.md](docs/V1_ARCHITECTURE.md)** · Pitch + demo plan: **[docs/Pitch_Plan.md](docs/Pitch_Plan.md)** · Competitors: [docs/Competitors.md](docs/Competitors.md)

**Finals: Saturday 14 Nov**, report to MPH A (Block B, B2, SIM Clementi) **8:30–9:00 AM**. Feature freeze **Fri 13 Nov, noon**.
Format (organisers' advisory): **7 minutes, hard stop**, of which **4:00 is the live demo of one complete use case**, then 5 minutes Q&A.

## What's live now

| | Where | Status |
|---|---|---|
| Website (3D landing, judge chat, QR screen, dashboard) | https://nudgely-navy.vercel.app | ✅ redeploys on every push to `main` |
| Judge chat | https://nudgely-navy.vercel.app/try · QR at `/present` | ✅ real AI, saved to Supabase |
| Dashboard (team login) | `/login` → `/dashboard` | ✅ Thuta's account has team access |
| AI backend + WhatsApp bot | https://nudgely-api.onrender.com (`/health`) | ✅ |
| **Live send** (Campaign → Live) | Sends Aisha's reviewed nudge on WhatsApp to the demo phone | ✅ built · needs `LIVE_RECIPIENTS` in Render |
| Backup chat + QR on the backend | https://nudgely-api.onrender.com/try · `/qr` | ✅ |
| Load test: 12 people at once | 36/36 answered, typical reply 8 s, slowest 16 s | ✅ |
| Daily AI cap | 2,000 answered messages a day, then a person takes over | ✅ |

## Decisions (Thu 12 Nov)

- **MantaGO dropped from the live product.** Its API never gives us chat text, broadcasts never arrived (tested again today: the approved pack to Dythan never came), and messages to the connected number don't reach MantaGO at all. Everything runs on **WhatsApp's official Cloud API**. Old MantaGO code stays for the Streamlit backup only. Stage answer is in the run sheet.
- **Mock POS dropped.** It doesn't fit the one-use-case demo. The time went to the live send.
- **Demo = one customer's journey ("Aisha")**, not a tour. See the run sheet.
- **Judges use the web chat**, not WhatsApp: Meta's test number only reaches 5 approved phones.

## To do before the freeze (Fri noon)

| Task | Owner |
|---|---|
| Add `LIVE_RECIPIENTS` = `{"C001": "<Aisha phone, 65...>"}` in Render → Environment | Thuta |
| First real live send from the dashboard to the Aisha phone; check the reply shows her history | Thuta + Dythan |
| `gh auth refresh -h github.com -s workflow`, then Claude pushes the keep-awake job | Thuta |
| Slides 1–8 and rehearse the demo from docs/Pitch_Plan.md (Dythan demo, Jack the rest) | Dythan + Jack |
| **Record the backup video** of the full Aisha journey, save it on the presenting laptop | Dythan |
| Business slide: problem size, pricing, cost per shop, competitors (sourced) | Shareef |
| Jailbreak / Singlish / fake product checks on the live bot | Jack |
| Rehearse aloud twice with a timer, on the laptop we bring | Everyone |
| Tag the frozen version `finals-v1`; **no pushes to `main` after noon** | Thuta (Claude) |

## Finals morning (Sat)

1. **Aisha phone** sends any WhatsApp message to **+1 555-164-9508** (opens WhatsApp's 24-hour window; without it the live send refuses).
2. Open https://nudgely-api.onrender.com/health and the website once to wake both (the keep-awake job does this too once pushed).
3. Log in to the dashboard on the presenting laptop; check the Campaign → Live section shows Aisha.
4. Laptop: charger, display adapter, notifications muted, sleep off, backup video on the desktop.

## Judge pinch points

| Question | Honest answer | Owner |
|---|---|---|
| "What is working now, and what is proposed?" | Working: web + WhatsApp AI chat, tags with evidence, handover, STOP, dashboard, live send to a demo phone, uplift model on public data. Proposed: real business number, sales upload, pilot | Thuta |
| "Why not MantaGO?" | We started on it. Its API doesn't share incoming chat text and its WhatsApp delivery didn't work on our account, so we built on WhatsApp's official API, which makes the AI conversation possible | Thuta |
| "What starts and ends the conversation?" | Starts: the owner approves a nudge for a customer the uplift model picked, or the customer messages first. Ends: the customer's question is answered, a person takes over, or STOP | Dythan |
| "When does it hand over to a person?" | HUMAN, complaints/refunds, photos and voice notes, anything it can't verify (prices, stock not in the list), and when the daily AI cap is hit | Jack |
| "How do you know it brought people back?" | No-message comparison group + `returns.py` matches sales to who was messaged | Jack |
| "Your evidence is overseas data" | True: 57% of extra visits from the top 30%, about 1.9x random, 38–85% over seven splits. Next step is a local pilot | Shareef |
| "What if it makes up a price?" | Every reply is checked; invented price → handed to a person | Jack |
| "What if a service fails?" | AI falls back to other models; if all fail, a person takes over; backup video if the venue Wi-Fi fails | Thuta |
| "What does it cost per shop?" | ~$0.00025 per AI reply + WhatsApp fees | Shareef |
| "Is my data safe? PDPA?" | Phone numbers never stored (hashed), names stripped before the AI, team-only dashboard, STOP works | Thuta |
| "What would a pilot need?" | One shop, a real WhatsApp business number, 4 weeks of sales export, consent wording | Shareef |

## Demo rules

- The bot answers about items the shop stocks; anything else goes to a person **on purpose**.
- Never show phone numbers, keys or dashboards with secrets on screen.
- If something fails live, switch to the backup video **and say it's the backup**. Never present simulated output as live.

## Git rules

Frontend in `web/`, backend in `api/` and `nudgely/`. `main` deploys both, so run the checks before pushing. After Fri noon, only fixes agreed by Thuta.
