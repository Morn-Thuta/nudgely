/**
 * Builds docs/How_the_model_works.pptx - the plain-English deck on how the
 * uplift model works. Prose version: docs/HOW_THE_MODEL_WORKS.md.
 *
 * Edit the numbers here, not the slides: nothing is drawn by hand.
 *
 *   npm install pptxgenjs          # once, anywhere; then point NODE_PATH at it
 *   node scripts/build_model_deck.js [out.pptx] [path/to/apply_theme.js]
 *
 * The second argument is Claude's pptx-skill helper that writes theme colours
 * into the package - pptxgenjs cannot. Without it the deck still builds, but
 * every scheme colour falls back to Office's stock palette, so the greens go.
 */

const pptxgen = require("pptxgenjs");

const THEME = {
  name: "Nudgely",
  headFontFace: "Cambria",
  bodyFontFace: "Calibri",
  colors: {
    dk1: "0D1E17", lt1: "FFFFFF", dk2: "12251D", lt2: "EDF5F0",
    accent1: "0E9F6E", accent2: "3FD79A", accent3: "6C8578",
    accent4: "C2603F", accent5: "2E4A3D", accent6: "A7C4B5",
    hlink: "0E9F6E", folHlink: "6C8578",
  },
};

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE";            // 13.3 x 7.5
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
pres.author = "Bongo Gang";
pres.title = "How the Nudgely model works";
const C = pres.SchemeColor;

const M = 0.7;

// ----------------------------------------------------------------- layouts
pres.defineSlideMaster({
  title: "TITLE_DARK", background: { color: C.text2 },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: M + 0.2, y: 2.45, w: 11.4, h: 1.5,
        fontSize: 48, bold: true, color: C.background1, valign: "bottom" }, text: " " } },
    { placeholder: { options: { name: "body", type: "body", x: M + 0.2, y: 4.1, w: 10.2, h: 1.3,
        fontSize: 20, color: C.accent2, valign: "top" }, text: " " } },
  ],
});

pres.defineSlideMaster({
  title: "SECTION_DARK", background: { color: C.text2 },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: M + 0.2, y: 2.7, w: 11.4, h: 2.1,
        fontSize: 40, bold: true, color: C.accent2, valign: "middle" }, text: " " } },
  ],
});

const lightObjects = (extra) => ([
  { placeholder: { options: { name: "title", type: "title", x: M, y: 0.52, w: 12.0, h: 0.85,
      fontSize: 36, bold: true, color: C.text1, valign: "middle" }, text: " " } },
  { text: { text: "Nudgely  ·  how the model works", options: { x: M, y: 6.85, w: 6, h: 0.3,
      fontSize: 10, color: C.accent3, isTextBox: true, margin: 0 } } },
  { placeholder: { options: { name: "slideNumber", type: "sldNum", x: 12.3, y: 6.85, w: 0.5, h: 0.3,
      fontSize: 10, color: C.accent3, align: "right" } } },
  ...(extra || []),
]);

pres.defineSlideMaster({ title: "TITLE_ONLY", background: { color: C.background1 }, objects: lightObjects() });

pres.defineSlideMaster({
  title: "CONTENT", background: { color: C.background1 },
  objects: lightObjects([
    { placeholder: { options: { name: "body", type: "body", x: M, y: 1.55, w: 12.0, h: 5.1,
        fontSize: 16, color: C.text1 }, text: " " } },
  ]),
});

pres.defineSlideMaster({
  title: "CHART", background: { color: C.background1 },
  objects: lightObjects([
    { placeholder: { options: { name: "chart", type: "chart", x: M, y: 1.55, w: 7.7, h: 4.9,
        color: C.text1 }, text: " " } },
    { placeholder: { options: { name: "body", type: "body", x: 8.6, y: 1.7, w: 4.05, h: 4.75,
        fontSize: 15, color: C.text1 }, text: " " } },
  ]),
});

