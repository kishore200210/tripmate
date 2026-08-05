/**
 * src/types/index.ts
 *
 * Global TypeScript type definitions for TripMate.
 *
 * What belongs here:
 *   - API response interfaces (ApiResponse<T>, PaginatedResponse<T>)
 *   - Shared domain types (User, Trip, Destination)
 *   - Utility types (Nullable<T>, Optional<T>)
 *
 * Convention:
 *   - Use `interface` for object shapes.
 *   - Use `type` for unions, intersections, and aliases.
 *   - Export everything — import from "@/types" using the barrel.
 */

// ── Shared API Types ───────────────────────────────────────

export interface ApiError {
  error: {
    message: string;
    detail: string | null;
  };
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  has_next: boolean;
}

// Domain types will be added as modules are implemented.
export type Nullable<T> = T | null;
export type Optional<T> = T | undefined;
