import { Workspace } from "@/components/workspace";
export default function Layout({ children }: { children: React.ReactNode }) {
  return <Workspace demo>{children}</Workspace>;
}