pres.defineSlideMaster({
  title: "CLOSE_DARK", background: { color: C.text2 },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: M + 0.2, y: 0.9, w: 11.4, h: 1.0,
        fontSize: 38, bold: true, color: C.background1, valign: "middle" }, text: " " } },
    { placeholder: { options: { name: "body", type: "body", x: M + 0.2, y: 2.2, w: 11.4, h: 2.3,
        fontSize: 20, color: C.background1 }, text: " " } },
  ],
});

// ------------------------------------------------------------- helpers
const declaredSections = {};
function newSlide(masterName, sectionTitle) {
  if (!declaredSections[sectionTitle]) { pres.addSection({ title: sectionTitle }); declaredSections[sectionTitle] = true; }
  return pres.addSlide({ masterName: masterName, sectionTitle: sectionTitle });
}
const shadow = () => ({ type: "outer", blur: 10, offset: 2, angle: 90, color: "9FB5A9", opacity: 0.35 });

function card(slide, opts) {
  const fill = opts.fill || C.background2;
  slide.addShape(pres.ShapeType.roundRect, {
    x: opts.x, y: opts.y, w: opts.w, h: opts.h, rectRadius: 0.12,
    fill: { color: fill }, line: { color: fill },
    shadow: shadow(), objectName: opts.name,
  });
}

function circleNum(slide, o) {
  const d = o.d || 0.52;
  const fill = o.fill || C.accent1;
  slide.addShape(pres.ShapeType.ellipse, { x: o.x, y: o.y, w: d, h: d,
    fill: { color: fill }, line: { color: fill }, objectName: o.name });
  slide.addText(o.text, { x: o.x, y: o.y, w: d, h: d, align: "center", valign: "middle",
    fontSize: 15, bold: true, color: "FFFFFF", isTextBox: true, margin: 0 });
}

// ============================================================ 1. title
{
  const s = newSlide("TITLE_DARK", "Opening");
  s.addText("How the model works", { placeholder: "title" });
  s.addText("One number per customer, and what it is actually for", { placeholder: "body" });
  s.addShape(pres.ShapeType.roundRect, { x: 0.9, y: 1.55, w: 2.5, h: 0.46, rectRadius: 0.23,
    fill: { color: C.accent1 }, line: { color: C.accent1 }, objectName: "brand-pill" });
  s.addText("NUDGELY", { x: 0.9, y: 1.55, w: 2.5, h: 0.46, align: "center", valign: "middle",
    fontSize: 13, bold: true, charSpacing: 3, color: "FFFFFF", isTextBox: true, margin: 0 });
  s.addText("Bongo Gang  ·  AI-GNITION 2026", { x: 0.9, y: 5.55, w: 7, h: 0.4, fontSize: 13,
    color: C.accent6, isTextBox: true, margin: 0 });
  s.addNotes("Plain-English walkthrough of the uplift model. The one thing to land: the model picks who, not what we say.");
}

// ============================================================ 2. the problem
{
  const s = newSlide("TITLE_ONLY", "The problem");
  s.addText("You cannot message everyone", { placeholder: "title" });

  const stats = [
    { n: "30", l: "customers in the shop", sub: "a real shop has thousands" },
    { n: "9", l: "actually get a message", sub: "the ones worth spending on" },
    { n: "21", l: "are left alone on purpose", sub: "and the shop is better off for it" },
  ];
  stats.forEach(function (d, i) {
    const x = M + i * 4.1;
    card(s, { x: x, y: 1.9, w: 3.8, h: 2.1, name: "stat-" + i });
    s.addText(d.n, { x: x + 0.3, y: 2.05, w: 3.2, h: 0.95, fontSize: 44, bold: true,
      color: C.accent1, isTextBox: true, margin: 0, valign: "middle" });
    s.addText(d.l, { x: x + 0.3, y: 3.0, w: 3.2, h: 0.35, fontSize: 15, bold: true,
      color: C.text1, isTextBox: true, margin: 0 });
    s.addText(d.sub, { x: x + 0.3, y: 3.38, w: 3.2, h: 0.4, fontSize: 12,
      color: C.accent3, isTextBox: true, margin: 0 });
  });

  s.addText("So the real question is not “who might come back?”\nIt is “which few people are worth a message?”", {
    x: M, y: 4.5, w: 12.0, h: 1.3, fontSize: 24, italic: true, color: C.text1,
    isTextBox: true, margin: 0, lineSpacingMultiple: 1.3,
  });
  s.addNotes("Set up the constraint first. Everything the model does is a way of spending a limited number of messages well.");
}

