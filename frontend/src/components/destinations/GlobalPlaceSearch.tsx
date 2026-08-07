"use client";

/**
 * src/components/destinations/GlobalPlaceSearch.tsx
 *
 * Global destination search component allowing users to search any location
 * worldwide via OpenStreetMap Nominatim geocoding, preview details & coordinates,
 * and seamlessly initiate trip creation.
 */

import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import {
  Search,
  MapPin,
  Compass,
  Navigation,
  Globe2,
  Plus,
  Loader2,
  X,
  Info,
} from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { usePlaceSearch } from "@/hooks/useDataAPI";
import type { PlaceResult } from "@/types";

// ── Country Code → Flag Emoji ──────────────────────────────────────────────────
function countryFlag(code: string | null | undefined): string {
  if (!code || code.length !== 2) return "🌍";
  return String.fromCodePoint(
    ...code.toUpperCase().split("").map((c) => 0x1f1e6 + c.charCodeAt(0) - 65)
  );
}

// ── Image helper ───────────────────────────────────────────────────────────────
function getPlaceImageUrl(placeName: string): string {
  return `https://images.unsplash.com/photo-1488646953014-85cb44e25828?auto=format&fit=crop&w=1200&q=80&place=${encodeURIComponent(placeName)}`;
}

export function GlobalPlaceSearch() {
  const router = useRouter();
  const [searchInput, setSearchInput] = useState("");
  const [debouncedQuery, setDebouncedQuery] = useState("");
  const [selectedPlace, setSelectedPlace] = useState<PlaceResult | null>(null);
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);

  const containerRef = useRef<HTMLDivElement>(null);

  // Debounce query (350ms)
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedQuery(searchInput.trim());
    }, 350);
    return () => clearTimeout(timer);
  }, [searchInput]);

  const { data: results = [], isFetching } = usePlaceSearch(debouncedQuery);

  // Auto-open dropdown when results arrive
  useEffect(() => {
    if (results.length > 0 && debouncedQuery.length >= 2 && !selectedPlace) {
      setIsDropdownOpen(true);
    }
  }, [results, debouncedQuery, selectedPlace]);

  // Click outside listener to close dropdown
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsDropdownOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleSelectPlace = (place: PlaceResult) => {
    setSelectedPlace(place);
    setSearchInput(place.display_name || place.name);
    setIsDropdownOpen(false);
  };

  const handleClear = () => {
    setSearchInput("");
    setDebouncedQuery("");
    setSelectedPlace(null);
    setIsDropdownOpen(false);
  };

  const handlePlanTrip = () => {
    if (!selectedPlace) return;
    const name = encodeURIComponent(selectedPlace.name);
    const country = encodeURIComponent(selectedPlace.country || "");
    router.push(`/trips?plan=true&place_name=${name}&place_country=${country}`);
  };

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="bg-gradient-to-r from-blue-900 via-indigo-900 to-slate-900 rounded-2xl p-6 sm:p-8 text-white shadow-xl relative overflow-hidden">
        <div className="absolute right-0 top-0 translate-x-12 -translate-y-12 w-64 h-64 bg-blue-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="relative z-10 max-w-2xl space-y-3">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-500/20 text-blue-300 text-xs font-semibold backdrop-blur-xs border border-blue-400/20">
            <Globe2 className="w-3.5 h-3.5" />
            Global OpenStreetMap Search
          </div>
          <h2 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-white">
            Search Any Place in the World
          </h2>
          <p className="text-neutral-300 text-sm leading-relaxed">
            Find any city, town, island, region, or tourist destination across 190+ countries and instantly start planning your journey.
          </p>
        </div>
      </div>

      {/* Search Input Bar with Suggestions Dropdown */}
      <div ref={containerRef} className="relative max-w-3xl mx-auto">
        <div className="relative flex items-center">
          <Search className="absolute left-4 h-5 w-5 text-neutral-400 pointer-events-none" />
          <Input
            value={searchInput}
            onChange={(e) => {
              setSearchInput(e.target.value);
              setSelectedPlace(null);
              setIsDropdownOpen(true);
            }}
            onFocus={() => {
              if (results.length > 0 && !selectedPlace) setIsDropdownOpen(true);
            }}
            placeholder="Type any place e.g. Germany, Kyoto, Chengalpattu, Paris, Machu Picchu…"
            className="pl-12 pr-10 py-6 text-base rounded-xl border-neutral-200 bg-white shadow-md focus-visible:ring-2 focus-visible:ring-blue-600 focus-visible:border-transparent text-neutral-900"
          />
          {searchInput && (
            <button
              onClick={handleClear}
              type="button"
              className="absolute right-3.5 text-neutral-400 hover:text-neutral-600 p-1 rounded-full hover:bg-neutral-100 transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>

        {/* Dropdown Suggestions */}
        {isDropdownOpen && (
          <div className="absolute top-full left-0 right-0 mt-2 bg-white rounded-xl border border-neutral-200 shadow-2xl z-50 overflow-hidden max-h-96 overflow-y-auto divide-y divide-neutral-100">
            {isFetching && (
              <div className="p-4 flex items-center justify-center gap-2 text-neutral-500 text-sm">
                <Loader2 className="w-4 h-4 animate-spin text-blue-600" />
                Searching global geocoding index…
              </div>
            )}

            {!isFetching && results.length === 0 && debouncedQuery.length >= 2 && (
              <div className="p-6 text-center text-neutral-500 space-y-1">
                <p className="text-sm font-medium text-neutral-800">No matching destinations found</p>
                <p className="text-xs text-neutral-400">Try spelling out the full city or country name.</p>
              </div>
            )}

            {!isFetching &&
              results.map((place) => (
                <button
                  key={place.place_id}
                  onClick={() => handleSelectPlace(place)}
                  className="w-full text-left p-4 hover:bg-blue-50/70 transition-colors flex items-start gap-3.5 group cursor-pointer"
                >
                  <div className="p-2 rounded-lg bg-neutral-100 group-hover:bg-blue-100 text-neutral-600 group-hover:text-blue-700 transition-colors mt-0.5 shrink-0">
                    <MapPin className="w-4 h-4" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-neutral-900 group-hover:text-blue-900 truncate">
                        {place.name}
                      </span>
                      <span className="text-base">{countryFlag(place.country_code)}</span>
                      {place.place_type && (
                        <Badge variant="outline" className="text-[10px] font-normal text-neutral-500 border-neutral-200">
                          {place.place_type}
                        </Badge>
                      )}
                    </div>
                    <p className="text-xs text-neutral-500 truncate mt-0.5">
                      {place.display_name}
                    </p>
                    {place.latitude !== null && place.longitude !== null && (
                      <p className="text-[11px] font-mono text-neutral-400 mt-1 flex items-center gap-1">
                        <Navigation className="w-3 h-3 text-neutral-400" />
                        {place.latitude?.toFixed(4)}°, {place.longitude?.toFixed(4)}°
                      </p>
                    )}
                  </div>
                </button>
              ))}
          </div>
        )}
      </div>

      {/* Selected Location Detailed Card */}
      {selectedPlace ? (
        <Card className="max-w-3xl mx-auto bg-white border border-neutral-200 shadow-xl overflow-hidden rounded-2xl transition-all animate-in fade-in-50 duration-300">
          <div className="relative h-64 w-full bg-slate-900">
            <img
              src={getPlaceImageUrl(selectedPlace.name)}
              alt={selectedPlace.name}
              className="w-full h-full object-cover opacity-85"
            />
            <div className="absolute inset-0 bg-gradient-to-t from-slate-950 via-slate-950/40 to-transparent" />
            <div className="absolute bottom-4 left-6 right-6 text-white flex flex-col sm:flex-row sm:items-end justify-between gap-4">
              <div>
                <div className="flex items-center gap-2 text-blue-300 text-xs font-semibold uppercase tracking-wider mb-1">
                  <span>{countryFlag(selectedPlace.country_code)}</span>
                  <span>{selectedPlace.country || "Worldwide Destination"}</span>
                </div>
                <h3 className="text-2xl sm:text-3xl font-extrabold text-white">
                  {selectedPlace.name}
                </h3>
                {selectedPlace.state && (
                  <p className="text-neutral-300 text-xs mt-0.5">
                    {selectedPlace.state}, {selectedPlace.country}
                  </p>
                )}
              </div>
              {selectedPlace.place_type && (
                <Badge className="bg-blue-600/80 hover:bg-blue-600 text-white backdrop-blur-xs px-3 py-1 text-xs font-medium self-start sm:self-auto">
                  {selectedPlace.place_type}
                </Badge>
              )}
            </div>
          </div>

          <CardContent className="p-6 space-y-6">
            {/* Details Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 bg-neutral-50 p-4 rounded-xl border border-neutral-100">
              <div className="space-y-1">
                <span className="text-xs font-semibold text-neutral-400 uppercase tracking-wider flex items-center gap-1.5">
                  <Navigation className="w-3.5 h-3.5 text-blue-600" />
                  Coordinates
                </span>
                <p className="text-sm font-mono font-medium text-neutral-800">
                  {selectedPlace.latitude !== null && selectedPlace.longitude !== null
                    ? `${selectedPlace.latitude?.toFixed(4)}° N, ${selectedPlace.longitude?.toFixed(4)}° E`
                    : "Coordinates Available"}
                </p>
              </div>

              <div className="space-y-1">
                <span className="text-xs font-semibold text-neutral-400 uppercase tracking-wider flex items-center gap-1.5">
                  <Globe2 className="w-3.5 h-3.5 text-blue-600" />
                  Full Location Path
                </span>
                <p className="text-sm text-neutral-700 truncate" title={selectedPlace.display_name}>
                  {selectedPlace.display_name}
                </p>
              </div>
            </div>

            {/* CTA Box */}
            <div className="flex flex-col sm:flex-row items-center justify-between gap-4 pt-2 border-t border-neutral-100">
              <div className="text-xs text-neutral-500 flex items-center gap-1.5">
                <Info className="w-4 h-4 text-blue-500 shrink-0" />
                <span>Ready to explore? Create a trip with this destination pre-filled.</span>
              </div>
              <Button
                onClick={handlePlanTrip}
                className="w-full sm:w-auto bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white font-semibold shadow-md px-6 py-5 rounded-xl"
              >
                <Plus className="w-4 h-4 mr-2" />
                Plan Trip to {selectedPlace.name}
              </Button>
            </div>
          </CardContent>
        </Card>
      ) : (
        /* Empty Prompt State */
        <div className="max-w-md mx-auto text-center py-12 px-4 space-y-3">
          <div className="w-12 h-12 rounded-full bg-blue-50 text-blue-600 mx-auto flex items-center justify-center">
            <Compass className="w-6 h-6" />
          </div>
          <h3 className="text-base font-semibold text-neutral-800">
            Search Any Place Worldwide
          </h3>
          <p className="text-xs text-neutral-500 leading-relaxed">
            Type any city, island, region, or attraction in the search box above to get instant coordinates, location tags, and plan your next custom trip.
          </p>
        </div>
      )}
    </div>
  );
}
