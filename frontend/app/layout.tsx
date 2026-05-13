import type { Metadata } from "next";
import Link from "next/link";
import { Landmark } from "lucide-react";
import "./globals.css";

export const metadata: Metadata = {
  title: "Civic Pulse",
  description: "Citizen-focused summaries of Kenyan civic reports and bills.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>
        <div className="min-h-screen bg-slate-50">
          <header className="sticky top-0 z-30 border-b border-slate-200/80 bg-white/90 backdrop-blur">
            <div className="mx-auto flex max-w-7xl flex-col gap-4 px-4 py-4 sm:px-6 lg:flex-row lg:items-center lg:justify-between lg:px-8">
              <Link className="group flex items-center gap-3" href="/">
                <span className="flex h-11 w-11 items-center justify-center rounded-xl bg-slate-950 text-white shadow-sm transition group-hover:bg-sky-800">
                  <Landmark aria-hidden="true" className="h-5 w-5" />
                </span>
                <span className="grid gap-0.5">
                  <strong className="text-xl font-bold tracking-tight text-slate-950">
                    Civic Pulse
                  </strong>
                  <span className="text-sm text-slate-500">
                    Public reports, bills, and institutional accountability
                  </span>
                </span>
              </Link>
              <div className="inline-flex w-fit items-center gap-2 rounded-full border border-slate-200 bg-slate-50 px-3 py-1.5 text-sm font-medium text-slate-600">
                <span className="h-2 w-2 rounded-full bg-emerald-500" />
                Generated civic summaries for public participation
              </div>
            </div>
          </header>
          {children}
        </div>
      </body>
    </html>
  );
}