// ============================================================ 3. the question
{
  const s = newSlide("SECTION_DARK", "The one question");
  s.addText([
    { text: "The model asks one question:\n", options: { fontSize: 26, color: "FFFFFF", bold: false, breakLine: true } },
    { text: "if I text this person, does anything change?", options: { fontSize: 40, color: C.accent2, bold: true } },
  ], { placeholder: "title" });
  s.addNotes("This is the whole idea in one line. Say it slowly.");
}

// ============================================================ 4. guess twice (core)
{
  const s = newSlide("TITLE_ONLY", "The one question");
  s.addText("It answers by guessing twice", { placeholder: "title" });
  s.addText("For every customer: the chance they come back if you say nothing, and the chance if you text them.", {
    x: M, y: 1.35, w: 12.0, h: 0.35, fontSize: 14, color: C.accent3, isTextBox: true, margin: 0 });

  const people = [
    { name: "Aisha Rahman", a: "28%", b: "39%", gap: "+11", verdict: "Message her", good: true },
    { name: "Amirah Salleh", a: "68%", b: "63%", gap: "−5", verdict: "Coming back anyway", good: false },
    { name: "Ravi Kumar", a: "2%", b: "3%", gap: "+1", verdict: "Nothing will bring him back", good: false },
  ];
  people.forEach(function (p, i) {
    const x = M + i * 4.1;
    card(s, { x: x, y: 1.85, w: 3.8, h: 3.8, name: "person-" + i });
    s.addText(p.name, { x: x + 0.28, y: 2.0, w: 3.24, h: 0.38, fontSize: 17, bold: true,
      color: C.text1, isTextBox: true, margin: 0 });

    s.addText("Say nothing", { x: x + 0.28, y: 2.5, w: 1.75, h: 0.3, fontSize: 13, color: C.accent3, isTextBox: true, margin: 0 });
    s.addText(p.a, { x: x + 2.1, y: 2.46, w: 1.42, h: 0.34, fontSize: 18, bold: true, align: "right",
      color: C.text1, isTextBox: true, margin: 0 });
    s.addText("Text them", { x: x + 0.28, y: 2.88, w: 1.75, h: 0.3, fontSize: 13, color: C.accent3, isTextBox: true, margin: 0 });
    s.addText(p.b, { x: x + 2.1, y: 2.84, w: 1.42, h: 0.34, fontSize: 18, bold: true, align: "right",
      color: C.text1, isTextBox: true, margin: 0 });

    s.addShape(pres.ShapeType.roundRect, { x: x + 0.28, y: 3.38, w: 3.24, h: 1.15, rectRadius: 0.1,
      fill: { color: p.good ? C.accent1 : "DDE7E1" }, line: { color: p.good ? C.accent1 : "DDE7E1" },
      objectName: "gap-" + i });
    s.addText("THE GAP", { x: x + 0.45, y: 3.5, w: 1.6, h: 0.26, fontSize: 10, bold: true, charSpacing: 2,
      color: p.good ? "C8F2E0" : C.accent3, isTextBox: true, margin: 0 });
    s.addText(p.gap, { x: x + 0.45, y: 3.76, w: 2.9, h: 0.68, fontSize: 36, bold: true,
      color: p.good ? "FFFFFF" : C.accent3, isTextBox: true, margin: 0, valign: "middle" });

    s.addText(p.verdict, { x: x + 0.28, y: 4.65, w: 3.24, h: 0.85, fontSize: 15, bold: p.good,
      color: p.good ? C.accent1 : C.accent3, isTextBox: true, margin: 0 });
  });

  s.addText("Real rows from the demo data. The names are fictional; the scores are not.", {
    x: M, y: 5.82, w: 12.0, h: 0.35, fontSize: 12, italic: true, color: C.accent3, isTextBox: true, margin: 0 });
  s.addNotes("The core slide. Aisha moves 11 points, so she is worth a message. Amirah is the best customer in the shop and the message does nothing for her. Ravi is gone either way. Spend the message on Aisha.");
}

