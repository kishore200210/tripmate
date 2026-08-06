/**
 * src/components/shared/Pagination.tsx
 *
 * Reusable prev/next pagination component with page count display.
 * Works with skip/limit (offset-based) pagination used by the backend.
 */

import { ChevronLeft, ChevronRight } from "lucide-react";
import { Button } from "@/components/ui/button";

interface PaginationProps {
  skip: number;
  limit: number;
  total: number;
  onSkipChange: (newSkip: number) => void;
}

export function Pagination({ skip, limit, total, onSkipChange }: PaginationProps) {
  const currentPage = Math.floor(skip / limit) + 1;
  const totalPages = Math.ceil(total / limit);

  if (totalPages <= 1) return null;

  const hasPrev = skip > 0;
  const hasNext = skip + limit < total;

  return (
    <div className="flex items-center justify-center gap-3 pt-4">
      <Button
        variant="outline"
        size="sm"
        onClick={() => onSkipChange(Math.max(0, skip - limit))}
        disabled={!hasPrev}
        aria-label="Previous page"
      >
        <ChevronLeft className="h-4 w-4" />
        Previous
      </Button>

      <span className="text-sm text-neutral-500">
        Page {currentPage} of {totalPages}
        <span className="ml-2 text-neutral-400">({total} total)</span>
      </span>

      <Button
        variant="outline"
        size="sm"
        onClick={() => onSkipChange(skip + limit)}
        disabled={!hasNext}
        aria-label="Next page"
      >
        Next
        <ChevronRight className="h-4 w-4" />
      </Button>
    </div>
  );
}
