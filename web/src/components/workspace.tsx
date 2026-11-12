"use client";
import {
  createContext,
  useContext,
  useEffect,
  useState,
  useCallback,
  useRef,
} from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  MessageCircle,
  Users,
  Send,
  ChartNoAxesCombined,
  FileSpreadsheet,
  LogOut,
  ArrowUpRight,
  RefreshCw,
  ChevronRight,
  Sparkles,
  QrCode,
} from "lucide-react";
import { Brand } from "@/components/brand";
import { supabase, CUSTOMER_COLUMNS } from "@/lib/supabase";
import type { Dataset } from "@/lib/types";
import demoData from "@/data/demo.json";
import { cn } from "@/lib/utils";
const empty: Dataset = { customers: [], messages: [], tags: [] };
type WorkspaceState = {
  data: Dataset;
  demo: boolean;
  loading: boolean;
  error: string;
  status: string;
  refresh: () => void;
};
const Context = createContext<WorkspaceState | null>(null);
export function useWorkspace() {
  const c = useContext(Context);
  if (!c) throw new Error("Workspace missing");
  return c;
}
export function Workspace({
  children,
  demo = false,
}: {
  children: React.ReactNode;
  demo?: boolean;
}) {
  const path = usePathname(),
    router = useRouter();
  const base = demo ? "/demo" : "/dashboard";
  const currentPage = path.endsWith("/customers")
    ? "Customers"
    : path.endsWith("/campaign")
      ? "Campaign"
      : path.endsWith("/results")
        ? "Results"
        : path.endsWith("/sales")
          ? "Your sales"
          : "Conversations";
  const [data, setData] = useState<Dataset>(
      demo ? (demoData as Dataset) : empty,
    ),
    [loading, setLoading] = useState(!demo),
    [error, setError] = useState(""),
    [status, setStatus] = useState(demo ? "Fictional demo" : "Connecting");
  const [authorized, setAuthorized] = useState(demo);
  const generation = useRef(0);
  const mounted = useRef(true);
  const refresh = useCallback(async () => {
    if (demo) return;
    const client = supabase();
    if (!client) return;
    const request = ++generation.current;
    try {
      const { data: auth, error: authError } = await client.auth.getUser();
      if (!mounted.current || request !== generation.current) return;
      if (
        authError ||
        !auth.user ||
        auth.user.app_metadata?.nudgely_team !== true
      ) {
        setAuthorized(false);
        setData(empty);
        router.replace("/login");
        return;
      }
      setAuthorized(true);
      const [customers, messages, tags] = await Promise.all([
        client
          .from("customers")
          .select(CUSTOMER_COLUMNS)
          .order("last_seen_at", { ascending: false })
          .limit(500),
        client
          .from("messages")
          .select("id,customer_id,sender,text,handover,created_at")
          .order("created_at", { ascending: false })
          .limit(1000),
        client
          .from("tags")
          .select("id,customer_id,type,value,evidence,created_at")
          .order("created_at", { ascending: false })
          .limit(1000),
      ]);
      if (!mounted.current || request !== generation.current) return;
      if (customers.error || messages.error || tags.error)
        throw new Error("query");
      setData({
        customers: customers.data ?? [],
        messages: (messages.data ?? []).reverse(),
        tags: tags.data ?? [],
      } as Dataset);
      setError("");
    } catch {
      if (mounted.current && request === generation.current)
        setError(
          "Could not refresh the workspace. Check the connection and database setup, then retry. Previously loaded data may be stale.",
        );
    } finally {
      if (mounted.current && request === generation.current) setLoading(false);
    }
  }, [demo, router]);
  useEffect(() => {
    mounted.current = true;
    if (demo) return;
    const client = supabase();
    if (!client) {
      router.replace("/login");
      return;
    }
    // This starts an external authenticated fetch; state updates occur after getUser resolves.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void refresh();
    const { data: listener } = client.auth.onAuthStateChange((event) => {
      if (event === "SIGNED_OUT") {
        generation.current++;
        setData(empty);
        setAuthorized(false);
        router.replace("/login");
      }
    });
    let timer: ReturnType<typeof setTimeout>;
    const changed = () => {
      clearTimeout(timer);
      timer = setTimeout(() => void refresh(), 250);
    };
    const channel = client.channel("nudgely-workspace");
    for (const table of ["customers", "messages", "tags"])
      channel.on(
        "postgres_changes",
        { event: "*", schema: "public", table },
        changed,
      );
    channel.subscribe((state) => {
      if (mounted.current)
        setStatus(
          state === "SUBSCRIBED"
            ? "Live updates connected"
            : "Polling every 15 seconds",
        );
    });
    const interval = setInterval(() => void refresh(), 15000);
    // generation is a request counter, not a DOM ref; invalidating it discards pending requests.
    return () => {
      mounted.current = false;
      // eslint-disable-next-line react-hooks/exhaustive-deps
      generation.current++;
      clearTimeout(timer);
      clearInterval(interval);
      listener.subscription.unsubscribe();
      void client.removeChannel(channel);
    };
  }, [demo, refresh, router]);
  async function signOut() {
    const client = supabase();
    if (!client) return;
    const { error } = await client.auth.signOut();
    if (error) {
      setError("Could not sign out. Please retry.");
      return;
    }
    setData(empty);
    setAuthorized(false);
    router.replace("/login");
  }
  return (
    <Context.Provider
      value={{
        data,
        demo,
        loading,
        error,
        status,
        refresh: () => void refresh(),
      }}
    >
      <div className="workspace">
        <aside className="sidebar">
          <Brand />
          <div className="workspace-shop">
            <span className="shop-initial">KF</span>
            <div>
              <strong>Kampung Fresh</strong>
              <span>
                {demo ? "Fictional shop · Preview" : "Team workspace"}
              </span>
            </div>
          </div>
          <p className="eyebrow sidebar-label">Your shop</p>
          <nav aria-label="Workspace navigation">
            {[
              { href: base, label: "Conversations", icon: MessageCircle },
              { href: `${base}/customers`, label: "Customers", icon: Users },
              { href: `${base}/campaign`, label: "Campaign", icon: Send },
              {
                href: `${base}/results`,
                label: "Results",
                icon: ChartNoAxesCombined,
              },
              { href: `${base}/sales`, label: "Your sales", icon: FileSpreadsheet },
            ].map((n) => (
              <Link
                href={n.href}
                key={n.href}
                className={cn("sidebar-link", path === n.href && "active")}
                aria-current={path === n.href ? "page" : undefined}
              >
                <n.icon size={19} />
                {n.label}
              </Link>
            ))}
          </nav>
          <div className="sidebar-bottom">
            <div className="sidebar-invite">
              <span className="sidebar-invite-icon">
                <Sparkles size={18} />
              </span>
              <strong>Try a little conversation.</strong>
              <p>Step into your customer’s shoes.</p>
              <Link href="/try">
                Meet the shop <ArrowUpRight size={15} />
              </Link>
            </div>
            <Link href="/present">
              <QrCode size={18} /> Show the QR code
            </Link>
            {demo ? (
              <Link href="/login">
                <LogOut size={18} /> Team sign in
              </Link>
            ) : (
              <button onClick={() => void signOut()}>
                <LogOut size={18} /> Sign out
              </button>
            )}
            <p>
              Names and chats in the demo are fictional. Historical results are
              not live campaign outcomes.
            </p>
          </div>
        </aside>
        <div className="workspace-body">
          <header className="workspace-top">
            <div className="workspace-breadcrumb">
              Your workspace <ChevronRight size={14} />
              <strong>{currentPage}</strong>
            </div>
            <span className="connection-state">
              <span className="status-dot" />
              {status}
            </span>
            <Link className="workspace-chat-link" href="/try">
              Try the chat <ArrowUpRight size={16} />
            </Link>
            <span className="workspace-avatar" aria-label="Kampung Fresh">
              KF
            </span>
            {!demo && (
              <button className="mobile-signout" onClick={() => void signOut()}>
                Sign out
              </button>
            )}
          </header>
          {demo && (
            <div className="demo-banner">
              <span className="demo-banner-label">
                <Sparkles size={14} /> Demo shop
              </span>
              <p>Explore fictional customers and practice a campaign.</p>
              <Link href="/login">
                Open your workspace <ArrowUpRight size={14} />
              </Link>
            </div>
          )}
          {error && (
            <div className="error workspace-error" role="alert">
              {error}
              <button onClick={() => void refresh()}>
                <RefreshCw size={15} /> Retry
              </button>
            </div>
          )}
          <main id="main" className="workspace-content">
            {!authorized && !demo ? (
              <div className="loading-state" role="status">
                Checking team access… <Link href="/login">Go to sign in</Link>
              </div>
            ) : loading ? (
              <div className="loading-state" role="status">
                Loading the customer book…
              </div>
            ) : (
              children
            )}
          </main>
        </div>
      </div>
    </Context.Provider>
  );
}
