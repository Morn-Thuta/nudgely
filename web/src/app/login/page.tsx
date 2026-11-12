"use client";
import { useState, type FormEvent } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Brand } from "@/components/brand";
import { supabase } from "@/lib/supabase";
import { Eye, EyeOff, ArrowUpRight, Check } from "lucide-react";
import { ShopFallback } from "@/components/landing/shop-fallback";
export default function Login() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const client = supabase();
  async function login(e: FormEvent) {
    e.preventDefault();
    if (!client || busy) return;
    setBusy(true);
    setError("");
    try {
      const { error } = await client.auth.signInWithPassword({
        email,
        password,
      });
      if (error)
        setError(
          "Could not sign in. Check your team account email and password.",
        );
      else {
        const { data } = await client.auth.getUser();
        // Team accounts see the demo shop's live dashboard; everyone else is a shop owner.
        if (data.user?.app_metadata?.nudgely_team === true)
          router.replace("/dashboard");
        else router.replace("/shop");
      }
    } catch {
      setError("Could not reach sign-in. Please try again.");
    } finally {
      setBusy(false);
    }
  }
  return (
    <div className="login-page">
      <header className="auth-header">
        <Brand />
        <Link href="/">
          Back to the little shop <ArrowUpRight size={15} />
        </Link>
      </header>
      <div className="login-layout">
        <aside className="login-story">
          <p className="eyebrow">A LITTLE MORE HUMAN. A LITTLE MORE LOCAL.</p>
          <h2>
            Good relationships
            <br />
            start with the
            <br />
            <span>little things.</span>
          </h2>
          <ShopFallback />
          <div className="login-promises">
            <p>
              <Check size={16} /> Remember the person behind the purchase.
            </p>
            <p>
              <Check size={16} /> Make your next message a thoughtful one.
            </p>
          </div>
        </aside>
        <main id="main" className="login-card">
          <p className="eyebrow">The shop workspace</p>
          <h1>Welcome back.</h1>
          <p>
            Sign in with your invited team account to see live conversations.
          </p>
          {client ? (
            <form onSubmit={login}>
              <label>
                Email
                <input
                  type="email"
                  autoComplete="username"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                />
              </label>
              <div className="password-field">
                <label htmlFor="team-password">Password</label>
                <span className="password-input">
                  <input
                    id="team-password"
                    type={showPassword ? "text" : "password"}
                    autoComplete="current-password"
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                  />
                  <button
                    type="button"
                    className="icon-button"
                    aria-label={
                      showPassword ? "Hide password" : "Show password"
                    }
                    aria-pressed={showPassword}
                    onClick={() => setShowPassword(!showPassword)}
                  >
                    {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                  </button>
                </span>
              </div>
              {error && (
                <p role="alert" className="error">
                  {error}
                </p>
              )}
              <button className="button primary" disabled={busy}>
                {busy ? "Signing in…" : "Sign in"}
              </button>
            </form>
          ) : (
            <p className="notice">
              The live workspace is not connected yet. You can still explore the
              fictional shop below.
            </p>
          )}
          <Link href="/demo" className="text-link">
            Explore the demo workspace <ArrowUpRight size={16} />
          </Link>
          <Link href="/signup" className="text-link">
            Running a shop? Create your account <ArrowUpRight size={16} />
          </Link>
          <p className="fine">
            Shop owners go to their own workspace. Team accounts open the demo shop’s dashboard.
          </p>
        </main>
      </div>
    </div>
  );
}