// ============================================================ 5. the rule
{
  const s = newSlide("TITLE_ONLY", "The one question");
  s.addText("Who you can change, not who will return", { placeholder: "title" });

  card(s, { x: M, y: 1.6, w: 12.0, h: 1.1, fill: C.accent5, name: "rule-band" });
  s.addText("We left alone both the customer who looks best and the customer who looks worst.", {
    x: M + 0.35, y: 1.6, w: 11.3, h: 1.1, fontSize: 19, color: "FFFFFF", isTextBox: true,
    margin: 0, valign: "middle" });

  const labels = [
    { t: "Persuadable", d: "Top 30% by gap. A message genuinely moves them.", act: "Message these", good: true },
    { t: "Sure Thing", d: "Small gap, but very likely to return anyway.", act: "Save the message", good: false },
    { t: "Lost Cause", d: "Small gap, and unlikely to return either way.", act: "Leave alone", good: false },
  ];
  labels.forEach(function (l, i) {
    const x = M + i * 4.1;
    card(s, { x: x, y: 3.05, w: 3.8, h: 2.6, name: "label-" + i });
    circleNum(s, { x: x + 0.28, y: 3.3, text: String(i + 1),
      fill: l.good ? C.accent1 : C.accent3, name: "label-num-" + i });
    s.addText(l.t, { x: x + 0.95, y: 3.32, w: 2.6, h: 0.48, fontSize: 19, bold: true,
      color: l.good ? C.accent1 : C.text1, isTextBox: true, margin: 0, valign: "middle" });
    s.addText(l.d, { x: x + 0.28, y: 4.02, w: 3.24, h: 1.05, fontSize: 14, color: C.text1,
      isTextBox: true, margin: 0 });
    s.addText(l.act.toUpperCase(), { x: x + 0.28, y: 5.12, w: 3.24, h: 0.32, fontSize: 11, bold: true,
      charSpacing: 1.5, color: l.good ? C.accent1 : C.accent3, isTextBox: true, margin: 0 });
  });
  s.addNotes("Three labels, all derived from the same gap number. The Sure Thing row is the one judges react to: it is the opposite of what a churn model would tell you.");
}

// ============================================================ 6. what goes in
{
  const s = newSlide("TITLE_ONLY", "Under the hood");
  s.addText("Ten numbers, straight from the receipts", { placeholder: "title" });
  s.addText("Phone, date and amount. Any shop can compute all ten from its own sales history.", {
    x: M, y: 1.35, w: 12.0, h: 0.35, fontSize: 14, color: C.accent3, isTextBox: true, margin: 0 });

  const groups = [
    { n: "1", t: "How long they have been a customer", d: "Months since their first purchase." },
    { n: "5", t: "How regular their visits are", d: "How much the gaps between visits vary, over three windows — and whether those gaps are getting shorter or longer." },
    { n: "2", t: "How steady their spending is", d: "How much their basket value jumps around, over two windows." },
    { n: "2", t: "Whether they have replied before", d: "Did they ever respond to an SMS, or to a chat message?" },
  ];
  groups.forEach(function (g, i) {
    const y = 1.9 + i * 1.15;
    circleNum(s, { x: M, y: y + 0.06, d: 0.58, text: g.n, name: "feat-" + i });
    s.addText(g.t, { x: M + 0.85, y: y, w: 7.4, h: 0.38, fontSize: 17, bold: true,
      color: C.text1, isTextBox: true, margin: 0 });
    s.addText(g.d, { x: M + 0.85, y: y + 0.38, w: 7.4, h: 0.62, fontSize: 13, color: C.accent3,
      isTextBox: true, margin: 0 });
  });

  card(s, { x: 9.0, y: 1.95, w: 3.7, h: 2.3, fill: C.accent5, name: "fairness" });
  s.addText("Deliberately not used", { x: 9.3, y: 2.15, w: 3.1, h: 0.35, fontSize: 14, bold: true,
    color: C.accent2, isTextBox: true, margin: 0 });
  s.addText([
    { text: "Gender", options: { bullet: true, breakLine: true } },
    { text: "Age", options: { bullet: true, breakLine: true } },
    { text: "Children", options: { bullet: true } },
  ], { x: 9.3, y: 2.55, w: 3.1, h: 1.5, fontSize: 15, color: "FFFFFF", isTextBox: true, margin: 0,
       paraSpaceAfter: 6 });
  s.addNotes("Ten features, all derivable from a receipt log. That is what makes it portable to a Singapore shop. The protected attributes are dropped on purpose and the app says so in its limitations.");
}

