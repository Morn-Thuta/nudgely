"use client";
import { useEffect, useRef, useState, type FormEvent } from "react";
import {
  ArrowUp,
  ArrowLeft,
  Leaf,
  UserRound,
  ArrowUpRight,
  MessageCircle,
} from "lucide-react";
import Link from "next/link";
import { chatOutput } from "@/lib/chat";
import { cn } from "@/lib/utils";
import { ShopFallback } from "./landing/shop-fallback";
type Turn = {
  id: string;
  sender: "customer" | "store" | "notice";
  text: string;
};
export function Chat({ mock }: { mock: boolean }) {
  const session = useRef("");
  const [name, setName] = useState("");
  const [text, setText] = useState("");
  const [turns, setTurns] = useState<Turn[]>([]);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState("");
  const [limited, setLimited] = useState(false);
  const [handover, setHandover] = useState(false);
  const end = useRef<HTMLDivElement>(null);
  const busy = useRef(false);
  const composer = useRef<HTMLTextAreaElement>(null);
  useEffect(() => {
    end.current?.scrollIntoView({ block: "nearest" });
  }, [turns, pending]);
  async function send(event: FormEvent) {
    event.preventDefault();
    if (busy.current || limited || !text.trim()) return;
    if (!session.current) {
      let id = crypto.randomUUID();
      try {
        id = sessionStorage.getItem("nudgely-session") || id;
        sessionStorage.setItem("nudgely-session", id);
      } catch {
        /* Storage may be unavailable; keep this page's session. */
      }
      session.current = id;
    }
    busy.current = true;
    setPending(true);
    setError("");
    const message = text.trim();
    setText("");
    setTurns((t) => [
      ...t,
      { id: crypto.randomUUID(), sender: "customer", text: message },
    ]);
    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: session.current,
          name: name.trim(),
          text: message,
        }),
        signal: AbortSignal.timeout(60000),
      });
      const body = await response.json();
      if (!response.ok) {
        setError(body.error || "The message could not be completed.");
        setLimited(Boolean(body.limited));
        return;
      }
      const result = chatOutput.parse(body);
      setHandover(result.handover);
      setTurns((t) => [
        ...t,
        {
          id: crypto.randomUUID(),
          sender: result.reply ? "store" : "notice",
          text:
            result.reply ||
            (result.handover
              ? "Your message is recorded for a person to review. The demo does not guarantee a staffed response."
              : "Your message was received. No automatic reply was sent; type START if you previously opted out."),
        },
      ]);
    } catch {
      setError(
        "The connection was interrupted. Your message may have arrived. Please wait before sending it again.",
      );
    } finally {
      busy.current = false;
      setPending(false);
    }
  }
  return (
    <div className={cn("chat-page", turns.length > 0 && "chat-started")}>
      <header className="chat-header">
        <Link href="/" aria-label="Back to Nudgely">
          <ArrowLeft size={21} />
        </Link>
        <div className="shop-avatar">
          <Leaf size={23} />
        </div>
        <div>
          <strong>Kampung Fresh</strong>
          <p>
            {mock
              ? "Offline rehearsal · scripted replies"
              : "Nudgely demo · AI shop assistant"}
          </p>
        </div>
        <Link className="chat-workspace-link" href="/demo">
          Explore workspace <ArrowUpRight size={15} />
        </Link>
      </header>
      <div className="chat-layout">
        <aside className="chat-welcome">
          <p className="eyebrow">A little visit to the shop</p>
          <h2>
            Same friendly shop.
            <br />
            <span>A new way to say hello.</span>
          </h2>
          <ShopFallback />
          <p>
            Remembering what matters.
            <br />
            One conversation at a time.
          </p>
          <span className="pill">
            <Leaf size={13} /> Powered by Nudgely
          </span>
        </aside>
        <div className="chat-room">
          <main id="main" className="chat-main">
            <div className="chat-intro">
              <span className="pill">A fictional neighbourhood grocer</span>
              <h1>Hello, neighbour.</h1>
              <p>
                Ask about the shop. Plan your next grocery run.
                <br />
                See what a thoughtful reply feels like.
              </p>
              <label className="name-field">
                <UserRound size={16} />
                <span className="sr-only">Your name (optional)</span>
                <input
                  value={name}
                  maxLength={40}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Your name (optional)"
                  autoComplete="off"
                  disabled={turns.length > 0}
                />
              </label>
              <p className="fine">
                Demo chats may appear on the team’s dashboard. Use fictional
                details; don’t share phone numbers or private information.
              </p>
            </div>
            {turns.length === 0 && (
              <div className="suggestions">
                <p className="fine">A few things you could ask</p>
                {[
                  "Do you have oat milk?",
                  "I'm planning a birthday party",
                  "Can I speak to a person?",
                ].map((s) => (
                  <button
                    key={s}
                    onClick={() => {
                      setText(s);
                      composer.current?.focus();
                    }}
                  >
                    {s} <ArrowUp size={14} />
                  </button>
                ))}
              </div>
            )}
            <div
              className="chat-turns"
              role="log"
              aria-label="Conversation"
              aria-live="polite"
              aria-relevant="additions"
            >
              {turns.map((t) => (
                <div key={t.id} className={cn("chat-turn", t.sender)}>
                  <span>
                    {t.sender === "customer"
                      ? "You"
                      : t.sender === "store"
                        ? "Kampung Fresh"
                        : "Delivery note"}
                  </span>
                  <p>{t.text}</p>
                </div>
              ))}
            </div>
            {pending && (
              <p className="typing" role="status">
                Kampung Fresh is thinking…{" "}
                <span className="fine">
                  The first reply can take a little longer.
                </span>
              </p>
            )}
            {handover && (
              <p className="notice">
                A person has been requested. This demo may not be staffed.
              </p>
            )}
            <div ref={end} />
          </main>
          <footer className="chat-composer">
            <form onSubmit={send}>
              <label className="sr-only" htmlFor="chat-message">
                Message Kampung Fresh
              </label>
              <textarea
                ref={composer}
                id="chat-message"
                value={text}
                onChange={(e) => setText(e.target.value)}
                maxLength={500}
                rows={2}
                placeholder="Ask Kampung Fresh something…"
                disabled={limited}
                onKeyDown={(e) => {
                  if (
                    e.key === "Enter" &&
                    !e.shiftKey &&
                    !e.nativeEvent.isComposing
                  ) {
                    e.preventDefault();
                    e.currentTarget.form?.requestSubmit();
                  }
                }}
              />
              <button
                className="send-button"
                aria-label="Send message"
                disabled={pending || limited || !text.trim()}
              >
                <ArrowUp size={22} />
              </button>
            </form>
            {error && (
              <p className="error" role="alert">
                {error}
              </p>
            )}
            <div className="composer-help">
              <span>HUMAN for help · STOP to opt out · START to resume</span>
              <span>{text.length}/500</span>
            </div>
            <p className="fine">
              {mock
                ? "Rehearsal only. Nothing reaches the AI or live dashboard."
                : "AI can make mistakes. Up to 30 messages per session."}
            </p>
          </footer>
          <div className="chat-room-caption">
            <MessageCircle size={13} /> A fictional shop. A thoughtful
            conversation.
          </div>
        </div>
      </div>
    </div>
  );
}
