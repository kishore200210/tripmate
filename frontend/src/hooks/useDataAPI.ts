/**
 * src/hooks/useDataAPI.ts
 *
 * React Query hooks for all data-fetching operations.
 *
 * Convention:
 *   - All hooks wrap `useQuery` or `useMutation` from @tanstack/react-query.
 *   - Cache keys are defined as const arrays for easy invalidation.
 *   - Hooks accept typed parameters so TypeScript catches invalid usage at compile time.
 */

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type {
  Destination,
  DestinationListResponse,
  DestinationCountResponse,
  PlaceResult,
  Trip,
  TripStatus,
  TripListResponse,
} from "@/types";

// ── Query Key Factories ────────────────────────────────────────────────────────
// Centralise cache keys to avoid typos and enable precise invalidation.

export const destinationKeys = {
  all: ["destinations"] as const,
  list: (params: DestinationParams) => ["destinations", "list", params] as const,
  detail: (id: string) => ["destinations", "detail", id] as const,
  count: ["destinations", "count"] as const,
};

export const tripKeys = {
  all: ["trips"] as const,
  list: (params: TripParams) => ["trips", "list", params] as const,
  detail: (id: string) => ["trips", "detail", id] as const,
  itinerary: (tripId: string) => ["itinerary", tripId] as const,
};

export const placeKeys = {
  search: (q: string) => ["places", "search", q] as const,
};

// ── Destination Hooks ──────────────────────────────────────────────────────────

export interface DestinationParams {
  q?: string;
  country?: string;
  tag?: string;
  skip?: number;
  limit?: number;
  sort_by?: string;
  sort_desc?: boolean;
}

/**
 * Fetch a paginated, filtered list of destinations.
 * All params are optional — omitting them returns the first page of all destinations.
 */
export function useDestinations(params: DestinationParams = {}) {
  return useQuery<DestinationListResponse>({
    queryKey: destinationKeys.list(params),
    queryFn: async () => {
      const searchParams = new URLSearchParams();
      if (params.q) searchParams.set("q", params.q);
      if (params.country) searchParams.set("country", params.country);
      if (params.tag) searchParams.set("tag", params.tag);
      if (params.skip !== undefined) searchParams.set("skip", String(params.skip));
      if (params.limit !== undefined) searchParams.set("limit", String(params.limit));
      if (params.sort_by) searchParams.set("sort_by", params.sort_by);
      if (params.sort_desc !== undefined) searchParams.set("sort_desc", String(params.sort_desc));

      const query = searchParams.toString();
      const { data } = await api.get<DestinationListResponse>(
        `/destinations/${query ? `?${query}` : ""}`
      );
      return data;
    },
    staleTime: 1000 * 60 * 2, // 2 minutes — destination catalog changes infrequently
  });
}

/** Fetch the total count of active destinations. Used by the dashboard card. */
export function useDestinationCount() {
  return useQuery<DestinationCountResponse>({
    queryKey: destinationKeys.count,
    queryFn: async () => {
      const { data } = await api.get<DestinationCountResponse>("/destinations/count");
      return data;
    },
    staleTime: 1000 * 60 * 5, // 5 minutes
  });
}

/** Fetch a single destination by ID. */
export function useDestination(id: string) {
  return useQuery<Destination>({
    queryKey: destinationKeys.detail(id),
    queryFn: async () => {
      const { data } = await api.get<Destination>(`/destinations/${id}`);
      return data;
    },
    enabled: !!id,
  });
}

// ── Place Search Hook ──────────────────────────────────────────────────────────

/**
 * Search for places worldwide via the backend Nominatim proxy.
 * Requires at least 2 characters. Results are cached for 5 minutes.
 * Use with a debounced query value in the component (300-500ms recommended).
 */
export function usePlaceSearch(query: string) {
  return useQuery<PlaceResult[]>({
    queryKey: placeKeys.search(query),
    queryFn: async ({ signal }) => {
      const { data } = await api.get<PlaceResult[]>("/places/search", {
        params: { q: query },
        signal,
      });
      return data;
    },
    enabled: query.trim().length >= 2,
    staleTime: 1000 * 60 * 5, // 5 minutes — mirrors backend cache TTL
    retry: false,              // Don't retry on network errors during typing
  });
}

// ── Trip Hooks ─────────────────────────────────────────────────────────────────

export interface TripParams {
  q?: string;
  status?: string;
  skip?: number;
  limit?: number;
}