// ============================================================ 7. how it gets there
{
  const s = newSlide("TITLE_ONLY", "Under the hood");
  s.addText("How it gets the gap: two models, then subtract", { placeholder: "title" });

  const boxes = [
    { t: "Model A", d: "Trained only on customers who were messaged.", out: "39%" },
    { t: "Model B", d: "Trained only on customers who were not.", out: "28%" },
  ];
  boxes.forEach(function (b, i) {
    const y = 1.8 + i * 1.95;
    card(s, { x: M, y: y, w: 5.3, h: 1.65, name: "model-" + i });
    s.addText(b.t, { x: M + 0.35, y: y + 0.18, w: 2.2, h: 0.4, fontSize: 19, bold: true,
      color: C.accent1, isTextBox: true, margin: 0 });
    s.addText(b.d, { x: M + 0.35, y: y + 0.62, w: 3.3, h: 0.85, fontSize: 14, color: C.text1,
      isTextBox: true, margin: 0 });
    s.addText(b.out, { x: M + 3.75, y: y + 0.5, w: 1.3, h: 0.6, fontSize: 24, bold: true, align: "right",
      color: C.text1, isTextBox: true, margin: 0, valign: "middle" });
  });

  s.addShape(pres.ShapeType.rightArrow, { x: 6.4, y: 2.95, w: 0.9, h: 0.55,
    fill: { color: C.accent6 }, line: { color: C.accent6 }, objectName: "arrow" });

  card(s, { x: 7.6, y: 1.8, w: 5.1, h: 3.8, fill: C.accent5, name: "subtract" });
  s.addText("Subtract", { x: 7.95, y: 2.05, w: 4.4, h: 0.45, fontSize: 22, bold: true,
    color: C.accent2, isTextBox: true, margin: 0 });
  s.addText("39%  −  28%", { x: 7.95, y: 2.62, w: 4.4, h: 0.6, fontSize: 26, color: "FFFFFF",
    isTextBox: true, margin: 0 });
  s.addText("= +11", { x: 7.95, y: 3.3, w: 4.4, h: 1.0, fontSize: 54, bold: true, color: C.accent2,
    isTextBox: true, margin: 0, valign: "middle" });
  s.addText("That gap is the model's entire output.", { x: 7.95, y: 4.45, w: 4.4, h: 0.8, fontSize: 15,
    color: "FFFFFF", isTextBox: true, margin: 0 });

  card(s, { x: M, y: 5.8, w: 12.0, h: 0.82, name: "why-valid" });
  s.addText([
    { text: "Why this is allowed to work:  ", options: { bold: true } },
    { text: "the training data comes from a randomised test — 687,000 grocery customers, SMS sent to a random half. Without the randomisation you would just be measuring who was already loyal." },
  ], { x: M + 0.35, y: 5.8, w: 11.3, h: 0.82, fontSize: 13, color: C.text1, isTextBox: true,
       margin: 0, valign: "middle" });
  s.addNotes("Two-model / T-learner approach, gradient boosting underneath. The randomised source data is the bit that makes the subtraction meaningful - worth saying if a judge is technical.");
}

