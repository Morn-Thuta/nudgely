import { NextResponse } from "next/server";
import { chatInput, chatOutput, mockReply } from "@/lib/chat";
export const maxDuration = 60;
export async function POST(request: Request) {
  // Browser requests stay same-origin. The configured upstream is never supplied by a visitor.
  const origin = request.headers.get("origin");
  if (origin && origin !== new URL(request.url).origin)
    return NextResponse.json(
      { error: "Please open the chat on this site." },
      { status: 403 },
    );
  const raw = await request.text();
  if (raw.length > 4096)
    return NextResponse.json({ error: "Message too long." }, { status: 413 });
  let body;
  try {
    body = chatInput.parse(JSON.parse(raw));
  } catch {
    return NextResponse.json(
      {
        error:
          "Enter a message of 1–500 characters and a name of up to 40 characters.",
      },
      { status: 400 },
    );
  }
  if (process.env.NUDGELY_CHAT_MODE === "mock")
    return NextResponse.json(mockReply(body.text));
  try {
    const base =
      process.env.NUDGELY_API_URL || "https://nudgely-api.onrender.com";
    const response = await fetch(new URL("/api/chat", base), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      cache: "no-store",
      signal: AbortSignal.timeout(55000),
    });
    if (!response.ok) {
      if (response.status === 429) {
        const payload = await response.json().catch(() => ({}));
        const capped =
          typeof payload.detail === "string" &&
          payload.detail.includes("message limit");
        return NextResponse.json(
          {
            error: capped
              ? "This demo has reached its 30-message limit. Thanks for trying Nudgely!"
              : "Please wait a few seconds before sending another message.",
            limited: capped,
          },
          { status: 429 },
        );
      }
      return NextResponse.json(
        {
          error:
            "The shop assistant is unavailable. Your message may have reached the server; please avoid sending it again immediately.",
        },
        { status: 502 },
      );
    }
    const result = chatOutput.safeParse(await response.json());
    if (!result.success)
      return NextResponse.json(
        {
          error:
            "The assistant returned an unexpected response. Please try again later.",
        },
        { status: 502 },
      );
    return NextResponse.json(result.data);
  } catch {
    return NextResponse.json(
      {
        error:
          "The assistant took too long to respond. It may still be processing your message; please wait before trying again.",
      },
      { status: 504 },
    );
  }
}
