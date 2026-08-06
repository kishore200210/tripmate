import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Plane, Calendar, FileText } from "lucide-react";
import Link from "next/link";
import { Button } from "@/components/ui/button";

export default function DashboardPage() {
  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-neutral-900">Dashboard</h1>
        <p className="text-neutral-500">Welcome back! Here&apos;s an overview of your travels.</p>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Upcoming Trips</CardTitle>
            <Plane className="h-4 w-4 text-neutral-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">2</div>
            <p className="text-xs text-neutral-500">Next trip in 14 days</p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Destinations Visited</CardTitle>
            <Calendar className="h-4 w-4 text-neutral-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">12</div>
            <p className="text-xs text-neutral-500">Across 5 countries</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Itineraries Generated</CardTitle>
            <FileText className="h-4 w-4 text-neutral-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">8</div>
            <p className="text-xs text-neutral-500">Using AI Concierge</p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Card className="col-span-1">
          <CardHeader>
            <CardTitle>Recent Trips</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center gap-4">
              <div className="h-10 w-10 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center font-bold">
                P
              </div>
              <div>
                <Link href="/trips/1" className="font-medium hover:underline text-neutral-900">Paris Getaway</Link>
                <p className="text-sm text-neutral-500">Oct 12 - Oct 18, 2026</p>
              </div>
              <div className="ml-auto">
                <span className="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold bg-green-100 text-green-800">
                  Upcoming
                </span>
              </div>
            </div>
            <div className="flex items-center gap-4">
              <div className="h-10 w-10 bg-orange-100 text-orange-600 rounded-full flex items-center justify-center font-bold">
                T
              </div>
              <div>
                <Link href="/trips/2" className="font-medium hover:underline text-neutral-900">Tokyo Adventure</Link>
                <p className="text-sm text-neutral-500">Mar 05 - Mar 15, 2026</p>
              </div>
              <div className="ml-auto">
                <span className="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold bg-neutral-100 text-neutral-800">
                  Completed
                </span>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="col-span-1 border-dashed border-2 bg-neutral-50 flex flex-col items-center justify-center py-12 text-center">
          <Plane className="w-12 h-12 text-neutral-300 mb-4" />
          <h3 className="text-lg font-medium text-neutral-900">Plan a new trip</h3>
          <p className="text-sm text-neutral-500 mb-4 max-w-[250px]">Use our AI Concierge to help you decide on your next adventure.</p>
          <Link href="/chat">
            <Button>Chat with AI</Button>
          </Link>
        </Card>
      </div>
    </div>
  );
}
