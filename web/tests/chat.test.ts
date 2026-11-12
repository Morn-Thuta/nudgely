import { afterEach, describe, it, expect, vi } from "vitest";
import { POST } from "../src/app/api/chat/route";
const request = (body: unknown, origin = "http://localhost") =>
  new Request("http://localhost/api/chat", {
    method: "POST",
    headers: { "content-type": "application/json", origin },
    body: JSON.stringify(body),
  });
const payload = {
  session_id: "12345678-abcd",
  name: "Judge",
  text: "oat milk?",
};
afterEach(() => {
  vi.unstubAllEnvs();
  vi.unstubAllGlobals();
});
describe("chat proxy", () => {
  it("rejects invalid messages and foreign origins before contacting the AI", async () => {
    const fetcher = vi.fn();
    vi.stubGlobal("fetch", fetcher);
    expect((await POST(request({ ...payload, text: " " }))).status).toBe(400);
    expect(
      (await POST(request(payload, "https://foreign.example"))).status,
    ).toBe(403);
    expect(fetcher).not.toHaveBeenCalled();
  });
  it("never reaches the network in explicit mock mode", async () => {
    vi.stubEnv("NUDGELY_CHAT_MODE", "mock");
    const fetcher = vi.fn();
    vi.stubGlobal("fetch", fetcher);
    const response = await POST(request(payload));
    expect((await response.json()).reply).toContain("offline rehearsal");
    expect(fetcher).not.toHaveBeenCalled();
  });
  it("preserves null replies and handover flags from the backend", async () => {
    vi.stubEnv("NUDGELY_CHAT_MODE", "live");
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockResolvedValue(
          Response.json({
            reply: null,
            handover: true,
            tags: [],
            customer_id: "WEB001",
          }),
        ),
    );
    const response = await POST(request(payload));
    expect(await response.json()).toEqual({
      reply: null,
      handover: true,
      tags: [],
      customer_id: "WEB001",
    });
  });
  it("shows rate limits without exposing arbitrary provider text", async () => {
    vi.stubEnv("NUDGELY_CHAT_MODE", "live");
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockResolvedValue(
          Response.json(
            { detail: "This demo chat has reached its message limit." },
            { status: 429 },
          ),
        ),
    );
    const response = await POST(request(payload));
    expect(response.status).toBe(429);
    expect((await response.json()).limited).toBe(true);
  });
  it("does not silently replace a failed live request with a fake reply", async () => {
    vi.stubEnv("NUDGELY_CHAT_MODE", "live");
    const fetcher = vi
      .fn()
      .mockRejectedValue(new Error("private upstream detail"));
    vi.stubGlobal("fetch", fetcher);
    const response = await POST(request(payload));
    expect(response.status).toBe(504);
    expect(fetcher).toHaveBeenCalledTimes(1);
    expect(JSON.stringify(await response.json())).not.toContain(
      "private upstream detail",
    );
  });
});
