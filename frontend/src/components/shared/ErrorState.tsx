/**
 * src/components/shared/ErrorState.tsx
 *
 * Generic error-state UI for use when API calls fail.
 */

import { AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";

interface ErrorStateProps {
  message?: string;
  onRetry?: () => void;
}

export function ErrorState({
  message = "Something went wrong. Please try again.",
  onRetry,
}: ErrorStateProps) {
  return (
    <div className="flex flex-col items-center justify-center rounded-xl border border-red-100 bg-red-50 py-16 px-8 text-center">
      <div className="mb-4 rounded-full bg-red-100 p-4">
        <AlertCircle className="h-8 w-8 text-red-500" />
      </div>
      <h3 className="text-lg font-semibold text-red-800">Error</h3>
      <p className="mt-1 max-w-sm text-sm text-red-600">{message}</p>
      {onRetry && (
        <Button variant="outline" className="mt-6 border-red-300 text-red-700 hover:bg-red-100" onClick={onRetry}>
          Try Again
        </Button>
      )}
    </div>
  );
}
