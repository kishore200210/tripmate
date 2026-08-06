"use client";

import Link from "next/link";
import { Plane, Calendar, MapPin, MoreHorizontal, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useTrips } from "@/hooks/useDataAPI";

export default function TripsPage() {
  const { data: trips, isLoading, isError } = useTrips();

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-neutral-900">My Trips</h1>
          <p className="text-neutral-500">Manage your upcoming and past adventures.</p>
        </div>
        <Button>
          <Plane className="w-4 h-4 mr-2" />
          Plan New Trip
        </Button>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-20">
          <Loader2 className="h-8 w-8 animate-spin text-neutral-400" />
        </div>
      ) : isError ? (
        <div className="text-center py-20 text-red-500">
          Failed to load trips. Please try again later.
        </div>
      ) : trips?.length === 0 ? (
        <div className="text-center py-20 text-neutral-500">
          You don&apos;t have any trips planned yet. Click &quot;Plan New Trip&quot; to get started!
        </div>
      ) : (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {trips?.map((trip: any) => (
            <Card key={trip.id} className="overflow-hidden flex flex-col transition-all hover:shadow-md">
              <div className="aspect-video relative overflow-hidden bg-neutral-200">
                {/* Fallback image */}
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img 
                  src={"https://images.unsplash.com/photo-1502602898657-3e91760cbb34?auto=format&fit=crop&q=80&w=800"} 
                  alt={trip.name} 
                  className="object-cover w-full h-full transition-transform hover:scale-105"
                />
                <div className="absolute top-4 right-4">
                  <Badge variant={trip.status === "PLANNED" ? "default" : "secondary"} className="shadow-sm">
                    {trip.status}
                  </Badge>
                </div>
              </div>
              <CardHeader className="pb-2">
                <div className="flex justify-between items-start">
                  <div>
                    <CardTitle className="text-xl mb-1">{trip.name}</CardTitle>
                    <CardDescription className="flex items-center">
                      <MapPin className="w-3 h-3 mr-1" />
                      Trip ID: {trip.id}
                    </CardDescription>
                  </div>
                  <Button variant="ghost" size="icon" className="h-8 w-8 -mr-2">
                    <MoreHorizontal className="w-4 h-4" />
                  </Button>
                </div>
              </CardHeader>
              <CardContent className="pb-4">
                <div className="flex items-center text-sm text-neutral-600">
                  <Calendar className="w-4 h-4 mr-2" />
                  {new Date(trip.start_date).toLocaleDateString()} - {new Date(trip.end_date).toLocaleDateString()}
                </div>
              </CardContent>
              <div className="border-t p-4 mt-auto bg-neutral-50 flex gap-2">
                <Link href={`/trips/${trip.id}`} className="flex-1">
                  <Button variant="outline" className="w-full">Details</Button>
                </Link>
                <Link href={`/trips/${trip.id}/itinerary`} className="flex-1">
                  <Button className="w-full">Itinerary</Button>
                </Link>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
