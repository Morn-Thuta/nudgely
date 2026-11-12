/**
 * Builds docs/Nudgely_Finals_Pitch.pptx - the 8-slide deck for the 7-minute finals pitch.
 * Content and timing follow docs/Pitch_Plan.md section 5; every number is from docs/Numbers.md.
 * The spoken script for each slide is in its speaker notes.
 *
 *   npm install pptxgenjs react-icons react react-dom sharp   # once, anywhere; point NODE_PATH at it
 *   node scripts/build_pitch_deck.js <qr.png> [out.pptx] [path/to/apply_theme.js]
 *
 * qr.png: the judges' QR code for https://nudgely-navy.vercel.app/try (any QR generator, or
 *   python -c "import segno; segno.make('https://nudgely-navy.vercel.app/try').save('qr.png', scale=24)").
 * apply_theme.js: Claude's pptx-skill helper that writes the theme colours into the file (pptxgenjs
 *   cannot). Without it the deck still builds, but scheme colours fall back to Office's stock blue.
 *
 * Headings use Outfit (the website's font, free on Google Fonts). Install it on the presenting laptop;
 * without it PowerPoint substitutes a similar sans, and every box has room to spare for that.
 */

const fs = require("fs");
const path = require("path");
const pptxgen = require("pptxgenjs");
const React = require("react");
const ReactDOMServer = require("react-dom/server");
const sharp = require("sharp");
const lu = require("react-icons/lu");

const [qrPath, outArg, themer] = process.argv.slice(2);
if (!qrPath || !fs.existsSync(qrPath)) {
  console.error("usage: node scripts/build_pitch_deck.js <qr.png> [out.pptx] [apply_theme.js]");
  process.exit(1);
}
const OUT = outArg || "docs/Nudgely_Finals_Pitch.pptx";

// The website's palette: cream paper, deep green, lime accent.
const HEX = {
  ink: "182C21", white: "FFFFFF", dark: "0C1D15", cream: "F4F5EF", green: "19704A", lime: "B9DF9B",
  muted: "5C6B61", warmInk: "82613D", line: "DBE2D8", warm: "F2E9D8", sage: "E6EEDD",
};
const THEME = {
  name: "Nudgely",
  headFontFace: "Outfit",
  bodyFontFace: "Calibri",
  colors: {
    dk1: HEX.ink, lt1: HEX.white, dk2: HEX.dark, lt2: HEX.cream,
    accent1: HEX.green, accent2: HEX.lime, accent3: HEX.muted, accent4: HEX.warmInk,
    accent5: HEX.line, accent6: HEX.warm, hlink: HEX.green, folHlink: HEX.muted,
  },
};

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.33 x 7.5
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
pres.author = "Bongo Gang";
pres.title = "Nudgely - AI-GNITION 2026 finals";
const C = pres.SchemeColor;
const M = 0.6; // side margin
const HEAD = "+mj-lt"; // theme heading font

// ---------------------------------------------------------------- layouts
pres.defineSlideMaster({
  title: "DARK",
  background: { color: C.text2 },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: M + 0.1, y: 2.2, w: 8.4, h: 1.6,
        fontSize: 60, bold: true, color: C.background1, valign: "bottom", align: "left" }, text: " " } },
    { placeholder: { options: { name: "body", type: "body", x: M + 0.1, y: 3.95, w: 8.4, h: 0.9,
        fontSize: 26, color: C.accent2, valign: "top", align: "left" }, text: " " } },
  ],
});

pres.defineSlideMaster({
  title: "CONTENT",
  background: { color: C.background2 },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: M, y: 0.45, w: 12.1, h: 0.95,
        fontSize: 36, bold: true, color: C.text1, valign: "middle", align: "left" }, text: " " } },
    { text: { text: "Kampung Fresh, Mei Ling, Hafiz and Aisha are fictional. Numbers: docs/Numbers.md",
        options: { x: M, y: 7.0, w: 9, h: 0.28, fontSize: 10, color: C.accent3, isTextBox: true, margin: 0 } } },
    { placeholder: { options: { name: "slideNumber", type: "sldNum", x: 12.2, y: 7.0, w: 0.5, h: 0.28,
        fontSize: 10, color: C.accent3, align: "right" } } },
  ],
});

