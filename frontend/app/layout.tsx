import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "BlueprintIQ — Construction Document Intelligence",
  description: "Upload construction documents and get traceable, evidence-grounded materials, procurement stages, and reasoning.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-blueprint-950 font-sans antialiased text-blueprint-100 selection:bg-signal-orange selection:text-blueprint-950">
        <main className="mx-auto max-w-7xl px-6 py-8">
          {children}
        </main>
      </body>
    </html>
  );
}