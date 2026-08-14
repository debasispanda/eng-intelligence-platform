import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { dashboardData } from "@/lib/dashboard-data";
import { AppHeader } from "@/components/header/app-header";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "AI Engineering Intelligence Platform",
  description:
    "Delivery health dashboard for engineering leaders with release, quality, and risk signals.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full app-body">
        <div className="app-shell">
          <AppHeader appTitle={dashboardData.appTitle} profile={dashboardData.profile} />
          <main className="app-main">{children}</main>
        </div>
      </body>
    </html>
  );
}
