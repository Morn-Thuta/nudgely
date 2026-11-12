import { NextResponse } from "next/server";
export const maxDuration = 60;

// The shop owner's calls (/api/owner/...) forwarded to the backend with the owner's sign-in token.
// The backend checks the token and scopes every call to that owner's own shop.
const MAX_BODY = 2_900_000; // a 2 MB sales file grows by a third as base64
type Ctx = { params: Promise<{ path: string[] }> };

async function forward(request: Request, ctx: Ctx, method: "GET" | "POST") {
  const origin = request.headers.get("origin");
  if (origin && origin !== new URL(request.url).origin)
    return NextResponse.json({ error: "Please use this site." }, { status: 403 });
  const { path } = await ctx.params;
  if (!path.length || !path.every((s) => /^[A-Za-z0-9_-]{1,64}$/.test(s)))
    return NextResponse.json({ error: "Not found." }, { status: 404 });
  const auth = request.headers.get("authorization");
  if (!auth?.startsWith("Bearer "))
    return NextResponse.json({ error: "Sign in first." }, { status: 401 });
  const body = method === "POST" ? await request.text() : undefined;
  if (body && body.length > MAX_BODY)
    return NextResponse.json(
      { error: "That file is over 2 MB. Export a shorter period (3 to 6 months is plenty)." },
      { status: 413 },
    );
  try {
    const base = process.env.NUDGELY_API_URL || "https://nudgely-api.onrender.com";
    const response = await fetch(new URL(`/api/owner/${path.join("/")}`, base), {
      method,
      headers: { "Content-Type": "application/json", Authorization: auth },
      body,
      cache: "no-store",
      signal: AbortSignal.timeout(58000),
    });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok)
      return NextResponse.json(
        {
          error:
            typeof payload.detail === "string" ? payload.detail : "Something went wrong. Try again.",
        },
        { status: response.status },
      );
    return NextResponse.json(payload);
  } catch {
    return NextResponse.json(
      { error: "The server took too long to answer. It may be waking up: wait 30 seconds and try again." },
      { status: 504 },
    );
  }
}

export async function GET(request: Request, ctx: Ctx) {
  return forward(request, ctx, "GET");
}
export async function POST(request: Request, ctx: Ctx) {
  return forward(request, ctx, "POST");
}
