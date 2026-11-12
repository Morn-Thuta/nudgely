import { z } from "zod";
export const chatInput = z.object({
  session_id: z.string().regex(/^[A-Za-z0-9-]{8,64}$/),
  name: z.string().max(40).default(""),
  text: z.string().trim().min(1).max(500),
});
export const chatOutput = z.object({
  reply: z.string().nullable(),
  handover: z.boolean(),
  tags: z.array(
    z.object({ type: z.string(), value: z.string(), evidence: z.string() }),
  ),
  customer_id: z.string(),
});
export type ChatOutput = z.infer<typeof chatOutput>;
export function mockReply(text: string): ChatOutput {
  const command = text.trim().toUpperCase();
  const reply =
    command === "STOP"
      ? "Rehearsal: you have opted out. Type START to resume."
      : command === "START"
        ? "Rehearsal: welcome back! How can we help?"
        : command === "HUMAN"
          ? "Rehearsal: someone from the shop would follow up here."
          : "This is an offline rehearsal reply, not AI output. In live mode, Kampung Fresh can answer product questions or ask a person to help.";
  return {
    reply,
    handover: command === "HUMAN",
    tags: [],
    customer_id: "DEMO-WEB",
  };
}
