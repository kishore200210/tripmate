"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Plane, Calendar, FileText, Loader2 } from "lucide-react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { useTrips, useDestinationCount } from "@/hooks/useDataAPI";
import { ErrorState } from "@/components/shared/ErrorState";

export default function DashboardPage() {
  const { data: tripsData, isLoading: tripsLoading, isError: tripsError, refetch: refetchTrips } = useTrips();
  const { data: countData, isLoading: countLoading } = useDestinationCount();

  const trips = tripsData?.items || [];
  const destinationsCount = countData?.total ?? 0;

  // Filter for upcoming trips (start date in future or status is planned/planning)
  const upcomingTrips = trips.filter((trip: any) => {
    if (!trip.start_date) return true;
    return new Date(trip.start_date) >= new Date();
  });

  const isLoading = tripsLoading || countLoading;

  if (isLoading) {
    return (
      <div className="flex justify-center items-center py-20">
        <Loader2 className="h-8 w-8 animate-spin text-neutral-400" />
      </div>
    );
  }

  if (tripsError) {
    return <ErrorState message="Failed to load dashboard data." onRetry={refetchTrips} />;
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-neutral-900">Dashboard</h1>
        <p className="text-neutral-500">Welcome back! Here&apos;s an overview of your travels.</p>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <Card className="bg-white">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Upcoming Trips</CardTitle>
            <Plane className="h-4 w-4 text-neutral-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{upcomingTrips.length}</div>
            <p className="text-xs text-neutral-500">Active and upcoming adventures</p>
          </CardContent>
        </Card>
        
        <Card className="bg-white">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Trips</CardTitle>
            <Calendar className="h-4 w-4 text-neutral-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{trips.length}</div>
            <p className="text-xs text-neutral-500">Trips planned in TripMate</p>
          </CardContent>
        </Card>

        <Card className="bg-white">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Destinations Available</CardTitle>
            <FileText className="h-4 w-4 text-neutral-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{destinationsCount}</div>
            <p className="text-xs text-neutral-500">Curated travel guides</p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Card className="col-span-1 bg-white">
          <CardHeader>
            <CardTitle>Recent Trips</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {trips.length === 0 ? (
              <div className="text-sm text-neutral-500 py-4 italic">
                No trips planned yet. Click &quot;Chat with AI&quot; or browse destinations to start planning!
              </div>
            ) : (
              trips.slice(0, 3).map((trip: any) => {
                const isUpcoming = !trip.start_date || new Date(trip.start_date) >= new Date();
                return (
                  <div key={trip.id} className="flex items-center gap-4 border-b pb-3 last:border-0 last:pb-0">
                    <div className="h-10 w-10 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center font-bold uppercase">
                      {trip.title[0]}
                    </div>
                    <div>
                      <Link href={`/trips/${trip.id}`} className="font-medium hover:underline text-neutral-900">
                        {trip.title}
                      </Link>
                      <p className="text-xs text-neutral-500">
                        {trip.start_date ? new Date(trip.start_date).toLocaleDateString() : "Flexible"} - {trip.end_date ? new Date(trip.end_date).toLocaleDateString() : "Flexible"}
                      </p>
                    </div>
                    <div className="ml-auto">
                      <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold ${isUpcoming ? "bg-green-100 text-green-800" : "bg-neutral-100 text-neutral-800"}`}>
                        {isUpcoming ? "Upcoming" : "Completed"}
                      </span>
                    </div>
                  </div>
                );
              })
            )}
          </CardContent>
        </Card>

        <Card className="col-span-1 border-dashed border-2 bg-neutral-50 flex flex-col items-center justify-center py-12 text-center">
          <Plane className="w-12 h-12 text-neutral-300 mb-4" />
          <h3 className="text-lg font-medium text-neutral-900">Plan a new trip</h3>
          <p className="text-sm text-neutral-500 mb-4 max-w-[250px]">Use our AI Concierge to help you decide on your next adventure.</p>
          <div className="flex gap-2">
            <Link href="/chat">
              <Button>Chat with AI</Button>
            </Link>
            <Link href="/destinations">
              <Button variant="outline">Browse Destinations</Button>
            </Link>
          </div>
        </Card>
      </div>
    </div>
  );
}
