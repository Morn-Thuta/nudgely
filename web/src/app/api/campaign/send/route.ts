import { forwardToBackend } from "@/lib/backend";
export const maxDuration = 60;
export async function POST(request: Request) {
  return forwardToBackend(request, "/api/campaign/send", "POST");
}
