# Finals run sheet (Sat 14 Nov 2026)

Built from the organisers' Finals Advisory: **7 minutes, hard stop. Explain the problem, show the
solution working, make the result easy to understand. One complete use case.** Then 5 minutes Q&A.

Fictional shop: **Kampung Fresh** (Tampines grocer). Fictional customer: **Aisha Rahman (C001)**,
played by a teammate's phone. Everything on screen is fictional or our own test data.

## Screens

| Screen | What |
|---|---|
| Projector | Laptop: slides → dashboard (https://nudgely-navy.vercel.app/dashboard, logged in) |
| "Aisha" phone | Teammate's phone, WhatsApp chat with **+1 555-164-9508**. Mirror it, or hold it to a document camera |
| Judges | Their own phones: QR at https://nudgely-navy.vercel.app/present → web chat |

## The 7 minutes

| Time | Section (advisory) | Screen | Say / do |
|---|---|---|---|
| 0:00–0:20 | **Problem** | Slide 2 | Neighbourhood shops send the same "10% off" broadcast to everyone. Regulars drift away and the owner never learns if the message worked. |
| 0:20–0:40 | **Result** | Slide 3 | Goal: more return visits per message. Measured against a no-message comparison group, not guessed. |
| 0:40–4:40 | **Live demo** | Dashboard + Aisha phone | The Aisha journey below. Keep the QR visible in a corner for judges. |
| 4:40–5:40 | **How it works** | Slide 5 | Uplift model picks *who*; the AI writes *what* from the customer's own chat; WhatsApp official API delivers; every reply checked; Supabase with team-only access; phone numbers never stored. |
| 5:40–6:20 | **Difference** | Slide 6 | (1) Messages only people a nudge actually changes, (2) every message grounded in what that customer said, (3) proves its own effect with a comparison group. |
| 6:20–7:00 | **Next step** | Slide 7 | Main limit: evidence is overseas data (57% of extra visits from the top 30%, ~1.9x random, 38–85% across splits). Pilot needs one shop, a WhatsApp business number and 4 weeks of sales. |

## Live demo: Aisha's journey (4:00)

Advisory checklist in brackets.

| # | Time | Do | Say |
|---|---|---|---|
| 1 | 0:00 | Dashboard → **Customers**: open Aisha | "Aisha asked about oat milk and is planning her son's birthday. The model says a nudge changes what she does: she's *Persuadable*." **[customer + segment]** |
| 2 | 0:30 | **Campaign**: audience slider; point at Will message / Held out / Skipped | "Regulars who'd come back anyway and people a message won't move are skipped. 10% are held back to measure the effect." **[decision branch]** |
| 3 | 1:00 | **Campaign → Live**: edit Aisha's draft, tick, **Send on WhatsApp**, confirm | "Nothing goes out until a person reads it and confirms." **[trigger + human approval]** |
| 4 | 1:30 | Aisha phone: message arrives. Aisha replies *"Is the oat milk back? Need it for the party Saturday"* | "It remembers what she said weeks ago." **[personalised response]** |
| 5 | 2:15 | Dashboard → **Conversations**: Aisha's chat updates by itself, with tags and the exact words behind each | "Every tag shows its evidence." |
| 6 | 2:45 | Aisha: *"Last order came 2 hours late, can I get a refund?"* → bot hands over; flag on the dashboard | "Refunds go to a person. It never pretends." **[needs a person]** |
| 7 | 3:15 | Aisha: *STOP* → confirmation; dashboard shows opted out | "One word and she's out. Excluded from every future campaign." **[opt-out]** |
| 8 | 3:40 | Point to the QR | "Try it yourselves now: scan, ask the shop anything." |

Exact replies vary (it's a live AI). Rehearse the same lines; if a reply surprises, read it out and move on.

## If something fails

| Failure | Do |
|---|---|
| Live send refuses: "24 hours" | The Aisha phone didn't message the shop this morning. Send "hi" from it, wait 5 s, send again |
| Message doesn't arrive in 30 s | Switch to the backup video: "This is our recorded run of the same flow." Never present it as live |
| Dashboard doesn't update | Refresh once. Then show the conversation on the phone instead |
| Venue Wi-Fi down | Phone hotspot for the laptop; else backup video |

## Q&A (30–45 s each: answer first, then the trade-off)

See the judge pinch points in [TEAM.md](../TEAM.md). Advisory questions to rehearse:
what works now vs proposed · what if a service fails · what data it uses · what needs human approval ·
how the owner verifies the result · what a pilot needs · why this segment · what starts and ends the
conversation · when it hands over · how retention is measured.

## Before Finals Day (advisory checklist)

- [ ] Stable version tagged `finals-v1` (Fri noon), nothing pushed after
- [ ] Full demo rehearsed on the presenting laptop, timed, twice
- [ ] Dashboard login, live send, WhatsApp bot all tested on Fri
- [ ] OpenRouter credit checked ($4.91 left on Thu, about 1,500+ replies; daily cap 2,000)
- [ ] Keys, Render/Vercel/Supabase consoles and phone numbers off screen
- [ ] Backup video saved locally on the laptop
- [ ] Notifications muted, sleep disabled, charger + display adapter packed
- [ ] Morning: Aisha phone messages the bot; /health opened; dashboard logged in
- [ ] Report to MPH A 8:30–9:00 AM

## Between rehearsals

Each run leaves Aisha opted out (STOP), flagged for a person and linked to the phone. Reset her:

```bash
python scripts/reset_demo_customer.py --yes
```

Then the Aisha phone sends the bot any message again (re-links nothing yet, but re-opens the 24-hour window).
Do a final reset on Sat morning before the venue, then one message from the Aisha phone.
