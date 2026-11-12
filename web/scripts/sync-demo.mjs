// Export only allowlisted fields from the committed fictional demo. Never read runtime inboxes or phone mappings.
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { parse } from "csv-parse/sync";
const root = fileURLToPath(new URL("../../", import.meta.url));
const read = (name) =>
  JSON.parse(fs.readFileSync(path.join(root, "data", name), "utf8"));
const consent = read("consent.json"),
  chats = read("chats.json"),
  tags = read("tags.json");
const rows = parse(
  fs.readFileSync(path.join(root, "data/customers.csv"), "utf8"),
  { columns: true, skip_empty_lines: true },
);
let msgId = 0,
  tagId = 0;
const timestamp = "2026-10-21T04:00:00Z";
const dataset = {
  customers: rows.map((c) => ({
    id: c.customer_id,
    channel: "demo",
    name: c.name,
    label: c.label,
    uplift: Number(c.uplift),
    p_no_msg: Number(c.p_no_msg),
    handover: false,
    opted_out: consent[c.customer_id]?.opted_in === false,
    created_at: timestamp,
    last_seen_at: timestamp,
  })),
  messages: rows.flatMap((c) =>
    (chats[c.customer_id] ?? []).map((m) => ({
      id: ++msgId,
      customer_id: c.customer_id,
      sender: m.from,
      text: m.text,
      handover: false,
      created_at: `${m.date}T04:00:00Z`,
    })),
  ),
  tags: rows.flatMap((c) =>
    (tags[c.customer_id]?.tags ?? [])
      .filter((t) => t.value && t.evidence)
      .map((t) => ({
        id: ++tagId,
        customer_id: c.customer_id,
        type: t.type,
        value: t.value,
        evidence: t.evidence,
        created_at: timestamp,
      })),
  ),
};
const dest = path.join(root, "web/src/data");
fs.mkdirSync(dest, { recursive: true });
for (const [name, value] of Object.entries({
  demo: dataset,
  drafts: read("messages.json"),
  evidence: read("uplift_transferable.json"),
  summary: read("uplift_summary.json"),
  scene: read("examples/scene_scores.json"),
})) {
  fs.writeFileSync(
    path.join(dest, `${name}.json`),
    JSON.stringify(value, null, 2) + "\n",
  );
}
console.log(
  `Synced ${rows.length} fictional customers; no private mapping or inbox exported.`,
);
