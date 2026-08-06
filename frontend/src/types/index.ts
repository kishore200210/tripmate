/**
 * src/types/index.ts
 *
 * Global TypeScript type definitions for TripMate.
 *
 * Convention:
 *   - Use `interface` for object shapes.
 *   - Use `type` for unions, intersections, and aliases.
 *   - Export everything — import from "@/types" using the barrel.
 */

// ── Shared API Types ───────────────────────────────────────────────────────────

export interface ApiError {
  error: {
    message: string;
    detail: string | null;
  };
}

/** Generic pagination envelope returned by all list endpoints. */
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  skip: number;
  limit: number;
}

// ── Utility Types ──────────────────────────────────────────────────────────────

export type Nullable<T> = T | null;
export type Optional<T> = T | undefined;

// ── Destination ────────────────────────────────────────────────────────────────

/** A travel destination catalog entry as returned by the API. */
export interface Destination {
  id: string;
  name: string;
  country: string;
  city: Nullable<string>;
  description: Nullable<string>;
  image_url: Nullable<string>;
  best_time_to_visit: Nullable<string>;
  avg_budget: Nullable<number>;
  duration_days: Nullable<number>;
  tags: Nullable<string[]>;
  created_at: string;
  updated_at: string;
}

/** Paginated response for GET /api/v1/destinations/ */
export type DestinationListResponse = PaginatedResponse<Destination>;

/** Lightweight count response for the dashboard card. */
export interface DestinationCountResponse {
  total: number;
}


// ── Trip ──────────────────────────────────────────────────────────────────────

export type TripStatus = "planning" | "confirmed" | "ongoing" | "completed" | "cancelled";

export interface Trip {
  id: string;
  title: string;
  description: Nullable<string>;
  start_date: Nullable<string>;
  end_date: Nullable<string>;
  budget: Nullable<number>;
  status: TripStatus;
  cover_image_url: Nullable<string>;
  destination_id: Nullable<string>;
  user_id: string;
  created_at: string;
  updated_at: string;
}

export type TripListResponse = PaginatedResponse<Trip>;
