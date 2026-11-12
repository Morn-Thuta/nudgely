"use client";
import { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { Upload } from "lucide-react";
import { MAX_UPLOAD, fileToBase64, ownerApi, pct, when, type Campaign, type CampaignSummary } from "@/lib/owner";

const VERDICT: Record<string, string> = {
  worked: "The messages worked. Even the low end of the range is a gain.",
  "did not help": "The messages didn't help. Change the offer or the audience before sending again.",
  "too early to call": "Too early to call. The range still includes zero; each campaign you run narrows it.",
  waiting: "No answer yet. Upload your sales from the send date once their 30 days are up.",
};

export function OwnerResults() {
  const [list, setList] = useState<CampaignSummary[]>([]),
    [camp, setCamp] = useState<Campaign | null>(null),
    [busy, setBusy] = useState(false),
    [error, setError] = useState(""),
    [note, setNote] = useState("");
  const input = useRef<HTMLInputElement>(null);

  const open = useCallback(async (id: string) => {
    setError("");
    setNote("");
    try {
      setCamp(await ownerApi<Campaign>(`campaigns/${id}`));
    } catch (e) {
      setError((e as Error).message);
    }
  }, []);
  useEffect(() => {
    // Loads sent campaigns and opens the newest.
    void ownerApi<{ campaigns: CampaignSummary[] }>("campaigns")
      .then(({ campaigns }) => {
        const sent = campaigns.filter((c) => c.status === "sent");
        setList(sent);
        if (sent[0]) void open(sent[0].id);
      })
      .catch((e) => setError((e as Error).message));
  }, [open]);

  async function upload(file: File) {
    if (!camp) return;
    setError("");
    setNote("");
    if (file.size > MAX_UPLOAD) {
      setError("That file is over 2 MB. Export just the weeks since the campaign.");
      return;
    }
    setBusy(true);
    try {
      const out = await ownerApi<Campaign>(`campaigns/${camp.id}/returns`, {
        filename: file.name,
        data_base64: await fileToBase64(file),
      });
      setCamp(out);
      if (out.upload)
        setNote(
          `Read ${out.upload.purchases.toLocaleString()} purchases and updated ${out.upload.updated} customers.` +
            (out.upload.unreadable_rows ? ` ${out.upload.unreadable_rows} rows couldn't be read.` : ""),
        );
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  const r = camp?.results;
  return (
    <>
      <div className="page-heading">
        <div>
          <p className="eyebrow">Results</p>
          <h1>Did the messages bring them back?</h1>
          <p>
            Upload your sales from the day the campaign went out. Everyone in it, messaged or kept back, is
            checked the same way: did they buy anything within 30 days?
          </p>
        </div>
      </div>

      {!list.length ? (
        <section className="panel">
          <h2>No sent campaigns yet.</h2>
          <p>
            Rehearse or send one on <Link href="/shop/campaign">Campaign</Link>, then come back here.
          </p>
        </section>
      ) : (
        <section className="panel shop-upload">
          <div className="owner-row">
            <label htmlFor="results-pick">
              Campaign
              <select id="results-pick" value={camp?.id ?? ""} onChange={(e) => void open(e.target.value)}>
                {list.map((c) => (
                  <option key={c.id} value={c.id}>
                    {when(c.sent_at)} · {c.size} customers · {c.mode === "live" ? "sent on WhatsApp" : "rehearsed"}
                  </option>
                ))}
              </select>
            </label>
            <input
              ref={input}
              id="returns-file"
              type="file"
              accept=".csv,.xlsx,text/csv,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
              className="sr-only"
              onChange={(e) => {
                const f = e.target.files?.[0];
                if (f) void upload(f);
                e.target.value = "";
              }}
            />
            <button className="button primary" disabled={busy || !camp} onClick={() => input.current?.click()}>
              <Upload size={16} /> {busy ? "Checking…" : "Upload sales since the send"}
            </button>
          </div>
          {note && <p className="fine owner-ok">{note}</p>}
          {error && (
            <p className="error" role="alert">
              {error}
            </p>
          )}
        </section>
      )}

      {r && (
        <>
          <div className="workspace-stats">
            <div>
              <p>
                <span>Messaged ({r.messaged_back} of {r.messaged})</span>
                <strong>{r.messaged ? pct(r.rate_messaged) : "–"}</strong>
              </p>
            </div>
            <div>
              <p>
                <span>Kept back ({r.kept_back_back} of {r.kept_back})</span>
                <strong>{r.kept_back ? pct(r.rate_kept_back) : "–"}</strong>
              </p>
            </div>
            <div>
              <p>
                <span>Difference</span>
                <strong>
                  {r.difference == null ? "–" : `${r.difference >= 0 ? "+" : ""}${Math.round(r.difference * 100)} pts`}
                </strong>
              </p>
            </div>
          </div>
          <section className={`panel owner-verdict ${r.verdict === "worked" ? "good" : ""}`}>
            <h2>{VERDICT[r.verdict]}</h2>
            {r.low != null && r.high != null && (
              <p>
                With this many customers, the true effect is somewhere between {Math.round(r.low * 100)} and{" "}
                {Math.round(r.high * 100)} points.
              </p>
            )}
            {r.waiting > 0 && (
              <p className="fine">
                {r.waiting} {r.waiting === 1 ? "customer isn’t" : "customers aren’t"} settled yet. Upload sales
                that cover the 30 days after the send to settle them.
              </p>
            )}
          </section>
        </>
      )}
    </>
  );
}
