import { describe, it, expect } from "vitest";
import { planCampaign, draftProblems } from "../src/lib/campaign";
import demo from "../src/data/demo.json";
import type { Customer, Draft } from "../src/lib/types";
const customers = demo.customers as Customer[];
describe("campaign boundaries", () => {
  it("excludes opted-out and unscored people even if they would otherwise rank first", () => {
    const people = [
      ...customers,
      { ...customers[0], id: "OPTED", opted_out: true, uplift: 0.99 },
      { ...customers[0], id: "NEW", uplift: null },
    ];
    const plan = planCampaign(people, 30, 10);
    expect(
      plan
        .filter(
          (p) =>
            p.customer.id === "OPTED" ||
            p.customer.id === "NEW" ||
            p.customer.id === "C014",
        )
        .every((p) => p.group === "Skipped"),
    ).toBe(true);
  });
  it("holds out one of ten selected customers reproducibly, independent of incoming order", () => {
    const plan = planCampaign(customers, 10, 10);
    expect(plan.filter((p) => p.group === "Will message")).toHaveLength(9);
    expect(plan.filter((p) => p.group === "Held out")).toHaveLength(1);
    expect(planCampaign([...customers].reverse(), 10, 10)).toEqual(plan);
  });
  it("blocks missing opt-out, missing tags, oversized discounts and non-Persuadable discounts", () => {
    const bad = {
      customer_id: "C001",
      message: "Take 90% off",
      tags_used: [],
      reason: "",
    } satisfies Draft;
    expect(draftProblems(bad, "Sure Thing")).toHaveLength(4);
    expect(draftProblems(undefined, "Persuadable")).toEqual([
      "No cached draft",
    ]);
  });
  it("exports no phone mapping or backend identity columns", () => {
    for (const c of customers) {
      expect(c).not.toHaveProperty("mantago_client_id");
      expect(c).not.toHaveProperty("key_hash");
    }
    expect(customers.find((c) => c.id === "C014")?.opted_out).toBe(true);
  });
});