// ============================================================ 8. what it does not do
{
  const s = newSlide("TITLE_ONLY", "Boundaries");
  s.addText("The model picks names, never words", { placeholder: "title" });

  const steps = [
    { t: "The model", d: "Picks who gets a message. One gap number per person.", on: true },
    { t: "The LLM", d: "Writes what to say, from that customer's own chat history.", on: false },
    { t: "MantaGO", d: "Delivers it over WhatsApp.", on: false },
    { t: "A human", d: "Reads every draft and ticks a box before anything sends.", on: false },
  ];
  steps.forEach(function (st, i) {
    const x = M + i * 3.08;
    card(s, { x: x, y: 1.85, w: 2.78, h: 2.5, fill: st.on ? C.accent1 : C.background2, name: "pipe-" + i });
    s.addText(st.t, { x: x + 0.25, y: 2.05, w: 2.28, h: 0.45, fontSize: 19, bold: true,
      color: st.on ? "FFFFFF" : C.text1, isTextBox: true, margin: 0 });
    s.addText(st.d, { x: x + 0.25, y: 2.58, w: 2.28, h: 1.6, fontSize: 14,
      color: st.on ? "E6FAF1" : C.text1, isTextBox: true, margin: 0 });
    if (i < 3) {
      s.addShape(pres.ShapeType.rightArrow, { x: x + 2.85, y: 2.98, w: 0.17, h: 0.26,
        fill: { color: C.accent6 }, line: { color: C.accent6 }, objectName: "pipe-arrow-" + i });
    }
  });

  card(s, { x: M, y: 4.62, w: 5.85, h: 1.78, name: "meet" });
  s.addText("Where the two meet", { x: M + 0.3, y: 4.8, w: 5.25, h: 0.35, fontSize: 15, bold: true,
    color: C.accent1, isTextBox: true, margin: 0 });
  s.addText("A discount is only allowed on someone the model called Persuadable, capped at 10%. That is a permission check, not the model writing anything.", {
    x: M + 0.3, y: 5.18, w: 5.25, h: 1.05, fontSize: 13, color: C.text1, isTextBox: true, margin: 0 });

  card(s, { x: 6.85, y: 4.62, w: 5.85, h: 1.78, name: "cant" });
  s.addText("What it cannot tell you", { x: 7.15, y: 4.8, w: 5.25, h: 0.35, fontSize: 15, bold: true,
    color: C.accent4, isTextBox: true, margin: 0 });
  s.addText("Which wording works. Choosing the best message type per person needs uplift scored per variant, which needs A/B data from real sends. We do not have that yet.", {
    x: 7.15, y: 5.18, w: 5.25, h: 1.05, fontSize: 13, color: C.text1, isTextBox: true, margin: 0 });
  s.addNotes("This is the question people get wrong most often. Model = who, LLM = what, MantaGO = delivery, human = approval.");
}

// ============================================================ 9. does it work
{
  const s = newSlide("CHART", "Does it work");
  s.addText("Does the picking actually beat guessing?", { placeholder: "title" });

  s.addChart(pres.ChartType.bar, [{
    name: "Share of all extra visits captured",
    labels: ["Pick 30% at random", "Old model, 190 columns", "Nudgely, 10 columns"],
    values: [30, 44.8, 57],
  }], {
    placeholder: "chart",
    barDir: "col", barGapWidthPct: 90,
    chartColors: ["C3D4CB", "A7C4B5", "0E9F6E"],
    showTitle: true, title: "Share of all extra visits the top 30% captures",
    titleFontSize: 13, titleColor: "6C8578", titleFontFace: "+mn-lt",
    showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: '0.0"%"',
    dataLabelFontSize: 13, dataLabelFontBold: true, dataLabelColor: "0D1E17", dataLabelFontFace: "+mn-lt",
    showLegend: false,
    valAxisMaxVal: 70, valAxisMinVal: 0,
    valAxisLabelColor: "6C8578", catAxisLabelColor: "0D1E17",
    valAxisLabelFontSize: 11, catAxisLabelFontSize: 12,
    valAxisLabelFontFace: "+mn-lt", catAxisLabelFontFace: "+mn-lt",
    valGridLine: { color: "E3EBE6", size: 1 }, catGridLine: { style: "none" },
  });

  s.addText([
    { text: "Reading this honestly", options: { fontSize: 17, bold: true, color: C.accent1, breakLine: true } },
    { text: "Message the top 30% the model picks and you capture 57% of all the extra visits available — nearly twice what random picking gets you.", options: { breakLine: true } },
    { text: " ", options: { breakLine: true, fontSize: 8 } },
    { text: "But always quote the spread. ", options: { bold: true } },
    { text: "Across seven random splits it swings between 38% and 85%. The direction is solid; the exact number is noisy.", options: { breakLine: true } },
    { text: " ", options: { breakLine: true, fontSize: 8 } },
    { text: "Dropping from 190 columns to ten a shop can actually compute did not cost accuracy — it gained." },
  ], { placeholder: "body" });
  s.addNotes("57% is the mean over seven splits of the transferable model. Say the spread in the same breath. Note the Results tab in the app shows 52.9% - that is the 190-column model on a single split, a different measurement.");
}

