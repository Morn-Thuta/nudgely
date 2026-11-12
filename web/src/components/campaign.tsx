"use client";
import { useState } from "react";
import { ArrowDown, Send, ShieldCheck } from "lucide-react";
import { useWorkspace } from "./workspace";
import { planCampaign, draftProblems } from "@/lib/campaign";
import type { Draft } from "@/lib/types";
import draftsJson from "@/data/drafts.json";
const drafts = draftsJson as Record<string, Draft>;
export function Campaign() {
  const { data } = useWorkspace();
  const [budget, setBudget] = useState(10),
    [holdout, setHoldout] = useState(10),
    [reviewed, setReviewed] = useState(""),
    [completed, setCompleted] = useState<string[]>([]),
    [tab, setTab] = useState("Will message");
  const plan = planCampaign(data.customers, budget, holdout),
    chosen = plan.filter((r) => r.group === "Will message");
  const key = JSON.stringify(
    plan.map((r) => [r.customer.id, r.group, drafts[r.customer.id]?.message]),
  );
  const invalid = chosen.some(
    (r) => draftProblems(drafts[r.customer.id], r.customer.label).length > 0,
  );
  const done = completed.includes(key);
  const extra = chosen.reduce((n, r) => n + (r.customer.uplift ?? 0), 0);
  function download() {
    const csv =
      "customer_id,status\n" +
      chosen.map((r) => `${r.customer.id},simulated`).join("\n");
    const url = URL.createObjectURL(new Blob([csv], { type: "text/csv" }));
    const a = document.createElement("a");
    a.href = url;
    a.download = "nudgely-rehearsal.csv";
    a.click();
    URL.revokeObjectURL(url);
  }
  return (
    <>
      <div className="page-heading">
        <div>
          <p className="eyebrow">A thoughtful nudge</p>
          <h1>A little intention goes a long way.</h1>
          <p>Choose an audience. Keep a comparison group. Review every word.</p>
        </div>
        <span className="pill">Rehearsal only</span>
      </div>
      <p className="notice">
        <ShieldCheck size={18} /> This is a rehearsal. Explore the audience and
        review the drafts. No messages will be sent.
      </p>
      <nav className="campaign-steps" aria-label="Campaign steps">
        <a href="#campaign-audience">
          <span>01</span> Choose your audience
        </a>
        <a href="#campaign-drafts">
          <span>02</span> Review the words
        </a>
        <a href="#campaign-review">
          <span>03</span> Run a rehearsal
        </a>
      </nav>
      <section id="campaign-audience" className="panel campaign-controls">
        <div className="panel-heading">
          <div>
            <p className="eyebrow">Step 01</p>
            <h2>Who needs a little nudge?</h2>
          </div>
          <a className="text-link" href="#campaign-drafts">
            Review drafts <ArrowDown size={15} />
          </a>
        </div>
        <label>
          Audience size, including holdout <strong>{budget}</strong>
          <input
            type="range"
            min={1}
            max={Math.max(1, data.customers.length)}
            value={budget}
            onChange={(e) => setBudget(+e.target.value)}
          />
        </label>
        <label>
          Holdout group <strong>{holdout}%</strong>
          <input
            type="range"
            min={0}
            max={50}
            step={5}
            value={holdout}
            onChange={(e) => setHoldout(+e.target.value)}
          />
        </label>
      </section>
      <div className="metric-grid">
        {[
          ["Will message", chosen.length],
          ["Held out", plan.filter((r) => r.group === "Held out").length],
          ["Skipped", plan.filter((r) => r.group === "Skipped").length],
          ["Predicted extra visits", extra.toFixed(1)],
        ].map(([label, value]) => (
          <div className="metric" key={label}>
            <span>{label}</span>
            <strong>{value}</strong>
          </div>
        ))}
      </div>
      <p className="fine">
        Only positive-uplift Persuadables qualify. Explicit opt-outs are
        excluded. Predicted extra visits are the sum of selected uplift scores,
        not measured returns.
      </p>
      <div id="campaign-drafts" className="section-title">
        <div>
          <p className="eyebrow">Step 02</p>
          <h2>Make every message count.</h2>
        </div>
        <span className="pill">{chosen.length} drafts to review</span>
      </div>
      <nav className="view-switch" aria-label="Campaign groups">
        {["Will message", "Held out", "Skipped"].map((group) => (
          <button
            key={group}
            aria-pressed={tab === group}
            onClick={() => setTab(group)}
          >
            {group} ({plan.filter((r) => r.group === group).length})
          </button>
        ))}
      </nav>
      <div className="draft-list">
        {plan
          .filter((r) => r.group === tab)
          .map((r) => (
            <article key={r.customer.id} className="draft-card">
              <div>
                <h3>{r.customer.name || r.customer.id}</h3>
                <span className="pill">{r.customer.label}</span>
              </div>
              <p className="fine">{r.reason}</p>
              {r.group === "Will message" && (
                <>
                  <p>
                    {drafts[r.customer.id]?.message ||
                      "No cached draft for this customer."}
                  </p>
                  <p className="fine">{drafts[r.customer.id]?.reason}</p>
                  {draftProblems(drafts[r.customer.id], r.customer.label).map(
                    (p) => (
                      <p className="error" key={p}>
                        {p}
                      </p>
                    ),
                  )}
                </>
              )}
            </article>
          ))}
        {!plan.some((r) => r.group === tab) && (
          <p className="empty">
            No customers in this group. Adjust the audience or holdout above.
          </p>
        )}
      </div>
      <section id="campaign-review" className="panel review-panel">
        <p className="eyebrow">Step 03</p>
        <h2>Take one last look.</h2>
        <p>
          These are cached October demonstration drafts. Stock, offers and dates
          require fresh human review before any future delivery.
        </p>
        <label className="check-row">
          <input
            type="checkbox"
            checked={reviewed === key}
            onChange={(e) => setReviewed(e.target.checked ? key : "")}
          />{" "}
          I’ve reviewed every selected draft for this rehearsal.
        </label>
        <button
          className="button primary"
          disabled={!chosen.length || invalid || reviewed !== key || done}
          onClick={() => setCompleted((c) => [...c, key])}
        >
          <Send size={16} /> Simulate campaign
        </button>
        {invalid && (
          <p className="error">
            Missing or invalid drafts block simulation. Complete them before
            continuing.
          </p>
        )}
        {done && (
          <div role="status" className="notice">
            Simulation complete: {chosen.length} simulated,{" "}
            {plan.filter((r) => r.group === "Held out").length} held out. No
            live deliveries.
            <button className="text-link" onClick={download}>
              Download simulation log
            </button>
          </div>
        )}
        <p className="fine">
          Rehearsal history stays on this page until you leave or refresh. It is
          not a persistent delivery record.
        </p>
      </section>
    </>
  );
}