// ---------------------------------------------------------------- helpers
const declared = {};
function newSlide(master, section) {
  if (!declared[section]) {
    pres.addSection({ title: section });
    declared[section] = true;
  }
  return pres.addSlide({ masterName: master, sectionTitle: section });
}
const shadow = () => ({ type: "outer", blur: 12, offset: 2, angle: 90, color: "A9B8AE", opacity: 0.3 });

async function icon(Icon, hex, px = 256) {
  const svg = ReactDOMServer.renderToStaticMarkup(React.createElement(Icon, { color: "#" + hex, size: px }));
  const png = await sharp(Buffer.from(svg)).resize(px, px).png().toBuffer();
  return "image/png;base64," + png.toString("base64");
}

async function iconCircle(s, Icon, x, y, d, fill, iconHex, name) {
  s.addShape(pres.ShapeType.ellipse, { x, y, w: d, h: d, fill: { color: fill }, line: { color: fill },
    objectName: name + "-circle" });
  const pad = d * 0.25;
  s.addImage({ data: await icon(Icon, iconHex), x: x + pad, y: y + pad, w: d - 2 * pad, h: d - 2 * pad,
    altText: name, objectName: name + "-icon" });
}

function card(s, x, y, w, h, fill, name, withShadow = true) {
  s.addShape(pres.ShapeType.roundRect, { x, y, w, h, rectRadius: 0.14, fill: { color: fill },
    line: { color: fill }, shadow: withShadow ? shadow() : undefined, objectName: name });
}

function text(s, t, o) {
  s.addText(t, { isTextBox: true, margin: 0, color: C.text1, valign: "top", ...o });
}

