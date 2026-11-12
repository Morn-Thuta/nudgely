"use client";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import Link from "next/link";
import { ArrowUpRight, FileSpreadsheet, Heart, Upload, UserRoundCheck, Users } from "lucide-react";
import { useOwner } from "./owner-shell";
import { MAX_UPLOAD, fileToBase64, ownerApi, pct, points, type OwnerCustomer } from "@/lib/owner";

const LABELS = ["All", "Persuadable", "Sure Thing", "Lost Cause"] as const;

export function OwnerCustomers() {
  const { shop, refresh } = useOwner();
  const [customers, setCustomers] = useState<OwnerCustomer[] | null>(null),
    [busy, setBusy] = useState(false),
    [error, setError] = useState(""),
    [note, setNote] = useState(""),
    [label, setLabel] = useState<(typeof LABELS)[number]>("All");
  const input = useRef<HTMLInputElement>(null);

  const load = useCallback(async () => {
    try {
      setCustomers((await ownerApi<{ customers: OwnerCustomer[] }>("customers")).customers);
    } catch (e) {
      setError((e as Error).message);
    }
  }, []);
  useEffect(() => {
    // Fetches the shop's saved customers; state is set after the request resolves.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void load();
  }, [load]);

  async function upload(file: File) {
    setError("");
    setNote("");
    if (file.size > MAX_UPLOAD) {
      setError("That file is over 2 MB. Export a shorter period (3 to 6 months is plenty).");
      return;
    }
    setBusy(true);
    try {
      const out = await ownerApi<{
        saved: number;
        rows_used: number;
        rows_read: number;
        as_of: string;
        dropped: Record<string, number>;
        columns: Record<string, string>;
      }>("sales", { filename: file.name, data_base64: await fileToBase64(file) });
      const skipped = Object.entries(out.dropped).map(([why, n]) => `${n} with ${why}`);
      setNote(
        `Scored and saved ${out.saved} customers from ${out.rows_used.toLocaleString()} of ` +
          `${out.rows_read.toLocaleString()} purchases, up to ${out.as_of}.` +
          (skipped.length ? ` Skipped ${skipped.join(", ")}.` : ""),
      );
      await Promise.all([load(), refresh()]);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  const rows = useMemo(
    () => (customers ?? []).filter((c) => label === "All" || c.label === label),
    [customers, label],
  );
  const count = (l: string) => (customers ?? []).filter((c) => c.label === l).length;

  return (
    <>
      <div className="page-heading">
        <div>
          <p className="eyebrow">Your customers</p>
          <h1>Who a message would actually move.</h1>
          <p>
            Upload your till’s sales export. Every customer is scored by how much a message would change
            their chance of coming back, and kept here for your campaigns.
          </p>
        </div>
        {shop.scored_up_to && <span className="pill">Sales up to {shop.scored_up_to}</span>}
      </div>

      <section className="panel shop-upload">
        <div className="shop-upload-row">
          <input
            ref={input}
            id="owner-sales-file"
            type="file"
            accept=".csv,.xlsx,text/csv,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            className="sr-only"
            onChange={(e) => {
              const f = e.target.files?.[0];
              if (f) void upload(f);
              e.target.value = "";
            }}
          />
          <button className="button primary" disabled={busy} onClick={() => input.current?.click()}>
            <Upload size={16} /> {busy ? "Scoring…" : customers?.length ? "Upload newer sales" : "Upload your sales"}
          </button>
        </div>
        <p className="fine">
          <FileSpreadsheet size={14} className="inline-icon" /> CSV or Excel, under 2 MB, one row per purchase
          with <b>who bought</b> (phone or member id), <b>the date</b> and <b>the amount</b>. A newer file
          re-scores the same customers.
        </p>
        {note && <p className="fine owner-ok">{note}</p>}
        {error && (
          <p className="error" role="alert">
            {error}
          </p>
        )}
      </section>

      {customers && customers.length > 0 && (
        <>
          <div className="workspace-stats">
            <div>
              <span className="stat-icon">
                <Users size={20} />
              </span>
              <p>
                <span>Customers scored</span>
                <strong>{customers.length}</strong>
              </p>
            </div>
            <div>
              <span className="stat-icon">
                <Heart size={20} />
              </span>
              <p>
                <span>Worth messaging (Persuadable)</span>
                <strong>{count("Persuadable")}</strong>
              </p>
            </div>
            <div>
              <span className="stat-icon warm">
                <UserRoundCheck size={20} />
              </span>
              <p>
                <span>
                  Not worth a message ({count("Sure Thing")} coming back anyway, {count("Lost Cause")} unlikely
                  either way)
                </span>
                <strong>{count("Sure Thing") + count("Lost Cause")}</strong>
              </p>
            </div>
          </div>
          <div className="toolbar">
            <label>
              Show
              <select
                id="owner-label-filter"
                value={label}
                onChange={(e) => setLabel(e.target.value as (typeof LABELS)[number])}
              >
                {LABELS.map((l) => (
                  <option key={l}>{l}</option>
                ))}
              </select>
            </label>
            <Link className="text-link" href="/shop/campaign">
              Plan a campaign for the {count("Persuadable")} worth messaging <ArrowUpRight size={14} />
            </Link>
          </div>
          <div className="table-wrap">
            <table>
              <caption className="sr-only">Your customers, ranked by how much a message would change them</caption>
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
                      {c.ref}
                      <small className="shop-sub">
                        customer for {c.months_as_customer} {c.months_as_customer === 1 ? "month" : "months"}
                      </small>
                    </td>
                    <td>
                      <span className="pill">{c.label}</span>
                    </td>
                    <td className="tabular-nums">{pct(c.p_no_msg)}</td>
                    <td className="tabular-nums">{pct(c.p_msg)}</td>
                    <td className={`tabular-nums ${c.uplift >= 0 ? "shop-up" : "shop-down"}`}>{points(c.uplift)}</td>
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
        </>
      )}
      {customers && customers.length === 0 && (
        <section className="panel">
          <h2>No customers yet.</h2>
          <p>Upload your sales above. Scoring takes a few seconds, then your campaign can be planned.</p>
        </section>
      )}
    </>
  );
}
