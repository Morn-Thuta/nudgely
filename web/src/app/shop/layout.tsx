import { OwnerShell } from "@/components/owner-shell";
export default function Layout({ children }: { children: React.ReactNode }) {
  return <OwnerShell>{children}</OwnerShell>;
}