(async function build() {
  // ============================================================ 1. Team + one line
  {
    const s = newSlide("DARK", "Story");
    s.addText([{ text: "nudgely", options: {} }, { text: " ↗", options: { color: C.accent2 } }], { placeholder: "title" });
    s.addText("A little nudge. A lasting connection.", { placeholder: "body" });
    text(s, "Team Bongo Gang  ·  AI-GNITION 2026 Finals", { x: M + 0.1, y: 5.55, w: 8, h: 0.4, fontSize: 16,
      color: C.background1, bold: true });
    text(s, "Thuta  ·  Dythan  ·  Jack  ·  Shareef  ·  Jayden", { x: M + 0.1, y: 6.0, w: 8, h: 0.4,
      fontSize: 16, color: C.accent6 });
    s.addShape(pres.ShapeType.ellipse, { x: 9.45, y: 1.7, w: 3.3, h: 3.3, fill: { color: C.accent1 },
      line: { color: C.accent1 }, objectName: "brand-disc" });
    s.addImage({ data: await icon(lu.LuSprout, HEX.lime), x: 10.25, y: 2.5, w: 1.7, h: 1.7, altText: "Nudgely sprout",
      objectName: "brand-sprout" });
    s.addNotes(
      "One breath on this slide, then move to slide 2.\n\n" +
        "PROBLEM (0:00-0:20, Jack, 50 words max) starts on the next slide.");
  }

  // ============================================================ 2. User and problem
  {
    const s = newSlide("CONTENT", "Story");
    s.addText("Mei Ling messages everyone the same way", { placeholder: "title" });

    // The shop: awning, sign, window and door, built from shapes.
    const sx = M + 0.2, sy = 1.95;
    card(s, sx, sy + 0.95, 3.9, 3.0, C.background1, "shop-body");
    s.addShape(pres.ShapeType.rect, { x: sx - 0.15, y: sy + 0.55, w: 4.2, h: 0.55, fill: { color: C.accent1 },
      line: { color: C.accent1 }, objectName: "shop-awning" });
    for (let i = 0; i < 6; i++)
      s.addShape(pres.ShapeType.rect, { x: sx - 0.15 + i * 0.7 + 0.35, y: sy + 0.55, w: 0.35, h: 0.55,
        fill: { color: C.accent2 }, line: { color: C.accent2 }, objectName: `awning-stripe-${i}` });
    card(s, sx + 0.55, sy, 2.8, 0.5, C.text2, "shop-sign", false);
    text(s, "KAMPUNG FRESH", { x: sx + 0.55, y: sy, w: 2.8, h: 0.5, fontSize: 15, bold: true, charSpacing: 3,
      color: C.accent2, align: "center", valign: "middle", fontFace: HEAD });
    card(s, sx + 0.35, sy + 1.45, 1.9, 1.3, C.accent6, "shop-window", false);
    s.addImage({ data: await icon(lu.LuStore, HEX.warmInk), x: sx + 0.95, y: sy + 1.75, w: 0.7, h: 0.7,
      altText: "shop", objectName: "shop-window-icon" });
    card(s, sx + 2.55, sy + 1.45, 1.0, 2.25, C.accent5, "shop-door", false);
    text(s, "Mei Ling, 52", { x: sx, y: sy + 4.15, w: 3.9, h: 0.4, fontSize: 18, bold: true, fontFace: HEAD });
    text(s, "Runs Kampung Fresh in Tampines", { x: sx, y: sy + 4.55, w: 3.9, h: 0.35, fontSize: 14,
      color: C.accent3 });

    // Three WhatsApp moments.
    const rows = [
      { who: "KF", fill: C.accent1, bubble: C.accent2, msg: "10% off everything this Sunday!", sub: "Sunday blast, to every customer",
        tag: "Same message for all" },
      { who: "H", fill: C.accent3, bubble: C.background1, msg: "See you Saturday!", sub: "Hafiz, 61 · comes every Saturday anyway",
        tag: "Discount given away" },
      { who: "A", fill: C.accent4, bubble: C.background1, msg: "can tell me when oat milk is back?",
        sub: "Aisha, 34 · Seen 3 weeks ago, no reply", tag: "Lost to the supermarket" },
    ];
    const bx = 5.5;
    for (const [i, r] of rows.entries()) {
      const y = 1.85 + i * 1.65;
      s.addShape(pres.ShapeType.ellipse, { x: bx, y: y + 0.1, w: 0.62, h: 0.62, fill: { color: r.fill },
        line: { color: r.fill }, objectName: `avatar-${i}` });
      text(s, r.who, { x: bx, y: y + 0.1, w: 0.62, h: 0.62, fontSize: 15, bold: true, color: C.background1,
        align: "center", valign: "middle" });
      card(s, bx + 0.85, y, 4.0, 0.82, r.bubble, `bubble-${i}`);
      text(s, r.msg, { x: bx + 1.05, y, w: 3.65, h: 0.82, fontSize: 17, valign: "middle" });
      text(s, r.sub, { x: bx + 0.9, y: y + 0.92, w: 4.4, h: 0.32, fontSize: 12, color: C.accent3 });
      s.addShape(pres.ShapeType.roundRect, { x: 10.6, y: y + 0.17, w: 2.1, h: 0.48, rectRadius: 0.24,
        fill: { color: C.accent6 }, line: { color: C.accent6 }, objectName: `outcome-${i}` });
      text(s, r.tag, { x: 10.6, y: y + 0.17, w: 2.1, h: 0.48, fontSize: 12, bold: true, color: C.accent4,
        align: "center", valign: "middle" });
    }
    s.addNotes(
      "PROBLEM (0:00-0:20), Jack, 50 words max:\n\n" +
        "\"This is Mei Ling. She runs Kampung Fresh in Tampines. Every Sunday she sends the same '10% off' to all her " +
        "customers. Hafiz comes every Saturday anyway, so that's margin given away. Aisha asked about oat milk three " +
        "weeks ago. Nobody remembered. She shops at the supermarket now.\"");
  }

  // ============================================================ 3. Pain point + expected result
  {
    const s = newSlide("CONTENT", "Story");
    s.addText("Blasting barely works", { placeholder: "title" });
    text(s, "+0.7", { x: M, y: 1.75, w: 3.6, h: 1.5, fontSize: 88, bold: true, color: C.accent1, fontFace: HEAD,
      valign: "middle" });
    text(s, "points", { x: M + 0.05, y: 3.2, w: 3.4, h: 0.45, fontSize: 22, bold: true, fontFace: HEAD });
    text(s, "10.3% came back with no SMS, 11.0% with one", { x: M + 0.05, y: 3.75, w: 3.5, h: 0.75, fontSize: 15 });
    text(s, "687,000 grocery shoppers, randomised test (Lenta)", { x: M + 0.05, y: 4.6, w: 3.5, h: 0.6, fontSize: 12,
      color: C.accent3 });

    s.addChart(pres.ChartType.bar, [{ name: "Came back", labels: ["No SMS", "SMS"], values: [10.3, 11.0] }], {
      x: 4.35, y: 1.65, w: 3.9, h: 4.6, barDir: "col", barGapWidthPct: 60,
      chartColors: [HEX.muted, HEX.green], invertedColors: [HEX.muted],
      showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: '0.0"%"', dataLabelFontSize: 14,
      dataLabelColor: HEX.ink, dataLabelFontFace: "+mn-lt",
      valAxisMinVal: 0, valAxisMaxVal: 12, valAxisHidden: true, valGridLine: { style: "none" },
      catAxisLabelColor: HEX.muted, catAxisLabelFontSize: 14, catAxisLabelFontFace: "+mn-lt",
      catGridLine: { style: "none" }, showLegend: false, objectName: "lenta-bars",
    });

    s.addShape(pres.ShapeType.rightArrow, { x: 8.4, y: 3.55, w: 0.75, h: 0.55, fill: { color: C.accent2 },
      line: { color: C.accent2 }, objectName: "arrow" });
    card(s, 9.35, 1.85, 3.35, 4.1, C.text2, "measure-card");
    await iconCircle(s, lu.LuScale, 9.7, 2.2, 0.8, C.accent1, HEX.lime, "measure");
    text(s, "We measure one thing", { x: 9.7, y: 3.2, w: 2.75, h: 0.5, fontSize: 18, bold: true, color: C.accent2,
      fontFace: HEAD });
    text(s, "Extra return visits per message, against customers who got nothing", { x: 9.7, y: 3.75, w: 2.75, h: 1.6,
      fontSize: 18, color: C.background1 });
    s.addNotes(
      "RESULT (0:20-0:40), Jack, 50 words max:\n\n" +
        "\"Blasting barely works: in a randomised test on 687,000 grocery shoppers, an SMS lifted visits from 10.3% " +
        "to 11.0%. Mei Ling needs the right message to the right person. We measure one thing: extra return visits " +
        "per message, against customers who got nothing.\"\n\n" +
        "HANDOVER, said while Shareef walks to the laptop (no silence): \"Shareef is Mei Ling for the next four minutes.\"");
  }

  // ============================================================ 4. Live demo
  {
    const s = newSlide("DARK", "Demo");
    s.addText("Live: Kampung Fresh", { placeholder: "title" });
    s.addText("Mei Ling's dashboard  ·  Aisha's WhatsApp", { placeholder: "body" });
    s.addShape(pres.ShapeType.roundRect, { x: M + 0.1, y: 1.5, w: 1.55, h: 0.5, rectRadius: 0.25,
      fill: { color: C.accent2 }, line: { color: C.accent2 }, objectName: "live-pill" });
    s.addShape(pres.ShapeType.ellipse, { x: M + 0.32, y: 1.67, w: 0.17, h: 0.17, fill: { color: C.accent1 },
      line: { color: C.accent1 }, objectName: "live-dot" });
    text(s, "LIVE", { x: M + 0.6, y: 1.5, w: 0.9, h: 0.5, fontSize: 15, bold: true, charSpacing: 3, color: C.text2,
      valign: "middle" });
    await iconCircle(s, lu.LuMessageCircle, 9.75, 1.95, 2.9, C.accent1, HEX.lime, "demo");
    s.addNotes(
      "LIVE DEMO (0:40-4:40), Shareef, 4:00. Show this for 2 seconds, then the dashboard + Aisha's WhatsApp.\n\n" +
        "Beats (Pitch_Plan.md section 3): Aisha in Customers (Persuadable, oat milk + party tags) -> Hafiz is a Sure " +
        "Thing -> Campaign skips Hafiz, holds back a comparison group -> edit Aisha's draft, tick, Send on WhatsApp -> " +
        "it arrives -> Aisha asks about oat milk, AI replies with new tags -> refund request -> Needs a person -> STOP -> " +
        "Opted out badge -> back to slide 8.\n\n" +
        "If anything fails, decide in 5 seconds (section 4). Never present the recording as live.\n\n" +
        "Close: \"Everything you just saw happened live. Jack?\"");
  }

  // ============================================================ 5. How it works
  {
    const s = newSlide("CONTENT", "How it works");
    s.addText("Pick who, say what, prove it worked", { placeholder: "title" });
    const steps = [
      [lu.LuReceipt, "Chats + sales", "the shop's own data"],
      [lu.LuTarget, "Uplift model", "who a message changes"],
      [lu.LuPenLine, "AI writes", "from their own words"],
      [lu.LuUserCheck, "Owner approves", "nothing sends alone"],
      [lu.LuSend, "WhatsApp", "official API"],
      [lu.LuTags, "Replies tagged", "each with its evidence"],
      [lu.LuScale, "No-message group", "shows the real lift"],
    ];
    const groups = [["Pick who", 0, 2], ["Say what", 2, 6], ["Prove it", 6, 7]];
    const gap = 0.32, w = (12.1 - gap * 6) / 7, y = 2.55, h = 3.15;
    const xAt = (i) => M + i * (w + gap);
    for (const [label, a, b] of groups) {
      const x = xAt(a), right = xAt(b - 1) + w;
      s.addShape(pres.ShapeType.roundRect, { x, y: 1.75, w: right - x, h: 0.5, rectRadius: 0.25,
        fill: { color: C.accent1 }, line: { color: C.accent1 }, objectName: `group-${label}` });
      text(s, label, { x, y: 1.75, w: right - x, h: 0.5, fontSize: 16, bold: true, color: C.background1,
        align: "center", valign: "middle", fontFace: HEAD });
    }
    for (const [i, [Icon, title, sub]] of steps.entries()) {
      const x = xAt(i);
      card(s, x, y, w, h, C.background1, `step-${i}`);
      await iconCircle(s, Icon, x + (w - 0.8) / 2, y + 0.35, 0.8, C.accent2, HEX.green, `step-${i}`);
      text(s, title, { x: x + 0.1, y: y + 1.35, w: w - 0.2, h: 0.75, fontSize: 16, bold: true, align: "center",
        fontFace: HEAD });
      text(s, sub, { x: x + 0.1, y: y + 2.15, w: w - 0.2, h: 0.8, fontSize: 13, color: C.accent3, align: "center" });
      if (i < steps.length - 1)
        s.addShape(pres.ShapeType.rightArrow, { x: x + w + 0.06, y: y + h / 2 - 0.11, w: gap - 0.12, h: 0.22,
          fill: { color: C.accent1 }, line: { color: C.accent1 }, objectName: `arrow-${i}` });
    }
    text(s, "Runs on ten numbers any shop's receipts have: phone, date, amount", { x: M, y: 6.1, w: 12.1, h: 0.4,
      fontSize: 15, color: C.accent3, align: "center" });
    s.addNotes(
      "HOW IT WORKS (4:40-5:40), Jack, 140 words max across slides 5 and 6. Slide 5:\n\n" +
        "\"Three parts. First, an uplift model. It doesn't ask who might leave; it asks who a message actually changes. " +
        "It runs on ten things any shop's receipts have. Second, an AI reads each conversation and keeps the details " +
        "with the customer's exact words as evidence, then drafts the nudge from them. Third, every campaign keeps a " +
        "no-message group, so the shop sees its own lift.\"");
  }

  // ============================================================ 6. Data, safety, human control
  {
    const s = newSlide("CONTENT", "How it works");
    s.addText("Data, safety, human control", { placeholder: "title" });
    const tiles = [
      [lu.LuUserCheck, "Owner approves every send"],
      [lu.LuPhoneOff, "Phone numbers never stored"],
      [lu.LuEyeOff, "Names hidden from the AI"],
      [lu.LuHand, "Unsure? A person takes over"],
      [lu.LuOctagonX, "STOP works everywhere"],
      [lu.LuGauge, "Daily cap on AI spend"],
    ];
    const tw = 3.85, th = 2.2, gx = 0.28, gy = 0.35;
    for (const [i, [Icon, label]] of tiles.entries()) {
      const x = M + (i % 3) * (tw + gx), y = 1.75 + Math.floor(i / 3) * (th + gy);
      card(s, x, y, tw, th, C.background1, `tile-${i}`);
      await iconCircle(s, Icon, x + 0.35, y + 0.4, 0.95, C.accent1, HEX.lime, `tile-${i}`);
      text(s, label, { x: x + 0.35, y: y + 1.45, w: tw - 0.6, h: 0.55, fontSize: 19, bold: true, fontFace: HEAD,
        valign: "middle" });
    }
    s.addNotes(
      "Slide 6, said as a list (~25 s):\n\n" +
        "\"Nothing is sent without a person approving it. Phone numbers are never stored, only scrambled. Names are " +
        "removed before text reaches the AI. Every reply is checked; if it can't verify a price or stock, or someone " +
        "asks for a refund, a person takes over. STOP works on every channel. And a daily cap stops runaway AI costs.\"");
  }

  // ============================================================ 7. Difference
  {
    const s = newSlide("CONTENT", "Why us");
    s.addText("Only Nudgely picks by uplift and proves the lift", { placeholder: "title" });
    const cols = ["Rules and tags", "Predicted risk", "Uplift"];
    const rowsY = ["Extra visits vs a no-message group", "Opens and clicks", "No proof"];
    const cells = [
      ["", "Optimove (big brands)", "Nudgely, for a 300‑customer shop"],
      ["SleekFlow · WATI · respond.io · MantaGO · Eber · StoreHub", "Klaviyo (online stores)", ""],
      ["WhatsApp Business app", "", ""],
    ];
    const gx0 = 3.45, gy0 = 2.2, cw = 3.0, ch = 1.12, g = 0.12;
    text(s, "How it picks who to message  →", { x: gx0, y: 1.55, w: 3 * cw + 2 * g, h: 0.35, fontSize: 13,
      bold: true, color: C.accent3, align: "center" });
    for (const [c, label] of cols.entries())
      text(s, label, { x: gx0 + c * (cw + g), y: 1.82, w: cw, h: 0.35, fontSize: 15, bold: true, align: "center",
        fontFace: HEAD, color: c === 2 ? C.accent1 : C.text1 });
    text(s, "How it proves it worked  ↓", { x: M, y: 1.82, w: 2.7, h: 0.35, fontSize: 13, bold: true,
      color: C.accent3 });
    for (const [r, label] of rowsY.entries()) {
      text(s, label, { x: M, y: gy0 + r * (ch + g), w: 2.65, h: ch, fontSize: 15, bold: true, fontFace: HEAD,
        valign: "middle", color: r === 0 ? C.accent1 : C.text1 });
      for (let c = 0; c < 3; c++) {
        const us = r === 0 && c === 2;
        const x = gx0 + c * (cw + g), y = gy0 + r * (ch + g);
        card(s, x, y, cw, ch, us ? C.accent1 : cells[r][c] ? C.background1 : C.accent5, `cell-${r}-${c}`, us);
        if (cells[r][c])
          text(s, cells[r][c], { x: x + 0.2, y, w: cw - 0.4, h: ch, fontSize: us ? 17 : 14, bold: us,
            color: us ? C.background1 : C.text1, align: "center", valign: "middle", fontFace: us ? HEAD : undefined });
      }
    }
    text(s, "WhatsApp tools send well. Enterprise suites measure lift. Nudgely does both for a corner shop.",
      { x: M, y: 6.15, w: 12.1, h: 0.4, fontSize: 14, color: C.accent3, align: "center" });
    s.addNotes(
      "DIFFERENCE (5:40-6:20), Jack, 95 words max:\n\n" +
        "\"WhatsApp tools like SleekFlow and WATI are great at sending, but you choose who gets what by hand, and you " +
        "see opens, not extra visits. Enterprise suites like Optimove measure lift, but they're built for big brands " +
        "with marketing teams. Nudgely is the only one that, for a corner shop, picks who a message changes, writes it " +
        "from their own words, and proves it worked.\"\n\n" +
        "If asked: \"we found no Singapore player using uplift\" (not \"there are none\"). Sources: docs/Competitors.md.");
  }

  // ============================================================ 8. Next step / pilot
  {
    const s = newSlide("CONTENT", "Why us");
    s.addText("Proven overseas. Next: one Singapore shop", { placeholder: "title" });

    card(s, M, 1.75, 4.3, 4.55, C.text2, "evidence-card");
    text(s, "57%", { x: M + 0.35, y: 1.95, w: 3.6, h: 1.4, fontSize: 80, bold: true, color: C.accent2,
      fontFace: HEAD, valign: "middle" });
    text(s, "of the extra visits came from our top 30%, against 30% at random", { x: M + 0.35, y: 3.4, w: 3.6,
      h: 1.05, fontSize: 17, color: C.background1 });
    text(s, "About 1.9x random. Ranged 38–85% across 7 test splits on public grocery data (Lenta).",
      { x: M + 0.35, y: 4.6, w: 3.6, h: 1.0, fontSize: 12, color: C.accent6 });

    const px = 5.2;
    card(s, px, 1.75, 4.15, 4.55, C.background1, "pilot-card");
    text(s, "Our limitation", { x: px + 0.35, y: 1.95, w: 3.5, h: 0.4, fontSize: 14, bold: true, color: C.accent4 });
    text(s, "The evidence is overseas", { x: px + 0.35, y: 2.35, w: 3.5, h: 0.5, fontSize: 19, bold: true,
      fontFace: HEAD });
    text(s, "A four-week pilot needs", { x: px + 0.35, y: 3.15, w: 3.5, h: 0.4, fontSize: 14, bold: true,
      color: C.accent1 });
    text(s, [
      { text: "One Singapore shop", options: { bullet: true, breakLine: true } },
      { text: "Its own WhatsApp number", options: { bullet: true, breakLine: true } },
      { text: "Four weeks of sales", options: { bullet: true, breakLine: true } },
      { text: "A no-message group", options: { bullet: true } },
    ], { x: px + 0.35, y: 3.6, w: 3.5, h: 2.4, fontSize: 18, paraSpaceAfter: 8 });

    const qx = 9.6;
    card(s, qx, 1.75, 3.1, 4.55, C.background1, "qr-card");
    s.addImage({ path: path.resolve(qrPath), x: qx + 0.3, y: 1.95, w: 2.5, h: 2.5, altText: "QR code to talk to Kampung Fresh",
      objectName: "judges-qr" });
    text(s, "Talk to Kampung Fresh", { x: qx + 0.2, y: 4.6, w: 2.7, h: 0.45, fontSize: 18, bold: true,
      align: "center", fontFace: HEAD });
    text(s, "nudgely-navy.vercel.app/try", { x: qx + 0.2, y: 5.1, w: 2.7, h: 0.4, fontSize: 13, color: C.accent3,
      align: "center" });
    s.addNotes(
      "NEXT STEP (6:20-7:00), Jack, 95 words max. QR stays up into Q&A:\n\n" +
        "\"Our honest limitation: the evidence is overseas. On a public grocery dataset our top 30% captured 57% of " +
        "the extra visits, about 1.9 times random, though it ranged from 38 to 85% across tests. A Singapore shop still " +
        "has to prove it. So the next step is a four-week pilot: one shop, its WhatsApp number, a sales export, and a " +
        "no-message group. Scan the code and talk to Kampung Fresh yourselves. Thank you.\"\n\n" +
        "STOP AT 7:00 even mid-sentence. Dythan shows 1:00 at 6:00 and STOP at 6:50.");
  }

  await pres.writeFile({ fileName: OUT });
  if (themer) {
    const { applyTheme } = require(themer);
    await applyTheme(OUT, THEME);
    console.log("written " + OUT + " (themed)");
  } else {
    console.log("written " + OUT + " - NO THEME APPLIED, colours will be Office defaults");
  }
})().catch((e) => {
  console.error(e);
  process.exit(1);
});
