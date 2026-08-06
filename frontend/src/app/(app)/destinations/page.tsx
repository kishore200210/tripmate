"use client";

/**
 * src/app/(app)/destinations/page.tsx
 *
 * Destinations list page with real-time search, country filter, and pagination.
 *
 * State:
 *   - searchInput: controlled input value (not debounced)
 *   - debouncedSearch: what's actually sent to the API (400ms debounce)
 *   - country: active country filter
 *   - skip: pagination offset
 *
 * All state changes reset `skip` to 0 to avoid empty pages.
 */

import { useState, useEffect, useCallback } from "react";
import { Search, Globe, MapPin, Loader2, X } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { DestinationCard } from "@/components/destinations/DestinationCard";
import { EmptyState } from "@/components/shared/EmptyState";
import { ErrorState } from "@/components/shared/ErrorState";
import { Pagination } from "@/components/shared/Pagination";
import { useDestinations } from "@/hooks/useDataAPI";

const PAGE_SIZE = 12;

/** Common countries derived from the full list — used to pre-populate the filter. */
const POPULAR_COUNTRIES = [
  "Australia", "Brazil", "Canada", "China", "Egypt", "France",
  "Germany", "Greece", "India", "Indonesia", "Italy", "Japan",
  "Mexico", "Morocco", "Nepal", "New Zealand", "Peru", "Portugal",
  "Singapore", "South Africa", "Spain", "Switzerland", "Thailand",
  "Turkey", "United Kingdom", "United States", "Vietnam",
];

export default function DestinationsPage() {
  const [searchInput, setSearchInput] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [country, setCountry] = useState("");
  const [skip, setSkip] = useState(0);

  // 400ms debounce: only update the API query after the user stops typing.
  useEffect(() => {
    const timer = setTimeout(() => setDebouncedSearch(searchInput), 400);
    return () => clearTimeout(timer);
  }, [searchInput]);

  // Reset to first page whenever filters change.
  useEffect(() => {
    setSkip(0);
  }, [debouncedSearch, country]);

  const { data, isLoading, isError, refetch } = useDestinations({
    q: debouncedSearch || undefined,
    country: country || undefined,
    skip,
    limit: PAGE_SIZE,
    sort_by: "name",
  });

  const destinations = data?.items ?? [];
  const total = data?.total ?? 0;

  const handleClearFilters = useCallback(() => {
    setSearchInput("");
    setDebouncedSearch("");
    setCountry("");
    setSkip(0);
  }, []);

  const hasActiveFilters = searchInput || country;

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-neutral-900">
          Destinations
        </h1>
        <p className="mt-1 text-neutral-500">
          Explore{" "}
          {total > 0 ? (
            <span className="font-medium text-neutral-700">{total}</span>
          ) : (
            "our"
          )}{" "}
          curated travel destinations around the world.
        </p>
      </div>

      {/* Search & filter toolbar */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
        {/* Search input */}
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-neutral-400" />
          <Input
            id="destination-search"
            placeholder="Search destinations…"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            className="pl-9"
          />
          {searchInput && (
            <button
              onClick={() => setSearchInput("")}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-neutral-400 hover:text-neutral-700"
              aria-label="Clear search"
            >
              <X className="h-4 w-4" />
            </button>
          )}
        </div>

        {/* Country filter */}
        <div className="relative w-full sm:w-[200px]">
          <Globe className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-neutral-400 pointer-events-none" />
          <select
            id="country-filter"
            value={country || "all"}
            onChange={(e) => setCountry(e.target.value === "all" ? "" : e.target.value)}
            className="w-full pl-9 pr-8 py-2 border rounded-md text-sm text-neutral-800 bg-white hover:bg-neutral-50 focus:outline-none focus:ring-1 focus:ring-neutral-400 appearance-none transition-colors"
            aria-label="Filter by country"
          >
            <option value="all">All countries</option>
            {POPULAR_COUNTRIES.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
          <div className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none text-neutral-500">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" />
            </svg>
          </div>
        </div>

        {/* Clear filters */}
        {hasActiveFilters && (
          <Button variant="ghost" size="sm" onClick={handleClearFilters}>
            <X className="mr-1 h-3.5 w-3.5" />
            Clear
          </Button>
        )}
      </div>

      {/* Content area */}
      {isLoading ? (
        <div className="flex justify-center py-20">
          <Loader2 className="h-8 w-8 animate-spin text-neutral-400" />
        </div>
      ) : isError ? (
        <ErrorState
          message="Failed to load destinations. Please check your connection and try again."
          onRetry={() => refetch()}
        />
      ) : destinations.length === 0 ? (
        <EmptyState
          icon={MapPin}
          title={hasActiveFilters ? "No destinations found" : "No destinations yet"}
          message={
            hasActiveFilters
              ? "Try adjusting your search or filters to find what you're looking for."
              : "Destinations will appear here once they are added by an admin."
          }
          action={
            hasActiveFilters ? (
              <Button variant="outline" onClick={handleClearFilters}>
                Clear filters
              </Button>
            ) : undefined
          }
        />
      ) : (
        <>
          <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {destinations.map((dest) => (
              <DestinationCard key={dest.id} destination={dest} />
            ))}
          </div>

          <Pagination
            skip={skip}
            limit={PAGE_SIZE}
            total={total}
            onSkipChange={setSkip}
          />
        </>
      )}
    </div>
  );
}
