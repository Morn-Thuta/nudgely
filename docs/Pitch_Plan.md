# Finals pitch and demo plan (Sat 14 Nov 2026)

**Presenters:** Jack (story, how it works, difference, next step) · Dythan (live demo, playing the shop owner).
**Off stage:** Thuta plays **Aisha** on her phone and watches the backend · Shareef keeps time and holds the backup video.
**Format (organisers' advisory):** 7:00 hard stop, then 5:00 Q&A. One complete use case. Never present simulated output as live.

Everything shown is fictional (Kampung Fresh, Mei Ling, Aisha, Hafiz) or our own test data. Numbers come only from [Numbers.md](Numbers.md).
Competitor facts: [Competitors.md](Competitors.md).

---

## 1. The story we tell

One shop, one owner, two customers. The intro sets them up; the demo pays them off.

| Who | Role in the story | In our data |
|---|---|---|
| **Mei Ling**, 52 | Runs **Kampung Fresh**, a neighbourhood grocer in Tampines. Knows her regulars by face, sends a Sunday-night WhatsApp blast to everyone | The dashboard user (Dythan plays her) |
| **Aisha Rahman**, 34 | Asked *"can tell me when oat milk is back?"* three weeks ago, and is planning her son's birthday party. Nobody followed up. She's drifting to the supermarket | C001 · *Persuadable*, highest predicted uplift |
| **Hafiz Rahim**, 61 | Comes every Saturday for rice, eggs and kai lan. Gets the "10% off" blast anyway, so Mei Ling gives away margin for nothing | C021 · *Sure Thing* |

The problem in one line: **Mei Ling messages everyone the same way, so she pays Hafiz to do what he'd do anyway and still loses Aisha.**
The promise in one line: **the right nudge, to the person it will bring back, in their own words, proven against people who got nothing.**

---

## 2. The seven minutes

Speaking speed: about 140 words a minute. Word counts below are the limit, not a target.

| Clock | Section | Who | Slide / screen |
|---|---|---|---|
| 0:00–0:20 | Problem | Jack | Slide 1 → 2 |
| 0:20–0:40 | Result | Jack | Slide 3 |
| 0:40–4:40 | **Live demo** | Dythan | Slide 4 (2 s), then the dashboard + Aisha's WhatsApp |
| 4:40–5:40 | How it works | Jack | Slides 5 and 6 |
| 5:40–6:20 | Difference | Jack | Slide 7 |
| 6:20–7:00 | Next step | Jack | Slide 8 (QR stays up into Q&A) |

### 0:00–0:20 · Problem (Jack, ≤ 50 words)

> *Slide 1 for one breath: "nudgely · Bongo Gang".*
> "This is Mei Ling. She runs Kampung Fresh in Tampines. Every Sunday she sends the same '10% off' to all her customers. Hafiz comes every Saturday anyway, so that's margin given away. Aisha asked about oat milk three weeks ago. Nobody remembered. She shops at the supermarket now."

Slide 2: illustration of the shop with three phone bubbles: the blast, Hafiz's "see you Saturday", Aisha's unanswered "can tell me when oat milk is back?" with a faded "Seen 3 weeks ago".

### 0:20–0:40 · Result (Jack, ≤ 50 words)

> "Blasting barely works: in a randomised test on 687,000 grocery shoppers, an SMS lifted visits from 10.3% to 11.0%. Mei Ling needs the right message to the right person. We measure one thing: extra return visits per message, against customers who got nothing."

Slide 3: "+0.7 points" big (Lenta, Numbers.md #3) → arrow → "Measured: extra visits per message vs a no-message group".

Handover line (Jack): **"Dythan is Mei Ling for the next four minutes."** Dythan steps to the laptop while Jack says it. Do not wait in silence.

### 0:40–4:40 · Live demo (Dythan, 4:00): see section 3

### 4:40–5:40 · How it works (Jack, ≤ 140 words)

Slide 5, one diagram, left to right: **Chats + sales → Uplift model → AI writes the message → Owner approves → WhatsApp → Replies tagged → Holdout comparison**.

> "Three parts. First, an uplift model. It doesn't ask who might leave; it asks who a message actually changes. It runs on ten things any shop's receipts have. Second, an AI reads each conversation and keeps the details with the customer's exact words as evidence, then drafts the nudge from them. Third, every campaign keeps a no-message group, so the shop sees its own lift."

Slide 6, "Data, safety, human control" (say these as a list, ~25 s):

> "Nothing is sent without a person approving it. Phone numbers are never stored, only scrambled. Names are removed before text reaches the AI. Every reply is checked; if it can't verify a price or stock, or someone asks for a refund, a person takes over. STOP works on every channel. And a daily cap stops runaway AI costs."

### 5:40–6:20 · Difference (Jack, ≤ 95 words)

Slide 7: 2×2 positioning. X axis "Who to message: rules/tags → causal uplift". Y axis "Proof: open/click rates → measured lift vs holdout". WhatsApp tools (WhatsApp Business app, SleekFlow, WATI, respond.io, MantaGO) bottom-left; enterprise retention suites (Optimove, Klaviyo) top-left/top-middle; Nudgely top-right, labelled "for a 300-customer shop".

> "WhatsApp tools like SleekFlow and WATI are great at sending, but you choose who gets what by hand, and you see opens, not extra visits. Enterprise suites like Optimove measure lift, but they're built for big brands with marketing teams. Nudgely is the only one that, for a corner shop, picks who a message changes, writes it from their own words, and proves it worked."

### 6:20–7:00 · Next step (Jack, ≤ 95 words)

Slide 8: "Limitation → Pilot ask", with the judges' QR in the corner.

> "Our honest limitation: the evidence is overseas. On a public grocery dataset our top 30% captured 57% of the extra visits, about 1.9 times random, though it ranged from 38 to 85% across tests. A Singapore shop still has to prove it. So the next step is a four-week pilot: one shop, its WhatsApp number, a sales export, and a no-message group. Scan the code and talk to Kampung Fresh yourselves. Thank you."

**Stop at 7:00 even mid-sentence.** Shareef shows a "1:00" card at 6:00 and "STOP" at 6:50.

---

## 3. The live demo, click by click (Dythan, 4:00)

### Screen layout on the projector

- **Left 60%:** Chrome window, dashboard at https://nudgely-navy.vercel.app/dashboard, signed in, zoom 110%.
- **Right 40%:** **WhatsApp Web** in a separate Chrome profile, linked to the Aisha phone, opened straight on the chat with **+1 555-164-9508** (save the contact as "Kampung Fresh"). Chat list collapsed / scrolled so no other chats or numbers show. Notifications off.
- Thuta (as Aisha) types on the phone; it appears in WhatsApp Web on screen. If mirroring fails, Dythan reads the phone aloud.

### Beat by beat

| # | Clock | Do (Dythan) | Say (Dythan) | Checklist item |
|---|---|---|---|---|
| 1 | 0:40 | **Customers** → search "Aisha" → open **Aisha Rahman** | "Here's Aisha in Mei Ling's customer book. Nudgely read her chats and kept two things, with her own words: she wants oat milk back, and her son's birthday party. The model marks her *Persuadable*: a message is likely to bring her back." | Customer + segment |
| 2 | 1:10 | Close; point at **Hafiz Rahim** in the list | "Hafiz is a *Sure Thing*: he comes every Saturday. Messaging him only gives away a discount." | Personalisation by history |
| 3 | 1:25 | **Campaign** → leave the audience slider, point at the three tabs | "So the campaign skips Hafiz, and holds back a comparison group who get nothing. That group is how Mei Ling will see if it worked." | Decision branch + measurement |
| 4 | 1:55 | Scroll to **Live** → Aisha's draft. Change one word so judges see it's editable. Tick *I've read this message*. **Send on WhatsApp** → confirm | "Nothing goes out until Mei Ling reads it, edits it and confirms." | Trigger + human approval |
| 5 | 2:20 | Right side: the message arrives in Aisha's WhatsApp | "That's a real WhatsApp message, just sent." | Trigger, live |
| 6 | 2:30 | Aisha types: **"Wah thanks! Is the oat milk really back? Need it for the party Saturday"** | While waiting (6–10 s): "She's replying to the shop's AI assistant, not to Mei Ling. Watch Mei Ling's inbox." → click **Conversations**, open Aisha | Personalised response |
| 7 | 2:50 | Reply arrives on both screens; point at new tag chips | "It answered from what it knows about her, and noted what she just said. Every tag shows the words it came from." | Personalised + memory |
| 8 | 3:15 | Aisha types: **"Last order came 2 hours late, I want a refund"** | "Now something the AI shouldn't decide." | Needs a person |
| 9 | 3:30 | Reply + the **Needs a person** flag on the conversation | "Refunds go to a person. It says so honestly and flags Mei Ling." | Handoff |
| 10 | 3:50 | Aisha types: **STOP** | "And if she's had enough…" | Opt-out |
| 11 | 4:05 | Confirmation on WhatsApp; **Opted out** badge on the dashboard | "One word. She's out of every future campaign, automatically." | Declines |
| 12 | 4:20 | Back to slide (QR) | "Everything you just saw happened live. Jack?" | Close |

Replies are generated live, so exact words vary. If a reply surprises you, read it out and move on. Do not retry on stage.

### Filling AI waits (6–10 s each)

Use these, never silence: "It's checking her history…" · "Every reply is checked before it's sent…" · "Meanwhile on Mei Ling's side…" (click to Conversations).

---

## 4. If something fails (decide in 5 seconds)

| What happens | Do |
|---|---|
| Send says "24 hours" | Aisha never messaged this morning. Thuta sends "hi" from the phone, Dythan clicks Send again after 5 s |
| Send errors anything else | Say "Let me show you the recorded run of this step," Shareef plays the backup video from beat 4. Say clearly it's the recording |
| No reply after 20 s | "The AI is slow on venue Wi-Fi; here's the recording of this step." Backup video |
| Dashboard doesn't update | Refresh once; else read the reply from WhatsApp Web |
| Projector / laptop dies | Jack continues with slides on the spare laptop; Dythan shows the phone to the front row |
| Over time at 4:40 | Skip beats 10–11 (STOP); Jack mentions opt-out in How it works |

---

## 5. Slides (8 maximum, advisory list)

| # | Advisory slot | Content | Owner |
|---|---|---|---|
| 1 | Team + one line | "nudgely · A little nudge. A lasting connection." · Bongo Gang names | Dythan |
| 2 | User and problem | Mei Ling, Hafiz, Aisha scenario illustration | Dythan |
| 3 | Pain point + expected result | Lenta +0.7 pts SMS stat → "extra visits per message vs no-message group" | Jack |
| 4 | Live demo | Title card "Live: Kampung Fresh" (2 s) | Dythan |
| 5 | How it works | One left-to-right diagram | Jack |
| 6 | Data, safety, human control | Six icons: approve · no numbers stored · names removed · reply check → person · STOP · daily cap | Jack |
| 7 | Difference | Positioning 2×2 from Competitors.md | Shareef → Dythan |
| 8 | Next step / pilot | 57% / 1.9x / 38–85% (footnote: Lenta, 7 splits) · pilot ask · judges' QR (https://nudgely-navy.vercel.app/present) | Shareef → Jack |

Style: the landing page look (cream, green, Outfit font). One idea per slide, ≤ 15 words of text. Speaker words live here, not on the slides.

---

## 6. Q&A (5:00): answer first, 30–45 s, then the trade-off

**Jack answers:** AI, data, model, measurement, safety. **Dythan answers:** product, flow, what's live. If unsure, the other adds one sentence, no more.

| Question | Answer | Who |
|---|---|---|
| What is working now, and what is proposed? | Working: WhatsApp and web chat with live AI, tags with evidence, handover, STOP, the dashboard, live send to a demo phone, the uplift model on public data. Proposed: a real business number, sales import, the local pilot | Dythan |
| Why this segment? | Neighbourhood shops already run on WhatsApp but have no marketing team; their customers are few enough that every wasted or annoying message matters | Jack |
| What starts and ends the conversation? | Starts: the owner approves a nudge for someone the model picked, or the customer messages first. Ends: question answered, a person takes over, or STOP | Dythan |
| When does it hand over? | Refunds and complaints, HUMAN, photos or voice notes, anything it can't verify like a price or stock not in the shop's list, and if the daily AI budget runs out | Jack |
| How do you measure retention? | Every campaign holds back a random no-message group. We match the shop's sales to both groups and compare return visits. The difference is the lift | Jack |
| What data does it use? | The shop's own chats and receipts. No age, gender or children, on purpose. Phone numbers are never stored; names are removed before the AI | Jack |
| What needs human approval? | Every outgoing campaign message. The AI only answers customers who wrote first, and hands over when unsure | Dythan |
| What if a service fails? | The AI falls back to other models; if all fail, a person takes over. If WhatsApp is down nothing is sent, and the owner sees it | Jack |
| How does the owner verify the result? | Every campaign keeps a held-back group. In a pilot, the shop's sales export is matched to both groups and the difference in return visits is the lift. Today the Results page shows the public-data evidence; per-campaign results need the pilot's sales | Dythan |
| What would a pilot need? | One shop, a WhatsApp business number, a 4-week sales export, consent wording at signup, and a no-message group | Jack |
| Why not MantaGO? | We started on MantaGO. Its API doesn't share incoming chat text and its WhatsApp delivery didn't work on our account, so we built on WhatsApp's official API, which is what makes the AI conversation possible. MantaGO-style platforms are natural delivery partners | Jack |
| Your evidence is overseas | True, and we say so: 57% from the top 30%, about 1.9x random, ranged 38–85%. That's why we ask for a pilot, not a sale | Jack |
| What does it cost? | About $0.00025 per AI reply plus WhatsApp's per-message fee | Jack |
| Isn't this just SleekFlow / WATI? | They send; we decide who and what, and prove it. We'd plug into them as the delivery layer | Jack |

---

## 7. Before Finals Day

| When | What | Who |
|---|---|---|
| Fri before noon | Freeze. Tag `finals-v1`. No pushes after | Thuta |
| Fri | Slides 1–8 done in the landing style | Dythan (+Shareef slides 7–8) |
| Fri | **Two timed full rehearsals** on the presenting laptop, with the real send each time. Reset Aisha between runs: `python scripts/reset_demo_customer.py --yes`, then Aisha phone says "hi" | All |
| Fri | Record the backup video of the full 4:00 demo; save it on the laptop desktop and on Shareef's laptop | Dythan |
| Fri | Set up WhatsApp Web in its own Chrome profile on the presenting laptop, linked to the Aisha phone | Thuta + Dythan |
| Sat 7:30 | Reset Aisha. Aisha phone sends "hi" to the bot. Open /health. Sign in to the dashboard. Check Campaign → Live shows Aisha | Thuta |
| Sat 8:30 | Report to MPH A. Laptop charged, charger, HDMI/USB-C adapter, phone hotspot ready | All |
| Before going on | Notifications off (laptop and Aisha phone), sleep off, browser zoom set, both windows arranged, slides on slide 1 | Dythan |

### Rehearsal scorecard (fill in each run)

| Run | Total time | Demo time | Send worked | Reply time | Handover flag | STOP badge | Notes |
|---|---|---|---|---|---|---|---|
| 1 | | | | | | | |
| 2 | | | | | | | |
