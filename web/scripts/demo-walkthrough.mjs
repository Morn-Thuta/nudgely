// Captures screenshots + a screen recording of the finals demo click path for docs/Demo_Walkthrough.md.
//   node scripts/demo-walkthrough.mjs [baseUrl] [outDir]
// Uses the public /demo workspace (same screens as /dashboard, fictional data) and the real /try chat
// for the AI reply, handover and STOP steps. The Campaign "Live" panel only appears for signed-in team
// accounts, so here its two API calls are intercepted and the screenshots are labelled as such.
import { chromium } from "@playwright/test";
import fs from "node:fs";
import path from "node:path";

const base = process.argv[2] || "https://nudgely-navy.vercel.app";
const out = path.resolve(process.argv[3] || "../docs/demo");
fs.mkdirSync(out, { recursive: true });
const videoDir = path.join(out, "_video");

const browser = await chromium.launch({ channel: "msedge" });
const context = await browser.newContext({
  viewport: { width: 1366, height: 768 },
  deviceScaleFactor: 1,
  recordVideo: { dir: videoDir, size: { width: 1366, height: 768 } },
});
const page = await context.newPage();
const pause = (ms) => page.waitForTimeout(ms);
const shot = async (name) => {
  await pause(400);
  await page.screenshot({ path: path.join(out, `${name}.png`) });
  console.log("saved", name);
};

// Live panel: pretend this browser is a signed-in team member with Aisha as the demo phone.
await page.route("**/api/campaign/live", (r) =>
  r.fulfill({ json: { customer_ids: ["C001"] } }),
);
await page.route("**/api/campaign/send", (r) =>
  r.fulfill({ json: { sent: true, customer_id: "C001", message_id: "walkthrough" } }),
);

// 1. Conversations: Aisha's history
await page.goto(`${base}/demo`);
await page.getByPlaceholder("Find a customer…").fill("Aisha");
await page.getByRole("button", { name: /Aisha Rahman/ }).first().click();
await shot("01-conversations-aisha");

// 2. Customers: Aisha's profile
await page.goto(`${base}/demo/customers`);
await page.getByPlaceholder("Search name or ID…").fill("Aisha");
await page.getByRole("button", { name: "Aisha Rahman", exact: true }).click();
await pause(600);
await shot("02-customer-aisha");
await page.keyboard.press("Escape");

// 3. Customers: Hafiz is a Sure Thing
await page.getByPlaceholder("Search name or ID…").fill("Hafiz");
await shot("03-customer-hafiz");

// 4. Campaign: audience, held out, skipped
await page.goto(`${base}/demo/campaign`);
await pause(800);
await shot("04-campaign-audience");
await page.getByRole("button", { name: /^Skipped/ }).click();
await page.getByText("Hafiz Rahim").first().scrollIntoViewIfNeeded();
await shot("05-campaign-skipped-hafiz");

// 5. Live send panel
const live = page.locator(".live-send");
await live.scrollIntoViewIfNeeded();
await pause(500);
const box = live.locator("textarea").first();
await box.click();
await page.keyboard.press("End");
await page.keyboard.type(" ", { delay: 60 });
await live.getByRole("checkbox").check();
await shot("06-live-send-ready");
page.once("dialog", (d) => d.accept());
await live.getByRole("button", { name: /Send on WhatsApp/ }).click();
await pause(800);
await shot("07-live-send-sent");

// 6-8. The same AI on the web chat: reply, handover, STOP
await page.goto(`${base}/try`);
await page.getByPlaceholder("Your name (optional)").fill("Walkthrough");
const ask = async (text, wait) => {
  await page.getByPlaceholder("Ask Kampung Fresh something…").fill(text);
  await page.getByRole("button", { name: "Send message" }).click();
  await page.waitForFunction(
    (n) => document.querySelectorAll(".chat-turn.store, .chat-turn.notice").length >= n && !document.querySelector(".typing"),
    wait,
    { timeout: 90000 },
  );
  await pause(1500);
};
await ask("Is the oat milk back? Need it for my son's party Saturday", 1);
await shot("08-ai-reply");
await pause(2500);
await ask("Last order came 2 hours late, I want a refund", 2);
await shot("09-handover");
await pause(2500);
await ask("STOP", 3);
await shot("10-stop");

await context.close();
await browser.close();
const [video] = fs.readdirSync(videoDir).filter((f) => f.endsWith(".webm"));
fs.renameSync(path.join(videoDir, video), path.join(out, "demo-click-path.webm"));
fs.rmSync(videoDir, { recursive: true, force: true });
console.log("video", path.join(out, "demo-click-path.webm"));
