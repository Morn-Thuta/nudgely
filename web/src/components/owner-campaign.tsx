"use client";
import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { ArrowUpRight, Check, PenLine, Send, ShieldCheck, Sparkles } from "lucide-react";
import { useOwner } from "./owner-shell";
import { ownerApi, points, when, type Campaign, type CampaignRow, type CampaignSummary } from "@/lib/owner";

const SOURCE: Record<string, string> = {
  ai: "Written by the AI from your offer and note",
  template: "Plain sentence (the AI's version broke a rule, or the AI wasn't available)",
  edited: "Edited by you",
};

export function OwnerCampaign() {
  const { shop } = useOwner();
  const [list, setList] = useState<CampaignSummary[]>([]),
    [camp, setCamp] = useState<Campaign | null>(null),
    [size, setSize] = useState<number>(shop.persuadable || 1),
    [hold, setHold] = useState(10),
    [busy, setBusy] = useState(""),
    [error, setError] = useState(""),
    [sure, setSure] = useState(false);

  const open = useCallback(async (id: string) => {
    setError("");
    try {
      setCamp(await ownerApi<Campaign>(`campaigns/${id}`));
    } catch (e) {
      setError((e as Error).message);
    }
  }, []);

  const loadList = useCallback(async () => {
    try {
      const { campaigns } = await ownerApi<{ campaigns: CampaignSummary[] }>("campaigns");
      setList(campaigns);
      return campaigns;
    } catch (e) {
      setError((e as Error).message);
      return [];
    }
  }, []);

  useEffect(() => {
    // Loads the shop's campaigns and opens the newest; state is set after the requests resolve.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void loadList().then((c) => c[0] && open(c[0].id));
  }, [loadList, open]);

  async function act(label: string, path: string, body: unknown = {}) {
    setBusy(label);
    setError("");
    try {
      const next = await ownerApi<Campaign>(path, body);
      setCamp(next);
      await loadList();
      return next;
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy("");
    }
  }

  // The backend writes a few messages per request; keep asking until every one is written.
  async function writeAll(start: Campaign) {
    setBusy("write");
    setError("");
    try {
      let next = start;
      for (let round = 0; round < 500; round++) {
        if (!next.rows.some((r) => r.group === "messaged" && !r.message)) break;
        next = await ownerApi<Campaign>(`campaigns/${next.id}/write`, {});
        setCamp(next);
      }
      await loadList();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy("");
    }
  }

  const messaged = camp?.rows.filter((r) => r.group === "messaged") ?? [];
  const held = camp?.rows.filter((r) => r.group === "holdout") ?? [];
  const unwritten = messaged.filter((r) => !r.message).length;
  const approved = messaged.filter((r) => r.approved).length;
  const draft = camp?.status === "draft";

  return (
    <>
      <div className="page-heading">
        <div>
          <p className="eyebrow">Campaign</p>
          <h1>Message the ones it would move.</h1>
          <p>
            Nudgely picks your most movable customers, keeps a few back to measure against, and writes each
            message into your approved WhatsApp template. You read every one before anything is sent.
          </p>
        </div>
      </div>

      <section className="panel owner-plan">
        <p className="eyebrow">New campaign</p>
        {shop.persuadable ? (
          <div className="owner-row">
            <label htmlFor="plan-size">
              Customers to reach
              <input
                id="plan-size"
                type="number"
                min={1}
                max={shop.persuadable}
                value={size}
                onChange={(e) => setSize(Math.max(1, Math.min(shop.persuadable, Number(e.target.value) || 1)))}
              />
              <small className="fine">Up to {shop.persuadable}, your Persuadable customers, best first.</small>
            </label>
            <label htmlFor="plan-hold">
              Keep back to compare
              <select id="plan-hold" value={hold} onChange={(e) => setHold(Number(e.target.value))}>
                {[0, 10, 20, 30].map((p) => (
                  <option key={p} value={p}>
                    {p}%
                  </option>
                ))}
              </select>
              <small className="fine">Kept back on purpose, so you can see what the messages really did.</small>
            </label>
            <button
              className="button primary"
              disabled={!!busy}
              onClick={() => void act("plan", "campaigns", { size, holdout_pct: hold })}
            >
              {busy === "plan" ? "Planning…" : "Plan campaign"}
            </button>
          </div>
        ) : (
          <p>
            No Persuadable customers yet. <Link href="/shop">Upload your sales</Link> first.
          </p>
        )}
        {list.length > 0 && (
          <div className="owner-row owner-history">
            <label htmlFor="campaign-pick">
              Open a campaign
              <select id="campaign-pick" value={camp?.id ?? ""} onChange={(e) => void open(e.target.value)}>
                {list.map((c) => (
                  <option key={c.id} value={c.id}>
                    {when(c.created_at)} · {c.size} customers ·{" "}
                    {c.status === "draft" ? "draft" : c.mode === "live" ? "sent on WhatsApp" : "rehearsed"}
                  </option>
                ))}
              </select>
            </label>
          </div>
        )}
      </section>

      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}

      {camp && (
        <>
          <div className="workspace-stats">
            <div>
              <span className="stat-icon">
                <Send size={20} />
              </span>
              <p>
                <span>Getting a message</span>
                <strong>{messaged.length}</strong>
              </p>
            </div>
            <div>
              <span className="stat-icon warm">
                <ShieldCheck size={20} />
              </span>
              <p>
                <span>Kept back to compare</span>
                <strong>{held.length}</strong>
              </p>
            </div>
            <div>
              <span className="stat-icon">
                <Sparkles size={20} />
              </span>
              <p>
                <span>Extra visits expected (model estimate)</span>
                <strong>{camp.expected_extra_visits.toFixed(1)}</strong>
              </p>
            </div>
          </div>

          {draft ? (
            <section className="panel owner-actions">
              <p className="eyebrow">
                Step {unwritten ? 1 : approved ? 3 : 2} of 3
              </p>
              <h2>
                {unwritten
                  ? "Write the messages."
                  : approved
                    ? `${approved} of ${messaged.length} approved. Send when you're ready.`
                    : "Read them, fix anything, approve."}
              </h2>
              <div className="owner-row">
                {unwritten > 0 && (
                  <button
                    className="button primary"
                    disabled={!!busy}
                    onClick={() => void writeAll(camp)}
                  >
                    <PenLine size={16} />{" "}
                    {busy === "write"
                      ? `Writing… ${messaged.length - unwritten} of ${messaged.length} done`
                      : `Write ${unwritten} messages`}
                  </button>
                )}
                {!unwritten && (
                  <button
                    className="button secondary"
                    disabled={!!busy}
                    onClick={() => void act("approve", `campaigns/${camp.id}/approve-all`)}
                  >
                    <Check size={16} /> Approve every message without a problem
                  </button>
                )}
                {approved > 0 && (
                  <button
                    className="button secondary"
                    disabled={!!busy}
                    onClick={() => void act("rehearse", `campaigns/${camp.id}/send`, { live: false })}
                  >
                    {busy === "rehearse" ? "Rehearsing…" : "Run a rehearsal (nothing is sent)"}
                  </button>
                )}
              </div>
              {approved > 0 && (
                <div className="owner-live">
                  {shop.whatsapp_connected ? (
                    <>
                      <label className="check-row">
                        <input type="checkbox" checked={sure} onChange={(e) => setSure(e.target.checked)} /> I’ve
                        read every approved message, and these customers agreed to hear from us on WhatsApp.
                      </label>
                      <button
                        className="button primary"
                        disabled={!sure || !!busy}
                        onClick={() => void act("live", `campaigns/${camp.id}/send`, { live: true })}
                      >
                        <Send size={16} /> {busy === "live" ? "Sending…" : `Send ${approved} on WhatsApp`}
                      </button>
                    </>
                  ) : (
                    <p className="fine">
                      To send for real, connect your WhatsApp number and approved template in{" "}
                      <Link href="/shop/settings">Settings</Link>.
                    </p>
                  )}
                </div>
              )}
            </section>
          ) : (
            <section className="panel">
              <p className="eyebrow">{camp.mode === "live" ? "Sent on WhatsApp" : "Rehearsed"}</p>
              <h2>
                {camp.mode === "live" ? "Sent" : "Rehearsed"} {when(camp.sent_at)}.
              </h2>
              <p>
                In about 30 days, upload your sales from the send date on{" "}
                <Link href="/shop/results">
                  Results <ArrowUpRight size={13} />
                </Link>{" "}
                to see who came back, messaged against kept back.
              </p>
            </section>
          )}

          <div className="owner-cards">
            {messaged.map((r) => (
              <MessageCard
                key={r.id}
                row={r}
                draft={draft}
                busy={!!busy}
                onSave={(blank) => act("row", `campaigns/${camp.id}/rows/${r.id}`, { blank })}
                onApprove={(ok) => act("row", `campaigns/${camp.id}/rows/${r.id}`, { approved: ok })}
              />
            ))}
          </div>
          {held.length > 0 && (
            <p className="fine owner-held">
              Kept back on purpose ({held.length}): {held.map((r) => r.ref).join(", ")}. They get no message, so
              you can compare.
            </p>
          )}
        </>
      )}
    </>
  );
}

