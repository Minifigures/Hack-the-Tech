import "./globals.css";
import type { Metadata } from "next";
import { SiteNav } from "@/components/site-nav";

export const metadata: Metadata = {
  title: "EvalForge — CI/CD for Reliable AI Agents",
  description:
    "EvalForge is an AI reliability cockpit: evals, traces, guardrails, and a deploy gate for RAG and agent systems.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen font-sans antialiased">
        <SiteNav />
        <main className="mx-auto w-full max-w-7xl px-6 pb-24 pt-6">{children}</main>
      </body>
    </html>
  );
}