/** Fetch all trips belonging to the authenticated user with optional filtering/pagination. */
export function useTrips(params: TripParams = {}) {
  return useQuery<TripListResponse>({
    queryKey: tripKeys.list(params),
    queryFn: async () => {
      const searchParams = new URLSearchParams();
      if (params.q) searchParams.set("q", params.q);
      if (params.status) searchParams.set("trip_status", params.status);
      if (params.skip !== undefined) searchParams.set("skip", String(params.skip));
      if (params.limit !== undefined) searchParams.set("limit", String(params.limit));

      const query = searchParams.toString();
      const { data } = await api.get<TripListResponse>(
        `/trips/${query ? `?${query}` : ""}`
      );
      return data;
    },
  });
}

/** Fetch a single trip by ID. */
export function useTrip(id: string) {
  return useQuery<Trip>({
    queryKey: tripKeys.detail(id),
    queryFn: async () => {
      const { data } = await api.get<Trip>(`/trips/${id}`);
      return data;
    },
    enabled: !!id,
  });
}

/**
 * Fetch the itinerary timeline for a trip.
 * Backend: GET /api/v1/trips/{trip_id}/itinerary/
 * Returns: { trip_id, items: ItineraryItemResponse[], total_items }
 */
export function useItinerary(tripId: string) {
  return useQuery({
    queryKey: tripKeys.itinerary(tripId),
    queryFn: async () => {
      const { data } = await api.get(`/trips/${tripId}/itinerary/`);
      return data;
    },
    enabled: !!tripId,
  });
}

/**
 * Fetch AI itinerary metadata for a trip.
 */
export function useAIItineraryDetails(tripId: string) {
  return useQuery({
    queryKey: ["ai_itinerary", tripId],
    queryFn: async () => {
      const { data } = await api.get(`/trips/${tripId}/itinerary/ai-details`);
      return data;
    },
    enabled: !!tripId,
    retry: false, // Don't retry if 404 (not generated yet)
  });
}

export interface AIGeneratePayload {
  preferences?: string;
}

export function useGenerateItinerary(tripId: string) {
  const queryClient = useQueryClient();
  return useMutation<any, Error, AIGeneratePayload>({
    mutationFn: async (payload) => {
      const { data } = await api.post(`/trips/${tripId}/itinerary/generate`, payload);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: tripKeys.itinerary(tripId) });
      queryClient.invalidateQueries({ queryKey: ["ai_itinerary", tripId] });
    },
  });
}

export interface RegenerateDayPayload {
  dayNo?: number;
  preferences?: string;
}

export function useRegenerateDayPlan(tripId: string, initialDayNo?: number) {
  const queryClient = useQueryClient();
  return useMutation<any, Error, RegenerateDayPayload>({
    mutationFn: async (payload) => {
      const targetDay = payload.dayNo ?? initialDayNo;
      if (!targetDay || targetDay <= 0) {
        throw new Error("Invalid day number specified for regeneration.");
      }
      const { data } = await api.post(`/trips/${tripId}/itinerary/generate/${targetDay}`, {
        preferences: payload.preferences,
      });
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: tripKeys.itinerary(tripId) });
      queryClient.invalidateQueries({ queryKey: ["ai_itinerary", tripId] });
    },
  });
}

export interface CreateTripPayload {
  title: string;
  description?: string;
  start_date?: string;
  end_date?: string;
  budget?: number;
  destination_id?: string;
}

/** Create a new trip. Invalidates the trips cache on success. */
export function useCreateTrip() {
  const queryClient = useQueryClient();

  return useMutation<Trip, Error, CreateTripPayload>({
    mutationFn: async (payload) => {
      const { data } = await api.post<Trip>("/trips/", payload);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["trips"] });
    },
  });
}

export interface UpdateTripPayload {
  title?: string;
  description?: string;
  start_date?: string;
  end_date?: string;
  budget?: number;
  status?: TripStatus;
  destination_id?: string;
}

/** Update an existing trip. Invalidates the trips cache and detail cache on success. */
export function useUpdateTrip(id: string) {
  const queryClient = useQueryClient();

  return useMutation<Trip, Error, UpdateTripPayload>({
    mutationFn: async (payload) => {
      const { data } = await api.patch<Trip>(`/trips/${id}`, payload);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["trips"] });
      queryClient.invalidateQueries({ queryKey: tripKeys.detail(id) });
    },
  });
}

/** Delete a trip. Invalidates the trips cache on success. */
export function useDeleteTrip() {
  const queryClient = useQueryClient();

  return useMutation<void, Error, string>({
    mutationFn: async (id) => {
      await api.delete(`/trips/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["trips"] });
    },
  });
}

/** Trigger PDF itinerary generation for a trip. */
export function useGeneratePDF(tripId: string) {
  return useMutation<{ task_id: string; status: string }, Error, void>({
    mutationFn: async () => {
      const { data } = await api.post<{ task_id: string; status: string }>(`/pdf/itinerary/${tripId}`);
      return data;
    },
  });
}