function MessageCard({
  row,
  draft,
  busy,
  onSave,
  onApprove,
}: {
  row: CampaignRow;
  draft: boolean;
  busy: boolean;
  onSave: (blank: string) => Promise<unknown>;
  onApprove: (ok: boolean) => Promise<unknown>;
}) {
  const [editing, setEditing] = useState(false),
    [text, setText] = useState(row.blank);
  return (
    <article className="draft-card">
      <div>
        <h3>{row.ref}</h3>
        <span className="pill">{row.label}</span>
        <span className="fine">
          {" "}
          · last visit {row.since} ago · {points(row.uplift)} if messaged
        </span>
      </div>
      {row.message ? <p>{row.message}</p> : <p className="fine">Not written yet.</p>}
      {row.source && <p className="fine">{SOURCE[row.source]}</p>}
      {row.problems.length > 0 && (
        <p className="error" role="alert">
          {row.problems.join("; ")}
        </p>
      )}
      {!draft && (
        <p className="fine">
          {row.status === "simulated" ? "Rehearsed, not sent" : row.status}
          {row.error ? `: ${row.error}` : ""}
        </p>
      )}
      {draft && row.message && (
        <div className="owner-row">
          {editing ? (
            <>
              <label className="sr-only" htmlFor={`blank-${row.id}`}>
                Your sentence
              </label>
              <input
                id={`blank-${row.id}`}
                className="owner-blank"
                value={text}
                maxLength={140}
                onChange={(e) => setText(e.target.value)}
              />
              <button
                className="button secondary"
                disabled={busy}
                onClick={() => void onSave(text).then(() => setEditing(false))}
              >
                Save
              </button>
            </>
          ) : (
            <button className="text-link" onClick={() => setEditing(true)}>
              <PenLine size={14} /> Change the sentence
            </button>
          )}
          <label className="check-row">
            <input
              type="checkbox"
              checked={row.approved}
              disabled={busy || row.problems.length > 0}
              onChange={(e) => void onApprove(e.target.checked)}
            />{" "}
            Approved
          </label>
        </div>
      )}
    </article>
  );
}
