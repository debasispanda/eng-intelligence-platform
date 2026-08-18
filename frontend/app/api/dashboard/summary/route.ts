import { NextResponse } from "next/server";
import { getDeliverySummary } from "@/lib/dashboard-api";

export async function GET() {
  try {
    return NextResponse.json(await getDeliverySummary());
  } catch {
    return NextResponse.json(
      { detail: "Dashboard summary is unavailable." },
      { status: 503 },
    );
  }
}
