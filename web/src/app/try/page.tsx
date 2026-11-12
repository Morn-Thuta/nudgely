import { Chat } from "@/components/chat";
export const metadata = { title: "Try Kampung Fresh" };
export const dynamic = "force-dynamic";
export default function TryPage() {
  return <Chat mock={process.env.NUDGELY_CHAT_MODE === "mock"} />;
}
