"use client";

import Link from "next/link";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useDestinations } from "@/hooks/useDataAPI";
import { Loader2 } from "lucide-react";

export default function DestinationsPage() {
  const { data: destinations, isLoading, isError } = useDestinations();

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-neutral-900">Destinations</h1>
          <p className="text-neutral-500">Explore places to visit and get inspired.</p>
        </div>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-20">
          <Loader2 className="h-8 w-8 animate-spin text-neutral-400" />
        </div>
      ) : isError ? (
        <div className="text-center py-20 text-red-500">
          Failed to load destinations. Please try again later.
        </div>
      ) : destinations?.length === 0 ? (
        <div className="text-center py-20 text-neutral-500">
          No destinations available at this time.
        </div>
      ) : (
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {destinations?.map((dest: any) => (
            <Card key={dest.id} className="overflow-hidden flex flex-col transition-all hover:shadow-md">
              <div className="aspect-[4/3] overflow-hidden bg-neutral-200">
                {/* Fallback image if backend doesn't provide one */}
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img 
                  src={dest.image_url || "https://images.unsplash.com/photo-1502602898657-3e91760cbb34?auto=format&fit=crop&q=80&w=800"} 
                  alt={dest.name} 
                  className="object-cover w-full h-full transition-transform hover:scale-105"
                />
              </div>
              <CardHeader>
                <div className="flex items-center justify-between mb-1">
                  <CardTitle className="text-xl">{dest.name}</CardTitle>
                  <Badge variant="secondary" className="font-mono">Budget: {dest.budget_level}/5</Badge>
                </div>
                <CardDescription className="line-clamp-2">{dest.description || dest.country}</CardDescription>
              </CardHeader>
              <CardContent className="flex-1">
                <div className="flex flex-wrap gap-2">
                  <Badge variant="outline" className="text-xs">Climate: {dest.climate_type}</Badge>
                  <Badge variant="outline" className="text-xs">Activity: {dest.activity_intensity}</Badge>
                </div>
              </CardContent>
              <CardFooter className="border-t pt-4 bg-neutral-50">
                <Link href={`/destinations/${dest.id}`} className="w-full">
                  <Button variant="ghost" className="w-full justify-center text-blue-600 hover:text-blue-700 hover:bg-blue-50">
                    View Details
                  </Button>
                </Link>
              </CardFooter>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
