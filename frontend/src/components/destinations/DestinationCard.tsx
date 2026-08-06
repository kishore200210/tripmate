/**
 * src/components/destinations/DestinationCard.tsx
 *
 * Reusable card component for a single destination in the grid listing.
 */

import Link from "next/link";
import { MapPin, Clock, DollarSign, CalendarDays } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { Destination } from "@/types";

const FALLBACK_IMAGE =
  "https://images.unsplash.com/photo-1476514525535-07fb3b4ae5f1?auto=format&fit=crop&q=80&w=800";

interface DestinationCardProps {
  destination: Destination;
}

export function DestinationCard({ destination: dest }: DestinationCardProps) {
  const location = [dest.city, dest.country].filter(Boolean).join(", ");

  return (
    <article className="group flex flex-col overflow-hidden rounded-xl border bg-white shadow-sm transition-all duration-200 hover:shadow-lg hover:-translate-y-0.5">
      {/* Hero image */}
      <div className="relative aspect-[4/3] overflow-hidden bg-neutral-100">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src={dest.image_url || FALLBACK_IMAGE}
          alt={`${dest.name} cover photo`}
          className="h-full w-full object-cover transition-transform duration-300 group-hover:scale-105"
        />
        {/* Duration badge overlay */}
        {dest.duration_days && (
          <span className="absolute top-3 right-3 inline-flex items-center gap-1 rounded-full bg-black/60 px-2.5 py-1 text-xs font-medium text-white backdrop-blur-sm">
            <CalendarDays className="h-3 w-3" />
            {dest.duration_days}d
          </span>
        )}
      </div>

      {/* Card body */}
      <div className="flex flex-1 flex-col p-4 gap-3">
        {/* Name + budget */}
        <div className="flex items-start justify-between gap-2">
          <h2 className="text-lg font-semibold leading-tight text-neutral-900 line-clamp-1">
            {dest.name}
          </h2>
          {dest.avg_budget != null && (
            <Badge variant="secondary" className="shrink-0 font-mono text-xs">
              <DollarSign className="mr-0.5 h-3 w-3" />
              {Number(dest.avg_budget).toLocaleString()}
            </Badge>
          )}
        </div>

        {/* Location */}
        <p className="flex items-center gap-1.5 text-sm text-neutral-500">
          <MapPin className="h-3.5 w-3.5 shrink-0" />
          {location}
        </p>

        {/* Best time */}
        {dest.best_time_to_visit && (
          <p className="flex items-center gap-1.5 text-xs text-neutral-400">
            <Clock className="h-3 w-3 shrink-0" />
            Best: {dest.best_time_to_visit}
          </p>
        )}

        {/* Description */}
        {dest.description && (
          <p className="text-sm text-neutral-600 line-clamp-2 flex-1">
            {dest.description}
          </p>
        )}

        {/* Tags */}
        {dest.tags && dest.tags.length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {dest.tags.slice(0, 3).map((tag) => (
              <Badge key={tag} variant="outline" className="text-xs capitalize">
                {tag}
              </Badge>
            ))}
          </div>
        )}

        {/* CTA */}
        <div className="mt-auto pt-2 border-t">
          <Link href={`/destinations/${dest.id}`} className="block w-full">
            <Button
              variant="ghost"
              className="w-full text-blue-600 hover:text-blue-700 hover:bg-blue-50"
            >
              View Details
            </Button>
          </Link>
        </div>
      </div>
    </article>
  );
}
