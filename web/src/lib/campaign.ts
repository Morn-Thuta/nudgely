import type { Customer, Draft } from "./types";
export type PlanRow = {
  customer: Customer;
  group: "Will message" | "Held out" | "Skipped";
  reason: string;
};
// Fixed-seed ordering, independent of database row order. This is a rehearsal planner;
// the Python sender remains authoritative for actual delivery.
function hash(id: string) {
  let n = 42;
  for (const c of id) n = Math.imul(n ^ c.charCodeAt(0), 16777619);
  return n >>> 0;
}
export function planCampaign(
  customers: Customer[],
  budget: number,
  holdout: number,
): PlanRow[] {
  const sorted = [...customers].sort(
    (a, b) =>
      (b.uplift ?? -Infinity) - (a.uplift ?? -Infinity) ||
      a.id.localeCompare(b.id),
  );
  const eligible = sorted.filter(
    (c) =>
      !c.opted_out &&
      c.label === "Persuadable" &&
      c.uplift !== null &&
      c.uplift > 0,
  );
  const chosen = eligible.slice(0, Math.max(0, Math.floor(budget))),
    chosenIds = new Set(chosen.map((c) => c.id));
  const count = Math.min(
    chosen.length,
    Math.round((chosen.length * Math.max(0, Math.min(50, holdout))) / 100),
  );
  const held = new Set(
    [...chosen]
      .sort((a, b) => hash(a.id) - hash(b.id) || a.id.localeCompare(b.id))
      .slice(0, count)
      .map((c) => c.id),
  );
  return sorted.map((customer) => ({
    customer,
    group: held.has(customer.id)
      ? "Held out"
      : chosenIds.has(customer.id)
        ? "Will message"
        : "Skipped",
    reason: customer.opted_out
      ? "Opted out — excluded"
      : held.has(customer.id)
        ? "Fixed-seed comparison group"
        : chosenIds.has(customer.id)
          ? "Highest positive uplift within the audience budget"
          : customer.uplift === null
            ? "Not scored"
            : customer.label !== "Persuadable"
              ? "Outside the Persuadable group"
              : "Outside this audience budget",
  }));
}
export function draftProblems(
  draft: Draft | undefined,
  label: string,
): string[] {
  if (!draft) return ["No cached draft"];
  const errors = [];
  if (!draft.message.trim()) errors.push("Empty draft");
  if (draft.message.length > 300) errors.push("Over 300 characters");
  if (!draft.message.trim().endsWith("Reply STOP to opt out"))
    errors.push("Missing opt-out line");
  if (!draft.tags_used.length) errors.push("No tags referenced");
  const discounts = [...draft.message.matchAll(/(\d+(?:\.\d+)?)\s*%/g)].map(
    (m) => +m[1],
  );
  if (discounts.some((n) => n > 10)) errors.push("Discount exceeds 10%");
  if (discounts.length && label !== "Persuadable")
    errors.push("Discount outside Persuadable group");
  return errors;
}
