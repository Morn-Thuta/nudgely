"use client";
import { useEffect, useRef, useState } from "react";
import {
  Search,
  X,
  ArrowUpRight,
  Users,
  Heart,
  UserRoundCheck,
} from "lucide-react";
import { useWorkspace } from "./workspace";
import { percent } from "@/lib/utils";
export function Customers() {
  const { data, demo } = useWorkspace();
  const [search, setSearch] = useState(""),
    [label, setLabel] = useState("All"),
    [selected, setSelected] = useState("");
  const rows = data.customers.filter(
    (c) =>
      (label === "All" || c.label === label) &&
      `${c.name} ${c.id}`.toLowerCase().includes(search.toLowerCase()),
  );
  const current = data.customers.find((c) => c.id === selected);
  const dialog = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    if (current && !dialog.current?.open) dialog.current?.showModal();
    if (!current && dialog.current?.open) dialog.current.close();
  }, [current]);
  return (
    <>
      <div className="page-heading">
        <div>
          <p className="eyebrow">Your customer book</p>
          <h1>People, beyond the purchase.</h1>
          <p>
            Understand who might benefit from a nudge, and what they care about.
          </p>
        </div>
        <span className="pill">{data.customers.length} customers</span>
      </div>
      <div className="workspace-stats">
        <div>
          <span className="stat-icon">
            <Users size={20} />
          </span>
          <p>
            <span>People in your customer book</span>
            <strong>{data.customers.length}</strong>
          </p>
        </div>
        <div>
          <span className="stat-icon">
            <Heart size={20} />
          </span>
          <p>
            <span>Could benefit from a nudge</span>
            <strong>
              {
                data.customers.filter(
                  (c) => c.label === "Persuadable" && !c.opted_out,
                ).length
              }
            </strong>
          </p>
        </div>
        <div>
          <span className="stat-icon warm">
            <UserRoundCheck size={20} />
          </span>
          <p>
            <span>Opted out of messages</span>
            <strong>{data.customers.filter((c) => c.opted_out).length}</strong>
          </p>
        </div>
      </div>
      <div className="toolbar">
        <label className="search">
          <Search size={18} />
          <span className="sr-only">Search customers</span>
          <input
            placeholder="Search name or ID…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </label>
        <label>
          Customer label
          <select value={label} onChange={(e) => setLabel(e.target.value)}>
            {["All", "Persuadable", "Sure Thing", "Lost Cause", "New"].map(
              (l) => (
                <option key={l}>{l}</option>
              ),
            )}
          </select>
        </label>
      </div>
      <div className="table-wrap">
        <table>
          <caption className="sr-only">Customers and predicted uplift</caption>
          <thead>
            <tr>
              <th>Customer</th>
              <th>Label</th>
              <th>Predicted uplift</th>
              <th>Chat memory</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((c) => (
              <tr key={c.id}>
                <td>
                  <div className="customer-identity">
                    <span className="avatar">
                      {(c.name || c.id).slice(0, 1)}
                    </span>
                    <div>
                      <button
                        className="customer-name"
                        onClick={() => setSelected(c.id)}
                      >
                        {c.name || "Visitor"} <ArrowUpRight size={13} />
                      </button>
                      <small>
                        {c.id} · {c.channel}
                      </small>
                    </div>
                  </div>
                </td>
                <td>
                  <span className="pill">{c.label}</span>
                </td>
                <td className="tabular-nums">
                  {c.uplift === null
                    ? "Not scored"
                    : `${c.uplift >= 0 ? "+" : ""}${(c.uplift * 100).toFixed(1)} points`}
                </td>
                <td>
                  {data.tags.find((t) => t.customer_id === c.id)?.value ||
                    "No tags yet"}
                </td>
                <td>
                  {c.opted_out
                    ? "Opted out"
                    : c.handover
                      ? "Needs a person"
                      : c.channel === "demo"
                        ? "Fictional profile"
                        : "Active conversation"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {!rows.length && (
          <div className="empty">
            <p>No customers match.</p>
            <button
              className="text-link"
              onClick={() => {
                setSearch("");
                setLabel("All");
              }}
            >
              Reset filters
            </button>
          </div>
        )}
      </div>
      <dialog
        ref={dialog}
        className="customer-dialog"
        aria-labelledby="customer-detail-title"
        onClose={() => setSelected("")}
        onClick={(e) => {
          if (e.target === e.currentTarget) dialog.current?.close();
        }}
      >
        {current && (
          <div className="customer-dialog-content">
            <div className="page-heading">
              <div>
                <p className="eyebrow">Customer profile · {current.id}</p>
                <h2 id="customer-detail-title">{current.name || current.id}</h2>
              </div>
              <button
                className="icon-button"
                aria-label="Close details"
                onClick={() => dialog.current?.close()}
              >
                <X size={20} />
              </button>
            </div>
            <p>
              {current.p_no_msg === null
                ? "No return prediction available."
                : `${percent(current.p_no_msg, 1)} estimated chance of returning without a message.`}{" "}
              {current.opted_out
                ? "This customer is excluded from campaigns."
                : "An active record is not proof of marketing consent."}
            </p>
            <div className="feature-grid">
              {data.tags
                .filter((t) => t.customer_id === current.id)
                .map((t) => (
                  <article className="memory-card" key={t.id}>
                    <span className="pill">{t.type.replaceAll("_", " ")}</span>
                    <h3>{t.value}</h3>
                    <blockquote>“{t.evidence}”</blockquote>
                  </article>
                ))}
            </div>
            {!data.tags.some((t) => t.customer_id === current.id) && (
              <p className="empty">
                No chat memories yet. Useful details will appear after a
                conversation.
              </p>
            )}
          </div>
        )}
      </dialog>
      <p className="fine">
        {demo
          ? "These 30 profiles use the original Lenta demo scores with fictional names and chats. The newer ten-feature model is reported separately on Results."
          : "New chat visitors are not automatically scored. A purchase history is needed before targeting them."}{" "}
        “Lost Cause” is the model’s technical label for low predicted response,
        not a judgement about a person.
      </p>
    </>
  );
}
