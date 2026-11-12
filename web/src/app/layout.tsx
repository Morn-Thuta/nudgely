import type { Metadata } from "next";
import "@fontsource-variable/outfit";
import "@fontsource-variable/dm-sans";
import "./globals.css";
import "./app-ui.css";
export const metadata: Metadata = {
  title: {
    default: "Nudgely — A little nudge. A lasting connection.",
    template: "%s · Nudgely",
  },
  description:
    "Help your neighbourhood shop remember its customers, send thoughtful messages, and measure what brings them back.",
};
export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>
        <a href="#main" className="skip-link">
          Skip to content
        </a>
        {children}
      </body>
    </html>
  );
}
