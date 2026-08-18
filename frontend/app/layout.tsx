import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { AppHeader } from "@/components/header/app-header";
import { DashboardProvider } from "@/components/dashboard/dashboard-provider";
import {
  getDashboardOverview,
  getRiskAssessments,
} from "@/lib/dashboard-api";
import type {
  DashboardOverview,
  RiskAssessment,
  UserProfile,
} from "@/lib/dashboard-types";

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

const unavailableProfile: UserProfile = {
  name: "Dashboard unavailable",
  role: "Profile data could not be loaded",
  email: "",
  avatarInitials: "!",
};

export default async function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  let overview: DashboardOverview | null = null;
  let error: string | null = null;
  let risks: RiskAssessment[] = [];
  let riskError: string | null = null;

  try {
    overview = await getDashboardOverview();
  } catch {
    error = "Dashboard data is unavailable. Check the backend connection and try again.";
  }

  if (overview !== null) {
    const riskResult = await Promise.allSettled([getRiskAssessments()]);

    if (riskResult[0].status === "fulfilled") {
      risks = riskResult[0].value;
    } else {
      riskError = "Risk intelligence is temporarily unavailable.";
    }
  }

  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full app-body">
        <DashboardProvider
          error={error}
          overview={overview}
          riskError={riskError}
          risks={risks}
          summary={null}
          summaryError={null}
        >
          <div className="app-shell">
            <AppHeader
              appTitle={overview?.appTitle ?? "Engineering Intelligence"}
              profile={overview?.profile ?? unavailableProfile}
            />
            <main className="app-main">{children}</main>
          </div>
        </DashboardProvider>
      </body>
    </html>
  );
}
