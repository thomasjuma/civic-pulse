import type { Metadata } from "next";
import Link from "next/link";
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
        <div className="site-shell">
          <header className="masthead">
            <div className="masthead-inner">
              <Link className="brand" href="/">
                <strong>Civic Pulse</strong>
                <span>Public reports, bills, and institutional accountability</span>
              </Link>
              <div className="topline">Generated civic summaries for public participation</div>
            </div>
          </header>
          {children}
        </div>
      </body>
    </html>
  );
}

