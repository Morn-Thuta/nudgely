"use client";
import { useMemo, useRef, useState } from "react";
import {
  Download,
  FileSpreadsheet,
  Heart,
  Store,
  Upload,
  UserRoundCheck,
  Users,
} from "lucide-react";

// "Your sales": a shop uploads its till export, Model 2 scores every customer.
// The file goes to the backend (/api/shop/score), is scored and dropped; nothing is saved.

type Scored = {
  id: string;
  label: "Persuadable" | "Sure Thing" | "Lost Cause";
  p_no_msg: number;
  p_msg: number;
  uplift: number;
  purchases: number;
  avg_spend: number;
  months_as_customer: number;
  days_since_last: number;
};
type Result = {
  as_of: string;
  columns: { phone: string; date: string; amount: string };
  rows_read: number;
  rows_used: number;
  dropped: Record<string, number>;
  summary: {
    customers: number;
    persuadable: number;
    sure_thing: number;
    lost_cause: number;
    extra_visits_if_persuadables_messaged: number;
  };
  customers: Scored[];
};

const MAX_BYTES = 2_000_000;
const LABELS = ["All", "Persuadable", "Sure Thing", "Lost Cause"] as const;
const MEANING: Record<Scored["label"], string> = {
  Persuadable: "A message changes their mind. Message these.",
  "Sure Thing": "Coming back anyway. A message is wasted.",
  "Lost Cause": "Unlikely to come back either way.",
};

// Phone numbers never go on screen (stage rule); member ids are fine.
const shown = (id: string) => (/^\d{7,}$/.test(id) ? `•••• ${id.slice(-4)}` : id);
const pct = (n: number) => `${Math.round(n * 100)}%`;
const points = (n: number) => `${n >= 0 ? "+" : ""}${(n * 100).toFixed(1)} pts`;

function toBase64(file: Blob): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result).split(",")[1] ?? "");
    reader.onerror = () => reject(new Error("Couldn't read that file."));
    reader.readAsDataURL(file);
  });
}

