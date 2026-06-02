import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Tapeology",
  description: "Single-ticker tape-reading cockpit — what is the tape doing right now?",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen antialiased">{children}</body>
    </html>
  );
}
