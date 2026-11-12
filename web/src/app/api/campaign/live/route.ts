import { forwardToBackend } from "@/lib/backend";
export const maxDuration = 60;
export async function GET(request: Request) {
  return forwardToBackend(request, "/api/campaign/live", "GET");
}