export function ShopScore() {
  const [result, setResult] = useState<Result | null>(null),
    [fileName, setFileName] = useState(""),
    [busy, setBusy] = useState(false),
    [error, setError] = useState(""),
    [label, setLabel] = useState<(typeof LABELS)[number]>("All");
  const input = useRef<HTMLInputElement>(null);

  async function score(file: Blob, name: string) {
    setError("");
    if (file.size > MAX_BYTES) {
      setError("That file is over 2 MB. Export a shorter period (3 to 6 months is plenty).");
      return;
    }
    setBusy(true);
    setFileName(name);
    try {
      const response = await fetch("/api/shop/score", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ filename: name, data_base64: await toBase64(file) }),
      });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(payload.error || "Scoring failed.");
      setResult(payload as Result);
      setLabel("All");
    } catch (e) {
      setResult(null);
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  async function scoreSample() {
    const response = await fetch("/sample-sales.csv");
    await score(await response.blob(), "sample-sales.csv");
  }

  function download() {
    if (!result) return;
    const head = "customer,type,chance_if_no_message,chance_if_messaged,change,purchases,avg_spend,months_as_customer,days_since_last_visit";
    const lines = result.customers.map((c) =>
      [c.id, c.label, c.p_no_msg, c.p_msg, c.uplift, c.purchases, c.avg_spend, c.months_as_customer, c.days_since_last].join(","),
    );
    const url = URL.createObjectURL(new Blob([[head, ...lines].join("\n")], { type: "text/csv" }));
    const a = Object.assign(document.createElement("a"), { href: url, download: "nudgely-scored-customers.csv" });
    a.click();
    URL.revokeObjectURL(url);
  }

  const rows = useMemo(
    () => (result?.customers ?? []).filter((c) => label === "All" || c.label === label),
    [result, label],
  );
  const dropped = Object.entries(result?.dropped ?? {});

  return (
    <>
      <div className="page-heading">
        <div>
          <p className="eyebrow">Your sales</p>
          <h1>Score your shop from its sales.</h1>
          <p>
            Upload the sales export from your till. Nudgely works out ten numbers per customer from
            it and predicts how much a message would change each one. Nothing is saved.
          </p>
        </div>
        {result && <span className="pill">{result.summary.customers} customers</span>}
      </div>

      <section className="panel shop-upload">
        <div className="shop-upload-row">
          <input
            ref={input}
            type="file"
            accept=".csv,.xlsx,text/csv,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            className="sr-only"
            onChange={(e) => {
              const f = e.target.files?.[0];
              if (f) void score(f, f.name);
              e.target.value = "";
            }}
          />
          <button className="button primary" disabled={busy} onClick={() => input.current?.click()}>
            <Upload size={16} /> {busy ? "Scoring…" : "Upload sales file"}
          </button>
          <button className="button secondary" disabled={busy} onClick={() => void scoreSample()}>
            <Store size={16} /> Use a sample shop
          </button>
          {fileName && !busy && !error && <span className="fine">Scored {fileName}</span>}
        </div>
        <p className="fine">
          <FileSpreadsheet size={14} className="inline-icon" /> CSV or Excel, under 2 MB, one row per
          purchase with <b>who bought</b> (phone or member id), <b>the date</b> and <b>the amount</b>.
          Column names like “Mobile No”, “Date of purchase” and “Total (SGD)” are fine. 3 to 6 months
          of sales works best.
        </p>
        {error && (
          <p className="error" role="alert">
            {error}
          </p>
        )}
      </section>

      {result && (
        <>
          <div className="workspace-stats">
            <div>
              <span className="stat-icon">
                <Users size={20} />
              </span>
              <p>
                <span>Customers scored</span>
                <strong>{result.summary.customers}</strong>
              </p>
            </div>
            <div>
              <span className="stat-icon">
                <Heart size={20} />
              </span>
              <p>
                <span>Worth messaging (Persuadable)</span>
                <strong>{result.summary.persuadable}</strong>
              </p>
            </div>
            <div>
              <span className="stat-icon warm">
                <UserRoundCheck size={20} />
              </span>
              <p>
                <span>
                  Not worth a message ({result.summary.sure_thing} coming back anyway,{" "}
                  {result.summary.lost_cause} unlikely either way)
                </span>
                <strong>{result.summary.sure_thing + result.summary.lost_cause}</strong>
              </p>
            </div>
          </div>
          <p className="fine shop-read">
            Read {result.rows_used.toLocaleString()} of {result.rows_read.toLocaleString()} purchases,
            up to {result.as_of}, using the columns “{result.columns.phone}”, “{result.columns.date}”
            and “{result.columns.amount}”.
            {dropped.length > 0 &&
              ` Skipped: ${dropped.map(([why, n]) => `${n} with ${why}`).join(", ")}.`}
          </p>

          <div className="toolbar">
            <label>
              Show
              <select value={label} onChange={(e) => setLabel(e.target.value as (typeof LABELS)[number])}>
                {LABELS.map((l) => (
                  <option key={l}>{l}</option>
                ))}
              </select>
            </label>
            <button className="text-link" onClick={download}>
              <Download size={14} /> Download all {result.summary.customers} (CSV)
            </button>
          </div>
          <div className="table-wrap">
            <table>
              <caption className="sr-only">Customers ranked by how much a message would change them</caption>
              <thead>
                <tr>
                  <th>Customer</th>
                  <th>Type</th>
                  <th>If you send nothing</th>
                  <th>If you message them</th>
                  <th>Change</th>
                  <th>Visits</th>
                  <th>Last visit</th>
                  <th>Avg basket</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((c) => (
                  <tr key={c.id}>
                    <td className="tabular-nums">
                      {shown(c.id)}
                      <small className="shop-sub">
                        customer for {c.months_as_customer}{" "}
                        {c.months_as_customer === 1 ? "month" : "months"}
                      </small>
                    </td>
                    <td>
                      <span className="pill" title={MEANING[c.label]}>
                        {c.label}
                      </span>
                    </td>
                    <td className="tabular-nums">{pct(c.p_no_msg)}</td>
                    <td className="tabular-nums">{pct(c.p_msg)}</td>
                    <td className={`tabular-nums ${c.uplift >= 0 ? "shop-up" : "shop-down"}`}>
                      {points(c.uplift)}
                    </td>
                    <td className="tabular-nums">{c.purchases}</td>
                    <td className="tabular-nums">
                      {c.days_since_last === 0 ? "today" : c.days_since_last === 1 ? "yesterday" : `${c.days_since_last} days ago`}
                    </td>
                    <td className="tabular-nums">${c.avg_spend.toFixed(2)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <section className="panel">
            <p className="eyebrow">How it scored them</p>
            <h2>Ten numbers from your receipts, one model.</h2>
            <p>
              From each customer’s purchases Nudgely works out how long they’ve been a customer, how
              regular their visits are over the last 2 weeks, 1 month and 3 months, whether they’re
              visiting more or less often lately, and how much their basket size varies. The model
              learned what those numbers mean from a real experiment on 687,000 supermarket
              customers, where a random group got a message and the rest didn’t. On customers it
              had never seen, its top 30% caught about 57% of the extra visits (ranging 38–85%
              across tests), against 30% for picking at random.
            </p>
            <p className="fine">
              “Persuadable” is the top 30% of this shop by change. Scores are estimates: a campaign
              with a kept-back group is how you check them.
            </p>
          </section>
        </>
      )}
    </>
  );
}
