import type { Metadata } from "next";
import "./globals.css";
import { NavBar } from "@/components/NavBar";

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
      <body className="min-h-screen antialiased">
        {/* The persistent app-level navigation (Cockpit · Journal · Studies) — the first
            multi-page surface (J-51). It sits above every page; the cockpit remains the home and
            stays one screen below it. */}
        <NavBar />
        {children}
      </body>
    </html>
  );
}
