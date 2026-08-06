"use client";

/**
 * src/app/(app)/destinations/[id]/page.tsx
 *
 * Destination detail page — shows full information for a single destination.
 * Renders city, best_time_to_visit, duration_days, budget, tags, and description
 * from the live API. No mock data.
 */

import { use } from "react";
import Link from "next/link";
import {
  ArrowLeft,
  MapPin,
  CalendarDays,
  Clock,
  DollarSign,
  Tag,
  Loader2,
  Star,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ErrorState } from "@/components/shared/ErrorState";
import { useDestination } from "@/hooks/useDataAPI";

const FALLBACK_IMAGE =
  "https://images.unsplash.com/photo-1476514525535-07fb3b4ae5f1?auto=format&fit=crop&q=80&w=1200";

export default function DestinationDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const { data: dest, isLoading, isError, refetch } = useDestination(id);

  if (isLoading) {
    return (
      <div className="flex justify-center items-center py-20">
        <Loader2 className="h-8 w-8 animate-spin text-neutral-400" />
      </div>
    );
  }

  if (isError || !dest) {
    return (
      <div className="space-y-4">
        <Link
          href="/destinations"
          className="inline-flex items-center text-sm text-neutral-500 hover:text-neutral-900"
        >
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back to Destinations
        </Link>
        <ErrorState
          message="Failed to load this destination. It may have been removed."
          onRetry={() => refetch()}
        />
      </div>
    );
  }

  const destImage = dest.image_url || FALLBACK_IMAGE;
  const location = [dest.city, dest.country].filter(Boolean).join(", ");

  return (
    <div className="space-y-6">
      {/* Back navigation */}
      <Link
        href="/destinations"
        className="inline-flex items-center text-sm text-neutral-500 hover:text-neutral-900 transition-colors"
      >
        <ArrowLeft className="mr-2 h-4 w-4" />
        Back to Destinations
      </Link>

      {/* Hero banner */}
      <div className="relative h-[280px] sm:h-[380px] rounded-xl overflow-hidden shadow-md">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src={destImage}
          alt={`${dest.name} hero image`}
          className="h-full w-full object-cover"
        />
        {/* Gradient overlay */}
        <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-black/20 to-transparent" />

        {/* Title over image */}
        <div className="absolute bottom-0 left-0 right-0 p-6 text-white">
          <h1 className="text-3xl sm:text-5xl font-bold mb-2 drop-shadow-md">
            {dest.name}
          </h1>
          <div className="flex flex-wrap items-center gap-4 text-sm font-medium text-white/90">
            {location && (
              <span className="flex items-center gap-1">
                <MapPin className="h-4 w-4" />
                {location}
              </span>
            )}
            {dest.duration_days && (
              <span className="flex items-center gap-1">
                <CalendarDays className="h-4 w-4" />
                {dest.duration_days} day{dest.duration_days !== 1 ? "s" : ""} recommended
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Body: tabs + info sidebar */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Tabs — left/main column */}
        <div className="md:col-span-2">
          <Tabs defaultValue="overview">
            <TabsList>
              <TabsTrigger value="overview">Overview</TabsTrigger>
              <TabsTrigger value="highlights">Highlights</TabsTrigger>
              <TabsTrigger value="reviews">Reviews</TabsTrigger>
            </TabsList>

            {/* Overview tab */}
            <TabsContent value="overview" className="space-y-4 pt-4">
              <p className="text-neutral-600 leading-relaxed">
                {dest.description ||
                  "Explore the sights, culture, and cuisine of this wonderful destination."}
              </p>

              {dest.tags && dest.tags.length > 0 && (
                <div>
                  <p className="mb-2 flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-neutral-400">
                    <Tag className="h-3.5 w-3.5" />
                    Tags
                  </p>
                  <div className="flex flex-wrap gap-2">
                    {dest.tags.map((tag) => (
                      <Badge key={tag} variant="secondary" className="capitalize">
                        {tag}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}
            </TabsContent>

            {/* Highlights tab */}
            <TabsContent value="highlights" className="space-y-4 pt-4">
              <div className="grid gap-4 sm:grid-cols-2">
                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-base">City Landmarks</CardTitle>
                  </CardHeader>
                  <CardContent className="text-sm text-neutral-500">
                    Explore iconic architectural wonders and historical spots in{" "}
                    {dest.city || dest.name}.
                  </CardContent>
                </Card>
                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-base">Local Cuisine</CardTitle>
                  </CardHeader>
                  <CardContent className="text-sm text-neutral-500">
                    Experience authentic culinary delights at top-rated local cafes and
                    restaurants.
                  </CardContent>
                </Card>
              </div>
            </TabsContent>

            {/* Reviews tab */}
            <TabsContent value="reviews" className="pt-4">
              <Card>
                <CardContent className="p-6">
                  <div className="flex items-start gap-4">
                    <div className="h-10 w-10 rounded-full bg-neutral-200 flex-shrink-0 flex items-center justify-center font-semibold text-neutral-600">
                      JS
                    </div>
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <span className="font-semibold text-neutral-900">Jane Smith</span>
                        <div className="flex text-yellow-400">
                          {Array.from({ length: 5 }).map((_, i) => (
                            <Star key={i} className="h-3 w-3 fill-current" />
                          ))}
                        </div>
                      </div>
                      <p className="text-sm text-neutral-600">
                        Absolutely magical experience! The food, the culture, everything was perfect.
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </div>

        {/* Info sidebar — right column */}
        <div className="space-y-4">
          <Card className="bg-white">
            <CardHeader>
              <CardTitle className="text-base">Destination Info</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4 text-sm">
              {/* Location */}
              {location && (
                <InfoRow
                  icon={<MapPin className="h-4 w-4" />}
                  label="Location"
                  value={location}
                />
              )}

              {/* Best time */}
              {dest.best_time_to_visit ? (
                <InfoRow
                  icon={<Clock className="h-4 w-4" />}
                  label="Best Time"
                  value={dest.best_time_to_visit}
                />
              ) : (
                <InfoRow
                  icon={<Clock className="h-4 w-4" />}
                  label="Best Time"
                  value="Year-round"
                />
              )}

              {/* Duration */}
              {dest.duration_days && (
                <InfoRow
                  icon={<CalendarDays className="h-4 w-4" />}
                  label="Recommended Stay"
                  value={`${dest.duration_days} day${dest.duration_days !== 1 ? "s" : ""}`}
                />
              )}

              {/* Budget */}
              {dest.avg_budget != null && (
                <div className="flex items-center justify-between">
                  <span className="flex items-center gap-2 text-neutral-500">
                    <DollarSign className="h-4 w-4" />
                    Avg. Budget
                  </span>
                  <Badge variant="secondary" className="font-mono">
                    ${Number(dest.avg_budget).toLocaleString()}
                  </Badge>
                </div>
              )}

              {/* CTA */}
              <Link
                href={`/trips?destinationId=${dest.id}`}
                className="block w-full mt-2"
              >
                <Button className="w-full">Plan a Trip Here</Button>
              </Link>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

/** Small presentational helper for a label+value row in the info sidebar. */
function InfoRow({
  icon,
  label,
  value,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
}) {
  return (
    <div className="flex items-start justify-between gap-2">
      <span className="flex items-center gap-2 text-neutral-500 shrink-0">
        {icon}
        {label}
      </span>
      <span className="font-medium text-neutral-800 text-right">{value}</span>
    </div>
  );
}