// ============================================================ 10. limitations
{
  const s = newSlide("TITLE_ONLY", "Does it work");
  s.addText("Say these before a judge does", { placeholder: "title" });

  const lims = [
    { t: "No recency feature", d: "The training data exposes no “days since last purchase”, so every lapsed customer scored Lost Cause. A win-back tool that refuses to message people who left is a design problem — and it is first on the fix list." },
    { t: "The lift is small, the interval wide", d: "Under one percentage point, with a spread you could drive a bus through. Honest framing beats a big number." },
    { t: "Trained on Russian grocery, not Singapore", d: "The features transfer; the behaviour may not. A real pilot needs two to four weeks with a holdout measured the same way." },
    { t: "The demo people are fictional", d: "Names and chats are invented. The model scores behind them are real test rows." },
  ];
  lims.forEach(function (l, i) {
    const x = M + (i % 2) * 6.15;
    const y = 1.8 + Math.floor(i / 2) * 2.45;
    card(s, { x: x, y: y, w: 5.85, h: 2.2, name: "lim-" + i });
    s.addText(l.t, { x: x + 0.3, y: y + 0.2, w: 5.25, h: 0.4, fontSize: 17, bold: true,
      color: C.accent4, isTextBox: true, margin: 0 });
    s.addText(l.d, { x: x + 0.3, y: y + 0.66, w: 5.25, h: 1.4, fontSize: 13, color: C.text1,
      isTextBox: true, margin: 0 });
  });
  s.addNotes("Volunteering the weaknesses is the strongest move available. The recency gap in particular - own it before it is found.");
}

// ============================================================ 11. close
{
  const s = newSlide("CLOSE_DARK", "Close");
  s.addText("The whole thing, in three lines", { placeholder: "title" });
  s.addText([
    { text: "The model gives one number per customer: how much a message changes them.", options: { bullet: true, breakLine: true } },
    { text: "You message the few it can change — not the loyal, not the lost.", options: { bullet: true, breakLine: true } },
    { text: "A holdout group gets nothing on purpose, so the difference proves it worked.", options: { bullet: true } },
  ], { placeholder: "body", paraSpaceAfter: 14 });

  card(s, { x: 0.9, y: 4.8, w: 11.4, h: 1.5, fill: C.accent5, name: "closing-line" });
  s.addText("It is not about who is likely to come back.\nIt is about who you can change.", {
    x: 1.3, y: 4.8, w: 10.6, h: 1.5, fontSize: 22, bold: true, italic: true, color: C.accent2,
    isTextBox: true, margin: 0, valign: "middle", lineSpacingMultiple: 1.2 });
  s.addNotes("Close on the one-liner. If there is time, the natural follow-up question is how we measure it: the holdout.");
}

(async function () {
  const out = process.argv[2] || "docs/How_the_model_works.pptx";
  await pres.writeFile({ fileName: out });
  const themer = process.argv[3];
  if (themer) {
    const { applyTheme } = require(themer);
    await applyTheme(out, THEME);
    console.log("written " + out + " (themed)");
  } else {
    console.log("written " + out + " - NO THEME APPLIED, colours will be Office defaults");
  }
})();
