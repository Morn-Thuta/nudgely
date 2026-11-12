"use client";
import { useRef, useState } from "react";
import Link from "next/link";
import {
  Search,
  MessageCircle,
  Users,
  UserRoundCheck,
  ArrowLeft,
  Sparkles,
} from "lucide-react";
import { useWorkspace } from "./workspace";
import { cn } from "@/lib/utils";
export function Conversations() {
  const { data, demo } = useWorkspace();
  const searchRef = useRef<HTMLInputElement>(null);
  const threadRef = useRef<HTMLHeadingElement>(null);
  const [query, setQuery] = useState(""),
    [selected, setSelected] = useState(""),
    [onlyHelp, setOnlyHelp] = useState(false);
  const customers = data.customers.filter(
    (c) =>
      (demo || c.channel !== "demo") &&
      (!onlyHelp || c.handover) &&
      `${c.name} ${c.id}`.toLowerCase().includes(query.toLowerCase()),
  );
  const current = customers.find((c) => c.id === selected) ?? customers[0];
  const messages = current
    ? data.messages
        .filter((m) => m.customer_id === current.id)
        .sort((a, b) => a.created_at.localeCompare(b.created_at) || a.id - b.id)
    : [];
  const tags = current
    ? data.tags.filter((t) => t.customer_id === current.id)
    : [];
  return (
    <>
      <div className="page-heading">
        <div>
          <p className="eyebrow">The conversation starts here</p>
          <h1>A little more personal.</h1>
          <p>
            Follow each conversation, understand the context, and know when to
            step in.
          </p>
        </div>
        <Link
          className="button primary"
          href={demo ? "/demo/campaign" : "/dashboard/campaign"}
        >
          Plan a nudge <Sparkles size={16} />
        </Link>
      </div>
      <div className="workspace-stats">
        <div>
          <span className="stat-icon">
            <Users size={20} />
          </span>
          <p>
            <span>Customer conversations</span>
            <strong>
              {
                data.customers.filter((c) => demo || c.channel !== "demo")
                  .length
              }
            </strong>
          </p>
        </div>
        <div>
          <span className="stat-icon">
            <MessageCircle size={20} />
          </span>
          <p>
            <span>Messages in the customer book</span>
            <strong>{data.messages.length}</strong>
          </p>
        </div>
        <div>
          <span className="stat-icon warm">
            <UserRoundCheck size={20} />
          </span>
          <p>
            <span>Waiting for a person</span>
            <strong>
              {
                data.customers.filter(
                  (c) => c.handover && (demo || c.channel !== "demo"),
                ).length
              }
            </strong>
          </p>
        </div>
      </div>
      <div className={cn("inbox", selected && "mobile-thread-open")}>
        <section className="inbox-list" aria-label="Conversations">
          <div className="inbox-list-heading">
            <h2>Inbox</h2>
            <span className="pill">{customers.length}</span>
          </div>
          <label className="search">
            <Search size={17} />
            <span className="sr-only">Search conversations</span>
            <input
              ref={searchRef}
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Find a customer…"
            />
          </label>
          <label className="check-row">
            <input
              type="checkbox"
              checked={onlyHelp}
              onChange={(e) => setOnlyHelp(e.target.checked)}
            />{" "}
            Needs a person
          </label>
          <div className="conversation-list">
            {customers.map((c) => {
              const last = data.messages
                .filter((m) => m.customer_id === c.id)
                .at(-1);
              return (
                <button
                  key={c.id}
                  onClick={() => {
                    setSelected(c.id);
                    requestAnimationFrame(() =>
                      threadRef.current?.focus({ preventScroll: true }),
                    );
                  }}
                  className={cn(
                    "conversation-button",
                    current?.id === c.id && "selected",
                  )}
                  aria-pressed={current?.id === c.id}
                >
                  <span className="avatar">{(c.name || c.id).slice(0, 1)}</span>
                  <span>
                    <strong>{c.name || "Visitor"}</strong>
                    <small>{last?.text || "No messages yet"}</small>
                    <span className="fine">
                      {c.channel} ·{" "}
                      {c.handover
                        ? "Needs a person"
                        : c.opted_out
                          ? "Opted out"
                          : c.id}
                    </span>
                  </span>
                </button>
              );
            })}
          </div>
          {!customers.length && (
            <div className="empty">
              <MessageCircle />
              <p>
                {query || onlyHelp
                  ? "No conversations match this filter."
                  : "Your next conversation starts on a judge’s phone."}
              </p>
              {query || onlyHelp ? (
                <button
                  className="text-link"
                  onClick={() => {
                    setQuery("");
                    setOnlyHelp(false);
                  }}
                >
                  Clear filters
                </button>
              ) : (
                <Link href="/present">Show the QR code ↗</Link>
              )}
            </div>
          )}
        </section>
        <section className="inbox-thread" aria-label="Selected conversation">
          {current ? (
            <>
              <button
                className="thread-back"
                onClick={() => {
                  setSelected("");
                  requestAnimationFrame(() =>
                    searchRef.current?.focus({ preventScroll: true }),
                  );
                }}
              >
                <ArrowLeft size={17} /> All conversations
              </button>
              <header>
                <span className="avatar">
                  {(current.name || current.id).slice(0, 1)}
                </span>
                <div>
                  <h2 ref={threadRef} tabIndex={-1}>
                    {current.name || "Visitor"}
                  </h2>
                  <p>
                    {current.id} · {current.channel}
                  </p>
                </div>
                <span className="pill">
                  {current.opted_out
                    ? "Opted out"
                    : current.handover
                      ? "Needs a person"
                      : "AI assistant"}
                </span>
              </header>
              <div
                className="thread-messages"
                role="log"
                aria-label="Customer messages"
                aria-live="polite"
                aria-relevant="additions"
              >
                {messages.length ? (
                  messages.map((m) => (
                    <div key={m.id} className={cn("chat-turn", m.sender)}>
                      <span>
                        {m.sender === "customer"
                          ? current.name || "Visitor"
                          : "Kampung Fresh"}
                        {m.handover ? " · Handed to a person" : ""}
                      </span>
                      <p>{m.text}</p>
                      <time dateTime={m.created_at}>
                        {new Date(m.created_at).toLocaleString("en-SG", {
                          timeZone: "Asia/Singapore",
                          day: "numeric",
                          month: "short",
                          hour: "2-digit",
                          minute: "2-digit",
                        })}{" "}
                        SGT
                      </time>
                    </div>
                  ))
                ) : (
                  <p className="empty">No messages recorded yet.</p>
                )}
              </div>
              <footer>
                {current.handover
                  ? "A person has been requested. Follow up through the shop’s connected channel."
                  : "Read-only conversation view. Replies are handled by the connected assistant."}
              </footer>
            </>
          ) : (
            <div className="empty">
              <MessageCircle size={30} />
              <h2>Make room for a conversation.</h2>
              <p>New chats appear here when the backend writes to Supabase.</p>
            </div>
          )}
        </section>
        <aside className="memory-panel">
          <p className="eyebrow">
            <Sparkles size={14} /> Chat memory
          </p>
          <h3>The details that matter.</h3>
          <p className="fine">
            Tags extracted from the conversation, with the words behind them.
          </p>
          {tags.map((t) => (
            <article className="memory-card" key={t.id}>
              <span className="pill">{t.type.replaceAll("_", " ")}</span>
              <h4>{t.value}</h4>
              <blockquote>“{t.evidence}”</blockquote>
            </article>
          ))}
          {!tags.length && (
            <p className="empty">
              No tags yet. They’ll appear here as the conversation develops.
            </p>
          )}
        </aside>
      </div>
      {!demo && (
        <p className="fine">
          Shows the latest 500 customers and 1,000 messages and tags. Older
          history may be outside this demo view.
        </p>
      )}
    </>
  );
}
